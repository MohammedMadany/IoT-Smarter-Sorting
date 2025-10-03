import cv2
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_input(source=None, resolution=(320, 240)):
    """Initialize camera or video input."""
    if source is None:
        # Use camera
        try:
            from picamera2 import Picamera2
            picam2 = Picamera2()
            config = picam2.create_preview_configuration(main={"size": resolution})
            picam2.configure(config)
            picam2.start()
            logger.info("Camera initialized with resolution %s", resolution)
            return picam2, 'camera'
        except ImportError:
            logger.error("Picamera2 not available, falling back to OpenCV camera")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Failed to open camera")
                raise ValueError("Failed to open camera")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            logger.info("OpenCV camera initialized with resolution %s", resolution)
            return cap, 'camera'
    else:
        # Use video
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logger.error("Failed to open video: %s", source)
            raise ValueError("Failed to open video")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        logger.info("Video input initialized: %s", source)
        return cap, 'video'

def capture_frame(input_source, input_type):
    """Capture a single frame from camera or video."""
    try:
        if input_type == 'camera':
            if hasattr(input_source, 'capture_array'):
                frame = input_source.capture_array()
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                ret, frame = input_source.read()
                if not ret:
                    logger.warning("Failed to capture camera frame")
                    return None
                return frame
        elif input_type == 'video':
            ret, frame = input_source.read()
            if not ret:
                logger.warning("End of video reached")
                return None
            return frame
    except Exception as e:
        logger.error("Frame capture failed: %s", e)
        return None

def stream_real_time(input_source, input_type, inference_func=None, duration=None, display=False):
    """Stream frames in real-time, optionally with inference and display."""
    start_time = time.time()
    try:
        while True:
            frame = capture_frame(input_source, input_type)
            if frame is None:
                break
            if inference_func:
                frame = inference_func(frame)
            if display:
                cv2.imshow('Stream', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            if duration and time.time() - start_time > duration:
                break
            time.sleep(0.05)  # ~20 FPS
    except KeyboardInterrupt:
        logger.info("Stream stopped by user")
    finally:
        if input_type == 'camera':
            if hasattr(input_source, 'stop'):
                input_source.stop()
            else:
                input_source.release()
        elif input_type == 'video':
            input_source.release()
        if display:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    input_source, input_type = initialize_input(source='data/test_video.mp4')
    stream_real_time(input_source, input_type, display=True)