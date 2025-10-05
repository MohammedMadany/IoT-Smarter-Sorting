from inference_sdk import InferenceHTTPClient
import cv2
import numpy as np
import logging
import os
import base64

logger = logging.getLogger(__name__)

# Roboflow setup
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="IIF7of2dU2cycjWpZ30i"  # Your key
)
MODEL_ID = "yolo-tomato-quality-assessment/1"  # Correct project_id/version_id (no workspace)

def classify(frame):
    """Classify tomato using YOLOv11 (Fresh=Red/good, Rotten=Green/bad)."""
    try:
        # Resize frame (640x640 for YOLOv11)
        frame_resized = cv2.resize(frame, (640, 640))
        # Convert to base64 (no temp file)
        _, buffer = cv2.imencode('.jpg', frame_resized)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        # Run inference
        results = CLIENT.infer(img_base64, model_id=MODEL_ID)
        predictions = results['predictions']
        if predictions:
            # Get highest confidence prediction
            top_pred = max(predictions, key=lambda x: x['confidence'])
            confidence = top_pred['confidence']
            class_name = top_pred['class'].lower()
            if confidence > 0.5:
                if 'fresh' in class_name:
                    return 'Red'  # Good (ripe)
                elif 'rotten' in class_name:
                    return 'Green'  # Bad (rotten/unripe)
        return 'Uncertain'  # Reject
    except Exception as e:
        logger.error("Classification error: %s", str(e))
        return 'Uncertain'