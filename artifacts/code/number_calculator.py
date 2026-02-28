def calculate_sum_and_average(numbers):
    """
    Calculate the sum and average of a list of numbers.
    
    This function takes a list of numeric values and returns both their sum
    and arithmetic mean (average). It includes comprehensive error handling
    for various edge cases.
    
    Args:
        numbers (list): A list of numeric values (int or float)
    
    Returns:
        tuple: A tuple containing (sum, average) where:
            - sum (float): The sum of all numbers in the list
            - average (float): The arithmetic mean of the numbers
    
    Raises:
        TypeError: If the input is not a list or contains non-numeric values
        ValueError: If the list is empty
        
    Examples:
        >>> calculate_sum_and_average([1, 2, 3, 4, 5])
        (15.0, 3.0)
        
        >>> calculate_sum_and_average([10.5, 20.3, 15.2])
        (46.0, 15.333333333333334)
        
        >>> calculate_sum_and_average([42])
        (42.0, 42.0)
    """
    # Input validation: Check if input is a list
    if not isinstance(numbers, list):
        raise TypeError(f"Expected a list, but got {type(numbers).__name__}")
    
    # Check if list is empty
    if len(numbers) == 0:
        raise ValueError("Cannot calculate sum and average of an empty list")
    
    # Validate that all elements are numeric
    for i, num in enumerate(numbers):
        if not isinstance(num, (int, float)):
            raise TypeError(f"Element at index {i} is not a number: {num} (type: {type(num).__name__})")
    
    # Calculate sum and average
    total_sum = sum(numbers)
    average = total_sum / len(numbers)
    
    return float(total_sum), float(average)


def main():
    """
    Demonstration function showing various use cases of calculate_sum_and_average.
    """
    print("=== Number Calculator Demo ===\n")
    
    # Test cases
    test_cases = [
        [1, 2, 3, 4, 5],
        [10.5, 20.3, 15.2],
        [42],
        [-1, -2, -3, -4, -5],
        [0, 0, 0],
        [3.14159, 2.71828, 1.41421]
    ]
    
    # Valid test cases
    for i, test_list in enumerate(test_cases, 1):
        try:
            result_sum, result_avg = calculate_sum_and_average(test_list)
            print(f"Test {i}: {test_list}")
            print(f"  Sum: {result_sum}")
            print(f"  Average: {result_avg:.4f}")
            print()
        except (TypeError, ValueError) as e:
            print(f"Test {i} failed: {e}")
            print()
    
    # Error handling demonstrations
    print("=== Error Handling Examples ===\n")
    
    error_cases = [
        ([], "Empty list"),
        ("not a list", "String instead of list"),
        ([1, 2, "three"], "Mixed types in list"),
        (None, "None value")
    ]
    
    for test_input, description in error_cases:
        try:
            result = calculate_sum_and_average(test_input)
            print(f"Unexpected success for {description}: {result}")
        except (TypeError, ValueError) as e:
            print(f"Expected error for {description}: {e}")
        print()


if __name__ == "__main__":
    main()