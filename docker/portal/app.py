from flask import Flask, jsonify, request
import requests
from prometheus_client import Gauge, start_http_server

app = Flask(__name__)

# Service information gauge
SERVICE_INFO = Gauge('outdialer_service_info', 'Service information', ['service'])

# Set the service info gauge
SERVICE_INFO.labels(service="portal").set(1)

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

    try:
        response = requests.post(
            campaign_manager_url,
            json=data,
            timeout=5
        )
        return response.text, response.status_code, {
            'Content-Type': 'application/json'
        }
    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Failed to forward request to Campaign Manager"
        }), 500

@app.route('/campaigns/<campaign_id>', methods=['GET'])
def get_campaign_status(campaign_id):
    # Forward to Campaign Manager
    campaign_manager_url = f"http://campaign:8080/campaigns/{campaign_id}"

    try:
        response = requests.get(campaign_manager_url, timeout=5)

        # Return the response from Campaign Manager
        return response.text, response.status_code, {'Content-Type': 'application/json'}
    except requests.exceptions.RequestException:
        # Handle connection errors
        return jsonify({"error": "Failed to connect to Campaign Manager"}), 500

if __name__ == '__main__':
    # Start the Prometheus metrics server on port 9090
    start_http_server(9090)
    app.run(host='0.0.0.0', port=8443, debug=False)
