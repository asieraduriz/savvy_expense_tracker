from typing import Callable, TypeVar, Optional, List

T = TypeVar("T")


def find_first(list: List[T], condition: Callable[[T], bool]) -> Optional[T]:
    """
    Finds the first element in a list that satisfies a condition.

    Args:
        list: The list to search.
        condition: A function that takes an element and returns True if it satisfies the condition.

    Returns:
        The first element that satisfies the condition, or None if no such element exists.
    """
    return next((item for item in list if condition(item)), None)


def object_is_empty(data: dict) -> bool:
    """
    Checks if all values in a dictionary are None.

    Args:
        data: The dictionary to check.

    Returns:
        True if all values in the dictionary are None, False otherwise.
    """
    if not data:  # Handle empty dictionaries
        return True
    return all(value is None for value in data.values())
