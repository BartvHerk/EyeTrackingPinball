import timeit

class Stopwatch:
    def __init__(self):
        self.start_time = 0
        self.time_elapsed = 0
        self.playing = False
    

    def set_time(self, time):
        self.time_elapsed = time / 1000
        self.start_time = timeit.default_timer()
    

    def play(self):
        self.start_time = timeit.default_timer()
        self.playing = True

    
    def pause(self):
        time_elapsed_since_start = timeit.default_timer() - self.start_time
        self.time_elapsed += time_elapsed_since_start
        self.playing = False

    
    def get_time(self):
        time_elapsed_since_start = timeit.default_timer() - self.start_time
        return int((self.time_elapsed + (time_elapsed_since_start if self.playing else 0)) * 1000)
