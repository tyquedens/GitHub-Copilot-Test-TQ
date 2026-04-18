import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index(self):
        """Test that GET / redirects to /static/index.html"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_all_activities(self):
        """Test that GET /activities returns all activities."""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # All activities present
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activity_has_required_fields(self):
        """Test that each activity has all required fields."""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)
    
    def test_initial_participants_present(self):
        """Test that activities have their initial participants."""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self):
        """Test successful signup for an activity."""
        # Arrange
        email = "test_student@mergington.edu"
        activity = "Basketball Team"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_nonexistent_activity(self):
        """Test signup for a non-existent activity."""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Club"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_already_registered(self):
        """Test that a student cannot sign up twice for the same activity."""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_adds_to_participants(self):
        """Test that signup actually adds the student to the participants list."""
        # Arrange
        email = "verify_addition@mergington.edu"
        activity = "Soccer Club"
        
        # Act
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]
    
    def test_signup_multiple_students(self):
        """Test that multiple students can sign up for the same activity."""
        # Arrange
        emails = ["student1@mergington.edu", "student2@mergington.edu"]
        activity = "Art Club"
        
        # Act
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        response = client.get("/activities")
        data = response.json()
        participants = data[activity]["participants"]
        for email in emails:
            assert email in participants


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""
    
    def test_remove_participant_success(self):
        """Test successful removal of a participant."""
        # Arrange
        email = "daniel@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_remove_from_nonexistent_activity(self):
        """Test removal from a non-existent activity."""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Fake Club"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_remove_nonexistent_participant(self):
        """Test removal of a participant who doesn't exist."""
        # Arrange
        email = "notregistered@mergington.edu"
        activity = "Debate Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Participant not found"
    
    def test_remove_actually_removes_participant(self):
        """Test that removal actually removes the participant from the list."""
        # Arrange
        email = "temp_participant@mergington.edu"
        activity = "Science Club"
        
        # Act - Add participant first
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Assert - Verify added
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Act - Remove
        client.delete(f"/activities/{activity}/participants/{email}")
        
        # Assert - Verify removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_signup_and_remove_workflow(self):
        """Test complete signup and removal workflow."""
        # Arrange
        email = "workflow_test@mergington.edu"
        activity = "Gym Class"
        
        # Assert - Initial state
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert - Signup successful
        assert signup_response.status_code == 200
        
        # Assert - Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        
        # Assert - Removal successful
        assert remove_response.status_code == 200
        
        # Assert - Verify removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]