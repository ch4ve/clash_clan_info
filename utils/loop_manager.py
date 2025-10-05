# Conteúdo de utils/loop_manager.py
import asyncio
import threading

class AsyncLoopManager:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    def run_coroutine(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()
loop_manager = AsyncLoopManager()
