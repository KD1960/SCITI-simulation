"""Named random streams from one master seed (spec §9.1).
Append new stream names at the END only; reordering changes every run."""
import numpy as np

STREAMS = ("demand", "ops", "quality", "personas", "disruptions", "rules", "lead")


def make_streams(seed: int) -> dict[str, np.random.Generator]:
    children = np.random.SeedSequence(seed).spawn(len(STREAMS))
    return {name: np.random.default_rng(c) for name, c in zip(STREAMS, children)}
