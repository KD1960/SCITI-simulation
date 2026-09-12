"""Ridge Line network: 48 nodes, links per the document (spec §5.1)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from sciti.data.loader import SKUS

ROLES = ("Supplier", "CM", "MFG", "DC", "Retail")
PRODUCTS = ("A", "B", "C")

SITES = {  # id: (role, city, lat, lon)
    "CM_1": ("CM", "Taipei, Taiwan", 25.03, 121.57),
    "CM_2": ("CM", "Bangalore, India", 12.97, 77.59),
    "CM_3": ("CM", "Guadalajara, Mexico", 20.67, -103.35),
    "CM_4": ("CM", "Munich, Germany", 48.14, 11.58),
    "MFG_US": ("MFG", "Los Angeles, CA", 34.05, -118.24),
    "MFG_China": ("MFG", "Shenzhen, China", 22.54, 114.06),
    "DC_Houston": ("DC", "Houston, TX", 29.76, -95.37),
    "DC_Dubai": ("DC", "Dubai, UAE", 25.20, 55.27),
    "DC_Shanghai": ("DC", "Shanghai, China", 31.23, 121.47),
    "DC_Sofia": ("DC", "Sofia, Bulgaria", 42.70, 23.32),
    "Retail_1": ("Retail", "Columbus, OH", 39.96, -83.00),
    "Retail_2": ("Retail", "São Paulo, Brazil", -23.55, -46.63),
    "Retail_3": ("Retail", "Barcelona, Spain", 41.39, 2.17),
    "Retail_4": ("Retail", "Nairobi, Kenya", -1.29, 36.82),
    "Retail_5": ("Retail", "Mumbai, India", 19.08, 72.88),
    "Retail_6": ("Retail", "Singapore", 1.35, 103.82),
    "Retail_7": ("Retail", "Tokyo, Japan", 35.68, 139.69),
    "Retail_8": ("Retail", "Melbourne, Australia", -37.81, 144.96),
}
DC_RETAIL = {
    "DC_Houston": ["Retail_1", "Retail_2"],
    "DC_Dubai": ["Retail_3", "Retail_4", "Retail_5"],
    "DC_Sofia": ["Retail_3"],
    "DC_Shanghai": ["Retail_5", "Retail_6", "Retail_7", "Retail_8"],
}


def great_circle_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 3958.8 * 2 * math.asin(min(1.0, math.sqrt(a)))


@dataclass
class Node:
    id: str
    role: str
    city: str
    lat: float
    lon: float
    skus: tuple[str, ...] = ()


@dataclass
class Network:
    nodes: dict[str, Node]
    order: list[str]
    upstream: dict[str, list[str]]
    downstream: dict[str, list[str]]
    bom: dict[str, int]
    skus: list[str]
    suppliers_of: dict[str, list[str]]
    cm_of: dict[str, str]
    source_share: dict[str, dict[str, float]] = field(default_factory=dict)

    def partners(self, node_id: str) -> list[str]:
        return sorted(set(self.upstream[node_id]) | set(self.downstream[node_id]))

    def miles(self, a: str, b: str) -> float:
        na, nb = self.nodes[a], self.nodes[b]
        return great_circle_miles(na.lat, na.lon, nb.lat, nb.lon)

    def by_role(self, role: str) -> list[str]:
        return [n for n in self.order if self.nodes[n].role == role]


def build_network(baseline: dict, assumptions) -> Network:
    bom = {sku: v["units"] for sku, v in baseline["bom"].items()}
    skus = [s for s in SKUS if s in baseline["bom"]]  # BOM order; baseline.json keys are sorted
    cm_of = {sku: v["cm"] for sku, v in baseline["bom"].items()}
    nodes: dict[str, Node] = {}
    sup_ids = sorted(baseline["suppliers"], key=lambda s: int(s.split("_")[1]))
    for k, sid in enumerate(sup_ids):
        s = baseline["suppliers"][sid]
        _, _, clat, clon = SITES[s["cm"]]
        ang = 2 * math.pi * (k % 12) / 12   # illustrative ring around the CM (spec §5.1)
        nodes[sid] = Node(sid, "Supplier", f"near {SITES[s['cm']][1]} (illustrative)",
                          clat + 4 * math.sin(ang), clon + 4 * math.cos(ang), (s["sku"],))
    for nid, (role, city, lat, lon) in SITES.items():
        made = tuple(sku for sku in skus if cm_of[sku] == nid) if role == "CM" else ()
        nodes[nid] = Node(nid, role, city, lat, lon, made)
    order = sup_ids + [n for r in ROLES[1:] for n in sorted((i for i in SITES if SITES[i][0] == r),
                                                             key=_natural)]
    up = {n: [] for n in order}
    down = {n: [] for n in order}

    def link(a, b):
        down[a].append(b)
        up[b].append(a)

    for sid in sup_ids:
        link(sid, baseline["suppliers"][sid]["cm"])
    for cm in ("CM_1", "CM_2", "CM_3", "CM_4"):
        for mfg in ("MFG_US", "MFG_China"):
            link(cm, mfg)
    for mfg in ("MFG_US", "MFG_China"):
        for dc in DC_RETAIL:
            link(mfg, dc)
    for dc, rets in DC_RETAIL.items():
        for r in rets:
            link(dc, r)
    up = {k: sorted(v) for k, v in up.items()}
    down = {k: sorted(v) for k, v in down.items()}
    suppliers_of = {sku: [s for s in sup_ids if baseline["suppliers"][s]["sku"] == sku] for sku in skus}
    share = {}
    for dc in DC_RETAIL:
        share[dc] = dict(assumptions.mfg_share[dc])
    for r in [n for n in order if nodes[n].role == "Retail"]:
        share[r] = dict(assumptions.dc_split.get(r, {up[r][0]: 1.0}))
    for buyer, s in share.items():
        if sorted(s) != up[buyer] or abs(sum(s.values()) - 1) > 1e-9:
            raise ValueError(f"source shares for {buyer} must cover {up[buyer]} and sum to 1: {s}")
    return Network(nodes, order, up, down, bom, skus, suppliers_of, cm_of, share)


def _natural(node_id: str):
    head, _, tail = node_id.rpartition("_")
    return (head, int(tail)) if tail.isdigit() else (node_id, 0)
