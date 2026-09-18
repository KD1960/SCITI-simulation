"""Named random streams from one master seed (spec §9.1).
Append new stream names at the END only; reordering changes every run."""
import zlib

import numpy as np

STREAMS = ("demand", "ops", "quality", "personas", "disruptions", "rules")


def make_streams(seed: int) -> dict[str, np.random.Generator]:
    children = np.random.SeedSequence(seed).spawn(len(STREAMS))
    return {name: np.random.default_rng(c) for name, c in zip(STREAMS, children)}


def shipment_rng(seed: int, src: str, dst: str, item: str, week: int) -> np.random.Generator:
    """Draws for one shipment, keyed by lane and week, so paired runs see the same draws
    no matter how many shipments came before."""
    lane = zlib.crc32(f"{src}|{dst}|{item}".encode())
    return np.random.default_rng([seed, lane, week])


def warning_draw(seed: int, disruption_index: int) -> float:
    """One draw in [0, 1) per disruption: subscribers whose warning_prob beats it see the event coming."""
    return float(np.random.default_rng([seed, zlib.crc32(b"warning"), disruption_index]).random())
