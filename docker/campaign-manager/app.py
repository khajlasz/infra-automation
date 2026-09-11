from flask import Flask, jsonify, request
import requests
import uuid
import threading
import time
from prometheus_client import Gauge, Counter, Histogram, start_http_server

app = Flask(__name__)

# Service information gauge
SERVICE_INFO = Gauge('outdialer_service_info', 'Service information', ['service'])

# Set the service info gauge
SERVICE_INFO.labels(service="campaign-manager").set(1)

# Campaign metrics
CAMPAIGNS_TOTAL = Counter('campaigns_total', 'Total campaigns executed', ['status'])
CAMPAIGNS_ACTIVE = Gauge('campaigns_active', 'Number of currently executing campaigns')
CAMPAIGN_EXECUTION_DURATION_SECONDS = Histogram('campaign_execution_duration_seconds', 'Campaign execution duration in seconds')

# In-memory storage for campaigns (for this milestone)
campaigns = {}
campaign_lock = threading.Lock()
template_mapping = {
    "customer-renewal-v1": "/prompts/customer-renewal-v1.wav"
}

def simulate_async_execution(campaign_id, numbers, prompt_source):
    """Simulate background execution of a campaign"""
    # Initialize terminal status to 'failed' as default
    terminal_status = "failed"

    # Check if campaign exists and transition to running state before instrumenting
    with campaign_lock:
        if campaign_id not in campaigns:
            # Campaign doesn't exist, return without incrementing metrics
            return

        # Transition to running state
        campaigns[campaign_id]["status"] = "running"

    # Only increment active gauge and start timing after confirming campaign exists and is running
    CAMPAIGNS_ACTIVE.inc()
    start_time = time.perf_counter()

    try:
        # Call the simulator - this is where the actual call processing happens
        simulator_url = "http://call_simulator:8081/execute"

        execute_response = requests.post(simulator_url, json={
            "campaign_id": campaign_id,
            "numbers": numbers,
            "prompt_source": prompt_source
        }, timeout=5)

        if execute_response.status_code == 200:
            # Get results from simulator response and store them
            result_data = execute_response.json()

            results = result_data.get("results")

            if (
                not isinstance(results, dict)
                or "successful" not in results
                or "failed" not in results
            ):
                raise ValueError("Invalid Call Simulator response")

            # Update only if campaign exists and mark as completed
            with campaign_lock:
                if campaign_id in campaigns:
                    campaigns[campaign_id]["status"] = "completed"
                    campaigns[campaign_id]["results"] = result_data["results"]
                    # Successful execution - change terminal status to completed (inside same lock)
                    terminal_status = "completed"
        else:
            # If simulator call fails or returns non-200, mark as failed
            with campaign_lock:
                if campaign_id in campaigns:
                    campaigns[campaign_id]["status"] = "failed"

    except (requests.exceptions.RequestException, ValueError):
        with campaign_lock:
            if campaign_id in campaigns:
                campaigns[campaign_id]["status"] = "failed"

    finally:
        # Decrement active campaigns gauge and record duration
        CAMPAIGNS_ACTIVE.dec()
        duration = time.perf_counter() - start_time
        CAMPAIGN_EXECUTION_DURATION_SECONDS.observe(duration)

        # Increment total counter with the final terminal status (unconditionally)
        CAMPAIGNS_TOTAL.labels(status=terminal_status).inc()

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "service": "campaign-manager",
        "port": 8080,
        "metrics_port": 9090
    })

@app.route('/campaigns', methods=['POST'])
def create_campaign():
    # Get the JSON data from the request
    data = request.get_json()

    # Validate required fields
    if not data or "template_id" not in data or "numbers" not in data:
        return jsonify({"error": "Missing required fields: template_id, numbers"}), 400

    template_id = data["template_id"]
    numbers = data["numbers"]

    # Validate template_id
    if template_id not in template_mapping:
        return jsonify({"error": "Invalid template_id"}), 400

    # Validate numbers
    if not isinstance(numbers, list) or len(numbers) == 0:
        return jsonify({"error": "Numbers must be a non-empty array"}), 400

    # Generate unique campaign ID
    campaign_id = str(uuid.uuid4())

    # Resolve template to prompt source
    prompt_source = template_mapping[template_id]

    # Create campaign in memory
    with campaign_lock:
        campaigns[campaign_id] = {
            "campaign_id": campaign_id,
            "template_id": template_id,
            "numbers": numbers,
            "prompt_source": prompt_source,
            "status": "queued"
        }

    # Start background execution (in a separate thread for this milestone)
    thread = threading.Thread(target=simulate_async_execution, args=(campaign_id, numbers, prompt_source))
    thread.start()

    # Return immediately with 202 Accepted
    return jsonify({
        "campaign_id": campaign_id,
        "status": "queued"
    }), 202

@app.route('/campaigns/<campaign_id>', methods=['GET'])
def get_campaign_status(campaign_id):
    with campaign_lock:
        if campaign_id not in campaigns:
            return jsonify({"error": "campaign_not_found"}), 404

        campaign = campaigns[campaign_id]

        # If campaign is completed, include results
        if campaign["status"] == "completed":
            response_data = {
                "campaign_id": campaign_id,
                "status": campaign["status"],
                "results": campaign["results"]
            }
        else:
            response_data = {
                "campaign_id": campaign_id,
                "status": campaign["status"]
            }

    return jsonify(response_data)

if __name__ == '__main__':
    # Start the Prometheus metrics server on port 9090
    start_http_server(9090)
    app.run(host='0.0.0.0', port=8080, debug=False)
