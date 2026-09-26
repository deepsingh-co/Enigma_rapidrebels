import pytest
from services.symbiosis.processing.processing_engine import ProcessingRequirementEngine


def test_fly_ash_cement_processing():
    res = ProcessingRequirementEngine.evaluate_processing(
        material="Fly Ash",
        target_resource="Cement & Concrete Clinker Replacement",
        condition="dry",
        form="powder"
    )

    assert res["requires_preprocessing"] is True
    assert res["processing_complexity"] == "Low"
    assert res["receiver_can_accept_directly"] is True
    assert res["processing_score"] >= 90.0


def test_mixed_material_processing_penalty():
    res = ProcessingRequirementEngine.evaluate_processing(
        material="Plastic Waste",
        target_resource="Compounded Thermoplastics",
        condition="mixed",
        form="scraps"
    )

    assert res["processing_complexity"] in ["Medium", "High"]
    assert any("sorting" in s.lower() for s in res["preprocessing_steps"])
