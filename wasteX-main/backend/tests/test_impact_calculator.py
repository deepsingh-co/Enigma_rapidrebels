import pytest
from services.symbiosis.environmental.impact_calculator import EnvironmentalImpactCalculator


def test_emission_factors():
    factor_data = EnvironmentalImpactCalculator.get_factor_data("fly ash")
    assert factor_data["factor"] >= 0.8
    assert "clinker" in factor_data["replaced_material"].lower()

    textile_factor = EnvironmentalImpactCalculator.get_factor_data("cotton fabric")
    assert textile_factor["factor"] >= 2.0


def test_calculate_impact():
    impact = EnvironmentalImpactCalculator.calculate_impact("Fly Ash", 5000, distance_km=120)
    assert impact["net_co2_saved_kg"] > 3000.0
    assert impact["net_co2_saved_tonnes"] > 3.0
    assert impact["waste_diverted_kg"] == 5000.0
    assert "CO₂e" in impact["metric_summary"]
    assert "data_source_citation" in impact
