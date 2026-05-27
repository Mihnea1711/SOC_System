from abc import ABC, abstractmethod
from typing import Any, Optional

class StateStore(ABC):
    """
    Abstract Base Class defining the interface for the Detection Engine's state management.
    
    This allows the engine to track stateful behavior (like failed login counts over time)
    without being tightly coupled to a specific backend (like local memory or Redis).
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the store."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set a value in the store with a Time-To-Live (TTL)."""
        pass

    @abstractmethod
    def increment(self, key: str, amount: int = 1, ttl_seconds: int = 60) -> int:
        """
        Increment a numeric counter. If the key doesn't exist, it should be created 
        with the specified TTL.
        
        Returns:
            The new incremented value.
        """
        pass

    @abstractmethod
    def add_to_set(self, key: str, value: Any, ttl_seconds: int = 60) -> int:
        """
        Add a value to a set. Useful for tracking unique items (like unique ports scanned).
        If the key doesn't exist, the set should be created with the specified TTL.
        
        Returns:
            The new size of the set.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a key from the store."""
        pass
