import wave

from .tones import Tone, Sine

try:
    import pyaudio

    playback = True
except:
    playback = False


class Melody(object):
    """
    Melody generator for a given waveform, sample rate and bit depth.

    This class takes the given "code"--an iterable with tuples of <frequency>
    and <duration> (in milliseconds)--and renders it into audio samples from
    the given waveform (a sine wave by default).

    It contains a very simple wav-file writer that can output the sequence of
    frequencies into a wav-file.

    See also:

    See the tones module for available tone generators and the selcall module
    for generating frequencies for a variety of selcall squelch codes.
    """

    def __init__(self, code, waveform=Sine, rate=44100, bits=16, signed=True):
        if not issubclass(waveform, Tone):
            raise ValueError(
                "The waveform parameter must be a class derived from tones.Tone")

        self.code = code
        self.waveform = waveform
        self.rate = rate
        self.bits = bits
        self.signed = signed

    def __iter__(self):
        """
        This method allows you to run a Melody object as a generator of audio
        samples, it will yield values as samples from the selcted waveform in
        the frequency and duration specified by the "code" until it is
        exhausted.
        """
        for frequency, duration in self.code:
            waveform = iter(
                self.waveform(frequency, self.rate, self.bits, signed=self.signed))

            frames = int((duration / 1000) * self.rate)

            for _ in range(0, frames):
                yield int(next(waveform))

    def wave(self, fn, attennuation=0):
        """
        This runs the generator in __iter__ and produces a wav file
        """
        self.signed = True

        with wave.open(fn, 'wb') as fp:
            fp.setnchannels(1)
            fp.setsampwidth(self.bits // 8)
            fp.setframerate(self.rate)
            fp.setcomptype('NONE', 'Not Compressed')

            for frame in self:
                frame //= attennuation
                fp.writeframesraw(
                    frame.to_bytes(self.bits // 8, 'little', signed=self.signed))

            fp.close()

    def play(self, attennuation=0):
        """
        This runs the generator in __iter__ and plays it back using pyaudio (if available)
        Note that this method does not do streaming, because pyaudio expects its input to be
        finite (it runs len()).
        """

        if not playback:
            quit("Can't play back, no pyaudio found")

        data = bytes()
        for frame in self:
            frame //= attennuation
            data += frame.to_bytes(self.bits // 8, 'little', signed=self.signed)

        pa = pyaudio.PyAudio()

        stream = pa.open(format=pa.get_format_from_width(self.bits // 8, self.signed),
                         channels=1,
                         rate=self.rate,
                         output=True)

        stream.write(data)

        stream.stop_stream()
        stream.close()

        pa.terminate()
