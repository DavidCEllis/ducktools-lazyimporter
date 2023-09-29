import sys
import pytest
from pathlib import Path


@pytest.fixture(scope="module", autouse=True)
def example_modules():
    # Folder with test examples to compile
    base_path = Path(__file__).parent / "example_modules"

    # Add test folder to path temporarily
    sys.path.append(str(base_path))
    try:
        yield
    finally:
        sys.path.remove(str(base_path))
