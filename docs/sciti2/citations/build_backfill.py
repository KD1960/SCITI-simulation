"""One-off backfill of citations.csv from the evidence documents written 2026-09-17 to 2026-09-19.

Run from the project root:  .venv/bin/python docs/sciti2/citations/build_backfill.py
It reads every 3-column "... | ... | Flag" table in the three evidence documents and writes
docs/sciti2/citations/citations.csv. After the backfill, add new rows to the CSV by hand (or by
script) as research is done; do not rerun this over a CSV that has been edited.
"""
import csv
import re
from pathlib import Path

ROOT = Path("docs/sciti2")
OUT = ROOT / "citations" / "citations.csv"
FIELDS = ["id", "date_added", "technology", "topic", "parameter", "citation", "year", "url", "finding",
          "quality_flag", "read_level", "role", "informs_value", "source_doc"]

TECH = [("blockchain", "blockchain"), ("routing", "routing"), ("rfid", "rfid"), ("robotics", "wh_robotics"),
        ("control tower", "control_tower"), ("ml demand", "ml_forecast"), ("aps", "aps"),
        ("risk intelligence", "risk_intel"), ("general anchors", "all"), ("disruption base rates", "disruptions"),
        ("recovery time", "risk_intel"), ("first-mover", "risk_intel"), ("advance warning", "risk_intel")]
# (document, technology) -> (topic, parameter, value the evidence informed)
EFFECT = {"blockchain": ("defect_mult", "0.82 (was 0.60); LOW 0.95-1.0, HIGH 0.65"),
          "routing": ("ship_cost_mult; co2_mult", "0.92 kept; co2 0.94 (was 0.90)"),
          "rfid": ("record_error_sd x; shrink_rate x", "0.2 kept (0.25 at stores); shrink 0.8 (was 0.5)"),
          "wh_robotics": ("handling_cost_per_unit x; dispatch_delay_days", "0.8 kept; -0.6 day (was -1.0)"),
          "control_tower": ("visibility", "0.6 (was 1.0); LOW 0.25-0.35, HIGH 0.85-0.95"),
          "ml_forecast": ("forecast_skill", "0.3 at DC/MFG, 0.1 at stores (was 0.3 everywhere)"),
          "aps": ("capacity_mult", "+0.08 kept; LOW +0.03, HIGH +0.15"),
          "risk_intel": ("recovery_weeks_saved; warning_prob; early_warning_weeks",
                         "min(2 weeks, 25% of outage); warning 0.3; lead 2 weeks")}
FAIL = {"blockchain": "P(fail) 0.65 / partial 0.25 @ 0.3-0.5 / full 0.10; platform death 0.4-0.6 over 5 yrs",
        "ml_forecast": "P(fail) 0.45 / partial 0.35 @ 0.5 / full 0.20", "risk_intel": "P(fail) 0.30 / partial 0.45 @ 0.35 / full 0.25",
        "control_tower": "P(fail) 0.25 / partial 0.50 @ 0.4 / full 0.25", "rfid": "P(fail) 0.20 / partial 0.40 @ 0.5-0.7 / full 0.40",
        "aps": "P(fail) 0.15 / partial 0.50 @ 0.45 / full 0.35", "wh_robotics": "P(fail) 0.15 / partial 0.55 @ 0.5-0.7 / full 0.30",
        "routing": "P(fail) 0.15 / partial 0.50 @ 0.5-0.7 / full 0.35 (borrowed)",
        "all": "general priors: BCG 30/44/26; Standish 31/50/19; 56% less value; fat-tailed overruns"}
# Which bound each key source anchors (substring of the citation -> role). Everything else is "context".
ROLES = {"ARC Advisory": "MID anchor", "Gartner TMS ROI": "LOW-HIGH range", "Cachon & Fisher (2000)": "LOW anchor",
         "Croson & Donohue": "MID anchor", "Cachon & Fisher (1997)": "HIGH anchor", "Steckel": "LOW anchor (can hurt)",
         "M5": "MID anchor; level effect (stores LOW)", "PLoS ONE": "LOW anchor", "McKinsey (2017)": "HIGH anchor (unsourced sample)",
         "Hardgrave, Aloysius & Goyal": "LOW anchor", "Project Zipper": "HIGH anchor", "Beck / ECR": "MID anchor",
         "Checkpoint": "HIGH anchor for shrink (vendor)", "Amazon/Kiva": "MID anchor", "Azadeh": "HIGH anchor",
         "DHL + Locus": "LOW anchor", "BCG AI scheduling": "LOW anchor", "Siemens Drives": "HIGH anchor",
         "Narayan": "HIGH anchor", "Culot": "context: no quality metric exists", "Cui, Gaur": "direction is contingent",
         "ERAI": "base rate (counterfeits are a small share of defects)", "Banker, Forbes": "MID anchor (detection lag)",
         "Nokia vs Ericsson": "MID anchor (2-3 week decision lag)", "Jain, Girotra": "form: proportional 16-20%",
         "Intel, T": "floor: ~10 days even for top programs", "DHL Resilience360": "MID anchor (warning share)",
         "Everstream": "lead time anchor (up to 14 days)", "McKinsey Global Institute": "disruption frequency anchor",
         "BCI Supply Chain": "disruption frequency anchor", "Litan": "MID anchor (5-14% reach production)",
         "Capgemini Research Institute (2018)": "MID anchor (3% at scale)", "Vadgama": "LOW anchor (pre-2022 data)",
         "TradeLens": "platform-death hazard", 'Gartner "AI in Organizations"': "MID anchor (~46% never reach production)",
         "S&P Global": "MID anchor", "Fildes, Goodwin": "partial-success mechanism (overrides)",
         "McKinsey Global Supply Chain Leader Survey": "MID anchor (15% miss objectives; 2% restart)",
         'McKinsey, "Decoding success"': "partial-success anchor (65% miss ROI)", "Nike": "tail risk (go-live disruption)",
         "Kroger": "late failure timing (2.5-4.5 yrs after go-live)", "Walmart mandate": "mandated-follower pattern",
         "BCG (2020)": "general prior 30/44/26", "Standish": "general prior; size gradient", "Flyvbjerg": "fat-tailed overruns",
         "Bloch, Blumberg": "general prior: 56% less value", "Gartner (Aug 2024)": "general prior: 76% miss a target",
         "SaaS churn": "proxy for lapse rate", "Sm\u00e5ros": "multi-party scaling (pilots rarely scale)"}
