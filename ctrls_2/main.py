import Jetson.GPIO as GPIO
from inputGUI import show_input_window

if __name__ == "__main__":
    try:
        show_input_window()  # Show input window on startup
    except KeyboardInterrupt:
        GPIO.cleanup()
