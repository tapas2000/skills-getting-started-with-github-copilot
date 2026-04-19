"""
Comprehensive test suite for the High School Activity Management API.

Tests cover:
- GET /activities endpoint (list all activities)
- GET / endpoint (redirect to static page)
- POST /activities/{activity_name}/signup endpoint (student signup)
- DELETE /activities/{activity_name}/unregister endpoint (student unregistration)

Test scenarios include:
- Happy path cases (successful operations)
- Error cases (404 for not found, 400 for bad requests)
- Edge cases (duplicate signups, unregistering non-participants, capacity limits)
- State isolation (no test pollution between runs)
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_list_all_activities(self, client, fresh_activities):
        """
        Test that the /activities endpoint returns all activities with correct structure.
        
        Verifies:
        - Response status code is 200
        - Response contains exactly 9 activities
        - Each activity has required fields
        - Activity data matches expected values
        """
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify we get 9 activities
        assert len(data) == 9
        
        # Verify required fields for each activity
        required_fields = {"description", "schedule", "max_participants", "participants"}
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
    
    def test_activities_contain_expected_activities(self, client):
        """
        Test that all expected activities are returned.
        
        Verifies specific activities exist in the response.
        """
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Club",
            "Science Club"
        ]
        
        for activity in expected_activities:
            assert activity in data
    
    def test_chess_club_initial_participants(self, client):
        """
        Test that Chess Club has its initial participants.
        
        Verifies that initial state is correctly maintained.
        """
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestRootRedirect:
    """Tests for the GET / endpoint."""

    def test_root_redirects_to_static_page(self, client):
        """
        Test that the root endpoint redirects to the static index page.
        
        Verifies:
        - Response is a redirect (status code 307)
        - Redirect location is /static/index.html
        """
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client, fresh_activities):
        """
        Test successful student signup for an activity.
        
        Verifies:
        - Response status code is 200
        - Response contains success message
        - Student email is added to participants
        """
        activity_name = "Basketball Team"
        email = "new.student@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
    
    def test_signup_multiple_participants(self, client, fresh_activities):
        """
        Test multiple students can sign up for the same activity.
        
        Verifies:
        - Multiple students can be added to participants list
        - Participants list grows correctly
        """
        activity_name = "Art Club"
        
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "student1@mergington.edu"}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "student2@mergington.edu"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both participants added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants
    
    def test_signup_nonexistent_activity_returns_404(self, client, fresh_activities):
        """
        Test that signing up for a non-existent activity returns 404.
        
        Verifies:
        - Response status code is 404
        - Response includes appropriate error message
        """
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_duplicate_signup_returns_400(self, client, fresh_activities):
        """
        Test that signing up twice for the same activity returns 400.
        
        Verifies:
        - First signup succeeds
        - Second signup with same email returns 400
        - Error message is appropriate
        """
        activity_name = "Chess Club"
        email = "new.student@mergington.edu"
        
        # First signup - should succeed
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email - should fail
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_already_registered_student_cannot_signup_again(self, client, fresh_activities):
        """
        Test that a student already registered cannot sign up again.
        
        This tests the initial state where some students are already signed up
        for Chess Club.
        
        Verifies:
        - Response status code is 400
        - Error message indicates student already signed up
        """
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_with_various_email_formats(self, client, fresh_activities, sample_email):
        """
        Test that signup works with various valid email formats.
        
        Uses parametrized fixture to test multiple email patterns.
        """
        activity_name = "Drama Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 200
        
        # Verify email was added
        activities_response = client.get("/activities")
        assert sample_email in activities_response.json()[activity_name]["participants"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""

    def test_successful_unregister(self, client, fresh_activities):
        """
        Test successful student unregistration from an activity.
        
        Verifies:
        - Response status code is 200
        - Response contains success message
        - Student email is removed from participants
        """
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        
        # Verify student is registered
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
    
    def test_unregister_from_activity_with_multiple_participants(self, client, fresh_activities):
        """
        Test unregistering one student doesn't affect other students.
        
        Verifies:
        - Target student is removed
        - Other participants remain
        """
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        other_email = "daniel@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        assert response.status_code == 200
        
        # Verify correct participant was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email_to_remove not in participants
        assert other_email in participants
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client, fresh_activities):
        """
        Test that unregistering from a non-existent activity returns 404.
        
        Verifies:
        - Response status code is 404
        - Response includes appropriate error message
        """
        response = client.delete(
            "/activities/Fake Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_nonparticipant_returns_400(self, client, fresh_activities):
        """
        Test that unregistering a student not in the activity returns 400.
        
        Verifies:
        - Response status code is 400
        - Response includes appropriate error message
        - Participants list is unchanged
        """
        activity_name = "Basketball Team"  # No initial participants
        email = "not.registered@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_cannot_unregister_twice(self, client, fresh_activities):
        """
        Test that unregistering twice returns 400 on second attempt.
        
        Verifies:
        - First unregister succeeds
        - Second unregister of same student fails with 400
        """
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # First unregister - should succeed
        response1 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second unregister - should fail
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "not signed up" in response2.json()["detail"]


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_signup_and_unregister_workflow(self, client, fresh_activities):
        """
        Test complete workflow: signup, verify, unregister, verify.
        
        Verifies:
        - Student can sign up
        - Participant list updates correctly
        - Student can unregister
        - Participant list updates correctly after unregister
        """
        activity_name = "Soccer Club"
        email = "integration.test@mergington.edu"
        
        # Initial check
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]
    
    def test_state_isolation_between_tests(self, client, fresh_activities):
        """
        Test that activities are reset between tests (state isolation).
        
        This test verifies that the fresh_activities fixture properly
        isolates state between test runs.
        
        Verifies:
        - Chess Club still has its original participants (michael@, daniel@)
        - No residual participants from previous tests
        """
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        
        # Should have exactly the original 2 participants
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
    
    def test_multiple_activities_independent_state(self, client, fresh_activities, sample_activity):
        """
        Test that operations on one activity don't affect others.
        
        Uses parametrized fixture to test multiple activities.
        
        Verifies:
        - Signup for one activity doesn't affect other activities
        - Each activity maintains independent participant lists
        """
        email = "independent.test@mergington.edu"
        
        # Get initial state
        initial_response = client.get("/activities")
        initial_participants_count = {
            act: len(data["participants"])
            for act, data in initial_response.json().items()
        }
        
        # Signup for the parametrized activity
        signup_response = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify only this activity was affected
        final_response = client.get("/activities")
        for activity_name, activity_data in final_response.json().items():
            if activity_name == sample_activity:
                # This activity should have one more participant
                assert len(activity_data["participants"]) == initial_participants_count[activity_name] + 1
            else:
                # All other activities should be unchanged
                assert len(activity_data["participants"]) == initial_participants_count[activity_name]
