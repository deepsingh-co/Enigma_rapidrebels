import pytest
from services.symbiosis.material_analysis.material_analyzer import MaterialPropertyAnalyzer


def test_material_property_analysis_prompt_example():
    analyzer = MaterialPropertyAnalyzer()
    res = analyzer.analyze_material_input("We generate 5000 kg of fly ash every month with 8% moisture.")

    assert res["material_name"] == "Fly Ash"
    assert res["material_category"] == "Cement"
    assert res["quantity"] == 5000.0
    assert res["availability_frequency"] == "monthly"

    # Moisture should be explicitly marked as NOT inferred (provided)
    moisture = res["physical_properties"]["moisture_content"]
    assert moisture["numeric_percent"] == 8.0
    assert moisture["is_inferred"] is False

    # Metadata should verify provided fields
    assert "material_name" in res["metadata"]["provided_fields"]
    assert "quantity" in res["metadata"]["provided_fields"]
    assert "physical_properties.moisture_content" in res["metadata"]["provided_fields"]

    # Preprocessing requirements should include screening and moisture control
    assert len(res["processing_requirements"]) >= 2
    assert "Hermetic" in res["required_conditions"] or "silo" in res["required_conditions"]


def test_cotton_material_analysis():
    analyzer = MaterialPropertyAnalyzer()
    res = analyzer.analyze_material_input("We produce 2500 kg of dry 100% pure cotton fabric scraps weekly in Surat.")

    assert "Cotton" in res["material_name"]
    assert res["material_category"] == "Textile"
    assert res["quantity"] == 2500.0
    assert res["availability_frequency"] == "weekly"
    assert res["physical_properties"]["form"]["value"] == "scraps"
