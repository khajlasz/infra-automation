from flask import Flask, jsonify, request
import time
from prometheus_client import Gauge, start_http_server

app = Flask(__name__)

# Service information gauge
SERVICE_INFO = Gauge('outdialer_service_info', 'Service information', ['service'])

# Set the service info gauge
SERVICE_INFO.labels(service="call-simulator").set(1)

def get_deterministic_outcome(number, campaign_id):
    """Generate deterministic call outcome based on inputs.

    This is a simple mechanism that provides bounded, testable outcomes.
    The same number + campaign combination always produces the same result,
    but different combinations produce varied outcomes.
    """
    # Create a hash-like value from string characters to get deterministic behavior
    hash_value = 0
    for char in number:
        hash_value = (hash_value * 31 + ord(char)) % 1000

    # Mix in campaign_id for additional variation
    campaign_hash = 0
    for char in campaign_id:
        campaign_hash = (campaign_hash * 31 + ord(char)) % 1000

    mixed_hash = (hash_value + campaign_hash) % 1000

    # Return success/failure with ~2/3 chance of success
    return "successful" if mixed_hash % 3 != 0 else "failed"

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

    # Simulate work with delay
    time.sleep(0.5)

    # Count successes and failures deterministically
    successful_count = 0
    failed_count = 0

    # Process each number with deterministic outcomes
    for number in numbers:
        outcome = get_deterministic_outcome(number, campaign_id)
        if outcome == "successful":
            successful_count += 1
        else:
            failed_count += 1

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
