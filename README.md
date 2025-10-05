# Edge Sorting Sentinel
Professional IoT edge computing project for real-time tomato sorting using YOLOv11 on Raspberry Pi.

## Setup
1. Activate venv: `source ../yolo_env/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Run main script: `python src/main.py`

## ThingsBoard Cloud Dashboard
- Sign up at https://thingsboard.cloud.
- Create device "Smart Sorter", copy access token to THINGSBOARD_TOKEN in main.py.
- Create dashboard with gauges for Red/Green/Reject, time-series chart for trends, pie for percentages, switches for start/stop/alarm.

## Tests
- Classifier: `python -c "from project_utils.classifier import classify; import cv2; frame = cv2.imread('data/test_image.jpg'); print(classify(frame))"`
- Analytics: `python visualize/analytics.py`

## Future
- Integrate Node-RED flows in ThingsBoard for alerts (e.g., email if Reject >50).