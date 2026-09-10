from flask import Flask, jsonify, request
import time
import random
from prometheus_client import Counter, Gauge, Histogram, start_http_server

app = Flask(__name__)

# Service information gauge
SERVICE_INFO = Gauge('outdialer_service_info', 'Service information', ['service'])

# Set the service info gauge
SERVICE_INFO.labels(service="call-simulator").set(1)

CALLS_TOTAL = Counter(
    "calls_total",
    "Total simulated calls",
    ["result"],
)

CALL_DURATION_SECONDS = Histogram(
    "call_duration_seconds",
    "Simulated call duration in seconds",
    buckets=(10, 20, 30, 45, 60, 75, 90),
)

def get_deterministic_call_result(number, campaign_id):
    """Generate a deterministic synthetic call result.

    The same number and campaign combination always produces the same
    technical outcome and simulated duration.
    """
    seed = f"{campaign_id}:{number}"
    rng = random.Random(seed)

    outcome = "successful" if rng.random() < 2 / 3 else "failed"

    if outcome == "successful":
        duration = rng.uniform(30.0, 90.0)
    else:
        duration = rng.uniform(10.0, 45.0)

    return outcome, duration

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "service": "call-simulator",
        "port": 8081,
        "metrics_port": 9090
    })

@app.route('/execute', methods=['POST'])
def execute_campaign():
    # Get the JSON data from the request
    data = request.get_json()

    # Validate required fields
    if not data or "campaign_id" not in data or "numbers" not in data or "prompt_source" not in data:
        return jsonify({"error": "Missing required fields: campaign_id, numbers, prompt_source"}), 400

    campaign_id = data["campaign_id"]
    numbers = data["numbers"]
    prompt_source = data["prompt_source"]

    # Validate numbers
    if not isinstance(numbers, list) or len(numbers) == 0:
        return jsonify({"error": "Numbers must be a non-empty array"}), 400

    # Count successes and failures deterministically
    successful_count = 0
    failed_count = 0

    # Process each number with deterministic outcomes and durations
    for number in numbers:
        outcome, duration = get_deterministic_call_result(
            number,
            campaign_id,
        )

        # start_time = time.perf_counter()

        time.sleep(duration / 100)

        # elapsed = time.perf_counter() - start_time
        CALL_DURATION_SECONDS.observe(duration)

        if outcome == "successful":
            successful_count += 1
            CALLS_TOTAL.labels(result="success").inc()
        else:
            failed_count += 1
            CALLS_TOTAL.labels(result="failed").inc()

    # Return aggregate results
    return jsonify({
        "campaign_id": campaign_id,
        "results": {
            "successful": successful_count,
            "failed": failed_count
        }
    })

if __name__ == '__main__':
    # Start the Prometheus metrics server on port 9090
    start_http_server(9090)
    app.run(host='0.0.0.0', port=8081, debug=False)
