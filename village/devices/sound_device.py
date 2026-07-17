import ctypes
import os
import queue
import re
import threading
import time
import traceback
from math import gcd
from typing import Any

import alsaaudio
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

from village.classes.enums import Active
from village.classes.null_classes import NullSoundDevice
from village.scripts.error_queue import error_queue
from village.scripts.log import log
from village.settings import settings

# SCHED_FIFO priority for the audio thread. Deliberately low: threaded IRQ
# handlers run at ~50, so anything above that can starve interrupts (USB, timers,
# SD card) and freeze the machine if the thread is slow to yield. Audio daemons
# use 5-20. Higher is not faster -- it only decides who goes first.
RT_PRIORITY = 20

# snd_pcm_state() -> name. Built from whatever PCM_STATE_* the module exposes, so
# it does not depend on us guessing the constant names. Asking libasound beats
# reading /proc/asound/.../status: no 1 kHz polling of a kernel file, and nothing
# pokes the driver's proc handler while another thread is writing to the PCM.
PCM_STATES = {
    getattr(alsaaudio, _n): _n[len("PCM_STATE_") :]
    for _n in dir(alsaaudio)
    if _n.startswith("PCM_STATE_")
}

# Buffer target, in MILLISECONDS. Frames are meaningless across sample rates:
# 512x4 is 21 ms at 96 kHz but 46 ms at 44.1 kHz. periodsize is derived from this
# and the actual rate, so the behaviour is the same whatever SAMPLERATE is set.
#
# This single number is BOTH:
#   - the stop() delay: audio already queued in the ring always plays
#   - the xrun margin: how long the worker can be starved before the ring dries
# They are the same thing. Bigger = safer stop-but-slower; smaller = the reverse.
# Onset does NOT depend on it (start_threshold is 1: playback starts on the
# first frame written), which is why it can be kept generously large.
BUFFER_MS = 20
PERIODS = 4


def get_sound_devices() -> list[str]:
    """Lists the sound cards, by ID, for the SOUND_DEVICE setting.

    Returns entries like 'DACPro (RPi DAC Pro)'. The ID is what gets stored,
    NOT the card index: indexes are handed out in the order the kernel registers
    the cards, so a kernel update or a config.txt change can renumber them and
    the setting would then point at the wrong card. The ID comes from the driver
    and does not move.
    """
    devices: list[str] = []
    try:
        for i in alsaaudio.card_indexes():
            try:
                cid, longname = alsaaudio.card_name(i)
            except Exception:
                continue
            cid = str(cid).strip()
            longname = (longname or "").strip()
            # Card names contain spaces ('RPi DAC Pro'), and name and longname
            # are often identical; do not print it twice.
            devices.append(
                f"{cid} ({longname})" if longname and longname != cid else cid
            )
    except Exception:
        pass
    return devices


def match_sound_device_setting(name: Any, possible_values: list[str]) -> str | None:
    """Matches a saved SOUND_DEVICE value to one of possible_values.

    SOUND_DEVICE may have been saved in a format older than what
    get_sound_devices() returns today: a bare card ID, an explicit 'hw:N,D',
    or the current 'ID (longname)'. Used by the settings UI so a value saved
    under an old format still selects the right entry in the dropdown instead
    of silently falling back to whichever one happens to be first.

    Returns:
        str | None: The matching entry from possible_values, or None if
        nothing matches.
    """
    text = str(name or "").strip()
    if not text:
        return None
    token = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip()

    m = re.match(r"^(?:plug)?hw:(\d+)(?:,\d+)?$", token)
    if m:
        card = int(m.group(1))
        try:
            indexes = alsaaudio.card_indexes()
            if card in indexes:
                pos = indexes.index(card)
                if pos < len(possible_values):
                    return possible_values[pos]
        except Exception:
            pass
        return None

    for entry in possible_values:
        if re.sub(r"\s*\([^)]*\)\s*$", "", entry).strip() == token:
            return entry
    for entry in possible_values:
        if re.sub(r"\s*\([^)]*\)\s*$", "", entry).strip().lower() == token.lower():
            return entry
    return None


