# ==========================================
# UNIT TESTS FOR GERMAN BESS MILP ENGINE
# ==========================================

import pytest
import pandas as pd
import numpy as np
from src.engine import generate_german_market_data, run_true_co_optimization

@pytest.fixture
def sample_data():
    return generate_german_market_data()

def test_market_data_generation(sample_data):
    """Test if market data generates 24 hours with required columns."""
    assert len(sample_data) == 24
    assert "DA_Price" in sample_data.columns
    assert "aFRR_Capacity_Price" in sample_data.columns
    assert "Industrial_Load_MW" in sample_data.columns

def test_optimization_execution(sample_data):
    """Test if the MILP model solves successfully and returns valid shapes."""
    results = run_true_co_optimization(sample_data, capacity_mwh=10.0, max_power_mw=5.0)
    
    assert "Optimized_Charge_MW" in results.columns
    assert "Optimized_Discharge_MW" in results.columns
    assert "Net_Grid_Load_MW" in results.columns
    assert len(results) == 24

def test_soc_and_power_boundaries(sample_data):
    """Test if battery physical constraints and power limits are respected."""
    results = run_true_co_optimization(sample_data, capacity_mwh=10.0, max_power_mw=5.0)
    
    # Check that State of Charge never exceeds capacity or drops below zero
    assert results["Optimized_SoC_MWh"].max() <= 10.0
    assert results["Optimized_SoC_MWh"].min() >= 0.0
    
    # Check that power limits and inverter boundaries are not violated
    assert results["Optimized_Charge_MW"].max() <= 5.0
    assert results["Optimized_Discharge_MW"].max() <= 5.0
