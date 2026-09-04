from flask import Flask, jsonify
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

if __name__ == '__main__':
    # Start the Prometheus metrics server on port 9090
    start_http_server(9090)
    app.run(host='0.0.0.0', port=8443, debug=False)
