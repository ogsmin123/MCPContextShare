import random, time

class RNG:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
    def choice(self, seq):
        return self.rng.choice(seq)
    def randint(self, a,b):
        return self.rng.randint(a,b)
    def random(self):
        return self.rng.random()

def sleep_ms(ms):
    time.sleep(ms/1000.0)
