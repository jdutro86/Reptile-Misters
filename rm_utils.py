import time

# just allows easier tracking of time
class Stopwatch(object):
    def __init__(self):
        self.start_time = time.time()
        self.running = False
        self.total_time = 0

    def start(self):
        if not self.running:
            self.start_time = time.time()
            self.running = True

    def stop(self):
        if self.running:
            self.total_time += time.time() - self.start_time
            self.running = False

    def reset(self):
        self.total_time = 0
        self.start_time = time.time()

    def value(self):
        if self.running:
            return self.total_time + time.time() - self.start_time
        else:
            return self.total_time
