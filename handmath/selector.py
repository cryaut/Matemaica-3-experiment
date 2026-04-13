import random

class VariantSelector:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.last_used = {} # token -> last chosen index

    def select(self, token: str, variants: list):
        if not variants:
            raise ValueError(f"No variants provided for token {token}")
            
        if len(variants) == 1:
            return variants[0]
        
        # Anti-repetition logic: avoid picking the exact same variant twice in a row
        last_idx = self.last_used.get(token, -1)
        choices = [i for i in range(len(variants)) if i != last_idx]
        
        if not choices:
            choices = [0] # Fallback if something goes wrong
            
        chosen_idx = self.rng.choice(choices)
        self.last_used[token] = chosen_idx
        
        return variants[chosen_idx]
