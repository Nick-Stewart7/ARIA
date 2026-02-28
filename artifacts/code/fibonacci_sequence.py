def fibonacci_sequence(n):
    """
    Calculate the Fibonacci sequence up to n terms using iteration.
    
    Args:
        n (int): Number of terms in the Fibonacci sequence to generate
        
    Returns:
        list: List containing the first n Fibonacci numbers
        
    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    """
    # Input validation
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    
    if n < 0:
        raise ValueError("Number of terms cannot be negative")
    
    # Handle edge cases
    if n == 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    # Initialize the sequence with first two terms
    fibonacci_list = [0, 1]
    
    # Generate remaining terms iteratively
    for i in range(2, n):
        next_term = fibonacci_list[i-1] + fibonacci_list[i-2]
        fibonacci_list.append(next_term)
    
    return fibonacci_list


def print_fibonacci_sequence(n):
    """
    Helper function to print the Fibonacci sequence in a formatted way.
    
    Args:
        n (int): Number of terms to generate and print
    """
    try:
        sequence = fibonacci_sequence(n)
        if sequence:
            print(f"Fibonacci sequence for {n} terms:")
            print(", ".join(map(str, sequence)))
        else:
            print("Empty sequence for n = 0")
    except (ValueError, TypeError) as e:
        print(f"Error: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_cases = [0, 1, 2, 5, 10, 15, -1, 3.5, "invalid"]
    
    print("Testing Fibonacci sequence function:")
    print("=" * 50)
    
    for test_n in test_cases:
        print(f"\nTesting with n = {test_n}:")
        print_fibonacci_sequence(test_n)
    
    print("\n" + "=" * 50)
    print("Additional examples:")
    
    # Some practical examples
    for n in [8, 12]:
        sequence = fibonacci_sequence(n)
        print(f"\nFirst {n} Fibonacci numbers: {sequence}")
        print(f"The {n}th Fibonacci number is: {sequence[-1]}")