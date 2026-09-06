from time import perf_counter

from flask import Flask, jsonify, request
import requests
from prometheus_client import Gauge, Counter, Histogram, start_http_server

app = Flask(__name__)

# Service information gauge
SERVICE_INFO = Gauge('outdialer_service_info', 'Service information', ['service'])

# Set the service info gauge
SERVICE_INFO.labels(service="portal").set(1)

# Portal metrics
PORTAL_REQUESTS_TOTAL = Counter('portal_requests_total', 'Total portal requests', ['operation', 'status'])
PORTAL_REQUEST_DURATION_SECONDS = Histogram('portal_request_duration_seconds', 'Portal request duration in seconds', ['operation'])

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "service": "portal",
        "port": 8443,
        "metrics_port": 9090
    })

@app.route('/campaigns', methods=['POST'])
def create_campaign():
    # Record request duration start
    start_time = perf_counter()
    status = "error"  # Default status
    
    try:
        data = request.get_json()

        if not data or "template_id" not in data or "numbers" not in data:
            return jsonify({
                "error": "Missing required fields: template_id, numbers"
            }), 400

        template_id = data["template_id"]
        numbers = data["numbers"]

        if not isinstance(template_id, str) or not template_id:
            return jsonify({
                "error": "template_id must be a non-empty string"
            }), 400

        if not isinstance(numbers, list) or not numbers:
            return jsonify({
                "error": "numbers must be a non-empty array"
            }), 400

        if not all(isinstance(number, str) for number in numbers):
            return jsonify({
                "error": "numbers must contain only strings"
            }), 400

        campaign_manager_url = "http://campaign:8080/campaigns"

        response = requests.post(
            campaign_manager_url,
            json=data,
            timeout=5
        )
        
        # Set status based on HTTP response code
        status = "success" if 200 <= response.status_code < 300 else "error"
        
        return response.text, response.status_code, {
            'Content-Type': 'application/json'
        }
    except requests.exceptions.RequestException:
        # Handle downstream failures
        return jsonify({
            "error": "Failed to forward request to Campaign Manager"
        }), 500

    finally:
        # Record counter and duration for all requests (success or failure)
        PORTAL_REQUESTS_TOTAL.labels(operation="create_campaign", status=status).inc()
        duration = perf_counter() - start_time
        PORTAL_REQUEST_DURATION_SECONDS.labels(operation="create_campaign").observe(duration)

@app.route('/campaigns/<campaign_id>', methods=['GET'])
def get_campaign_status(campaign_id):
    # Record request duration start
    start_time = perf_counter()
    status = "error"  # Default status
    
    try:
        # Forward to Campaign Manager
        campaign_manager_url = f"http://campaign:8080/campaigns/{campaign_id}"

        response = requests.get(campaign_manager_url, timeout=5)

        # Set status based on HTTP response code
        status = "success" if 200 <= response.status_code < 300 else "error"
        
        # Return the response from Campaign Manager
        return response.text, response.status_code, {'Content-Type': 'application/json'}
    except requests.exceptions.RequestException:
        # Handle downstream failures
        return jsonify({"error": "Failed to connect to Campaign Manager"}), 500

    finally:
        # Record counter and duration for all requests (success or failure)
        PORTAL_REQUESTS_TOTAL.labels(operation="get_campaign_status", status=status).inc()
        duration = perf_counter() - start_time
        PORTAL_REQUEST_DURATION_SECONDS.labels(operation="get_campaign_status").observe(duration)

if __name__ == '__main__':
    # Start the Prometheus metrics server on port 9090
    start_http_server(9090)
    app.run(host='0.0.0.0', port=8443, debug=False)
