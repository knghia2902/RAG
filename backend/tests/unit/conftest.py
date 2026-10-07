import pytest

@pytest.fixture(scope="session", autouse=True)
def migrate():
    """Unit tests do not require database migrations."""
    pass
