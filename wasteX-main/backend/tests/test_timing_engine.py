import pytest
from services.symbiosis.timing.timing_engine import TimingAvailabilityEngine


def test_timing_evaluation_compatible():
    res = TimingAvailabilityEngine.evaluate_timing(
        producer_qty=5000,
        producer_frequency="monthly",
        producer_start_day=1,
        producer_end_day=5,
        receiver_demand_qty=4000,
        receiver_frequency="monthly",
        receiver_start_day=1,
        receiver_end_day=10
    )

    assert res["timing_compatible"] is True
    assert res["status"] == "Timing Compatible"
    assert res["scheduling_overlap_days"] == 5
    assert res["quantity_overlap_kg"] == 4000.0
    assert res["demand_coverage_percent"] == 100.0


def test_timing_evaluation_partial():
    res = TimingAvailabilityEngine.evaluate_timing(
        producer_qty=3000,
        producer_frequency="weekly",
        producer_start_day=1,
        producer_end_day=8,
        receiver_demand_qty=6000,
        receiver_frequency="monthly",
        receiver_start_day=5,
        receiver_end_day=15
    )

    assert res["timing_compatible"] is True
    assert res["status"] == "Partially Compatible"
    assert res["scheduling_overlap_days"] == 4
    assert res["timing_score"] >= 60.0
    assert res["quantity_overlap_kg"] == 3000.0


def test_timing_evaluation_zero_overlap_conflict():
    res = TimingAvailabilityEngine.evaluate_timing(
        producer_qty=3000,
        producer_frequency="monthly",
        producer_start_day=1,
        producer_end_day=3,
        receiver_demand_qty=6000,
        receiver_frequency="monthly",
        receiver_start_day=25,
        receiver_end_day=30
    )

    assert res["timing_compatible"] is False
    assert res["status"] == "Timing Conflict"
    assert res["scheduling_overlap_days"] == 0
    assert res["timing_score"] == 20.0
