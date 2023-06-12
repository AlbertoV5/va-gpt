from torch import (
    Tensor,
    frombuffer,
    cat,
    sqrt,
    mean,
    square,
    max as tmax,
    log10,
)
from pyaudio import PyAudio

from app.types import AudioProcess, Broadcast
from app.audio.recorder import Recorder
from app.audio.capture import Capture
from app.audio.player import Player
from app.system.config import AudioConfig


class AudioChannel:
    """Load all audio configuration. Use open() to start generator process for recording input."""

    def __init__(self) -> None:
        pass

    def load(self, config: AudioConfig, channels: int = 1) -> None:
        # config
        self.config = config
        self.n_channels = channels
        # pyaudio
        self.frmt = self.config.channel.splformat
        self.audio = PyAudio()
        # system
        self.recorder = Recorder(self.config)
        self.player = Player()

    def start(self, broadcast: Broadcast, spls_max: int) -> AudioProcess:
        """Start live audio buffer stream with peak + rms gate.
        Peak values are measured on every buffer frame, while RMS only after
        the gate is closed (RMS of the whole capture).

        Args:
            broadcast (Broadcast): For broadcasting audio monitoring values.
            attend_spls (int): Limit sample position to count from when broadcasting.

        Yields:
            AudioProcess: Yields a sample position and an audio capture and
            expects to receive a new sample position.
            The capture holds a Tensor and audio metadata.
        """
        # Load constants from config.
        FS, DTYPE = self.config.channel.fullscale, self.config.channel.dtype
        PEAK, RMS = self.config.gate.dbpeak, self.config.gate.dbrms
        CHUNK, SR = self.config.channel.chunk, self.config.channel.samplerate
        REFRESH = int(SR / self.config.channel.refreshrate_hz)
        HOLD = int(self.config.gate.hold_sec * SR)
        TAIL = int(self.config.gate.tail_sec * SR)
        # Tensor to dBFS float, adds floor to avoid log(0).
        dbfs = lambda x: float(20 * log10(x + 1e-5))
        # spls tracks current samples, mon tracks last broadcast sample position.
        # latest tracks last peak position, marker tracks sample position at gate open.
        spls = mon = latest = marker = spls_max
        peak = rms = dbfs(Tensor([0]))
        peaks = []
        gate = False
        stream = self.audio.open(
            SR, self.n_channels, self.frmt, input=True, frames_per_buffer=CHUNK
        )
        # Flush first buffer read to avoid possible noise.
        stream.read(CHUNK, False)
        while True:
            x = frombuffer(stream.read(CHUNK, False), dtype=DTYPE) / FS
            peak = dbfs(tmax(abs(x)))
            peaks.append(peak)
            spls += CHUNK
            # Broadcast peak, rms, position in seconds, and gate status.
            if spls - mon > REFRESH:
                broadcast.mon(max(peaks), rms, max((spls_max - spls) / SR, 0), gate)
                mon = spls
                peaks = []
            # Open gate, reset main tensor and sample markers.
            if not gate and peak > PEAK:
                X = Tensor([])
                marker = latest = spls
                gate = True
            if gate:
                # Concatenate tensor while gate is open.
                X = cat((X, x), 0)
                # Update latest peak position.
                if peak > PEAK:
                    latest = spls
                # Close gate whenever current position minus latest peak position passes threshold.
                if spls - latest > HOLD:
                    gate = False
                    # Reduce size by HOLD sample size to exclude silence. Add tail to compensate.
                    size = X.shape[0] - HOLD + TAIL
                    # Calculate rms and peak dBFS values (only moment where RMS is calculated).
                    rms = dbfs(sqrt(mean(square(X[:size]))))
                    peak = dbfs(tmax(abs(X[:size])))
                    if rms < RMS:
                        continue
                    stream.stop_stream()
                    # Yields sample position at marker and capture, receive new sample position.
                    spls = mon = yield marker, Capture(
                        data=X[:size],
                        size=size,
                        sr=SR,
                        dbpeak=peak,
                        dbrms=rms,
                    )
                    # Exit process if outer process sent -1.
                    if spls == -1:
                        stream.close()
                        break
                    # Yield to continue with generator pattern.
                    yield marker
                    # Restart, same idea as above, flush first buffer read.
                    stream.start_stream()
                    stream.read(CHUNK, False)
