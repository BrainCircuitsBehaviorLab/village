import ctypes
import os
import queue
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

# SCHED_FIFO priority for the audio thread.
RT_PRIORITY = 50

# Buffer target, in MILLISECONDS.
# This single number is BOTH:
#   - the stop() delay: audio already queued in the ring always plays
#   - the xrun margin: how long the worker can be starved before the ring dries
# They are the same thing. Bigger = safer stop-but-slower; smaller = the reverse.
# Onset does NOT depend on it (start_threshold is 1: playback starts on the
# first frame written), which is why it can be kept generously large.
BUFFER_MS = 20
PERIODS = 4


def get_sound_devices() -> list[str]:
    """Retrieves a list of available ALSA playback device strings.

    Returns entries like 'hw:2,0'. Use one of these as the SOUND_DEVICE setting.
    """
    devices: list[str] = []
    try:
        for i in alsaaudio.card_indexes():
            try:
                name = alsaaudio.card_name(i)[0]
            except Exception:
                name = ""
            devices.append(f"hw:{i},0 ({name})" if name else f"hw:{i},0")
    except Exception:
        pass
    return devices


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

        self.device = self._resolve_device(settings.get("SOUND_DEVICE"))

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
        self._status_path = self._status_path_for(self.device)

        # ONE persistent worker, created here and kept alive. RT priority is set
        # once, inside it. play() only sets an Event (a futex wake, tens of us),
        # so no thread creation, no dlopen and no syscall in the play path.
        self._shutdown = False
        self._playing = False  # True while the worker is inside write()
        self._play_event = threading.Event()
        self._warm_up()

        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

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

    @staticmethod
    def _status_path_for(device: str) -> str:
        """Kernel status file for an ALSA device string like 'hw:2,0'."""
        try:
            body = device.split(":", 1)[1]
            card, dev = (body.split(",") + ["0"])[:2]
            return f"/proc/asound/card{int(card)}/pcm{int(dev)}p/sub0/status"
        except Exception:
            return ""

    def _pcm_state(self) -> str:
        """Reads the PCM state from the kernel: PREPARED / RUNNING / XRUN / SETUP.

        The kernel is the source of truth here; guessing the state from our own
        bookkeeping is what makes this fragile. Cheap (~50 us) and only ever
        called from dead time.
        """
        if not self._status_path:
            return "?"
        try:
            with open(self._status_path) as f:
                line = f.readline().strip()
            return line.replace("state: ", "") if line else "?"
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

    @staticmethod
    def _resolve_device(name: Any) -> str:
        """Maps the SOUND_DEVICE setting to an ALSA device string.

        Accepts an ALSA string directly ('hw:2,0'), or best-effort matches a
        card-name substring against the system cards. Falls back to 'hw:0,0'.
        """
        if not name:
            return "hw:0,0"
        name = str(name)
        # Direct ALSA device string (possibly with a trailing "(...)" comment).
        token = name.split()[0]
        if token.startswith(("hw:", "plughw:", "default", "sysdefault", "dmix")):
            return token
        # Best-effort: match tokens of the setting against card names.
        try:
            words = [w.lower() for w in name.replace(":", " ").split() if len(w) > 2]
            for i in alsaaudio.card_indexes():
                cid, clong = alsaaudio.card_name(i)
                hay = f"{cid} {clong}".lower()
                if any(w in hay for w in words):
                    return f"hw:{i},0"
        except Exception:
            pass
        log.error(f"Could not resolve SOUND_DEVICE '{name}', defaulting to hw:0,0")
        return "hw:0,0"

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
        log.error("Sound device: timed out waiting for the PCM to be ready")

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
                if len(sound):
                    try:
                        self._write_sound(sound)
                    except alsaaudio.ALSAAudioError:
                        pass  # stop() dropped it mid-write
                    except Exception:
                        try:
                            error_queue.put_nowait(("sound", traceback.format_exc()))
                        except queue.Full:
                            pass
                    finally:
                        self._playing = False
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
        """Shuts down the worker and closes the PCM."""
        self._shutdown = True
        try:
            self.pcm.drop()  # unblock the worker if it is writing
        except Exception:
            pass
        self._play_event.set()  # wake it so it can see _shutdown and exit
        if self._worker is not None:
            self._worker.join(timeout=1.0)
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
