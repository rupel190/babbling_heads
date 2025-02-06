import time
from gpiozero import MotionSensor


class MotionDetector:
    def __init__(self, debounce_time, callback=None):
        """
        MotionDetector class
        :param debounce_time: Time in seconds to prevent rapid re-triggers
        :param callback: Function to call on motion detection
        """
        self.debounce_time = debounce_time
        self.callback = callback if callback else self.default_callback
        self.last_triggered = 0

        self.PIR_SENSOR_1 = 23  # TODO: Make sure it's correct
        self.PIR_SENSOR_2 = 24
        self.pir1 = MotionSensor(self.PIR_SENSOR_1)
        self.pir2 = MotionSensor(self.PIR_SENSOR_2)

        self.pir1.when_motion = lambda: self.on_motion_detected("Pir 23")
        self.pir2.when_motion = lambda: self.on_motion_detected("Pir 24")

    def on_motion_detected(self, name):
        """Debounced motion detection"""
        current_time = time.time()
        if current_time - self.last_triggered >= self.debounce_time:
            self.last_triggered = current_time
            if self.callback:
                self.callback()
        else:
            print(
                f"Motion ignored / name = {name} / debounce_time = {self.debounce_time} / current_time = {current_time} / last_triggered = {self.last_triggered}!"
            )  # TODO: Delete, too much output

    def default_callback(self):
        print(f"Motion detected / name = !")
