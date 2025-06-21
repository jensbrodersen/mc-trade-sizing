import yaml
from influxdb_client import InfluxDBClient, Point

def load_config():
    with open("dps_config.yaml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

import socket
from urllib.parse import urlparse

def is_influxdb_reachable(url, timeout=2):
    """Check if the InfluxDB server is reachable."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80
        with socket.create_connection((host, port), timeout):
            return True
    except Exception:
        return False

def write_to_influxdb(data):
    """Writes simulation results to InfluxDB."""
    config = load_config()
    client = InfluxDBClient(url=config["influxdb_url"], token=config["influxdb_token"], org=config["influxdb_org"])
    write_api = client.write_api()

    for entry in data:
        point = (
            Point("simulation_results")
            .tag("source", "my_simulator")
            .field("hit_rate", entry.get("hit_rate", 0))
            .field("avg_win", entry.get("avg_win", 0))
            .field("avg_loss", entry.get("avg_loss", 0))
        )
        write_api.write(bucket=config["influxdb_bucket"], record=point)

    #print("\n✅ Simulation results successfully written to InfluxDB!")
    client.close()

config = load_config()
client = InfluxDBClient(url=config["influxdb_url"], token=config["influxdb_token"], org=config["influxdb_org"])
