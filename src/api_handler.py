import sys
import os
import signal
from flask import Flask, jsonify, request
import requests
from collections import OrderedDict
import json
import threading
import time

app = Flask(__name__)

# Load simulation results into a global variable (will be updated dynamically)
simulation_data = []

@app.route("/api/simulations", methods=["GET"])
def get_simulations():
    """Returns the simulation results as JSON via REST API with fixed key order and proper encoding."""
    response_json = json.dumps([OrderedDict(entry) for entry in simulation_data], ensure_ascii=False, indent=4)
    return app.response_class(response_json, content_type="application/json")

@app.route("/shutdown", methods=["POST"])
def shutdown():
    """Endpoint to stop the Flask API server."""
    print("\n🚫 Stopping REST API via shutdown endpoint...")

    func = request.environ.get("tool.server.shutdown")

    if func:
        func()
        print("\n✅ API has successfully shut down.")

    print("\n💡 Ensuring complete termination of the script.")
    os._exit(0)  # Fully exit the Python process

def stop_server(timeout_duration):
    """Stops the Flask API after the given timeout duration."""
    print(f"\n⏳ REST API will automatically stop after {timeout_duration} seconds...")

    time.sleep(timeout_duration)  # Wait dynamically based on JSON config

    print("\n🚫 Stopping REST API...")

    try:
        requests.post("http://127.0.0.1:5000/shutdown")  # Call shutdown endpoint via API
    except requests.exceptions.RequestException:
        print("⚠ Warning: Could not reach shutdown endpoint. Exiting manually.")
        os._exit(0)  # Last resort exit

def start_api(data, timeout_duration):
    """Starts the Flask API server with simulation data and dynamic timeout."""
    global simulation_data
    simulation_data = data
    print("\n✅ REST API started at http://127.0.0.1:5000/api/simulations")
    
    # Start the timeout process in a background thread
    threading.Thread(target=stop_server, args=(timeout_duration,), daemon=True).start()

    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)

