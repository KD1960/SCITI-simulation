from sciti.config import Config
from sciti.data.demand import DemandModel
from sciti.engine.state import init_state
from sciti.network import build_network
from sciti.rng import make_streams
from sciti.tech.catalog import load_catalog


def make_state(baseline, weeks=30, seed=1):
    cfg = Config(name="t", seed=seed, weeks=weeks)
    net = build_network(baseline, cfg.assumptions)
    dm = DemandModel.from_baseline(baseline, cfg.demand.trend_cap, cfg.demand.growth_mult)
    streams = make_streams(seed)
    demand = dm.generate(weeks, streams["demand"])
    return init_state(cfg, baseline, net, dm, demand, load_catalog(), streams)
