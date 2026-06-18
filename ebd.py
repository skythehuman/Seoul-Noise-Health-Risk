"""
ebd.py — EBD Computation Pipeline
==================================
Implements the EU Environmental Noise Directive (END) framework for
estimating the Environmental Burden of Disease (EBD) attributed to
traffic noise-induced Ischemic Heart Disease (IHD).
"""

import math
from dataclasses import dataclass

# ── Constants ────────────────────────────────────────────────────────
WHO_LDEN_THRESHOLD = 53       # dB(A)
RR_BASE            = 1.08     # per 10 dB above threshold
RR_PER_DB          = 10
DISABILITY_WEIGHT  = 0.521    # Im et al. (2023)

ELDERLY_THRESHOLD  = 620      # 33rd percentile of 65+PO
EBD_THRESHOLD      = 239      # 67th percentile of EBD (DALYs)


@dataclass
class EBDResult:
    """Complete output of the EBD pipeline."""
    lden: float
    rr: float
    paf: float
    ylls: float
    ylds: float
    dalys: float
    ebd: float
    risk_level: str
    exceeds_who: bool


def calc_rr(lden: float) -> float:
    """
    IHD Relative Risk (EU END).

    RR = exp( ln(1.08)/10 × (Lden − 53) )  if Lden > 53
    RR = 1                                   otherwise
    """
    if lden <= WHO_LDEN_THRESHOLD:
        return 1.0
    exponent = (math.log(RR_BASE) / RR_PER_DB) * (lden - WHO_LDEN_THRESHOLD)
    return math.exp(exponent)


def calc_paf(rr: float) -> float:
    """
    Population Attributable Fraction (Rockhill et al., 1998).

    For a single-exposure-group simplification:
    PAF = (RR − 1) / RR
    """
    if rr <= 1:
        return 0.0
    return (rr - 1) / rr


def calc_ylls(population: float, mortality_rate: float,
              remaining_life_exp: float) -> float:
    """
    Years of Life Lost.

    YLLs = (population × mortalityRate / 100,000) × remaining life expectancy
    """
    deaths = population * (mortality_rate / 100_000)
    return deaths * remaining_life_exp


def calc_ylds(population: float, prevalence_rate: float) -> float:
    """
    Years Lived with Disability.

    YLDs = (population × prevalenceRate / 100,000) × DW(0.521)
    """
    cases = population * (prevalence_rate / 100_000)
    return cases * DISABILITY_WEIGHT


def classify_risk(elderly_pop: float, ebd: float) -> str:
    """
    Three-tier risk classification.

    High:   65+PO ≥ 620  AND  EBD ≥ 239
    Medium: 65+PO ≥ 620  OR   EBD ≥ 239
    Low:    both below thresholds
    """
    e_high = elderly_pop >= ELDERLY_THRESHOLD
    b_high = ebd >= EBD_THRESHOLD
    if e_high and b_high:
        return "High"
    if e_high or b_high:
        return "Medium"
    return "Low"


def compute_ebd(lden: float, population: float, elderly_pop: float,
                mortality_rate: float, prevalence_rate: float,
                remaining_life_exp: float) -> EBDResult:
    """Run the full EBD pipeline and return all intermediate values."""
    rr = calc_rr(lden)
    paf = calc_paf(rr)
    ylls = calc_ylls(population, mortality_rate, remaining_life_exp)
    ylds = calc_ylds(population, prevalence_rate)
    dalys = ylls + ylds
    ebd = paf * dalys
    risk = classify_risk(elderly_pop, ebd)

    return EBDResult(
        lden=lden, rr=rr, paf=paf,
        ylls=ylls, ylds=ylds, dalys=dalys, ebd=ebd,
        risk_level=risk,
        exceeds_who=lden > WHO_LDEN_THRESHOLD,
    )
