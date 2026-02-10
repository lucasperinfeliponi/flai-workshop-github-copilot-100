"""
Tests for the High School Management System API

These tests cover all endpoints including:
- Root redirect
- Getting activities
- Signing up for activities
- Unregistering from activities
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    })
    yield


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_participants(self, client):
        """Test that activities contain participant information"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self, client):
        """Test successfully signing up a new student"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_student_to_participants(self, client):
        """Test that signup actually adds student to participants list"""
        client.post("/activities/Chess Club/signup?email=jane@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "jane@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_student_fails(self, client):
        """Test that signing up same student twice fails"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is already signed up for this activity"

    def test_signup_multiple_students(self, client):
        """Test signing up multiple different students"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(f"/activities/Chess Club/signup?email={email}")
            assert response.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        for email in emails:
            assert email in participants


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_student_success(self, client):
        """Test successfully unregistering an existing student"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_removes_student_from_participants(self, client):
        """Test that unregister actually removes student from participants list"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from nonexistent activity fails"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_not_registered_student_fails(self, client):
        """Test that unregistering student who isn't registered fails"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=nonregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"

    def test_unregister_after_signup(self, client):
        """Test the full lifecycle: signup then unregister"""
        email = "testuser@mergington.edu"
        
        # First signup
        response = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response.status_code == 200
        
        # Verify student is registered
        response = client.get("/activities")
        data = response.json()
        assert email in data["Programming Class"]["participants"]
        
        # Now unregister
        response = client.delete(f"/activities/Programming Class/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify student is removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Programming Class"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for common user workflows"""

    def test_student_switches_activities(self, client):
        """Test a student switching from one activity to another"""
        email = "switcher@mergington.edu"
        
        # Sign up for Chess Club
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 200
        
        # Unregister from Chess Club
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 200
        
        # Sign up for Programming Class
        response = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response.status_code == 200
        
        # Verify final state
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]

    def test_multiple_activities_for_same_student(self, client):
        """Test that a student can be in multiple activities"""
        email = "multi@mergington.edu"
        
        # Sign up for multiple activities
        client.post(f"/activities/Chess Club/signup?email={email}")
        client.post(f"/activities/Programming Class/signup?email={email}")
        client.post(f"/activities/Gym Class/signup?email={email}")
        
        # Verify student is in all activities
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]
        assert email in data["Gym Class"]["participants"]
