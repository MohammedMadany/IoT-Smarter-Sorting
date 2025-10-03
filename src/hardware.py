import RPi.GPIO as GPIO
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPIO Pins (aligned with tutorial)
SERVO_MOVING_PIN = 25  # Servo 1 for moving tomatoes
SERVO_SORTING_PIN = 17  # Servo 2 for dropping to bins

# PWM objects will be initialized in initialize_gpio()
pwm_moving = None
pwm_sorting = None

# Initialize GPIO
def initialize_gpio():
    global pwm_moving, pwm_sorting
    GPIO.setmode(GPIO.BCM)  # Set BCM mode for pin numbering
    GPIO.setup([SERVO_MOVING_PIN, SERVO_SORTING_PIN], GPIO.OUT)
    pwm_moving = GPIO.PWM(SERVO_MOVING_PIN, 50)  # 50 Hz for servo
    pwm_sorting = GPIO.PWM(SERVO_SORTING_PIN, 50)
    pwm_moving.start(0)
    pwm_sorting.start(0)
    logger.info("GPIO initialized for servos")

# Servo Control
def move_servo(pin, duty):
    """Move servo with duty cycle (e.g., 2.0 for close, 7.0-12.0 for open/move)."""
    pwm = pwm_moving if pin == SERVO_MOVING_PIN else pwm_sorting
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)  # Allow servo to move
    pwm.ChangeDutyCycle(0)  # Stop signal
    logger.info("Servo on pin %d set to duty cycle %.1f", pin, duty)

# Cleanup
def cleanup():
    global pwm_moving, pwm_sorting
    if pwm_moving:
        pwm_moving.stop()
    if pwm_sorting:
        pwm_sorting.stop()
    GPIO.cleanup()
    logger.info("Hardware cleaned up")

if __name__ == "__main__":
    initialize_gpio()
    try:
        # Test Servo 1 (moving)
        move_servo(SERVO_MOVING_PIN, 7.0)
        time.sleep(1)
        move_servo(SERVO_MOVING_PIN, 2.0)
        # Test Servo 2 (sorting)
        move_servo(SERVO_SORTING_PIN, 12.0)
        time.sleep(1)
        move_servo(SERVO_SORTING_PIN, 2.0)
    except KeyboardInterrupt:
        cleanup()