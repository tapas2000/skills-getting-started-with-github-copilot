"""
Shared pytest fixtures for FastAPI activity management tests.

This module provides:
- TestClient fixture for making HTTP requests to the API
- Fresh activities data for state isolation between tests
- Parametrized test data for multiple activity/email scenarios
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add src directory to Python path to import app module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """
    Provide a TestClient for the FastAPI application.
    
    Returns:
        TestClient: A test client that can make HTTP requests to the app.
    """
    return TestClient(app)


@pytest.fixture
def fresh_activities():
    """
    Reset activities to their initial state before each test.
    
    This fixture ensures state isolation - each test starts with a clean
    copy of the activities, preventing test pollution.
    
    Yields:
        dict: The activities dictionary reset to initial state.
    """
    # Store original state
    original_state = {
        activity: {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": data["participants"].copy()  # Copy the list
        }
        for activity, data in activities.items()
    }
    
    # Reset activities before test
    for activity_name in activities:
        activities[activity_name]["participants"] = original_state[activity_name]["participants"].copy()
    
    yield activities
    
    # Restore original state after test
    for activity_name in activities:
        activities[activity_name]["participants"] = original_state[activity_name]["participants"].copy()


@pytest.fixture(params=[
    "student1@mergington.edu",
    "student.name@mergington.edu",
    "test.email.123@mergington.edu"
])
def sample_email(request):
    """
    Parametrized fixture providing various email formats for testing.
    
    Yields:
        str: Different email formats to test robustness.
    """
    return request.param


@pytest.fixture(params=[
    "Chess Club",
    "Programming Class",
    "Basketball Team",
    "Art Club",
    "Science Club"
])
def sample_activity(request):
    """
    Parametrized fixture providing various activity names for testing.
    
    Yields:
        str: Different activity names from the activities database.
    """
    return request.param
