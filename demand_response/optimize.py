import numpy as np
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value, LpStatus


PEAK_HOURS   = [8, 9, 10, 18, 19, 20]
FLAT_HOURS   = [7, 11, 12, 13, 14, 15, 16, 17, 21]
VALLEY_HOURS = [22, 23, 0, 1, 2, 3, 4, 5, 6]
HOURS        = list(range(24))

REDUCTION_FACTOR = {'IL': 1.0, 'SL': 0.0, 'AL': 0.4}

def tariff(h):
    if h in PEAK_HOURS:   return 1.257
    if h in FLAT_HOURS:   return 0.787
    return 0.299

PRICE = {h: tariff(h) for h in HOURS}


def run_optimization(appliances_qs):
    """
    Run LP optimization on a queryset of ApplianceProfile objects.
    Returns a dict with schedule, hourly profile, and metrics.
    """
    import pandas as pd

    # Build dataframe from DB queryset
    records = []
    for a in appliances_qs:
        records.append({
            'id':       a.id,
            'name':     a.name,
            'power_kw': a.power_kw,
            'duration': a.duration_hrs,
            'start':    a.start_window,
            'end':      a.end_window,
            'class':    a.appliance_class,
        })

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("No appliances found for this user.")

    il_df   = df[df['class'] == 'IL']
    flex_df = df[df['class'] != 'IL']

    # --- LP model (her core logic, unchanged) ---
    model = LpProblem("DR", LpMinimize)
    x = LpVariable.dicts("start",
        [(i, t) for i in flex_df.index for t in HOURS], cat="Binary")

    for i in flex_df.index:
        model += lpSum(x[(i, t)] for t in HOURS) == 1

    for i, row in flex_df.iterrows():
        dur, sw, ew = int(row['duration']), int(row['start']), int(row['end'])
        for t in HOURS:
            valid = True
            for k in range(dur):
                h = (t + k) % 24
                if sw <= ew:
                    if not (sw <= h <= ew): valid = False; break
                else:
                    if not (h >= sw or h <= ew): valid = False; break
            if not valid:
                model += x[(i, t)] == 0

    load_dr = lpSum(
        x[(i, t)] * sum(
            df.loc[i, 'power_kw'] * (1 - REDUCTION_FACTOR[df.loc[i, 'class']])
            for k in range(df.loc[i, 'duration'])
            if ((t + k) % 24) in PEAK_HOURS
        )
        for i in flex_df.index for t in HOURS
    )
    cost = lpSum(
        x[(i, t)] * sum(
            df.loc[i, 'power_kw'] * (1 - REDUCTION_FACTOR[df.loc[i, 'class']]) * PRICE[(t + k) % 24]
            for k in range(df.loc[i, 'duration'])
        )
        for i in flex_df.index for t in HOURS
    )
    smooth = lpSum(
        x[(i, t)] * df.loc[i, 'power_kw'] * (2 if t in PEAK_HOURS else 0)
        for i in flex_df.index for t in HOURS
    )

    model += load_dr + cost + 0.3 * smooth
    model.solve()

    if LpStatus[model.status] != 'Optimal':
        raise ValueError(f"Solver did not find optimal solution: {LpStatus[model.status]}")

    # --- Build schedule output ---
    schedule = []
    for i in flex_df.index:
        for t in HOURS:
            if value(x[(i, t)]) == 1:
                schedule.append({
                    'appliance':  df.loc[i, 'name'],
                    'class':      df.loc[i, 'class'],
                    'start_hour': t,
                    'duration':   int(df.loc[i, 'duration']),
                })

    # --- Hourly load profiles ---
    baseline  = np.zeros(24)
    optimized = np.zeros(24)

    for _, r in il_df.iterrows():
        for h in HOURS:
            baseline[h]  += r['power_kw']
            optimized[h] += r['power_kw']

    for _, r in flex_df.iterrows():
        s = int(r['start'])
        for k in range(int(r['duration'])):
            baseline[(s + k) % 24] += r['power_kw']

    for item in schedule:
        row = df[df['name'] == item['appliance']].iloc[0]
        factor = 1 - REDUCTION_FACTOR[row['class']]
        for k in range(item['duration']):
            optimized[(item['start_hour'] + k) % 24] += row['power_kw'] * factor

    baseline_cost  = sum(baseline[h]  * PRICE[h] for h in HOURS)
    optimized_cost = sum(optimized[h] * PRICE[h] for h in HOURS)

    return {
        'schedule':      schedule,
        'hourly':        [{'hour': h, 'baseline_kw': round(baseline[h], 3),
                           'optimized_kw': round(optimized[h], 3)} for h in HOURS],
        'baseline_cost':  round(baseline_cost, 2),
        'optimized_cost': round(optimized_cost, 2),
        'cost_saving':    round(baseline_cost - optimized_cost, 2),
        'peak_reduction': round(
            (baseline.max() - optimized.max()) / baseline.max() * 100, 2
        ),
    }