# The disruption base-rate table in evidence-table.md section 3 has a different layout, so its rows are listed here.
BASE_RATES = [("BCI Supply Chain Resilience Reports (2009-2018 trend; 2024)", "56-80% of firms have >=1 supply disruption a year; 1-5 a year for ~40-55% of firms", "IND", "https://www.thebci.org/resource/bci-supply-chain-resilience-report-2024.html"),
              ("McKinsey Global Institute (2020), Risk, resilience, and rebalancing in global value chains", "A >=1-month disruption about every 3.7 years per company; ~45% of a year's EBITDA lost per decade (modelled). Used to calibrate: rate 0.2 per site-year is realistic, 0.4 a stress case", "IND", "https://www.mckinsey.com/capabilities/operations/our-insights/risk-resilience-and-rebalancing-in-global-value-chains"),
              ("Resilinc EventWatch 2018; factory-fires report", "Natural-disaster supplier-site recovery 19-25 weeks; 9% of factory fires cause >4 weeks downtime; fires ~10% of alerts", "VND", "https://resilinc.ai/learning-center/white-papers-reports/factory-fires-the-top-supply-chain-disruption/"),
              ("Matsuo (2015), IJPE 161; IEEE Spectrum on Renesas", "Severe single-site event: ~13 weeks to restart", "PR", "https://www.sciencedirect.com/science/article/abs/pii/S0925527314002278")]

DOCS = [("evidence-table.md", "2026-09-17", "effect size"),
        ("risk-intel-evidence-and-sensitivity.md", "2026-09-19", "effect size"),
        ("implementation-failure-evidence.md", "2026-09-19", "implementation failure")]


def tech_of(heading: str) -> str:
    h = heading.lower()
    return next((t for key, t in TECH if key in h), "")


def main() -> None:
    rows = []
    for doc, date, topic in DOCS:
        tech, in_table = "", False
        for line in (ROOT / doc).read_text().splitlines():
            if line.startswith("#"):
                tech, in_table = tech_of(line) or tech, False
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
            if len(cells) == 3 and cells[2] == "Flag":
                in_table = True
                continue
            if not cells:
                in_table = False
            if not in_table or len(cells) != 3 or set(cells[0]) <= {"-", " "}:
                continue
            src, finding, flag = cells
            urls = re.findall(r"https?://\S+", src)
            citation = re.sub(r"\s*;?\s*https?://\S+", "", src).strip(" .;")
            years = re.findall(r"\b(19[89]\d|20[0-2]\d)\b", citation)
            snippet = "[S]" in flag or "snippet" in flag.lower() or "abstract" in flag.lower() or "summary" in flag.lower()
            if topic == "implementation failure":
                param, informs = "p_fail; p_partial; partial_fraction", FAIL.get(tech, "")
            elif tech == "disruptions":
                param, informs = "disruption rate and length (experiments)", "rate 0.2/0.4 per site-year; 65/27/8% length bands"
            else:
                param, informs = EFFECT.get(tech, ("", ""))
            rows.append({"date_added": date, "technology": tech, "topic": topic, "parameter": param,
                         "citation": citation.replace("*", ""), "year": years[0] if years else "",
                         "url": " ; ".join(u.rstrip(").,;") for u in urls), "finding": finding.replace("**", ""),
                         "quality_flag": re.sub(r"\s*\[.*?\]", "", flag).strip(),
                         "read_level": "snippet/abstract" if snippet else
                         ("not recorded" if doc == "evidence-table.md" else "page or full text"),
                         "role": next((v for k, v in ROLES.items() if k in citation), "context"), "informs_value": informs, "source_doc": f"docs/sciti2/{doc}"})
    for cit, finding, flag, url in BASE_RATES:
        rows.append({"date_added": "2026-09-17", "technology": "disruptions", "topic": "disruption base rates",
                     "parameter": "disruption rate and length (experiments)", "citation": cit,
                     "year": re.findall(r"(20[0-2]\d)", cit)[0], "url": url, "finding": finding, "quality_flag": flag,
                     "read_level": "snippet/abstract", "role": "base-rate anchor",
                     "informs_value": "rate 0.2 (realistic) / 0.4 (stress) per site-year; 65/27/8% length bands",
                     "source_doc": "docs/sciti2/evidence-table.md"})
    for i, r in enumerate(rows, 1):
        r["id"] = f"C{i:03d}"
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "citations written to", OUT)


if __name__ == "__main__":
    main()
