import json
import os
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value, PULP_CBC_CMD
from django.conf import settings

warnings.filterwarnings('ignore')

# ── Tariff and carbon constants (UK GBP) ─────────────────────────────────────
TARIFF = {
    'Peak':     38.0,   # pence/kWh
    'Normal':   20.0,
    'Off-Peak':  8.5,
}
CARBON = {
    'Peak':     0.35,   # kg CO2/kWh
    'Normal':   0.22,
    'Off-Peak': 0.12,
}
CRITICAL_RATIO = 0.60   # 60% of load is inflexible
FLEXIBLE_RATIO = 0.40   # 40% can be shifted

ML_DIR = os.path.join(settings.BASE_DIR, 'forecasting', 'ml')


def _load_peak_config():
    """
    Load peak threshold and peak hour set from forecast_results.json.
    Falls back to sensible defaults if the file is not found.
    """
    results_path = os.path.join(ML_DIR, 'forecast_results.json')
    if os.path.exists(results_path):
        with open(results_path) as f:
            data = json.load(f)
        peak_info = data.get('peak_info', {})
        global_threshold = peak_info.get('threshold', 2.0)
        peak_hours = set(peak_info.get('peak_hours', [16, 17, 18, 19]))
    else:
        global_threshold = 2.0
        peak_hours = {16, 17, 18, 19}

    return global_threshold, peak_hours


def _build_period_map(peak_hours: set) -> dict:
    """Map each hour 0-23 to Peak / Normal / Off-Peak."""
    off_peak_hours = {0, 1, 2, 3, 4, 5, 6, 23}
    period_map = {}
    for h in range(24):
        if h in peak_hours:
            period_map[h] = 'Peak'
        elif h in off_peak_hours:
            period_map[h] = 'Off-Peak'
        else:
            period_map[h] = 'Normal'
    return period_map


def _severity(load_kw: float, threshold_kw: float) -> str:
    ratio = load_kw / threshold_kw if threshold_kw > 0 else 1
    if ratio >= 2.0:   return 'critical'
    if ratio >= 1.5:   return 'high'
    if ratio >= 1.2:   return 'medium'
    return 'low'


