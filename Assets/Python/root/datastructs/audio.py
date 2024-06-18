from io import BytesIO
import soundfile as sf

class Audio:
    def __init__(self, bytes):
        io = BytesIO(bytes)
        self.data, self.samplerate = sf.read(io, dtype='float32')
        if len(self.data.shape) == 2:
            self.data = self.data[:, 0]

    def to_bytes(self) -> bytes:
        io = BytesIO()
        sf.write(io, self.data, self.samplerate, format='WAV')
        return io.getvalue()
