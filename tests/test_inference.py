import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model import load_onnx_model, run_inference, postprocess_detections
from src.camera import initialize_input, capture_frame
import cv2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_inference():
    session, input_name, output_name, class_names = load_onnx_model()
    input_source, input_type = initialize_input(source='data/test_video.mp4')
    frame = capture_frame(input_source, input_type)
    if frame is None:
        logger.error("Failed to load test video frame")
        return
    detections = run_inference(session, input_name, output_name, frame)
    if detections is not None:
        filtered = postprocess_detections(detections, conf_thres=0.05)
        logger.info("Inference test OK, filtered detections: %s", filtered)
    else:
        logger.error("Inference failed on test video frame")
    input_source.release()

if __name__ == "__main__":
    test_inference()