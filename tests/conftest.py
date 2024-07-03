import sys
import pytest
from pathlib import Path

import ducktools.lazyimporter as lazyimporter


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


@pytest.fixture(scope="session", autouse=True)
def false_defaults():
    # Tests ignore the environment variable that can set these to True
    process_state = lazyimporter.EAGER_PROCESS
    import_state = lazyimporter.EAGER_IMPORT

    lazyimporter.EAGER_PROCESS = False
    lazyimporter.EAGER_IMPORT = False

    yield

    lazyimporter.EAGER_PROCESS = process_state
    lazyimporter.EAGER_IMPORT = import_state
