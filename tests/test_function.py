# tests/test_function.py
import pytest
from scripts.function import multiply  # Import từ app/scripts

def test_multiply():
    # Test case 1: Nhân hai số dương
    assert multiply(3, 4) == 12, "3 * 4 nên bằng 12"

    # Test case 2: Nhân số dương và số âm
    assert multiply(5, -2) == -10, "5 * -2 nên bằng -10"

    # Test case 3: Nhân hai số âm
    assert multiply(-3, -4) == 12, "-3 * -4 nên bằng 12"

if __name__ == "__main__":
    pytest.main([__file__])