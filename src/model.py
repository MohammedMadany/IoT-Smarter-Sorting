import onnxruntime as ort
import cv2
import numpy as np
import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_onnx_model(model_path='models/model.onnx', class_yaml='data/classes.yaml'):
    try:
        session = ort.InferenceSession(model_path)
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        with open(class_yaml, 'r') as f:
            class_names = yaml.safe_load(f)['names']
        logger.info("Loaded ONNX model with %d classes: %s", len(class_names), class_names)
        return session, input_name, output_name, class_names
    except Exception as e:
        logger.error("Model load failed: %s", e)
        raise

def preprocess_frame(frame, input_size=(640, 640)):
    try:
        img = cv2.resize(frame, input_size)
        img = img.transpose(2, 0, 1)  # HWC to CHW
        img = np.ascontiguousarray(img).astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)
        return img
    except Exception as e:
        logger.error("Preprocess failed: %s", e)
        return None

def run_inference(session, input_name, output_name, frame):
    preprocessed = preprocess_frame(frame)
    if preprocessed is None:
        return None
    try:
        outputs = session.run([output_name], {input_name: preprocessed})
        return outputs[0]
    except Exception as e:
        logger.error("Inference failed: %s", e)
        return None

def postprocess_detections(detections, conf_thres=0.05, iou_thres=0.5, num_classes=3):
    try:
        detections = detections[0].T  # Transpose to (8400, 4 + num_classes)
        logger.info("Raw detections shape: %s, first 5 detections: %s", detections.shape, detections[:5])
        boxes, scores, classes = [], [], []
        for det in detections:
            if len(det) == 4 + num_classes:
                box = det[:4]  # x, y, w, h
                class_probs = det[4:]  # Probabilities for each class
                conf = np.max(class_probs)
                cls = np.argmax(class_probs)
                if conf > conf_thres:
                    x1 = box[0] - box[2] / 2
                    y1 = box[1] - box[3] / 2
                    x2 = box[0] + box[2] / 2
                    y2 = box[1] + box[3] / 2
                    boxes.append([x1, y1, x2, y2])
                    scores.append(conf)
                    classes.append(cls)
                else:
                    logger.warning("Skipping detection: conf=%.2f (below threshold)", conf)
            else:
                logger.warning("Invalid detection shape: %s", det.shape)
        # Apply NMS
        indices = cv2.dnn.NMSBoxes(boxes, scores, conf_thres, iou_thres)
        filtered = [[boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3], scores[i], classes[i]] for i in indices]
        logger.info("Postprocessed %d detections", len(filtered))
        return filtered
    except Exception as e:
        logger.error("Error postprocessing detections: %s", e)
        return []

if __name__ == "__main__":
    session, input_name, output_name, class_names = load_onnx_model()
    frame = cv2.imread('data/test_image.jpg')
    detections = run_inference(session, input_name, output_name, frame)
    filtered = postprocess_detections(detections)
    logger.info("Filtered detections: %s", filtered)