import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# Snapshot original state once at import time so every test starts clean
_initial_activities = copy.deepcopy(activities)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the shared in-memory activities dict before every test."""
    activities.clear()
    activities.update(copy.deepcopy(_initial_activities))


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200():
    # Arrange - initial data loaded by fixture

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200


def test_get_activities_returns_dict_of_activities():
    # Arrange - initial data loaded by fixture

    # Act
    data = client.get("/activities").json()

    # Assert
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_activities_have_required_keys():
    # Arrange - initial data loaded by fixture

    # Act
    data = client.get("/activities").json()

    # Assert
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    # Arrange
    activity_name = "Chess Club"
    new_email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert new_email in response.json()["message"]


def test_signup_adds_participant_to_activity():
    # Arrange
    activity_name = "Chess Club"
    new_email = "new@mergington.edu"

    # Act
    client.post(f"/activities/{activity_name}/signup", params={"email": new_email})

    # Assert
    data = client.get("/activities").json()
    assert new_email in data[activity_name]["participants"]


def test_signup_unknown_activity_returns_404():
    # Arrange
    unknown_activity = "Nonexistent Activity"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404


def test_signup_duplicate_returns_400():
    # Arrange - michael is already in Chess Club in the initial data
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_full_activity_returns_400():
    # Arrange - fill Chess Club (max 12, starts with 2) to capacity
    activity_name = "Chess Club"
    for i in range(10):
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": f"filler{i}@mergington.edu"},
        )

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "onemore@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/participants
# ---------------------------------------------------------------------------

def test_unregister_success():
    # Arrange - michael is in Chess Club in the initial data
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]


def test_unregister_removes_participant():
    # Arrange - michael is in Chess Club in the initial data
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    data = client.get("/activities").json()
    assert email not in data[activity_name]["participants"]


def test_unregister_unknown_activity_returns_404():
    # Arrange
    unknown_activity = "Nonexistent Activity"

    # Act
    response = client.delete(
        f"/activities/{unknown_activity}/participants",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404


def test_unregister_not_registered_student_returns_404():
    # Arrange
    activity_name = "Chess Club"
    unregistered_email = "nobody@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": unregistered_email},
    )

    # Assert
    assert response.status_code == 404
