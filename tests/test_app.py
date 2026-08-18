from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

BASELINE_ACTIVITIES = deepcopy(activities)


@pytest.fixture
def client():
    """Arrange a known backend state before each test."""
    activities.clear()
    activities.update(deepcopy(BASELINE_ACTIVITIES))

    with TestClient(app) as test_client:
        yield test_client

    activities.clear()
    activities.update(deepcopy(BASELINE_ACTIVITIES))


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert payload[expected_activity]["max_participants"] == 12
    assert "michael@mergington.edu" in payload[expected_activity]["participants"]


def test_signup_for_activity_adds_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_student(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_missing_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_removes_student(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(existing_email)}",
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {existing_email} from {activity_name}"}
    assert existing_email not in activities[activity_name]["participants"]


def test_remove_participant_rejects_missing_student(client):
    # Arrange
    activity_name = "Chess Club"
    missing_email = "missing@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(missing_email)}",
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
