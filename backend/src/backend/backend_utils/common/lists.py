
import asyncio
from typing import Any


class SafeAsyncList:
    """
    Thread-safe asynchronous list abstraction.

    This class provides a list-like container that can be safely
    accessed and modified concurrently from multiple coroutines
    without causing race conditions.
    """


    def __init__(
            self
        ):
        """
        Initialize an empty SafeAsyncList.

        Attributes
        ----------
        _list : list
            Internal list storing the items.

        _lock : asyncio.Lock
            Asynchronous lock to ensure thread-safe access.
        """

        self._list = []
        self._lock = asyncio.Lock()


    async def add(
            self, 
            item: Any
        ) -> None:
        """
        Append an item to the list safely.

        Ensures that only one coroutine at a time can modify
        the underlying list, preventing race conditions or
        data corruption.

        Parameters
        ----------
        item : Any
            The item to append to the list.

        Returns
        -------
        None
        """

        async with self._lock:
            self._list.append(item)


    async def get_all(
            self
        ) -> list:
        """
        Return a snapshot of all items in the list.

        The returned list is a shallow copy of the internal
        storage, so modifying it does not affect the original
        data.

        Returns
        -------
        list
            A copy of all items currently stored in the list.
        """

        return list(self._list)