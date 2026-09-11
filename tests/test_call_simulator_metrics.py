"""Tests for Call Simulator Prometheus metrics."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import prometheus_client
from prometheus_client import (
    CollectorRegistry,
    Counter as RealCounter,
    Gauge as RealGauge,
    Histogram as RealHistogram,
)


REPO_ROOT = Path(__file__).parents[1]

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


def load_call_simulator_module():
    spec = importlib.util.spec_from_file_location(
        "call_simulator_metrics_app",
        REPO_ROOT / "docker" / "call-simulator" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)

    with (
        patch.object(prometheus_client, "Gauge", new=isolated_gauge),
        patch.object(prometheus_client, "Counter", new=isolated_counter),
        patch.object(prometheus_client, "Histogram", new=isolated_histogram),
    ):
        spec.loader.exec_module(module)

    return module


simulator_module = load_call_simulator_module()

SERVICE_INFO = simulator_module.SERVICE_INFO
CALLS_TOTAL = simulator_module.CALLS_TOTAL
CALL_DURATION_SECONDS = simulator_module.CALL_DURATION_SECONDS

def get_counter_value(result):
    metric = CALLS_TOTAL.labels(result=result)

    for collected_metric in metric.collect():
        for sample in collected_metric.samples:
            if sample.name == "calls_total":
                return sample.value

    return 0.0


def get_histogram_count():
    for collected_metric in CALL_DURATION_SECONDS.collect():
        for sample in collected_metric.samples:
            if sample.name == "call_duration_seconds_count":
                return sample.value

    return 0.0

class CallSimulatorMetricsTests(unittest.TestCase):

    def setUp(self):
        simulator_module.app.testing = True
        self.client = simulator_module.app.test_client()

    def test_service_info_gauge_is_registered(self):
        samples = [
            sample
            for metric in SERVICE_INFO.collect()
            for sample in metric.samples
        ]

        self.assertTrue(
            any(
                sample.name == "outdialer_service_info"
                and sample.labels.get("service") == "call-simulator"
                and sample.value == 1
                for sample in samples
            )
        )

    @patch.object(simulator_module.time, "sleep")
    def test_execute_campaign_records_call_metrics(self, mock_sleep):
        initial_success = get_counter_value("success")
        initial_failed = get_counter_value("failed")
        initial_duration_count = get_histogram_count()

        numbers = [
            "+48111111111",
            "+48222222222",
            "+48333333333",
        ]

        response = self.client.post(
            "/execute",
            json={
                "campaign_id": "test-campaign-id",
                "numbers": numbers,
                "prompt_source": "/prompts/customer-renewal-v1.wav",
            },
        )

        self.assertEqual(response.status_code, 200)

        success_delta = (
            get_counter_value("success") - initial_success
        )
        failed_delta = (
            get_counter_value("failed") - initial_failed
        )
        duration_delta = (
            get_histogram_count() - initial_duration_count
        )

        self.assertEqual(
            success_delta + failed_delta,
            len(numbers),
        )
        self.assertEqual(
            duration_delta,
            len(numbers),
        )
        self.assertEqual(
            mock_sleep.call_count,
            len(numbers),
        )

    @patch.object(simulator_module.time, "sleep")
    def test_invalid_request_does_not_record_call_metrics(self, mock_sleep):
        initial_success = get_counter_value("success")
        initial_failed = get_counter_value("failed")
        initial_duration_count = get_histogram_count()

        response = self.client.post(
            "/execute",
            json={
                "campaign_id": "test-campaign-id",
                "numbers": [],
                "prompt_source": "/prompts/customer-renewal-v1.wav",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            get_counter_value("success"),
            initial_success,
        )
        self.assertEqual(
            get_counter_value("failed"),
            initial_failed,
        )
        self.assertEqual(
            get_histogram_count(),
            initial_duration_count,
        )
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
