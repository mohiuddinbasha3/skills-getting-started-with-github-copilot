"""
Comprehensive tests for the Mergington High School API.
Uses AAA (Arrange-Act-Assert) pattern for test structure.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Arrange: Provide a test client for API calls."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Arrange: Reset activities to initial state before each test.
    Returns a snapshot of activities to restore after test.
    """
    original_participants = {
        name: details["participants"].copy()
        for name, details in activities.items()
    }
    yield
    # Restore original state after test
    for name, details in activities.items():
        details["participants"] = original_participants[name]


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_success(self, client, reset_activities):
        """
        Arrange: Set up test client
        Act: GET /activities
        Assert: Response is 200 and contains activity data
        """
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_contains_all_activities(self, client, reset_activities):
        """
        Arrange: Known activity names
        Act: GET /activities
        Assert: All expected activities are present with correct structure
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Science Olympiad",
        ]
        for activity_name in expected_activities:
            assert activity_name in data

    def test_get_activities_has_correct_structure(self, client, reset_activities):
        """
        Arrange: API response
        Act: GET /activities and check structure
        Assert: Each activity has required fields
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]

        # Assert
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_participants_are_emails(self, client, reset_activities):
        """
        Arrange: Activity data with participants
        Act: GET /activities
        Assert: Participants are email strings
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, details in data.items():
            for participant in details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client, reset_activities):
        """
        Arrange: Clear a participant list and prepare new email
        Act: Sign up new participant for activity
        Assert: Participant added to list and response is 200
        """
        # Arrange
        activities["Tennis Club"]["participants"] = []
        new_email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            "/activities/Tennis%20Club/signup", params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        assert new_email in activities["Tennis Club"]["participants"]
        data = response.json()
        assert f"Signed up {new_email}" in data["message"]

    def test_signup_duplicate_email_fails(self, client, reset_activities):
        """
        Arrange: Participant already in an activity
        Act: Try to sign up same participant again
        Assert: Returns 400 error
        """
        # Arrange
        email = activities["Chess Club"]["participants"][0]

        # Act
        response = client.post(
            "/activities/Chess%20Club/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity_fails(self, client, reset_activities):
        """
        Arrange: Non-existent activity name
        Act: Try to sign up for invalid activity
        Assert: Returns 404 error
        """
        # Arrange
        email = "student@mergington.edu"

        # Act
        response = client.post(
            "/activities/NonexistentClub/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_increases_participant_count(self, client, reset_activities):
        """
        Arrange: Clear activity and get initial count
        Act: Sign up multiple participants
        Assert: Participant count increases correctly
        """
        # Arrange
        activities["Art Studio"]["participants"] = []
        initial_count = len(activities["Art Studio"]["participants"])
        emails = ["student1@mergington.edu", "student2@mergington.edu"]

        # Act
        for email in emails:
            client.post("/activities/Art%20Studio/signup", params={"email": email})

        # Assert
        final_count = len(activities["Art Studio"]["participants"])
        assert final_count == initial_count + len(emails)

    def test_signup_response_format(self, client, reset_activities):
        """
        Arrange: New email and activity
        Act: Sign up and check response
        Assert: Response has correct message format
        """
        # Arrange
        activities["Drama Club"]["participants"] = []
        email = "actor@mergington.edu"

        # Act
        response = client.post(
            "/activities/Drama%20Club/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Drama Club" in data["message"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_participant_success(self, client, reset_activities):
        """
        Arrange: Get existing participant
        Act: Unregister them from activity
        Assert: Participant removed and response is 200
        """
        # Arrange
        email = activities["Chess Club"]["participants"][0]
        initial_count = len(activities["Chess Club"]["participants"])

        # Act
        response = client.post(
            "/activities/Chess%20Club/unregister", params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert email not in activities["Chess Club"]["participants"]
        final_count = len(activities["Chess Club"]["participants"])
        assert final_count == initial_count - 1
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_non_participant_fails(self, client, reset_activities):
        """
        Arrange: Email not in activity
        Act: Try to unregister non-participant
        Assert: Returns 400 error
        """
        # Arrange
        email = "nobody@mergington.edu"

        # Act
        response = client.post(
            "/activities/Chess%20Club/unregister", params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_invalid_activity_fails(self, client, reset_activities):
        """
        Arrange: Non-existent activity
        Act: Try to unregister from invalid activity
        Assert: Returns 404 error
        """
        # Arrange
        email = "student@mergington.edu"

        # Act
        response = client.post(
            "/activities/FakeClub/unregister", params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_decreases_participant_count(self, client, reset_activities):
        """
        Arrange: Activity with participants
        Act: Unregister multiple participants
        Assert: Participant count decreases correctly
        """
        # Arrange
        initial_participants = activities["Programming Class"]["participants"].copy()
        emails_to_remove = initial_participants[:2]

        # Act
        for email in emails_to_remove:
            client.post(
                "/activities/Programming%20Class/unregister", params={"email": email}
            )

        # Assert
        final_count = len(activities["Programming Class"]["participants"])
        expected_count = len(initial_participants) - len(emails_to_remove)
        assert final_count == expected_count

    def test_unregister_response_format(self, client, reset_activities):
        """
        Arrange: Participant in activity
        Act: Unregister and check response
        Assert: Response has correct format
        """
        # Arrange
        email = activities["Tennis Club"]["participants"][0]

        # Act
        response = client.post(
            "/activities/Tennis%20Club/unregister", params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Tennis Club" in data["message"]


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static(self, client, reset_activities):
        """
        Arrange: Test client
        Act: GET /
        Assert: Redirects to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_root_with_follow_redirects(self, client, reset_activities):
        """
        Arrange: Test client with redirect following
        Act: GET / and follow redirects
        Assert: Final response is successful
        """
        # Act
        response = client.get("/", follow_redirects=True)

        # Assert
        assert response.status_code == 200


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_signup_when_activity_full(self, client, reset_activities):
        """
        Arrange: Fill activity to capacity
        Act: Try to sign up when full (current code allows over-capacity)
        Assert: Still adds participant (no capacity check in current implementation)
        """
        # Arrange
        activity = activities["Chess Club"]
        original_max = activity["max_participants"]
        activity["max_participants"] = 1
        activity["participants"] = ["existing@mergington.edu"]
        new_email = "full@mergington.edu"

        # Act
        response = client.post(
            "/activities/Chess%20Club/signup", params={"email": new_email}
        )

        # Assert - Current implementation adds participant even when full
        assert response.status_code == 200
        assert new_email in activity["participants"]

        # Restore
        activity["max_participants"] = original_max

    def test_signup_then_unregister_then_signup_again(self, client, reset_activities):
        """
        Arrange: Clear activity
        Act: Sign up -> unregister -> sign up same email
        Assert: Participant cycle works correctly
        """
        # Arrange
        activities["Basketball Team"]["participants"] = []
        email = "athlete@mergington.edu"

        # Act 1: Sign up
        response1 = client.post(
            "/activities/Basketball%20Team/signup", params={"email": email}
        )

        # Act 2: Unregister
        response2 = client.post(
            "/activities/Basketball%20Team/unregister", params={"email": email}
        )

        # Act 3: Sign up again
        response3 = client.post(
            "/activities/Basketball%20Team/signup", params={"email": email}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert email in activities["Basketball Team"]["participants"]

    def test_activity_name_with_special_url_encoding(self, client, reset_activities):
        """
        Arrange: Activity name with spaces
        Act: Sign up using URL-encoded activity name
        Assert: Works correctly
        """
        # Arrange
        email = "student@mergington.edu"

        # Act
        response = client.post(
            "/activities/Programming%20Class/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert email in activities["Programming Class"]["participants"]

    def test_multiple_concurrent_signups_same_activity(self, client, reset_activities):
        """
        Arrange: Clear activity
        Act: Sign up multiple participants sequentially
        Assert: All participants added correctly
        """
        # Arrange
        activities["Gym Class"]["participants"] = []
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu",
        ]

        # Act
        responses = []
        for email in emails:
            response = client.post("/activities/Gym%20Class/signup", params={"email": email})
            responses.append(response)

        # Assert
        assert all(r.status_code == 200 for r in responses)
        assert len(activities["Gym Class"]["participants"]) == len(emails)
        assert all(email in activities["Gym Class"]["participants"] for email in emails)
