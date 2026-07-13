"""Text-seeded deterministic PRNG (XorShift64Star).

Carried in spirit from the LeapForge lineage: all ENGINE-level randomness
(task selection, split shuffles, tie-breaks, candidate ordering) flows through
SHA-256-seeded streams so the TASK SETS and control flow are reproducible per
seed. Model sampling is the one non-deterministic layer and is documented as
such -- a hosted LLM cannot be made bit-reproducible, unlike the pure-Python
substrate of the earlier expeditions.
"""

import hashlib

_MASK = (1 << 64) - 1


class XorShift64Star(object):
    def __init__(self, seed_text):
        d = hashlib.sha256(str(seed_text).encode("utf-8")).digest()
        self.state = int.from_bytes(d[:8], "big") or 0x9E3779B97F4A7C15

    def u64(self):
        x = self.state
        x ^= x >> 12
        x ^= (x << 25) & _MASK
        x ^= x >> 27
        self.state = x
        return (x * 2685821657736338717) & _MASK

    def below(self, n):
        return self.u64() % n if n > 0 else 0

    def unit(self):
        return self.u64() / float(1 << 64)

    def choice(self, seq):
        return seq[self.below(len(seq))]

    def shuffle(self, seq):
        """In-place Fisher-Yates."""
        for i in range(len(seq) - 1, 0, -1):
            j = self.below(i + 1)
            seq[i], seq[j] = seq[j], seq[i]
        return seq
