import asyncio
import time

class Cooldown:
    def __init__(self, interval: float):
        self.interval = interval
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def wait(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self._last = time.monotonic()
