import random


def make_synthetic_rows(n_rows: int, seed: int | None = None) -> list[dict]:
    rng = random.Random(seed)
    return [
        {
            "patient_id": f"P{i + 1:04d}",
            "age": rng.randint(18, 90),
            "risk_score": round(rng.random(), 3),
        }
        for i in range(n_rows)
    ]