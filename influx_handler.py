import json
from influxdb_client import InfluxDBClient, Point

def load_config():
    """Load InfluxDB configuration from JSON file."""
    with open("input.json", "r", encoding="utf-8") as file:  # Nutze dein bestehendes JSON-File
        return json.load(file)

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
