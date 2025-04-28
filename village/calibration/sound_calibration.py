from threading import Thread


class SoundCalibration:
    def __init__(
        self, speaker: int, gain: float, sound: int, freq: int, duration: float
    ) -> None:
        self.speaker = speaker
        self.gain = gain
        self.sound = sound
        self.freq = freq
        self.duration = duration

    def run(self) -> None:

        pass

    #         if self.sound == 0: # sinusoidal
    #             sound = tone_generator(
    #                 duration=self.duration,
    #                 amplitude=self.gain,
    #                 frequency=self.freq,
    #                 ramp_time=0.005,
    #                 samplerate=sound_device.samplerate,
    #             )
    #         elif self.sound == 1: # white noise
    #             sound = whitenoise_generator(
    #                 duration=self.duration,
    #                 amplitude=self.gain,
    #                 samplerate=sound_device.samplerate,
    #             )
    #         else:
    #             sound = None

    #         if self.speaker == 0:
    #             sound_device.load(sound, None)
    #         else:
    #             sound_device.load(None, sound)

    #         sound_device.play()
    #         time.sleep(self.duration + 1)
    #         sound_device.stop()

    def run_in_thread(self, daemon=True) -> None:
        self.process = Thread(target=self.run, daemon=daemon)
        self.process.start()
        return


# sound = tone_generator(
#     duration=0.1, amplitude=0.01, frequency=6000, ramp_time=0.005, samplerate=44100
# )
