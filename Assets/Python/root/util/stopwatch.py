import time

class Stopwatch:
    def __init__(self):
        self._start_time = None
        self._is_running = False
        self._elapsed_time = 0

    def start(self):
        if not self._is_running:
            self._start_time = time.perf_counter()
            self._is_running = True

    def stop(self):
        if self._is_running:
            current_time = time.perf_counter()
            self._elapsed_time += current_time - self._start_time
            self._is_running = False

    def reset(self):
        self._start_time = None
        self._is_running = False
        self._elapsed_time = 0

    @property
    def elapsed(self):
        if self._is_running:
            current_time = time.perf_counter()
            return self._elapsed_time + (current_time - self._start_time)
        else:
            return self._elapsed_time
    
    def timeStamp(self, message):
        self.stop()
        print(f"{message} Time taken: {int(self.elapsed * 1000)} ms")
        self.start()