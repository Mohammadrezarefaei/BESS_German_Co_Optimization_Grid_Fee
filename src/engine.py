# ==========================================
# GERMAN BESS CO-OPTIMIZATION & PEAK SHAVING ENGINE
# ==========================================

import numpy as np
import pandas as pd
import pulp as plp

def generate_german_market_data():
    """
    Generates a 24-hour sample dataset including EPEX Day-Ahead prices,
    German aFRR capacity prices, and industrial load profiles for peak shaving.
    """
    np.random.seed(42)
    hours = pd.date_range(start="2026-06-01", periods=24, freq="h")
    
    # EPEX Day-Ahead prices (€/MWh) with typical duck-curve / peak behaviors
    da_prices = 80 + 40 * np.sin(np.linspace(0, 2 * np.pi, 24)) + np.random.normal(0, 15, 24)
    da_prices[18:21] = da_prices[18:21] + 120  # Evening price spike
    
    # aFRR capacity prices (€/MW/h)
    afrr_cap_prices = 25 + 10 * np.abs(np.cos(np.linspace(0, 2 * np.pi, 24))) + np.random.normal(0, 3, 24)
    
    # Industrial load profile (MW) exhibiting high peaks during midday
    industrial_load = 4.0 + 1.5 * np.sin(np.linspace(0, 2 * np.pi, 24)) + np.random.normal(0, 0.2, 24)
    industrial_load[10:14] = industrial_load[10:14] + 3.0  # Industrial peak hours requiring shaving
    
    df = pd.DataFrame({
        "Timestamp": hours,
        "DA_Price": da_prices,
        "aFRR_Capacity_Price": afrr_cap_prices,
        "Industrial_Load_MW": industrial_load
    })
    df.set_index("Timestamp", inplace=True)
    return df

def run_true_co_optimization(df, capacity_mwh=10.0, max_power_mw=5.0, efficiency=0.9, grid_fee_penalty_rate=150.0):
    """
    Solves the MILP co-optimization problem integrating Day-Ahead arbitrage, 
    aFRR capacity reservation, and a grid peak-shaving penalty term in the objective function.
    """
    model = plp.LpProblem("German_BESS_True_CoOptimization", plp.LpMaximize)
    time_steps = range(len(df))
    
    # Decision Variables
    charge = {t: plp.LpVariable(f"charge_{t}", lowBound=0, upBound=max_power_mw) for t in time_steps}
    discharge = {t: plp.LpVariable(f"discharge_{t}", lowBound=0, upBound=max_power_mw) for t in time_steps}
    reserve_afrr = {t: plp.LpVariable(f"reserve_afrr_{t}", lowBound=0, upBound=max_power_mw / 2) for t in time_steps}
    soc = {t: plp.LpVariable(f"soc_{t}", lowBound=0, upBound=capacity_mwh) for t in time_steps}
    
    # Binary variables for charging/discharging mutual exclusivity
    is_charging = {t: plp.LpVariable(f"is_charging_{t}", cat='Binary') for t in time_steps}
    
    # Auxiliary variable representing the peak grid load to be penalized
    peak_grid_load = plp.LpVariable("peak_grid_load", lowBound=0)
    
    da_prices = df["DA_Price"].values
    afrr_prices = df["aFRR_Capacity_Price"].values
    ind_load = df["Industrial_Load_MW"].values
    
    # Objective Function: Maximize Market Revenues MINUS a penalty proportional to the peak grid load
    market_revenue = plp.lpSum([
        (discharge[t] - charge[t]) * da_prices[t] + reserve_afrr[t] * afrr_prices[t]
        for t in time_steps
    ])
    
    model += market_revenue - (peak_grid_load * grid_fee_penalty_rate)
    
    # Constraints
    soc_init = capacity_mwh * 0.5
    
    for t in time_steps:
        net_grid_load_t = ind_load[t] - discharge[t] + charge[t]
        model += peak_grid_load >= net_grid_load_t
        
        model += charge[t] + reserve_afrr[t] <= max_power_mw
        model += discharge[t] + reserve_afrr[t] <= max_power_mw
        
        model += charge[t] <= max_power_mw * is_charging[t]
        model += discharge[t] <= max_power_mw * (1 - is_charging[t])
        
        if t == 0:
            model += soc[t] == soc_init + (charge[t] * efficiency - discharge[t] / efficiency) * 1.0
        else:
            model += soc[t] == soc[t-1] + (charge[t] * efficiency - discharge[t] / efficiency) * 1.0
            
    model += soc[len(time_steps)-1] >= soc_init
    
    # Solve via CBC solver
    model.solve(plp.PULP_CBC_CMD(msg=0))
    
    # Extract results
    results_df = df.copy()
    results_df["Optimized_Charge_MW"] = [plp.value(charge[t]) for t in time_steps]
    results_df["Optimized_Discharge_MW"] = [plp.value(discharge[t]) for t in time_steps]
    results_df["Optimized_Reserve_MW"] = [plp.value(reserve_afrr[t]) for t in time_steps]
    results_df["Optimized_SoC_MWh"] = [plp.value(soc[t]) for t in time_steps]
    results_df["Net_Grid_Load_MW"] = results_df["Industrial_Load_MW"] - results_df["Optimized_Discharge_MW"] + results_df["Optimized_Charge_MW"]
    
    return results_df
