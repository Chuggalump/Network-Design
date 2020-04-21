# Timer.py --- Hosts the timer class
import time


class Timer(object):
    stop_timer = -1

    # initialize the timer
    def __init__(self, duration):
        self._start_time = self.stop_timer
        self._duration = duration

    # Starts the timer
    def start(self):
        if self._start_time == self.stop_timer:
            self._start_time = time.time()

    # Stops the timer
    def stop(self):
        if self._start_time != self.stop_timer:
            self._start_time = self.stop_timer

    # Determines whether the timer is runnning
    def running(self):
        return self._start_time != self.stop_timer

    # Determines whether the timer timed out
    def timeout(self):
        if not self.running():
            return False
        else:
            return time.time() - self._start_time >= self._duration
