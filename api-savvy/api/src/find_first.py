def find_first(list, condition):
    """
    Finds the first element in a list that satisfies a condition.

    Args:
        list: The list to search.
        condition: A function that takes an element and returns True if it satisfies the condition.

    Returns:
        The first element that satisfies the condition, or None if no such element exists.
    """
    return next((item for item in list if condition(item)), None)
