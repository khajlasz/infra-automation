"""Tests for campaign creation and management functionality."""

import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests


REPO_ROOT = Path(__file__).parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)

    sys.modules[name] = module

    with patch("prometheus_client.Gauge"):
        spec.loader.exec_module(module)

    return module


portal_module = load_module(
    "portal_app",
    REPO_ROOT / "docker" / "portal" / "app.py"
)

campaign_module = load_module(
    "campaign_manager_app",
    REPO_ROOT / "docker" / "campaign-manager" / "app.py"
)

simulator_module = load_module(
    "call_simulator_app",
    REPO_ROOT / "docker" / "call-simulator" / "app.py"
)

portal_app = portal_module.app
campaign_app = campaign_module.app
simulator_app = simulator_module.app

campaigns = campaign_module.campaigns
campaign_lock = campaign_module.campaign_lock
simulate_async_execution = campaign_module.simulate_async_execution


class PortalCampaignCreationTests(unittest.TestCase):
    def setUp(self):
        self.portal_app = portal_app
        self.portal_app.testing = True
        self.client = self.portal_app.test_client()

    def test_create_campaign_forwards_to_campaign_manager(self):
        """Test that portal forwards campaign creation to campaign manager"""
        with patch('portal_app.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.text = json.dumps({
                "campaign_id": "test-campaign-id",
                "status": "queued"
            })
            mock_post.return_value = mock_response
            
            response = self.client.post('/campaigns', 
                                       json={
                                           "template_id": "customer-renewal-v1",
                                           "numbers": ["+48111111111", "+48222222222"]
                                       })
            
            # Check that the request was forwarded correctly with timeout
            mock_post.assert_called_once_with(
                "http://campaign:8080/campaigns",
                json={
                    "template_id": "customer-renewal-v1",
                    "numbers": ["+48111111111", "+48222222222"]
                },
                timeout=5
            )
            
            # Check response
            self.assertEqual(response.status_code, 202)
            data = json.loads(response.data.decode())
            self.assertEqual(data["campaign_id"], "test-campaign-id")
            self.assertEqual(data["status"], "queued")

    def test_create_campaign_handles_error_from_campaign_manager(self):
        """Test that portal properly handles errors from campaign manager"""
        with patch('portal_app.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = '{"error": "Internal Server Error"}'
            mock_post.return_value = mock_response
            
            response = self.client.post('/campaigns', 
                                       json={
                                           "template_id": "customer-renewal-v1",
                                           "numbers": ["+48111111111", "+48222222222"]
                                       })
            
            self.assertEqual(response.status_code, 500)
            
    def test_get_campaign_status_forwards_to_campaign_manager(self):
        """Test that portal forwards status queries to campaign manager"""
        with patch('portal_app.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = json.dumps({
                "campaign_id": "test-campaign-id",
                "status": "queued"
            })
            mock_get.return_value = mock_response
            
            response = self.client.get('/campaigns/test-campaign-id')
            
            # Check that the request was forwarded correctly with timeout
            mock_get.assert_called_once_with(
                "http://campaign:8080/campaigns/test-campaign-id",
                timeout=5
            )
            
            # Check response
            self.assertEqual(response.status_code, 200)


    def test_create_campaign_rejects_missing_required_fields(self):
        with patch('portal_app.requests.post') as mock_post:
            response = self.client.post('/campaigns', json={
                "template_id": "customer-renewal-v1"
            })

            self.assertEqual(response.status_code, 400)
            mock_post.assert_not_called()


    def test_create_campaign_rejects_empty_template_id(self):
        with patch('portal_app.requests.post') as mock_post:
            response = self.client.post('/campaigns', json={
                "template_id": "",
                "numbers": ["+48111111111"]
            })

            self.assertEqual(response.status_code, 400)
            mock_post.assert_not_called()


    def test_create_campaign_rejects_empty_numbers(self):
        with patch('portal_app.requests.post') as mock_post:
            response = self.client.post('/campaigns', json={
                "template_id": "customer-renewal-v1",
                "numbers": []
            })

            self.assertEqual(response.status_code, 400)
            mock_post.assert_not_called()


    def test_create_campaign_rejects_non_string_numbers(self):
        with patch('portal_app.requests.post') as mock_post:
            response = self.client.post('/campaigns', json={
                "template_id": "customer-renewal-v1",
                "numbers": ["+48111111111", 12345]
            })

            self.assertEqual(response.status_code, 400)
            mock_post.assert_not_called()

