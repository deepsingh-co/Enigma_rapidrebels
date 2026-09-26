import pytest
from services.symbiosis.logistics.logistics_engine import LogisticsFeasibilityEngine


def test_logistics_feasibility_mumbai_pune():
    res = LogisticsFeasibilityEngine.evaluate_logistics(
        producer_location="Mumbai, Maharashtra",
        receiver_location="Pune, Maharashtra",
        quantity_kg=5000.0,
        form="powder"
    )

    assert 100 <= res["distance_km"] <= 180
    assert "Tanker" in res["transport_mode"] or "Bulker" in res["transport_mode"]
    assert res["transportation_feasible"] is True
    assert res["estimated_transport_cost_inr"] > 2500.0
    assert res["estimated_transit_hours"] > 2.0


def test_logistics_vehicle_modes():
    tipper = LogisticsFeasibilityEngine.determine_transport_mode(15000, "rubble", 45)
    assert "Tipper" in tipper

    lcv = LogisticsFeasibilityEngine.determine_transport_mode(1500, "scraps", 30)
    assert "Light" in lcv or "LCV" in lcv
