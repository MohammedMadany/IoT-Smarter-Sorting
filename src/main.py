import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np
import time
import logging
from collections import Counter
import pandas as pd
from datetime import datetime
import paho.mqtt.client as mqtt
from src.hardware import initialize_gpio, move_servo, cleanup
import threading
from picamera2 import Picamera2  # For Pi Camera access

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Settings
CSV_FILE = 'data/sorting_counts.csv'  # CSV log
MQTT_BROKER = 'broker.hivemq.com'  # Public broker for testing
MQTT_PORT = 1883
MQTT_TOPIC = '/project/sorting/counts'  # MQTT topic

# Blynk Configuration (temporarily disabled)
BLYNK_AUTH = "Np_-A0Usy0S_47GzvzHZIHERP_Sp99-C"
BLYNK_SERVER = 'blynk-cloud.com'
BLYNK_PORT = 8441
blynk = None

# Initialize system state
running = True  # Controlled by Blynk Start/Stop
frame_count = 0  # Track frames globally

def classify(frame):
    """Classify frame using OpenCV HSV color detection for red/green."""
    if frame is None:
        return 'Uncertain'
    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Adjust for picamera2 output
    hsv = cv2.cvtColor(hsv, cv2.COLOR_RGB2HSV)
    
    # Red HSV range (adjust if needed)
    lower_red = np.array([0, 100, 100])
    upper_red = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([179, 255, 255])
    
    # Green HSV range (adjust if needed)
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    
    # Masks for red and green
    mask_red = cv2.inRange(hsv, lower_red, upper_red) + cv2.inRange(hsv, lower_red2, upper_red2)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    
    # Count non-zero pixels in masks
    red_count = cv2.countNonZero(mask_red)
    green_count = cv2.countNonZero(mask_green)
    
    # Determine label based on dominant color
    if red_count > green_count and red_count > 1000:  # Threshold for detection
        return 'Red'
    elif green_count > red_count and green_count > 1000:
        return 'Green'
    else:
        return 'Uncertain'  # Reject

def save_to_csv(counts):
    """Save classification counts to CSV with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')
    df = pd.DataFrame([{'Timestamp': timestamp, **counts}])
    df.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
    logger.info("Saved counts to CSV: %s", counts)

def publish_to_mqtt(counts):
    """Publish counts to MQTT for visualization."""
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(MQTT_TOPIC, str(counts), qos=1)
        client.disconnect()
        logger.info("Published to MQTT: %s", counts)
    except Exception as e:
        logger.error("MQTT publish failed: %s", str(e))

def simulate_counts(counts):
    """Simulate random detections for testing."""
    import random
    label = random.choice(['Red', 'Green', 'Reject'])
    counts[label] += 1
    logger.info("Simulated detection: %s", label)
    return label

# Blynk event handlers (temporarily disabled)
def start_stop_handler(value):
    global running
    running = value[0] == '1'
    logger.info("System %s", "started" if running else "stopped")

def alarm_handler(value):
    if value[0] == '1':
        logger.info("Alarm triggered")

def working_time_handler(value):
    logger.info("Working time updated: %s", value[0])

def blynk_thread():
    """Run Blynk in a separate thread (disabled for now)."""
    global blynk
    try:
        blynk = blynklib.Blynk(BLYNK_AUTH, server=BLYNK_SERVER, port=BLYNK_PORT)
        logger.info("Blynk connection established")
        while True:
            blynk.run()
    except Exception as e:
        logger.error("Blynk thread error: %s", str(e))

def main():
    initialize_gpio()
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (320, 240)})
    picam2.configure(config)
    picam2.start()
    logger.info("Pi Camera initialized")
    counts = Counter({'Red': 0, 'Green': 0, 'Reject': 0})

    # Start Blynk thread (disabled for now)
    # blynk_thread_instance = threading.Thread(target=blynk_thread)
    # blynk_thread_instance.daemon = True
    # blynk_thread_instance.start()

    try:
        while True:
            if not running:
                time.sleep(1)
                continue
            frame = picam2.capture_array()
            label = classify(frame)
            global frame_count
            frame_count += 1
            logger.info("Frame %d: Classified as %s", frame_count, label)
            if label == 'Green':
                move_servo(25, 12.0)  # Move Servo 1 (moving), adjust duty for green
                move_servo(17, 7.0)   # Move Servo 2 (sorting) for green
                counts['Green'] += 1
                logger.info("Green Tomato detected - Servos moved")
            elif label == 'Red':
                move_servo(25, 7.0)   # Move Servo 1 (moving), adjust duty for red
                move_servo(17, 12.0)  # Move Servo 2 (sorting) for red
                counts['Red'] += 1
                logger.info("Red Tomato detected - Servos moved")
            else:
                counts['Reject'] += 1
                logger.info("Uncertain detection - No action")
            save_to_csv(counts)
            publish_to_mqtt(counts)
            Update Blynk virtual pins (disabled for now)
            if blynk:
                blynk.virtual_write(0, counts['Red'])    # V0: Red Count
                blynk.virtual_write(1, counts['Green'])  # V1: Green Count
                blynk.virtual_write(2, counts['Reject']) # V2: Reject Count
            time.sleep(1)  # Delay for sorting
    except KeyboardInterrupt:
        logger.info("Shutting down via keyboard interrupt")
    except Exception as e:
        logger.error("Unexpected error in main loop: %s", str(e))
    finally:
        cleanup()
        picam2.stop()
        logger.info("System shutdown complete")

if __name__ == "__main__":
    main()