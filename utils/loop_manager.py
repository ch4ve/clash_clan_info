# Conteúdo de utils/loop_manager.py

import asyncio
import threading

class AsyncLoopManager:
    """
    Gerencia um único event loop de asyncio rodando em uma thread de background.
    Isso previne conflitos ao usar bibliotecas async em frameworks sync como o Streamlit.
    """
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run_coroutine(self, coro):
        """
        Executa uma corotina de forma segura a partir de uma thread síncrona.
        """
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

# Cria uma instância única (singleton) do gerente para ser usada em todo o app
loop_manager = AsyncLoopManager()
