# Edge Sorting Sentinel
Professional IoT edge computing project for real-time sorting (plastic/fruits) using YOLOv8/ONNX on Raspberry Pi.

## Setup
1. Activate venv: `source ../yolo_env/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Run main script: `python src/main.py`

## Tests
- Camera, streaming, AI, libraries: `python tests/test_camera.py`
- Inference: `python tests/test_inference.py`

## Future
- Integrate Node-RED/ThingsBoard for monitoring, visualization, and alerts (Telegram/email).
- Add hardware control (RFID, motors).