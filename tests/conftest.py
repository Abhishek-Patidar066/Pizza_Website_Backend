import pytest

from app.main import app, get_db


# ---------------------------------------------------------------------
# Mock database with sample pizza data
# ---------------------------------------------------------------------
MOCK_PIZZA_DATA = {
    "1": {
        "id": 1,
        "name": "Margherita",
        "size": "Medium",
        "price": 8.99,
        "toppings": ["tomato sauce", "mozzarella", "basil"],
    },
    "2": {
        "id": 2,
        "name": "Pepperoni",
        "size": "Medium",
        "price": 9.99,
        "toppings": ["tomato sauce", "mozzarella", "pepperoni"],
    },
    "3": {
        "id": 3,
        "name": "Vegetarian",
        "size": "Medium",
        "price": 10.99,
        "toppings": [
            "tomato sauce",
            "mozzarella",
            "bell peppers",
            "onions",
            "mushrooms",
        ],
    },
}


# ---------------------------------------------------------------------
# Mock Database Implementation
# ---------------------------------------------------------------------
class MockDB(dict):
    """Mock database that mimics SqliteDict behavior."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def commit(self):
        """Mock commit operation."""
        self.committed = True


# ---------------------------------------------------------------------
# Mock Dependency
# ---------------------------------------------------------------------
def get_mock_db():
    """Dependency that returns mock database."""
    mock_db = MockDB(MOCK_PIZZA_DATA.copy())
    return mock_db


# ---------------------------------------------------------------------
# Pytest Fixture to Override Dependency
# ---------------------------------------------------------------------
@pytest.fixture(autouse=True)
def override_get_db():
    """Override get_db dependency for all tests."""
    app.dependency_overrides[get_db] = get_mock_db
    yield
    app.dependency_overrides.clear()
