"""
Test suite for Portal service metrics instrumentation.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import requests
from unittest.mock import patch, MagicMock

# Import the app from the portal module directly
from docker.portal.app import app, PORTAL_REQUESTS_TOTAL, PORTAL_REQUEST_DURATION_SECONDS

def get_counter_value(operation, status):
    metric = PORTAL_REQUESTS_TOTAL.labels(
        operation=operation,
        status=status,
    )

    for sample in metric.collect()[0].samples:
        if sample.name == "portal_requests_total":
            return sample.value

    return 0.0

def get_histogram_count(operation):
    """Helper to get histogram count for a specific operation."""
    try:
        # Get the histogram sample for the operation
        histogram = PORTAL_REQUEST_DURATION_SECONDS.labels(operation=operation)
        # Access the summary samples - we want the count
        samples = histogram.collect()[0].samples
        if samples:
            # Look for the _count suffix which is used by Prometheus histograms
            for sample in samples:
                if sample.name.endswith('_count'):
                    return sample.value
        return 0.0
    except IndexError:
        return 0.0

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

def test_create_campaign_success_increments_counter_and_histogram(client):
    """Test that successful create campaign increments success counter and histogram."""
    # Get initial values
    initial_success_count = get_counter_value("create_campaign", "success")
    initial_histogram_count = get_histogram_count("create_campaign")
    
    # Mock docker.portal.app.requests.post to return a successful response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.text = '{"id": "test-campaign-id"}'
    mock_response.json.return_value = {"id": "test-campaign-id"}
    
    with patch('docker.portal.app.requests.post', return_value=mock_response):
        response = client.post('/campaigns', 
                             json={
                                 "template_id": "test-template",
                                 "numbers": ["1234567890", "0987654321"]
                             })
        
        assert response.status_code == 201

    # Verify counter increased by exactly 1
    final_success_count = get_counter_value("create_campaign", "success")
    assert final_success_count == initial_success_count + 1
    
    # Verify histogram observation count increased by exactly 1
    final_histogram_count = get_histogram_count("create_campaign")
    assert final_histogram_count == initial_histogram_count + 1

def test_create_campaign_validation_error_increments_error_counter_and_histogram(client):
    """Test that validation failure increments error counter and histogram."""
    # Get initial values
    initial_error_count = get_counter_value("create_campaign", "error")
    initial_histogram_count = get_histogram_count("create_campaign")
    
    # Test with missing required field
    response = client.post('/campaigns', 
                         json={
                             "template_id": "test-template"
                             # Missing "numbers" field
                         })
    
    assert response.status_code == 400

    # Verify counter increased by exactly 1
    final_error_count = get_counter_value("create_campaign", "error")
    assert final_error_count == initial_error_count + 1
    
    # Verify histogram observation count increased by exactly 1
    final_histogram_count = get_histogram_count("create_campaign")
    assert final_histogram_count == initial_histogram_count + 1

def test_create_campaign_downstream_error_increments_error_counter_and_histogram(client):
    """Test that downstream failure increments error counter and histogram."""
    # Get initial values
    initial_error_count = get_counter_value("create_campaign", "error")
    initial_histogram_count = get_histogram_count("create_campaign")
    
    # Mock docker.portal.app.requests.post to raise RequestException
    with patch('docker.portal.app.requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
        
        response = client.post('/campaigns',
                             json={
                                 "template_id": "test-template",
                                 "numbers": ["1234567890"]
                             })
        
        assert response.status_code == 500

    # Verify counter increased by exactly 1
    final_error_count = get_counter_value("create_campaign", "error")
    assert final_error_count == initial_error_count + 1
    
    # Verify histogram observation count increased by exactly 1
    final_histogram_count = get_histogram_count("create_campaign")
    assert final_histogram_count == initial_histogram_count + 1

def test_get_campaign_status_success_increments_counter_and_histogram(client):
    """Test that successful status lookup increments success counter and histogram."""
    # Get initial values
    initial_success_count = get_counter_value("get_campaign_status", "success")
    initial_histogram_count = get_histogram_count("get_campaign_status")
    
    # Mock docker.portal.app.requests.get to return a successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "running"}'
    mock_response.json.return_value = {"status": "running"}
    
    with patch('docker.portal.app.requests.get', return_value=mock_response):
        response = client.get('/campaigns/test-campaign-id')
        
        assert response.status_code == 200

    # Verify counter increased by exactly 1
    final_success_count = get_counter_value("get_campaign_status", "success")
    assert final_success_count == initial_success_count + 1
    
    # Verify histogram observation count increased by exactly 1
    final_histogram_count = get_histogram_count("get_campaign_status")
    assert final_histogram_count == initial_histogram_count + 1

def test_health_and_root_endpoints_do_not_change_counters(client):
    """Test that /health and / endpoints do not change Portal request counters."""
    # Get initial counter values
    initial_create_success = get_counter_value("create_campaign", "success")
    initial_create_error = get_counter_value("create_campaign", "error")
    initial_get_success = get_counter_value("get_campaign_status", "success")
    initial_get_error = get_counter_value("get_campaign_status", "error")
    
    # Make requests to endpoints that should not be instrumented
    response1 = client.get('/health')
    assert response1.status_code == 200
    
    response2 = client.get('/')
    assert response2.status_code == 200

    # Verify counter values are unchanged
    final_create_success = get_counter_value("create_campaign", "success")
    final_create_error = get_counter_value("create_campaign", "error")
    final_get_success = get_counter_value("get_campaign_status", "success")
    final_get_error = get_counter_value("get_campaign_status", "error")
    
    assert final_create_success == initial_create_success
    assert final_create_error == initial_create_error
    assert final_get_success == initial_get_success
    assert final_get_error == initial_get_error