class CampaignManagerTests(unittest.TestCase):
    def setUp(self):
        self.campaign_app = campaign_app
        self.campaign_app.testing = True
        self.client = self.campaign_app.test_client()

        with campaign_lock:
            campaigns.clear()

    def tearDown(self):
        with campaign_lock:
            campaigns.clear()

    @patch('campaign_manager_app.threading.Thread')
    def test_create_campaign_generates_id_and_returns_202(self, mock_thread):
        response = self.client.post(
            '/campaigns',
            json={
                "template_id": "customer-renewal-v1",
                "numbers": ["+48111111111", "+48222222222"]
            }
        )

        self.assertEqual(response.status_code, 202)

        data = response.get_json()
        self.assertIn("campaign_id", data)
        self.assertEqual(data["status"], "queued")

        with campaign_lock:
            stored_campaign = campaigns[data["campaign_id"]]

        self.assertEqual(stored_campaign["status"], "queued")
        self.assertEqual(
            stored_campaign["template_id"],
            "customer-renewal-v1"
        )

        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    def test_create_campaign_validates_template_id(self):
        response = self.client.post(
            '/campaigns',
            json={
                "template_id": "invalid-template",
                "numbers": ["+48111111111"]
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "Invalid template_id"
        )

    def test_create_campaign_validates_numbers(self):
        response = self.client.post(
            '/campaigns',
            json={
                "template_id": "customer-renewal-v1",
                "numbers": []
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "Numbers must be a non-empty array"
        )

    def test_create_campaign_validates_required_fields(self):
        response = self.client.post(
            '/campaigns',
            json={
                "template_id": "customer-renewal-v1"
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_get_campaign_status_unknown_id_returns_404(self):
        response = self.client.get('/campaigns/non-existent-id')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json()["error"],
            "campaign_not_found"
        )

    def test_get_campaign_status_returns_queued_status(self):
        campaign_id = "test-campaign-id"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": ["+48111111111"],
                "prompt_source": "/prompts/customer-renewal-v1.wav",
                "status": "queued"
            }

        response = self.client.get(f'/campaigns/{campaign_id}')

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["campaign_id"], campaign_id)
        self.assertEqual(data["status"], "queued")

    @patch('campaign_manager_app.requests.post')
    def test_worker_invokes_call_simulator_with_correct_parameters(
        self,
        mock_post
    ):
        campaign_id = "test-campaign-id"
        numbers = ["+48111111111", "+48222222222"]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued"
            }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "campaign_id": campaign_id,
            "results": {
                "successful": 1,
                "failed": 1
            }
        }
        mock_post.return_value = mock_response

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source
        )

        mock_post.assert_called_once_with(
            "http://call_simulator:8081/execute",
            json={
                "campaign_id": campaign_id,
                "numbers": numbers,
                "prompt_source": prompt_source
            },
            timeout=5
        )

    @patch('campaign_manager_app.requests.post')
    def test_worker_stores_results_and_marks_campaign_completed(
        self,
        mock_post
    ):
        campaign_id = "test-campaign-id"
        numbers = [
            "+48111111111",
            "+48222222222",
            "+48333333333"
        ]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued"
            }

        expected_results = {
            "successful": 2,
            "failed": 1
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "campaign_id": campaign_id,
            "results": expected_results
        }
        mock_post.return_value = mock_response

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source
        )

        with campaign_lock:
            campaign = campaigns[campaign_id]

        self.assertEqual(campaign["status"], "completed")
        self.assertEqual(campaign["results"], expected_results)

    @patch('campaign_manager_app.requests.post')
    def test_worker_marks_campaign_failed_on_non_200_response(
        self,
        mock_post
    ):
        campaign_id = "test-campaign-id"
        numbers = ["+48111111111"]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued"
            }

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source
        )

        with campaign_lock:
            status = campaigns[campaign_id]["status"]

        self.assertEqual(status, "failed")

    @patch(
        'campaign_manager_app.requests.post',
        side_effect=requests.exceptions.ConnectionError
    )
    def test_worker_marks_campaign_failed_on_connection_error(
        self,
        mock_post
    ):
        campaign_id = "test-campaign-id"
        numbers = ["+48111111111"]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued"
            }

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source
        )

        with campaign_lock:
            status = campaigns[campaign_id]["status"]

        self.assertEqual(status, "failed")

    @patch('campaign_manager_app.requests.post')
    def test_worker_marks_campaign_failed_on_invalid_results(
        self,
        mock_post
    ):
        campaign_id = "test-campaign-id"
        numbers = ["+48111111111"]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued"
            }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "campaign_id": campaign_id,
            "results": {}
        }
        mock_post.return_value = mock_response

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source
        )

        with campaign_lock:
            status = campaigns[campaign_id]["status"]

        self.assertEqual(status, "failed")

class CallSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.simulator_app = simulator_app
        self.simulator_app.testing = True
        self.client = self.simulator_app.test_client()

    @patch('call_simulator_app.time.sleep')
    def test_execute_campaign_returns_results(self, mock_sleep):
        """Test that execute campaign returns aggregate results"""
        response = self.client.post('/execute',
                                   json={
                                       "campaign_id": "test-campaign-id",
                                       "numbers": ["+48111111111", "+48222222222"],
                                       "prompt_source": "/prompts/customer-renewal-v1.wav"
                                   })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data["campaign_id"], "test-campaign-id")
        self.assertIn("results", data)
        self.assertIn("successful", data["results"])
        self.assertIn("failed", data["results"])

    def test_execute_campaign_validates_fields(self):
        """Test that execute campaign validates required fields"""
        response = self.client.post('/execute',
                                   json={
                                       "campaign_id": "test-campaign-id"
                                       # missing numbers and prompt_source
                                   })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn("error", data)

    def test_execute_campaign_validates_numbers(self):
        """Test that execute campaign validates numbers array"""
        response = self.client.post('/execute',
                                   json={
                                       "campaign_id": "test-campaign-id",
                                       "numbers": [],
                                       "prompt_source": "/prompts/customer-renewal-v1.wav"
                                   })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data["error"], "Numbers must be a non-empty array")

    @patch('call_simulator_app.time.sleep')       
    def test_execute_campaign_deterministic_results(self, mock_sleep):
        """Test that execute campaign produces deterministic results"""
        # Test with the same inputs multiple times
        results1 = []
        results2 = []
        
        for i in range(2):
            response = self.client.post('/execute',
                                       json={
                                           "campaign_id": "test-campaign-id",
                                           "numbers": ["+48111111111", "+48222222222"],
                                           "prompt_source": "/prompts/customer-renewal-v1.wav"
                                       })
            data = json.loads(response.data.decode())
            results1.append(data["results"]) if i == 0 else results2.append(data["results"])
        
        # The same input should produce the same results
        self.assertEqual(results1[0], results2[0])

    @patch('call_simulator_app.time.sleep')        
    def test_execute_campaign_successful_failed_totals_match_numbers(self, mock_sleep):
        """Test that successful + failed result counts equal the number of calls"""
        response = self.client.post('/execute',
                                   json={
                                       "campaign_id": "test-campaign-id",
                                       "numbers": ["+48111111111", "+48222222222", "+48333333333"],
                                       "prompt_source": "/prompts/customer-renewal-v1.wav"
                                   })
        
        data = json.loads(response.data.decode())
        results = data["results"] 
        self.assertEqual(results["successful"] + results["failed"], 3)
        

if __name__ == "__main__":
    unittest.main()