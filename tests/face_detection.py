import os
import cv2
import time
from ultralytics import YOLO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    model = YOLO('yolov8n.pt')  # Pre-trained YOLOv8 face model (download from ultralytics if needed)
    cap = cv2.VideoCapture(0)  # Raspberry Pi camera
    save_dir = 'data/face_images'
    os.makedirs(save_dir, exist_ok=True)
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            results = model(frame)
            annotated_frame = results[0].plot()
            cv2.imshow('Face Detection', annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Save image if face detected
            if len(results[0].boxes) > 0:
                frame_count += 1
                cv2.imwrite(f'{save_dir}/face_{frame_count}.jpg', frame)
                logger.info("Face detected and saved: face_%d.jpg", frame_count)
            time.sleep(0.05)  # ~20 FPS
    except KeyboardInterrupt:
        logger.info("Shutting down")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()