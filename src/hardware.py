import RPi.GPIO as GPIO
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPIO Pins
SERVO_MOVING_PIN = 25  # Servo 1 for moving tomatoes
SERVO_SORTING_PIN = 17  # Servo 2 for sorting (90° good, 180° bad)

pwm_moving = None
pwm_sorting = None

def initialize_gpio():
    global pwm_moving, pwm_sorting
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup([SERVO_MOVING_PIN, SERVO_SORTING_PIN], GPIO.OUT)
    pwm_moving = GPIO.PWM(SERVO_MOVING_PIN, 50)
    pwm_sorting = GPIO.PWM(SERVO_SORTING_PIN, 50)
    pwm_moving.start(0)
    pwm_sorting.start(0)
    logger.info("GPIO initialized for servos")

def move_servo(pin, duty):
    pwm = pwm_moving if pin == SERVO_MOVING_PIN else pwm_sorting
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)
    logger.info("Servo %d duty %.1f", pin, duty)

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