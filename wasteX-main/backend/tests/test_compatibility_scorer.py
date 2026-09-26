import pytest
from services.symbiosis.compatibility.compatibility_scorer import CompatibilityScorer


def test_distance_calculation():
    # Mumbai to Pune should be ~115-150 km
    dist = CompatibilityScorer.calculate_distance_km("Mumbai, Maharashtra", "Pune, Maharashtra")
    assert 100 <= dist <= 160

    # Same location should be short distance
    dist_same = CompatibilityScorer.calculate_distance_km("Mumbai", "Mumbai")
    assert dist_same <= 20.0


def test_quantity_compatibility():
    # 5,000 supply vs 6,000 demand
    score, desc = CompatibilityScorer.score_quantity_compatibility(5000, 6000)
    assert score >= 85.0
    assert "coverage" in desc.lower() or "demand" in desc.lower()


def test_quality_compatibility():
    score_dry, desc_dry = CompatibilityScorer.score_quality_compatibility("powder", "dry", "pozzolanic reaction")
    score_wet, desc_wet = CompatibilityScorer.score_quality_compatibility("powder", "wet", "thermal calcination")
    assert score_dry > score_wet


def test_composite_match_scoring():
    match = CompatibilityScorer.compute_composite_match(
        kg_confidence=0.95,
        supply_qty=5000,
        demand_qty=6000,
        form="powder",
        condition="dry",
        transforming_process="pozzolanic reaction",
        producer_location="Mumbai",
        receiver_location="Pune",
        producer_industry="Thermal Power",
        receiver_industry="Cement"
    )

    assert match["match_score"] >= 90.0
    assert match["material_compatibility"] >= 90.0
    assert match["distance_km"] > 0
    assert "quantity_compatibility" in match
