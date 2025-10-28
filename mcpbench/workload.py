import random

class AccessSampler:
    def __init__(self, n_items: int, kind: str, zipf_alpha: float=0.99, hotspot_fraction:float=0.05, hotspot_share:float=0.5, seed:int=42):
        self.rng = random.Random(seed)
        self.n = n_items
        self.kind = kind
        if kind == 'zipf':
            ranks = range(1, n_items+1)
            weights = [1/(r**zipf_alpha) for r in ranks]
            s = sum(weights)
            self.p = [w/s for w in weights]
        elif kind == 'hotspot':
            self.hot_n = max(1, int(n_items * hotspot_fraction))
            self.hot_ids = list(range(self.hot_n))
            self.cold_ids = list(range(self.hot_n, n_items))
            self.hot_p = hotspot_share / self.hot_n
            self.cold_p = (1 - hotspot_share) / max(1, (n_items - self.hot_n))

    def sample(self):
        if self.kind == 'zipf':
            x = self.rng.random(); c=0
            for i,p in enumerate(self.p):
                c += p
                if x <= c:
                    return i
            return self.n-1
        elif self.kind == 'hotspot':
            if self.rng.random() < 0.5:
                return self.rng.choice(self.hot_ids)
            return self.rng.choice(self.cold_ids)
        else:
            return self.rng.randrange(self.n)

class Workload:
    def __init__(self, kind: str, ops_per_sec: int, read_ratio: float):
        self.kind = kind
        self.ops_per_sec = ops_per_sec
        self.read_ratio = read_ratio

    def next_op(self, t: float):
        if self.kind == 'BU':
            burst = 2 if int(t) % 30 < 10 else 1
            return burst, 'read' if random.random() < 0.5 else 'write'
        else:
            return 1, 'read' if random.random() < self.read_ratio else 'write'
