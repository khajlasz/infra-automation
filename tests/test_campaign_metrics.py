"""Tests for Campaign Manager Prometheus metrics."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import prometheus_client
import requests
from prometheus_client import (
    CollectorRegistry,
    Counter as RealCounter,
    Gauge as RealGauge,
    Histogram as RealHistogram,
)


REPO_ROOT = Path(__file__).parents[1]

# Campaign Manager runs as a separate process/container in production.
# During pytest, however, several applications are loaded into one Python
# process. Give Campaign Manager its own registry so metric names do not
# collide with Portal metrics.
TEST_REGISTRY = CollectorRegistry()


def isolated_gauge(*args, **kwargs):
    kwargs["registry"] = TEST_REGISTRY
    return RealGauge(*args, **kwargs)


def isolated_counter(*args, **kwargs):
    kwargs["registry"] = TEST_REGISTRY
    return RealCounter(*args, **kwargs)


def isolated_histogram(*args, **kwargs):
    kwargs["registry"] = TEST_REGISTRY
    return RealHistogram(*args, **kwargs)


def load_campaign_manager_module():
    """Load Campaign Manager with real metrics in an isolated registry."""

    spec = importlib.util.spec_from_file_location(
        "campaign_manager_metrics_app",
        REPO_ROOT / "docker" / "campaign-manager" / "app.py",
    )

    module = importlib.util.module_from_spec(spec)

    # app.py imports Gauge/Counter/Histogram using:
    #
    #     from prometheus_client import Gauge, Counter, Histogram
    #
    # Temporarily replace those constructors while app.py is executed.
    # The created metrics are still real Prometheus objects; only their
    # registry is changed.
    with (
        patch.object(prometheus_client, "Gauge", new=isolated_gauge),
        patch.object(prometheus_client, "Counter", new=isolated_counter),
        patch.object(prometheus_client, "Histogram", new=isolated_histogram),
    ):
        spec.loader.exec_module(module)

    return module


campaign_module = load_campaign_manager_module()

campaigns = campaign_module.campaigns
campaign_lock = campaign_module.campaign_lock
simulate_async_execution = campaign_module.simulate_async_execution

SERVICE_INFO = campaign_module.SERVICE_INFO
CAMPAIGNS_TOTAL = campaign_module.CAMPAIGNS_TOTAL
CAMPAIGNS_ACTIVE = campaign_module.CAMPAIGNS_ACTIVE
CAMPAIGN_EXECUTION_DURATION_SECONDS = (
    campaign_module.CAMPAIGN_EXECUTION_DURATION_SECONDS
)


def get_counter_value(status):
    """Return campaigns_total value for one terminal status."""

    metric = CAMPAIGNS_TOTAL.labels(status=status)

    for collected_metric in metric.collect():
        for sample in collected_metric.samples:
            if sample.name == "campaigns_total":
                return sample.value

    return 0.0


def get_gauge_value():
    """Return current campaigns_active value."""

    for collected_metric in CAMPAIGNS_ACTIVE.collect():
        for sample in collected_metric.samples:
            if sample.name == "campaigns_active":
                return sample.value

    return 0.0


def get_histogram_count():
    """Return number of campaign duration observations."""

    for collected_metric in CAMPAIGN_EXECUTION_DURATION_SECONDS.collect():
        for sample in collected_metric.samples:
            if sample.name == "campaign_execution_duration_seconds_count":
                return sample.value

    return 0.0


class CampaignManagerMetricsTests(unittest.TestCase):

    def setUp(self):
        with campaign_lock:
            campaigns.clear()

    def tearDown(self):
        with campaign_lock:
            campaigns.clear()

    def test_service_info_gauge_is_registered(self):
        """Campaign Manager service identity is exported."""

        found = False

        for collected_metric in SERVICE_INFO.collect():
            for sample in collected_metric.samples:
                if (
                    sample.name == "outdialer_service_info"
                    and sample.labels.get("service") == "campaign-manager"
                ):
                    self.assertEqual(sample.value, 1)
                    found = True

        self.assertTrue(found)

    @patch.object(campaign_module.requests, "post")
    def test_successful_execution_increments_metrics(self, mock_post):
        initial_completed = get_counter_value("completed")
        initial_failed = get_counter_value("failed")
        initial_active = get_gauge_value()
        initial_duration_count = get_histogram_count()

        campaign_id = "test-campaign-success"
        numbers = ["+48111111111", "+48222222222"]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued",
            }

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "campaign_id": campaign_id,
            "results": {
                "successful": 1,
                "failed": 1,
            },
        }

        mock_post.return_value = response

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source,
        )

        self.assertEqual(
            get_counter_value("completed"),
            initial_completed + 1,
        )
        self.assertEqual(
            get_counter_value("failed"),
            initial_failed,
        )
        self.assertEqual(
            get_gauge_value(),
            initial_active,
        )
        self.assertEqual(
            get_histogram_count(),
            initial_duration_count + 1,
        )

    @patch.object(campaign_module.requests, "post")
    def test_non_200_response_increments_failed_counter(self, mock_post):
        initial_completed = get_counter_value("completed")
        initial_failed = get_counter_value("failed")
        initial_active = get_gauge_value()
        initial_duration_count = get_histogram_count()

        campaign_id = "test-campaign-http-error"
        numbers = ["+48111111111"]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued",
            }

        response = MagicMock()
        response.status_code = 500
        mock_post.return_value = response

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source,
        )

        self.assertEqual(
            get_counter_value("failed"),
            initial_failed + 1,
        )
        self.assertEqual(
            get_counter_value("completed"),
            initial_completed,
        )
        self.assertEqual(
            get_gauge_value(),
            initial_active,
        )
        self.assertEqual(
            get_histogram_count(),
            initial_duration_count + 1,
        )

    @patch.object(campaign_module.requests, "post")
    def test_request_exception_increments_failed_counter(self, mock_post):
        initial_completed = get_counter_value("completed")
        initial_failed = get_counter_value("failed")
        initial_active = get_gauge_value()
        initial_duration_count = get_histogram_count()

        campaign_id = "test-campaign-request-error"
        numbers = ["+48111111111"]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued",
            }

        mock_post.side_effect = requests.exceptions.RequestException(
            "Connection failed"
        )

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source,
        )

        self.assertEqual(
            get_counter_value("failed"),
            initial_failed + 1,
        )
        self.assertEqual(
            get_counter_value("completed"),
            initial_completed,
        )
        self.assertEqual(
            get_gauge_value(),
            initial_active,
        )
        self.assertEqual(
            get_histogram_count(),
            initial_duration_count + 1,
        )

    @patch.object(campaign_module.requests, "post")
    def test_invalid_response_increments_failed_counter(self, mock_post):
        initial_completed = get_counter_value("completed")
        initial_failed = get_counter_value("failed")
        initial_active = get_gauge_value()
        initial_duration_count = get_histogram_count()

        campaign_id = "test-campaign-invalid-response"
        numbers = ["+48111111111"]
        prompt_source = "/prompts/customer-renewal-v1.wav"

        with campaign_lock:
            campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "template_id": "customer-renewal-v1",
                "numbers": numbers,
                "prompt_source": prompt_source,
                "status": "queued",
            }

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "campaign_id": campaign_id,
            "results": {},
        }

        mock_post.return_value = response

        simulate_async_execution(
            campaign_id,
            numbers,
            prompt_source,
        )

        self.assertEqual(
            get_counter_value("failed"),
            initial_failed + 1,
        )
        self.assertEqual(
            get_counter_value("completed"),
            initial_completed,
        )
        self.assertEqual(
            get_gauge_value(),
            initial_active,
        )
        self.assertEqual(
            get_histogram_count(),
            initial_duration_count + 1,
        )

    def test_nonexistent_campaign_does_not_change_metrics(self):
        initial_completed = get_counter_value("completed")
        initial_failed = get_counter_value("failed")
        initial_active = get_gauge_value()
        initial_duration_count = get_histogram_count()

        simulate_async_execution(
            "nonexistent-campaign",
            ["+48111111111"],
            "/prompts/customer-renewal-v1.wav",
        )

        self.assertEqual(
            get_counter_value("completed"),
            initial_completed,
        )
        self.assertEqual(
            get_counter_value("failed"),
            initial_failed,
        )
        self.assertEqual(
            get_gauge_value(),
            initial_active,
        )
        self.assertEqual(
            get_histogram_count(),
            initial_duration_count,
        )


if __name__ == "__main__":
    unittest.main()