import pandas as pd
import paho.mqtt.client as mqtt
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_counts(detections, counts, class_names, low_conf_thres=0.05, reject_key='Reject'):
    if len(detections) == 0:
        counts[reject_key] += 1
        logger.info("No detections, incrementing Reject")
        return counts
    for det in detections:
        try:
            cls = int(det[5])
            conf = det[4]
            if conf < low_conf_thres:
                counts[reject_key] += 1
                logger.info("Low confidence detection (%.2f), incrementing Reject", conf)
            elif 0 <= cls < len(class_names):
                counts[class_names[cls]] += 1
                logger.info("Detected %s (conf: %.2f)", class_names[cls], conf)
            else:
                logger.warning("Invalid class index: %d", cls)
                counts[reject_key] += 1
        except (IndexError, ValueError) as e:
            logger.error("Error processing detection: %s", e)
            counts[reject_key] += 1
    logger.info("Updated counts: %s", counts)
    return counts

def save_to_csv(counts, csv_path='data/sorting_counts.csv'):
    try:
        df = pd.DataFrame([counts])
        header = not os.path.exists(csv_path)
        df.to_csv(csv_path, mode='a', header=header, index=False)
        logger.info("Saved to CSV: %s", csv_path)
    except Exception as e:
        logger.error("CSV save failed: %s", e)

def publish_to_mqtt(counts, broker="broker.hivemq.com", port=1883, topic="/project/sorting/counts"):
    try:
        client = mqtt.Client()
        client.connect(broker, port, 60)
        client.publish(topic, str(counts), qos=1)
        client.disconnect()
        logger.info("Published to MQTT: %s", counts)
    except Exception as e:
        logger.error("MQTT publish failed: %s", e)

if __name__ == "__main__":
    counts = {'PET': 1, 'PP': 2, 'Reject': 0}
    save_to_csv(counts)
    publish_to_mqtt(counts)