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
import threading
import blynklib
from picamera2 import Picamera2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Settings
CSV_FILE = 'data/sorting_counts.csv'
MQTT_BROKER = 'broker.hivemq.com'
MQTT_PORT = 1883
MQTT_TOPIC = '/project/sorting/counts'
BLYNK_AUTH = "Np_-A0Usy0S_47GzvzHZIHERP_Sp99-C"
BLYNK_SERVER = 'blynk-cloud.com'
BLYNK_PORT = 8080
blynk = None
running = True
frame_count = 0

def initialize_gpio():
    """Initialize GPIO for servos."""
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    for pin in [25, 17]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    logger.info("GPIO initialized for servos")

def move_servo(pin, duty_cycle):
    """Move servo to specified duty cycle."""
    import RPi.GPIO as GPIO
    pwm = GPIO.PWM(pin, 50)  # 50 Hz
    pwm.start(0)
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(1)
    pwm.stop()

def cleanup():
    """Clean up GPIO on exit."""
    import RPi.GPIO as GPIO
    GPIO.cleanup()
    logger.info("Hardware cleaned up")

def classify(frame):
    """Classify frame using HSV color detection (tunable ranges)."""
    if frame is None:
        return 'Uncertain'
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_RGB2HSV)
    
    # Tunable HSV ranges (adjust based on testing)
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    lower_red2 = np.array([160, 120, 70])
    upper_red2 = np.array([179, 255, 255])
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])
    
    mask_red = cv2.inRange(hsv, lower_red, upper_red) + cv2.inRange(hsv, lower_red2, upper_red2)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    
    red_count = cv2.countNonZero(mask_red)
    green_count = cv2.countNonZero(mask_green)
    
    if red_count > green_count and red_count > 2000:  # Increased threshold
        return 'Red'
    elif green_count > red_count and green_count > 2000:
        return 'Green'
    else:
        return 'Uncertain'

def save_to_csv(counts):
    """Save classification counts to CSV."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')
    df = pd.DataFrame([{'Timestamp': timestamp, **counts}])
    df.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
    logger.info("Saved counts to CSV: %s", counts)

def publish_to_mqtt(counts):
    """Publish counts to MQTT."""
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(MQTT_TOPIC, str(counts), qos=1)
        client.disconnect()
        logger.info("Published to MQTT: %s", counts)
    except Exception as e:
        logger.error("MQTT publish failed: %s", str(e))

def blynk_thread():
    """Handle Blynk connection and heartbeat."""
    global blynk
    blynk = blynklib.Blynk(BLYNK_AUTH, server=BLYNK_SERVER, port=BLYNK_PORT)
    logger.info("Blynk connection established")
    while True:
        blynk.run()
        time.sleep(10)  # Reduced heartbeat interval
        if blynk:
            blynk.virtual_write(6, 1)  # Dummy heartbeat

def start_stop_handler(value):
    global running
    running = value[0] == '1'
    logger.info("System %s from Blynk", "started" if running else "stopped")

def main():
    initialize_gpio()
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (320, 240)})
    picam2.configure(config)
    picam2.start()
    logger.info("Pi Camera initialized")
    counts = Counter({'Red': 0, 'Green': 0, 'Reject': 0})

    # Start Blynk thread
    blynk_thread_instance = threading.Thread(target=blynk_thread)
    blynk_thread_instance.daemon = True
    blynk_thread_instance.start()

    # Register Blynk handlers
    if blynk:
        blynk.on("V3", start_stop_handler)

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
                move_servo(25, 12.0)
                move_servo(17, 7.0)
                counts['Green'] += 1
                logger.info("Green Tomato detected - Servos moved")
            elif label == 'Red':
                move_servo(25, 7.0)
                move_servo(17, 12.0)
                counts['Red'] += 1
                logger.info("Red Tomato detected - Servos moved")
            else:
                counts['Reject'] += 1
                logger.info("Uncertain detection - No action")
            save_to_csv(counts)
            publish_to_mqtt(counts)
            # Real-time Blynk updates
            if blynk:
                blynk.virtual_write(0, counts['Red'])
                blynk.virtual_write(1, counts['Green'])
                blynk.virtual_write(2, counts['Reject'])
            # Real-time camera feed and counter display
            cv2.putText(frame, f'Red: {counts["Red"]}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(frame, f'Green: {counts["Green"]}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f'Reject: {counts["Reject"]}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 128, 128), 2)
            cv2.imshow('Camera Feed', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.5)  # Adjusted for smoother display
    except KeyboardInterrupt:
        logger.info("Shutting down via keyboard interrupt")
    except Exception as e:
        logger.error("Unexpected error in main loop: %s", str(e))
    finally:
        cleanup()
        picam2.stop()
        cv2.destroyAllWindows()
        logger.info("System shutdown complete")

if __name__ == "__main__":
    main()