def run_optimization_for_meter(mac_address: str, hourly_loads: list) -> dict:
    """
    Core optimizer — runs per smart meter using its 24-hour load curve.

    Parameters
    ----------
    mac_address  : str   — the meter's MAC address (e.g. 'AA:BB:CC:DD:EE:FF')
    hourly_loads : list  — 24 floats representing kWh consumption per hour (hour 0-23)

    Returns
    -------
    dict — full optimization result ready to save to DRResult model and return via API
    """
    if len(hourly_loads) != 24:
        raise ValueError(f"Expected 24 hourly values, got {len(hourly_loads)}")

    global_threshold, peak_hours = _load_peak_config()
    period_map    = _build_period_map(peak_hours)
    house_threshold = global_threshold / 4.0   # per-household share

    hours         = list(range(24))
    predicted     = [float(x) for x in hourly_loads]
    ai_labels     = [period_map[h] for h in hours]
    max_raw_load  = max(predicted)

    # ── LP optimization ───────────────────────────────────────────────────────
    lp_model = LpProblem(f"DR_{mac_address.replace(':', '')}", LpMinimize)
    shifted  = LpVariable.dicts("Shift", hours, lowBound=0)

    critical_load  = [CRITICAL_RATIO * x for x in predicted]
    flexible_load  = [FLEXIBLE_RATIO * x for x in predicted]
    total_flexible = sum(flexible_load)

    # Objective: minimise total electricity cost after shifting
    lp_model += lpSum(
        (critical_load[h] + shifted[h]) * TARIFF[ai_labels[h]]
        for h in hours
    )

    # Constraints
    lp_model += lpSum(shifted[h] for h in hours) == total_flexible   # conserve energy
    p_limit = 1.85 * max_raw_load
    for h in hours:
        lp_model += critical_load[h] + shifted[h] <= p_limit         # capacity limit
        lp_model += shifted[h] >= 0.05 * flexible_load[h]            # minimum shift

    lp_model.solve(PULP_CBC_CMD(msg=False))

    # ── Results ───────────────────────────────────────────────────────────────
    opt_total  = [critical_load[h] + value(shifted[h]) for h in hours]
    orig_cost  = sum(predicted[h] * TARIFF[ai_labels[h]] for h in hours) / 100.0    # GBP
    opt_cost   = sum(opt_total[h] * TARIFF[ai_labels[h]] for h in hours) / 100.0    # GBP
    co2_saved  = sum(
        (predicted[h] - opt_total[h]) * CARBON[ai_labels[h]]
        for h in hours
    )
    saving_gbp = orig_cost - opt_cost

    # ── Risk assessment ───────────────────────────────────────────────────────
    risk_flagged = max_raw_load > house_threshold
    severity     = _severity(max_raw_load, house_threshold) if risk_flagged else 'low'

    # ── Messages (her exact wording) ─────────────────────────────────────────
    if saving_gbp > 0:
        congrats_msg = (
            f"Congratulations! Through Smart Scheduling today, "
            f"you saved GBP {saving_gbp:.2f}."
        )
    else:
        congrats_msg = "Your load is already well-optimised for today."

    env_msg = (
        f"Environmental Impact: You reduced your domestic carbon footprint "
        f"by {co2_saved:.2f} kg of CO2."
    )

    if risk_flagged:
        notification = (
            f"RISK ALERT: Our smart meters detected a load spike event. "
            f"Your consumption reached {max_raw_load:.2f} kW, exceeding your "
            f"safe threshold of {house_threshold:.2f} kW. "
            f"Recommendation: Avoid running high-load appliances concurrently "
            f"during peak hours."
        )
    else:
        notification = (
            "GRID RISK SHIELD: System check normal. "
            "Your usage profile stayed entirely within safe capacity bounds."
        )

    return {
        'mac_address':        mac_address,
        'original_cost_gbp':  round(orig_cost,  4),
        'optimized_cost_gbp': round(opt_cost,   4),
        'cost_saving_gbp':    round(saving_gbp, 4),
        'carbon_reduced_kg':  round(co2_saved,  4),
        'has_risk':           risk_flagged,
        'risk_events':        1 if risk_flagged else 0,
        'peak_threshold_kw':  round(house_threshold, 4),
        'user_peak_load_kw':  round(max_raw_load,    4),
        'severity':           severity,
        'congratulations_message': congrats_msg,
        'environmental_message':   env_msg,
        'notification_text':       notification,
        'hourly_json': {
            'hours':               hours,
            'original_curve_kwh':  [round(x, 3) for x in predicted],
            'optimised_curve_kwh': [round(x, 3) for x in opt_total],
            'ai_labels':           ai_labels,
        }
    }


def run_optimization_for_user(user):
    """
    Run optimization for ALL active meters belonging to a user.
    Returns a list of result dicts — one per meter.
    """
    from properties.models import SmartMeter
    from forecasting.models import LoadReading

    meters = SmartMeter.objects.filter(
        property__owner=user, is_active=True
    )

    results = []
    for meter in meters:
        # Get the most recent 24 hourly readings for this meter
        # In production: filter by meter. For now, use global LoadReading.
        readings_qs = LoadReading.objects.order_by('-datetime')[:24]
        if readings_qs.count() < 24:
            continue

        hourly_loads = list(
            reversed([r.load_kwh for r in readings_qs])
        )

        try:
            result = run_optimization_for_meter(meter.mac_address, hourly_loads)
            result['meter_id'] = meter.id
            result['meter_label'] = meter.label
            results.append(result)
        except Exception as e:
            results.append({
                'mac_address': meter.mac_address,
                'error': str(e)
            })

    return results