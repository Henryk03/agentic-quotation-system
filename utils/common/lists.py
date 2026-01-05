
import asyncio
from typing import Any

class SafeAsyncList:
    """
    ADT for a thread-safe asynchronous list.
    """


    def __init__(self):
        self._list = []
        self._lock = asyncio.Lock()


    async def add(self, item: Any) -> None:
        """
        Safely append an item to the list.

        This method ensures that only one coroutine at a 
        time can modify the underlying list, preventing race
        conditions or data corruption.

        Args:
            item (Any):
                A generic item of any type to be inserted into
                the underlying list.
        """

        async with self._lock:
            self._list.append(item)