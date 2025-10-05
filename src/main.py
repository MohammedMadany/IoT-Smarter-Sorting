import sys
import os

# FIX: Add the project's root directory to the path 
# so 'src.hardware' and 'project_utils.classifier' can be imported.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

import threading
import time
import logging
import cv2
import pandas as pd
import paho.mqtt.client as mqtt
from collections import Counter
from datetime import datetime

# Local imports - these now work correctly
# Assuming these modules are correctly implemented in your project structure
from src.hardware import initialize_gpio, move_servo, cleanup
from picamera2 import Picamera2
from project_utils.classifier import classify

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global Settings and State ---
CSV_FILE = 'data/sorting_counts.csv'
THINGSBOARD_HOST = 'thingsboard.cloud'
THINGSBOARD_PORT = 1883 # Standard MQTT port for non-TLS
THINGSBOARD_TOKEN = "4IKb3Uj4JKNyhmSi9kA4" # Your device access token

running = True
frame_count = 0
counts = Counter({'Red': 0, 'Green': 0, 'Reject': 0})
mqtt_client = None
start_time = time.time() # **NEW: Track script start time**

# --- Paho MQTT Callback Functions ---
def on_connect(client, userdata, flags, rc):
    """Called when the MQTT client connects to the broker."""
    if rc == 0:
        logger.info("Paho MQTT Client connected to ThingsBoard successfully.")
        # Send initial status attribute after connection
        client.publish('v1/devices/me/attributes', '{"status": "Running", "deviceType": "Smart Sorter"}', qos=1)
    else:
        logger.error(f"Paho MQTT Client failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    """Called when the MQTT client disconnects."""
    logger.info(f"Paho MQTT Client disconnected with return code {rc}")

# --- Helper Functions ---
def save_to_csv(counts):
    """Appends sorting counts with a timestamp to the CSV file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')
    df = pd.DataFrame([{'Timestamp': timestamp, **counts}])
    df.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
    # logger.info("Saved counts to CSV: %s", counts) # Removed to avoid excessive logging

def tb_publisher():
    """Manages a persistent Paho MQTT connection and periodic telemetry publishing."""
    global mqtt_client
    global counts
    global running
    global start_time # Access the global start_time

    # 1. Initialize Paho Client
    mqtt_client = mqtt.Client(client_id='', protocol=mqtt.MQTTv311)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    
    # 2. Set ThingsBoard access token as username
    mqtt_client.username_pw_set(username=THINGSBOARD_TOKEN)

    # 3. Connect to ThingsBoard Cloud
    try:
        mqtt_client.connect(THINGSBOARD_HOST, THINGSBOARD_PORT, keepalive=60)
    except Exception as e:
        logger.error(f"Paho MQTT Connection failed: {e}")
        return

    mqtt_client.loop_start()

    while running:
        # **NEW: Calculate Working Time**
        current_time = time.time()
        working_time_sec = int(current_time - start_time) # Total runtime in seconds
        
        # Check connection status before trying to publish
        if mqtt_client.is_connected():
            try:
                # Prepare telemetry payload
                telemetry_data = dict(counts)
                telemetry_data['working_time'] = working_time_sec # **NEW KEY ADDED**

                # Publish to ThingsBoard (using json.dumps for clean JSON)
                import json
                payload = json.dumps(telemetry_data)
                mqtt_client.publish('v1/devices/me/telemetry', payload, qos=1)
                
                logger.info("Published to ThingsBoard: %s", telemetry_data)
            except Exception as e:
                logger.error(f"Paho MQTT Publish failed: {e}")
        else:
             logger.warning("Paho MQTT Client not connected. Waiting for reconnection.")

        # Publish every 5 seconds
        time.sleep(5) 

    # Stop the network loop and disconnect cleanly
    mqtt_client.loop_stop()
    if mqtt_client.is_connected():
        mqtt_client.disconnect()
    logger.info("ThingsBoard Publisher Thread stopped cleanly.")

# --- Main Logic ---
def main():
    global running
    global frame_count
    
    # Start the ThingsBoard publishing thread
    publisher_thread = threading.Thread(target=tb_publisher, daemon=True)
    publisher_thread.start()

    # Hardware and Camera Initialization
    initialize_gpio()
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    logger.info("Pi Camera initialized")

    try:
        while running:
            # Main loop handles classification and local data
            frame = picam2.capture_array()
            label = classify(frame)
            
            global counts
            frame_count += 1
            logger.info("Frame %d: Classified as %s", frame_count, label)

            # Sorting logic and count update
            if label == 'Red':
                move_servo(25, 7.0) 
                move_servo(17, 90)   
                counts['Red'] += 1
                logger.info("Good Tomato (Red) detected")
            elif label == 'Green':
                move_servo(25, 12.0)
                move_servo(17, 180) 
                counts['Green'] += 1
                logger.info("Bad Tomato (Green) detected")
            else:
                move_servo(25, 12.0)
                counts['Reject'] += 1
                logger.info("Uncertain detection - Rejected")

            save_to_csv(counts) 
            
            # Display frame (optional, for local debug)
            # You can add the working time here too if you like:
            current_runtime = int(time.time() - start_time)
            cv2.putText(frame, f'Runtime: {current_runtime}s', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.putText(frame, f'Red: {counts["Red"]}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f'Green: {counts["Green"]}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f'Reject: {counts["Reject"]}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.imshow('Camera Feed', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
                break
            
            time.sleep(0.5) 
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        running = False # Signal the publisher thread to stop
        if publisher_thread.is_alive():
            publisher_thread.join(timeout=6) 
        logger.info("Shutting down main process.")
        cleanup()
        picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Initialize start_time when the script begins
    start_time = time.time()
    main()