class SoundDevice:
    """Handles audio playback using ALSA directly (pyalsaaudio).

    Same interface as the sounddevice version, but writes to the PCM with
    writei (RW_INTERLEAVED), so playback starts fast (write into an empty PCM)
    and stop() can cut it immediately with drop() from another thread -- which
    the sounddevice/PortAudio path could not do on this DAC because it uses mmap.

    Attributes:
        samplerate (int): Audio sample rate.
        channels (int): Number of audio channels.
        periodsize (int): Frames per ALSA transfer (latency grain).
        periods (int): Number of periods in the ring buffer.
        device (str): ALSA device string, e.g. 'hw:2,0'.
        error (str): Last error message.
    """

    def __init__(self) -> None:
        """Initializes the SoundDevice with settings and opens the PCM."""
        self.samplerate = int(settings.get("SAMPLERATE"))
        self.channels = 2
        self.periods = PERIODS
        self.periodsize = self._pick_periodsize(self.samplerate)
        self.error = ""

        self.device, self.card_index = self._resolve_device(
            settings.get("SOUND_DEVICE")
        )

        # S32_LE: the PCM512x is 32-bit. hw: device -> writei, no plug layer.
        # rate is REQUIRED: without it pyalsaaudio defaults to 44100, so a tone
        # generated at self.samplerate plays at the wrong speed and pitch.
        self.pcm = alsaaudio.PCM(
            type=alsaaudio.PCM_PLAYBACK,
            mode=alsaaudio.PCM_NORMAL,
            rate=self.samplerate,
            channels=self.channels,
            format=alsaaudio.PCM_FORMAT_S32_LE,
            periodsize=self.periodsize,
            periods=self.periods,
            device=self.device,
        )
        info = self.pcm.info()
        log.info(
            f"Sound device '{self.device}': rate={info['rate']} "
            f"period_size={info['period_size']} "
            f"buffer_size={info['buffer_size']} "
            f"({1000 * info['buffer_size'] / info['rate']:.2f} ms buffered)"
        )
        if info["rate"] != self.samplerate:
            log.error(
                f"Sound device granted rate {info['rate']} Hz but "
                f"{self.samplerate} Hz was requested; pitch/duration will be wrong."
            )

        self._sound: np.ndarray = np.empty((0, 2), dtype=np.int32)
        self._stop_flag = False  # asks the worker to fade out
        self._lock = threading.Lock()

        # One period of silence, used to pre-pay the implicit prepare (~11.5 ms)
        # during dead time. Measured: a write on an XRUN'd PCM does the prepare
        # and writes NOTHING, leaving it PREPARED; the next write then costs
        # ~0.04 ms and starts the hardware at once. PREPARED survives dead time.
        self._silence = np.zeros(
            (info["buffer_size"], self.channels), dtype=np.int32
        ).tobytes()
        # Time for the ring buffer to drain after a write, so the PCM reaches
        # XRUN before we prime it.
        self.buffer_size = info["buffer_size"]
        self._drain_s = info["buffer_size"] / info["rate"] + 0.003

        # Raised-cosine ramp applied to every sound (onset and offset) and used
        # to fade out on stop(). Cosine, not linear: a linear ramp keeps the
        # amplitude continuous but its slope jumps at the corners, and that
        # discontinuity is a broadband transient -- an audible click.
        # 0 ms disables ramping entirely.
        self.ramp_ms = int(settings.get("SOUND_RAMP_MS"))
        self._ramp_frames = int(self.ramp_ms * self.samplerate / 1000)

        # ONE persistent worker, created here and kept alive. RT priority is set
        # once, inside it. play() only sets an Event (a futex wake, tens of us),
        # so no thread creation, no dlopen and no syscall in the play path.
        self._shutdown = False
        self._playing = False  # True while the worker is inside write()
        self._play_deadline = 0.0  # monotonic time by which playback must be done
        self._play_event = threading.Event()
        if not PCM_STATES:
            log.error(
                "pyalsaaudio exposes no PCM_STATE_* constants: the PCM state "
                "cannot be read, so the device cannot be re-armed and every "
                "play() will pay the ~11 ms prepare."
            )

        self._warm_up()

        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
        self._watchdog = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog.start()

    def _warm_up(self) -> None:
        """Plays one silent buffer so the DAC wakes up now, not on the first sound.

        The first playback after opening the PCM is what powers the DAC up (ASoC
        brings the codec out of standby, the PLL locks, it unmutes). That takes a
        few ms during which ALSA is already consuming frames but nothing comes out
        yet, so the first real stimulus would lose its onset -- missing its fade-in
        it restarts mid-waveform at full amplitude, which clicks, and it sounds
        short. Paying it here with silence costs ~35 ms of startup and nobody
        hears it. Runs before the worker thread exists, so nothing races on the PCM.
        """
        try:
            self.pcm.write(self._silence)
        except alsaaudio.ALSAAudioError:
            pass
        time.sleep(self._drain_s)
        self._rearm()

    @staticmethod
    def _pick_periodsize(rate: int) -> int:
        """periodsize giving a BUFFER_MS ring at this rate, as a power of two.

        Powers of two are what ALSA and the DMA are happiest with. Examples:
        96 kHz -> 512 (2048 frames, 21.3 ms); 48 kHz -> 256 (1024, 21.3 ms);
        44.1 kHz -> 256 (1024, 23.2 ms); 192 kHz -> 1024 (4096, 21.3 ms).
        """
        ideal = BUFFER_MS / 1000 * rate / PERIODS
        size = 2 ** round(np.log2(max(ideal, 16)))
        return int(min(max(size, 32), 4096))

    def _pcm_state(self) -> str:
        """PCM state from libasound: PREPARED / RUNNING / XRUN / SETUP / ...

        The kernel is still the source of truth (this is snd_pcm_state), but asked
        through the API instead of by reading /proc.
        """
        try:
            return PCM_STATES.get(self.pcm.state(), "?")
        except Exception:
            return "?"

    def _rearm(self) -> None:
        """Leaves the PCM in PREPARED so the next play() write starts instantly.

        Pays the ~11.5 ms prepare here, in dead time, instead of in play().
        Self-correcting: it checks the real state and moves it forward, so it
        works from RUNNING (wait to drain), XRUN (one prime) or SETUP (a prime
        plays one silent period, then drains, then a second prime).
        """
        for _ in range(4):
            state = self._pcm_state()
            if state == "PREPARED":
                return
            if state == "RUNNING":
                time.sleep(self._drain_s)  # let it finish, then it XRUNs
                continue
            try:
                self.pcm.write(self._silence)  # XRUN -> PREPARED (writes nothing)
            except alsaaudio.ALSAAudioError:
                pass
            except Exception:
                return

        # Never reached PREPARED. Not fatal, but every play() will now pay the
        # ~11 ms prepare, silently, so say so: SUSPENDED (needs snd_pcm_resume,
        # after a system suspend) and DISCONNECTED (card gone) end up here.
        log.error(
            f"Sound device: could not re-arm the PCM, stuck in "
            f"'{self._pcm_state()}'; the next play() will be slow."
        )

    @staticmethod
    def _resolve_device(name: Any) -> tuple[str, int]:
        """Maps the SOUND_DEVICE setting to an ALSA device string and card index.

        Accepts what get_sound_devices() lists ('DACPro (RPi DAC Pro)'), a bare
        card ID ('DACPro'), or an explicit 'hw:2,0'. The index is resolved from
        the ID at every start, so it survives cards being renumbered.

        Returns:
            tuple[str, int]: ('hw:N,D', N).
        """
        text = str(name or "").strip()
        # Card names contain spaces ('RPi DAC Pro'), so splitting on whitespace
        # would keep only 'RPi'. Strip the trailing ' (longname)' instead.
        token = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip()

        # Explicit hw:N,D (kept working, but the index is frozen in the setting).
        m = re.match(r"^(?:plug)?hw:(\d+)(?:,(\d+))?$", token)
        if m:
            card = int(m.group(1))
            return f"hw:{card},{int(m.group(2) or 0)}", card

        # Card ID, exact then case-insensitive.
        try:
            cards = {}
            for i in alsaaudio.card_indexes():
                try:
                    cards[alsaaudio.card_name(i)[0]] = i
                except Exception:
                    continue
            if token in cards:
                return f"hw:{cards[token]},0", cards[token]
            for cid, i in cards.items():
                if cid.lower() == token.lower():
                    return f"hw:{i},0", i
            if cards:
                cid, i = next(iter(cards.items()))
                log.error(
                    f"SOUND_DEVICE '{text}' matches no card. Available: "
                    f"{', '.join(cards)}. Falling back to '{cid}'."
                )
                return f"hw:{i},0", i
        except Exception:
            pass

        log.error(f"Could not resolve SOUND_DEVICE '{text}'; falling back to hw:0,0")
        return "hw:0,0", 0

    @staticmethod
    def _set_realtime_priority() -> None:
        """Best-effort SCHED_FIFO for THIS thread only (needs privileges).

        Uses the thread's own TID so only the audio thread goes real-time, not
        the whole PyQt application. Passing 0 would raise the entire process,
        which would defeat the point (and can starve the GUI). Silently ignored
        if not permitted. Call this from inside the audio thread.
        """
        try:
            # SYS_gettid on aarch64 is 178; returns this thread's kernel TID.
            tid = ctypes.CDLL("libc.so.6", use_errno=True).syscall(178)
            os.sched_setscheduler(tid, os.SCHED_FIFO, os.sched_param(RT_PRIORITY))  # type: ignore[attr-defined]
        except (PermissionError, OSError, AttributeError):
            pass

    def _pad_to_period(self, vec: np.ndarray) -> np.ndarray:
        """Pad a (frames, 2) array up to a whole number of periods with silence."""
        r = len(vec) % self.periodsize
        if r:
            pad = np.zeros((self.periodsize - r, self.channels), dtype=np.int32)
            vec = np.vstack((vec, pad))
        return np.ascontiguousarray(vec)

    @staticmethod
    def _ramp_curve(n: int) -> np.ndarray:
        """Raised-cosine fade-in curve of exactly n frames, 0 -> 1, shape (n, 1).

        Always built at the length needed. Slicing a longer curve would start or
        end at a mid amplitude, which is a step -- the click we are avoiding.
        """
        x = np.arange(n) / n
        return (0.5 * (1 - np.cos(np.pi * x)))[:, np.newaxis]

    def _wait_ready(self, timeout: float = 1.0) -> None:
        """Blocks until nothing is playing AND the PCM is armed (PREPARED).

        Waiting for _playing alone is not enough: the worker still has to re-arm,
        and a play() landing in that window would be delayed. Waiting here, in
        load(), keeps that cost out of play(), which is the time-critical call.
        """
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < timeout:
            if not self._playing and self._pcm_state() == "PREPARED":
                return
            time.sleep(0.001)
        log.error(
            f"Sound device: timed out waiting for the PCM to be ready "
            f"(state='{self._pcm_state()}', playing={self._playing}). If playing "
            f"is True the audio thread is stuck inside write(): the DAC most "
            f"likely did not restart. Dump the threads with: "
            f"sudo py-spy dump --pid {os.getpid()}"
        )

    def _apply_ramps(self, stereo: np.ndarray) -> np.ndarray:
        """Fades a float (frames, 2) array in at the start and out at the end.

        Clamped so the two ramps never overlap on very short sounds.
        """
        if self._ramp_frames <= 0 or len(stereo) == 0:
            return stereo
        r = min(self._ramp_frames, len(stereo) // 2)
        if r <= 0:
            return stereo
        up = self._ramp_curve(r)
        stereo[:r] *= up
        stereo[-r:] *= up[::-1]
        return stereo

    def load(self, left: Any, right: Any) -> None:
        """Stops any sound playing, then loads new data ready to be played.

        load() cuts whatever is sounding (stop() is idempotent, so it is free if
        nothing is) and waits until the device is armed again, so the following
        play() starts immediately. Expect load() to block for roughly the stop
        delay plus the re-arm (tens of ms) when it interrupts a sound; it does
        not block when idle.

        Args:
            left (Any): Left channel data (array-like, float in [-1, 1]).
            right (Any): Right channel data (array-like, float in [-1, 1]).

        Raises:
            ValueError: If inputs are invalid or lengths differ.
        """
        if left is None and right is not None:
            left = np.zeros(len(right))
        elif right is None and left is not None:
            right = np.zeros(len(left))
        elif left is None and right is None:
            raise ValueError("Sound error: Both vectors left and right are None.")

        if len(left) != len(right):
            raise ValueError(
                "Sound error: Left and right vectors must have same length."
            )

        self.stop()  # cut whatever is playing; a no-op if idle
        # The numpy work below overlaps the fade-out, so the wait is mostly free.
        vec = self.create_sound_vec(left, right)
        vec = self._pad_to_period(vec)
        self._wait_ready()  # fade and re-arm done: the next play() is instant
        with self._lock:
            self._sound = vec

    def load_wav(self, file: str) -> None:
        """Loads a WAV file, ready to be played.

        Args:
            file (str): Filename of the WAV file in the media directory.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If sample rate mismatches or channel count is unsupported.
        """
        self.stop()
        media_directory = settings.get("MEDIA_DIRECTORY")
        path = os.path.join(media_directory, file)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' does not exist.")

        samplerate, data = wavfile.read(path)
        if samplerate != self.samplerate:
            raise ValueError(
                f"Expected samplerate {self.samplerate}, but got {samplerate}."
            )

        # Normalize to float32 in range [-1.0, 1.0] if needed
        if data.dtype != np.float32:
            if np.issubdtype(data.dtype, np.integer):
                max_val = np.iinfo(data.dtype).max
                data = data.astype(np.float32) / max_val
            else:
                data = data.astype(np.float32)

        if data.ndim == 1:
            left = right = data
        elif data.shape[1] == 2:
            left, right = data[:, 0], data[:, 1]
        else:
            raise ValueError("Unsupported number of channels in WAV file.")

        self.load(left, right)

    def _write_sound(self, sound: np.ndarray) -> None:
        """Writes the sound, then a silent tail; fades out if stop() asks.

        With ramping off this is ONE write of the whole sound: a single Python
        call, libasound feeds the periods in C.

        With ramping on the sound is written in period-sized chunks so the stop
        flag can be checked between them: to fade out we must keep writing
        (dropping would throw the audio away), so stop() is no longer instant.
        The audio already queued in the ring (up to buffer_size) plays no matter
        what, so the sound dies roughly buffer + ramp_ms after stop().
        """
        if self._ramp_frames <= 0:
            self.pcm.write(sound.tobytes())
        else:
            n = len(sound)
            pos = 0
            while pos < n:
                if self._stop_flag:
                    r = min(self._ramp_frames, n - pos)
                    if r > 0:
                        # Starts at full amplitude, so it joins what is already
                        # queued with no discontinuity, and decays to zero.
                        seg = sound[pos : pos + r] * self._ramp_curve(r)[::-1]
                        self.pcm.write(
                            self._pad_to_period(seg.astype(np.int32)).tobytes()
                        )
                    break
                end = min(pos + self.periodsize, n)
                self.pcm.write(sound[pos:end].tobytes())
                pos = end

        # Silent tail: ALSA's ring is circular and nobody clears it, so on the
        # underrun the DMA would replay whatever bytes are still in it (the
        # previous tone). A whole buffer of zeros leaves it clean.
        self.pcm.write(self._silence)

    def _watchdog_loop(self) -> None:
        """Rescues a playback that never comes back.

        pcm.write() blocks with NO timeout: if the DMA stalls, the audio thread
        stays inside C for ever, _playing stays True and the device is dead until
        the process restarts. Nothing in that thread can notice -- it is blocked.
        So watch from outside and drop the PCM: a drop from another thread
        interrupts a blocking writei (that is exactly how stop() works), the write
        raises, and the worker re-arms and carries on. The sound is lost, but the
        device survives, which for a 24/7 system is the whole point.
        """
        while not self._shutdown:
            time.sleep(0.2)
            deadline = self._play_deadline
            if self._playing and deadline and time.monotonic() > deadline:
                self._play_deadline = 0.0
                log.error(
                    f"Sound device: playback overran by "
                    f"{time.monotonic() - deadline:.1f} s "
                    f"(state='{self._pcm_state()}'): the audio thread is stuck "
                    f"inside write(). Dropping the PCM to recover; this sound is "
                    f"lost. PID {os.getpid()} if you want py-spy."
                )
                try:
                    self.pcm.drop()
                except Exception:
                    pass

    def _worker_loop(self) -> None:
        """Persistent worker: plays on demand and re-arms the PCM in dead time.

        Created once and kept alive, so play() never pays thread creation nor
        the RT-priority setup (dlopen + syscall) -- those happen once, here.
        After every playback (or after stop() cut it) the PCM is left PREPARED,
        so the next play() write costs ~0.04 ms instead of ~11.5 ms.
        The 0.5 s timeout makes this self-healing: whatever state the PCM ends
        up in, it gets re-armed shortly after.
        """
        self._set_realtime_priority()
        while True:
            self._play_event.wait(timeout=0.5)
            if self._shutdown:
                break
            if self._play_event.is_set():
                self._play_event.clear()
                sound = self._sound
                try:
                    if len(sound):
                        self._write_sound(sound)
                except alsaaudio.ALSAAudioError:
                    pass  # stop()/watchdog dropped it mid-write
                except Exception:
                    try:
                        error_queue.put_nowait(("sound", traceback.format_exc()))
                    except queue.Full:
                        pass
                finally:
                    # OUTSIDE the len() check: if this is skipped, _playing sticks
                    # True for ever, and from then on every play() is ignored and
                    # every load() times out. The device would be dead until restart.
                    self._playing = False
                    self._play_deadline = 0.0
            self._rearm()

    def play(self) -> None:
        """Triggers playback: just wakes the worker. No drop() here.

        The PCM is already PREPARED (re-armed in dead time), so the worker's
        write starts the hardware immediately. Dropping here would put the PCM
        back in SETUP and make the write pay the ~11.5 ms prepare again.
        """
        with self._lock:
            if not len(self._sound):
                return
            if self._playing:
                # Already playing: ignore. Deterministic on purpose -- _playing is
                # set HERE, by the caller, not by the worker, so the outcome never
                # depends on whether the worker happened to wake up first.
                log.info("Sound device: play() ignored, a sound is already playing")
                return
            self._playing = True
            # How long this sound may legitimately take: its own duration, plus
            # the ring it has to drain, plus a second of slack. Past that, the
            # write is not slow, it is stuck.
            self._play_deadline = (
                time.monotonic()
                + len(self._sound) / self.samplerate
                + self._drain_s
                + 1.0
            )
            self._stop_flag = False
            self._play_event.set()

    def stop(self) -> None:
        """Stops playback immediately. A no-op if nothing is playing.

        Idempotent on purpose: dropping an idle PCM would move it out of
        PREPARED into SETUP, and the next play() would pay the ~11.5 ms prepare
        again. So a second stop(), or a stop() with no sound running, does
        nothing and leaves the PCM armed.
        """
        if not self._playing:
            return
        if self._ramp_frames <= 0:
            try:
                self.pcm.drop()  # instant (18 us) but abrupt: a step -> click
            except alsaaudio.ALSAAudioError:
                pass
        else:
            self._stop_flag = True  # worker fades out; not instant, but clean

    def shutdown(self) -> None:
        """Shuts down the worker and closes the PCM, but never closes it in use.

        Tolerates a half-built object: if __init__ raised (the PCM failed to open,
        say), __del__ still calls this and the attributes may not exist yet.

        Closing a PCM while another thread sits inside pcm.write() frees, from C,
        a structure that thread is still using. That can leave the driver's
        substream dangling -- bad enough that merely reading its /proc status can
        then take the kernel down. So if the worker will not join, the handle is
        deliberately leaked: process exit lets the kernel tear it down safely,
        which is far cheaper than corrupting the driver.
        """
        self._shutdown = True
        self._stop_flag = True  # make a chunked write stop feeding
        pcm = getattr(self, "pcm", None)
        if pcm is None:
            return
        try:
            pcm.drop()  # unblock the worker if it is writing
        except Exception:
            pass
        event = getattr(self, "_play_event", None)
        if event is not None:
            event.set()  # wake it so it can see _shutdown and exit

        if getattr(self, "_worker", None) is not None:
            self._worker.join(timeout=2.0)
            if self._worker.is_alive():
                log.error(
                    "Sound device: the audio thread did not finish; leaving the "
                    "PCM open on purpose (closing it while in use can crash the "
                    "driver). It is released when the process exits."
                )
                return

        # Join the watchdog too: it only sleeps in a loop (never blocks on the
        # PCM), so this is quick. Without it, a drop() fired from the watchdog
        # could race with the close() below -- two threads touching the same
        # PCM handle at once, which is the exact hazard this method exists to
        # avoid.
        watchdog = getattr(self, "_watchdog", None)
        if watchdog is not None:
            watchdog.join(timeout=0.5)

        try:
            self.pcm.close()
        except Exception:
            pass

    def __del__(self) -> None:
        """Destructor to ensure shutdown."""
        self.shutdown()

    def get_sound_from_wav(
        self, file: str, gain: float
    ) -> tuple[np.ndarray, np.ndarray]:
        media_directory = settings.get("MEDIA_DIRECTORY")
        path = os.path.join(media_directory, file)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' does not exist.")

        samplerate, data = wavfile.read(path)
        if np.issubdtype(data.dtype, np.integer):
            max_val = np.iinfo(data.dtype).max
            data = data.astype(np.float32) / max_val
        elif data.dtype != np.float32:
            data = data.astype(np.float32)

        if samplerate != self.samplerate:
            g = gcd(samplerate, self.samplerate)
            data = resample_poly(data, self.samplerate // g, samplerate // g, axis=0)
            data = data.astype(np.float32)

        if data.ndim == 1:
            left = right = data
        elif data.shape[1] == 2:
            left, right = data[:, 0], data[:, 1]
        else:
            raise ValueError("Unsupported number of channels in WAV file.")

        if gain != 1.0:
            if not 0.0 <= gain <= 1.0:
                raise ValueError(f"gain must be between 0 and 1, got {gain}.")
            left = left * gain
            right = right * gain

        return left, right

    def create_sound_vec(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Interleaves, ramps and converts float [-1, 1] channels into int32 stereo.

        The SOUND_RAMP_MS raised-cosine fade is applied here, so every sound
        that goes through load()/load_wav() gets it automatically.

        Args:
            left (np.ndarray): Left channel data (float in [-1, 1]).
            right (np.ndarray): Right channel data (float in [-1, 1]).

        Returns:
            np.ndarray: Interleaved contiguous int32 stereo data (frames, 2).
        """
        left = np.asarray(left, dtype=np.float64)
        right = np.asarray(right, dtype=np.float64)
        stereo = np.column_stack((left, right))
        stereo = self._apply_ramps(stereo)
        np.clip(stereo, -1.0, 1.0, out=stereo)
        stereo_i32 = (stereo * (2**31 - 1)).astype(np.int32)
        return np.ascontiguousarray(stereo_i32)


def get_sound_device() -> SoundDevice | NullSoundDevice:
    """Factory function to initialize the SoundDevice.

    Returns:
        SoundDevice | NullSoundDevice: An initialized SoundDevice or
        NullSoundDevice if disabled or initialization fails.
    """
    if settings.get("USE_SOUNDCARD") == Active.OFF:
        return NullSoundDevice()
    else:
        try:
            sound_device = SoundDevice()
            log.info("Sound device successfully initialized")
            return sound_device
        except Exception:
            log.error(
                "Could not initialize sound device", exception=traceback.format_exc()
            )
            return NullSoundDevice()


sound_device = get_sound_device()
