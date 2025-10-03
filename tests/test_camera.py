from picamera2 import Picamera2
import cv2
import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt
import onnxruntime as ort
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_libraries():
    logger.info("NumPy: %s", np.__version__)
    logger.info("Pandas: %s", pd.__version__)
    logger.info("MQTT: %s", mqtt.Client())
    logger.info("ONNX Runtime: %s", ort.__version__)
    logger.info("OpenCV: %s", cv2.__version__)
    logger.info("All libraries OK")

def test_camera(picam2):
    try:
        frame = picam2.capture_array()
        cv2.imwrite('data/test_image.jpg', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        logger.info("Camera test OK, image saved to data/test_image.jpg")
    except Exception as e:
        logger.error("Camera test failed: %s", e)
        raise

def test_real_time_stream(picam2, duration=10):
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            frame = picam2.capture_array()
            logger.info("Frame captured")
            time.sleep(0.05)
        logger.info("Real-time stream test OK")
    except Exception as e:
        logger.error("Stream test failed: %s", e)
        raise

def test_ai_inference():
    try:
        session = ort.InferenceSession('models/model.onnx')
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        dummy_input = np.random.rand(1, 3, 640, 640).astype(np.float32)  # Changed to 640x640
        outputs = session.run([output_name], {input_name: dummy_input})
        logger.info("AI inference test OK, output shape: %s", outputs[0].shape)
    except Exception as e:
        logger.error("AI inference test failed: %s", e)
        raise

if __name__ == "__main__":
    # Initialize single camera instance for all camera-related tests
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (320, 240)})
    picam2.configure(config)
    picam2.start()
    try:
        test_libraries()
        test_camera(picam2)
        test_real_time_stream(picam2)
        test_ai_inference()
    except Exception as e:
        logger.error("Tests failed: %s", e)
    finally:
        picam2.stop()