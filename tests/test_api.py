"""
Test cases for the FastAPI application endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_root_redirect(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/")
    assert response.status_code == 200


def test_get_activities(client, reset_activities):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    
    # Check structure of one activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity_success(client, reset_activities):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "test@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "test@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client, reset_activities):
    """Test signup for non-existent activity"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_duplicate_participant(client, reset_activities):
    """Test signup when participant is already registered"""
    response = client.post(
        "/activities/Chess Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 400
    
    data = response.json()
    assert data["detail"] == "Student is already signed up"


def test_signup_activity_full(client, reset_activities):
    """Test signup when activity is full"""
    # First, fill up the Chess Club (max 12 participants, currently has 2)
    for i in range(10):  # Add 10 more to reach 12
        response = client.post(
            f"/activities/Chess Club/signup?email=test{i}@mergington.edu"
        )
        assert response.status_code == 200
    
    # Now try to add one more (should fail)
    response = client.post(
        "/activities/Chess Club/signup?email=overflow@mergington.edu"
    )
    assert response.status_code == 400
    
    data = response.json()
    assert data["detail"] == "Activity is full"


def test_unregister_from_activity_success(client, reset_activities):
    """Test successful unregistration from an activity"""
    response = client.delete(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "michael@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_from_nonexistent_activity(client, reset_activities):
    """Test unregistration from non-existent activity"""
    response = client.delete(
        "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_unregister_non_participant(client, reset_activities):
    """Test unregistration when participant is not registered"""
    response = client.delete(
        "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    
    data = response.json()
    assert data["detail"] == "Student is not signed up for this activity"


def test_activities_data_structure(client, reset_activities):
    """Test that activities have the correct data structure"""
    response = client.get("/activities")
    activities = response.json()
    
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_name, str)
        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        
        assert isinstance(activity_data["description"], str)
        assert isinstance(activity_data["schedule"], str)
        assert isinstance(activity_data["max_participants"], int)
        assert isinstance(activity_data["participants"], list)
        
        # Check that participants list doesn't exceed max_participants
        assert len(activity_data["participants"]) <= activity_data["max_participants"]


def test_email_encoding_in_urls(client, reset_activities):
    """Test that special characters in emails are handled correctly"""
    # Test with email containing . characters (avoid + due to URL encoding issues)
    special_email = "test.user.name@mergington.edu"
    
    response = client.post(
        f"/activities/Programming Class/signup?email={special_email}"
    )
    assert response.status_code == 200
    
    # Verify the participant was added correctly
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert special_email in activities["Programming Class"]["participants"]
    
    # Test unregistration with the same email
    response = client.delete(
        f"/activities/Programming Class/unregister?email={special_email}"
    )
    assert response.status_code == 200


def test_activity_participant_count_limits(client, reset_activities):
    """Test that participant counts are enforced correctly"""
    # Test with Basketball Team (max 15, currently has 2)
    initial_count = len(client.get("/activities").json()["Basketball Team"]["participants"])
    max_participants = client.get("/activities").json()["Basketball Team"]["max_participants"]
    
    # Add participants up to the limit
    for i in range(max_participants - initial_count):
        response = client.post(
            f"/activities/Basketball Team/signup?email=player{i}@mergington.edu"
        )
        assert response.status_code == 200
    
    # Verify we're at the limit
    activities = client.get("/activities").json()
    assert len(activities["Basketball Team"]["participants"]) == max_participants
    
    # Try to add one more (should fail)
    response = client.post(
        "/activities/Basketball Team/signup?email=overflow@mergington.edu"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"