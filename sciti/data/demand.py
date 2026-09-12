"""Future demand from 2020–2024 weekly history (spec §5.2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class SeriesFit:
    level: float
    growth: float
    season: list[float]
    resid_sd: float
    phi: float
    n_hist: int


def fit_series(values: Sequence[float], trend_cap: float) -> SeriesFit:
    y = np.asarray(values, dtype=float)
    years = y.size // 52
    y = y[: years * 52]
    annual = y.reshape(years, 52).sum(axis=1)
    slope = np.polyfit(np.arange(years), np.log(np.maximum(annual, 1e-9)), 1)[0]
    growth = float(np.clip(np.exp(slope) - 1, -trend_cap, trend_cap))
    i = np.arange(y.size)
    trend = (1 + growth) ** (i / 52)
    detr = y / trend
    season = detr.reshape(years, 52).mean(axis=0)
    season = season / season.mean()
    level = float(np.mean(detr / season[i % 52]))
    fitted = level * trend * season[i % 52]
    resid = np.log(np.maximum(y, 1e-9) / fitted)
    sd = float(resid.std(ddof=1))
    phi = float(np.corrcoef(resid[:-1], resid[1:])[0, 1]) if sd > 0 else 0.0
    return SeriesFit(level, growth, [float(s) for s in season], sd, phi if phi > 0.2 else 0.0, int(y.size))


class DemandModel:
    def __init__(self, fits: dict[tuple[str, str], SeriesFit], growth_mult: float = 1.0):
        self.fits = fits
        self.growth_mult = growth_mult
        self.keys = sorted(fits)

    @classmethod
    def from_baseline(cls, baseline: dict, trend_cap: float, growth_mult: float) -> "DemandModel":
        fits = {(r, p): fit_series(series, trend_cap)
                for r, prods in baseline["demand_history"].items() for p, series in prods.items()}
        return cls(fits, growth_mult)

    def expected(self, retailer: str, product: str, week: int) -> float:
        f = self.fits[(retailer, product)]
        i = f.n_hist + week - 1
        return f.level * (1 + f.growth * self.growth_mult) ** (i / 52) * f.season[i % 52]

    def generate(self, weeks: int, rng: np.random.Generator) -> dict[tuple[str, str], np.ndarray]:
        out = {}
        for key in self.keys:
            f = self.fits[key]
            z = rng.standard_normal(weeks)
            e = np.empty(weeks)
            prev = 0.0
            scale = np.sqrt(1 - f.phi ** 2) * f.resid_sd
            for t in range(weeks):
                prev = f.phi * prev + scale * z[t]
                e[t] = prev
            mean = np.array([self.expected(*key, w) for w in range(1, weeks + 1)])
            out[key] = np.maximum(0.0, np.round(mean * np.exp(e - f.resid_sd ** 2 / 2)))
        return out
