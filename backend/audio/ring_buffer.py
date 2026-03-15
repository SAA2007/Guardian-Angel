"""Guardian Angel -- Audio Ring Buffer

Holds 1 second of pre-buffered audio before output, enabling
retroactive mute when detection triggers after audio has
already started playing.

Usage:
    buf = RingBuffer(sample_rate=44100, channels=2, chunk_size=1024)
    buf.push(chunk)
    buf.mute_last(3)         # silence last 3 chunks
    all_chunks = buf.get_all()
"""

import collections


class RingBuffer:
    """Fixed-size ring buffer for audio chunks.

    Holds exactly enough chunks to cover ``buffer_seconds``
    (default 1 second) of audio.  When full, oldest chunks
    are silently discarded as new ones are pushed.
    """

    def __init__(self, sample_rate, channels, chunk_size,
                 buffer_seconds=1.0):
        """Initialise ring buffer.

        Args:
            sample_rate: audio sample rate in Hz.
            channels: number of audio channels.
            chunk_size: frames per chunk.
            buffer_seconds: seconds of audio to hold (default 1.0).
        """
        self._sample_rate = sample_rate
        self._channels = channels
        self._chunk_size = chunk_size

        # How many chunks fit in buffer_seconds
        chunks_per_sec = sample_rate / chunk_size
        self._maxlen = max(1, int(chunks_per_sec * buffer_seconds))

        self._buffer = collections.deque(maxlen=self._maxlen)

    def push(self, chunk):
        """Add a chunk to the buffer.

        Args:
            chunk: raw PCM bytes.
        """
        self._buffer.append(chunk)

    def get_all(self):
        """Return a copy of all chunks, oldest first.

        Returns:
            list[bytes]: copy of buffered chunks.
        """
        return list(self._buffer)

    def mute_last(self, n_chunks):
        """Replace the last *n_chunks* with zeroed bytes.

        Used for retroactive mute — silences audio that was
        buffered before a trigger was detected.

        Args:
            n_chunks: number of recent chunks to silence.
        """
        buf = self._buffer
        total = len(buf)
        start = max(0, total - n_chunks)

        for i in range(start, total):
            original = buf[i]
            buf[i] = b"\x00" * len(original)

    def clear(self):
        """Empty the buffer entirely."""
        self._buffer.clear()

    def is_full(self):
        """True when buffer has reached its maximum length.

        Returns:
            bool: True if at capacity.
        """
        return len(self._buffer) >= self._maxlen

    @property
    def maxlen(self):
        """Maximum number of chunks this buffer holds."""
        return self._maxlen

    @property
    def current_length(self):
        """Current number of chunks in buffer."""
        return len(self._buffer)
