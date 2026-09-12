import numpy as np
import pytest

from sciti.data.demand import fit_series, DemandModel


def synthetic(growth=0.10, years=5, noise=0.0, seed=0):
    i = np.arange(52 * years)
    season = 1 + 0.3 * np.sin(2 * np.pi * i / 52)
    rng = np.random.default_rng(seed)
    return 1000 * (1 + growth) ** (i / 52) * season * rng.lognormal(0, noise, i.size) if noise else \
        1000 * (1 + growth) ** (i / 52) * season


def test_fit_recovers_growth_and_season():
    f = fit_series(synthetic(0.10), trend_cap=0.15)
    assert f.growth == pytest.approx(0.10, abs=0.005)
    assert np.mean(f.season) == pytest.approx(1.0)
    assert max(f.season) == pytest.approx(1.3, abs=0.02)
    assert f.n_hist == 260


def test_growth_is_capped():
    f = fit_series(synthetic(0.40), trend_cap=0.15)
    assert f.growth == 0.15


def test_generate_is_seeded_and_nonnegative(baseline):
    m = DemandModel.from_baseline(baseline, trend_cap=0.15, growth_mult=1.0)
    a = m.generate(156, np.random.default_rng(1))
    b = m.generate(156, np.random.default_rng(1))
    k = ("Retail_1", "A")
    assert np.array_equal(a[k], b[k])
    assert len(a[k]) == 156
    assert all((v >= 0).all() and np.array_equal(v, np.round(v)) for v in a.values())
    assert m.keys == sorted(m.keys) and len(m.keys) == 24


def test_first_year_matches_expected_within_5pct(baseline):
    m = DemandModel.from_baseline(baseline, trend_cap=0.15, growth_mult=1.0)
    k = ("Retail_3", "B")
    expected = sum(m.expected(*k, w) for w in range(1, 53))
    sims = [m.generate(52, np.random.default_rng(s))[k].sum() for s in range(10)]
    assert np.mean(sims) == pytest.approx(expected, rel=0.05)


def test_growth_mult_scales_future(baseline):
    lo = DemandModel.from_baseline(baseline, 0.15, growth_mult=0.0)
    hi = DemandModel.from_baseline(baseline, 0.15, growth_mult=2.0)
    assert hi.expected("Retail_1", "A", 150) > lo.expected("Retail_1", "A", 150)


def test_ar1_first_week_stationary():
    """AR(1) noise should start at stationary variance, not zero."""
    from sciti.data.demand import SeriesFit
    # Hand-made fit with high autocorrelation (φ = 0.8) and resid_sd = 0.5
    fit = SeriesFit(level=1000.0, growth=0.0, season=[1.0] * 52, resid_sd=0.5, phi=0.8, n_hist=260)
    m = DemandModel({("R", "P"): fit}, growth_mult=1.0)
    k = ("R", "P")

    # Generate 4 weeks for ~4000 seeds; use multiple independent RNG calls
    weeks = 4
    n_seeds = 4000
    week_1_means = []
    for seed in range(n_seeds):
        gen = m.generate(weeks, np.random.default_rng(seed))
        week_1_means.append(gen[k][0])

    week_1_mean = np.mean(week_1_means)
    expected_week_1 = fit.level * fit.season[0]  # growth=0, so trend = 1; season[260%52]=season[0]=1.0

    # Mean should be within 3% of expected
    assert week_1_mean == pytest.approx(expected_week_1, rel=0.03), \
        f"week_1_mean={week_1_mean}, expected={expected_week_1}, diff={abs(week_1_mean - expected_week_1) / expected_week_1:.3%}"
