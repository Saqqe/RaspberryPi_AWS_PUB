import time
import asyncio
import subprocess
import json
import os
from awscrt import mqtt
from awsiot import mqtt_connection_builder
from dotenv import load_dotenv
load_dotenv()

# AWS IoT - MQTT Configuration from Environment Variables
AWS_ENDPOINT = os.getenv('AWS_ENDPOINT')
CLIENT_ID = os.getenv('CLIENT_ID')
TOPIC = os.getenv('TOPIC')
CA_CERT_PATH = os.getenv('CA_CERT_PATH')
CERT_PATH = os.getenv('CERT_PATH')
PRIVATE_KEY_PATH = os.getenv('PRIVATE_KEY_PATH')

# Callback when the connection successfully connects
def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))

# Callback when a connection attempt fails
def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))

# Callback when a connection has been disconnected or shutdown successfully
def on_connection_closed(connection, callback_data):
    print("Connection closed")

# Establish MQTT Connection Using AWS SDK
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=AWS_ENDPOINT,
    cert_filepath=CERT_PATH,
    pri_key_filepath=PRIVATE_KEY_PATH,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30,
    ca_filepath=CA_CERT_PATH,
    on_connection_success=on_connection_success,
    on_connection_failure=on_connection_failure,
    on_connection_closed=on_connection_closed
)

async def get_cpu_temp():
    """
    Asynchronously fetches the CPU temperature using vcgencmd and publishes to AWS IoT via MQTT.
    """
    process = await asyncio.create_subprocess_shell(
        'vcgencmd measure_temp',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        temp_output = stdout.decode().strip()
        temp_value = temp_output.split('=')[1].split("'")[0]
        timestamp = int(time.time())  # Unix timestamp
        print(f"CPU temp: {temp_value} °C at {timestamp}")

        # Prepare and publish payload
        payload = json.dumps({
            "device_id": CLIENT_ID,
            "cpu_temp": temp_value,
            "timestamp": timestamp
        })
        mqtt_connection.publish(
            topic=TOPIC,
            payload=payload,
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
    else:
        print(f"Error fetching CPU temperature: {stderr.decode().strip()}")

async def main():
    # Connect to AWS IoT Core
    print(f"Connecting to {AWS_ENDPOINT} with client ID '{CLIENT_ID}'...")
    connect_future = mqtt_connection.connect()
    connect_result = await asyncio.wrap_future(connect_future)
    print("Connected to AWS IoT!")

    while True:
        await get_cpu_temp()
        await asyncio.sleep(5)  # Fetch temperature every 5 seconds

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTerminated by user")
        disconnect_future = mqtt_connection.disconnect()
        asyncio.run(asyncio.wrap_future(disconnect_future))
