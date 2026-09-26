import pytest
from fastapi.testclient import TestClient
from main import app
from services.symbiosis.knowledge_graph.kg_engine import W2RKGKnowledgeGraph
from services.symbiosis.timing.timing_engine import TimingAvailabilityEngine
from services.symbiosis.logistics.logistics_engine import LogisticsFeasibilityEngine
from services.symbiosis.processing.processing_engine import ProcessingRequirementEngine
from services.symbiosis.environmental.impact_calculator import EnvironmentalImpactCalculator
from services.symbiosis.opportunity.opportunity_engine import OpportunityAssessmentEngine
from services.symbiosis.material_analysis.material_analyzer import MaterialPropertyAnalyzer
from services.communication.twilio_service import TwilioCommunicationService


@pytest.fixture
def client():
    return TestClient(app)


# ==========================================
# 1. STRING SIMILARITY & KG NEGATIVE/EDGE TESTS
# ==========================================

def test_string_similarity_empty_and_punctuation():
    kg = W2RKGKnowledgeGraph.get_instance()
    assert kg.calculate_string_similarity("", "") == 0.0
    assert kg.calculate_string_similarity("   ", "   ") == 0.0
    assert kg.calculate_string_similarity("!!!", "fly ash") == 0.0
    assert kg.calculate_string_similarity("@@@###", "cotton scraps") == 0.0
    assert kg.calculate_string_similarity("fly ash", "fly ash") == 1.0
    assert kg.calculate_string_similarity("FLY ASH", "fly ash") == 1.0
    assert kg.calculate_string_similarity("fly ash", "cotton") < 0.3


def test_kg_find_matching_wastes_edge_cases():
    kg = W2RKGKnowledgeGraph.get_instance()
    assert kg.find_matching_wastes("") == []
    assert kg.find_matching_wastes("   ") == []
    assert kg.find_matching_wastes("!!!???") == []
    assert kg.find_matching_wastes("zzqqxx9988nonexistent") == []
    
    # Valid discovery
    results = kg.find_matching_wastes("fly ash")
    assert len(results) > 0
    assert any("fly ash" in r[0].lower() for r in results)


def test_kg_possible_uses_empty():
    kg = W2RKGKnowledgeGraph.get_instance()
    assert kg.get_possible_uses_for_waste("") == []
    assert kg.get_possible_uses_for_waste("???###") == []


# ==========================================
# 2. TWILIO NEGATIVE & VALIDATION TESTS
# ==========================================

def test_twilio_phone_validation():
    twilio = TwilioCommunicationService.get_instance()
    
    # Invalid numbers must raise ValueError
    with pytest.raises(ValueError):
        twilio.send_sms(to_phone="", message_body="Test")

    with pytest.raises(ValueError):
        twilio.send_sms(to_phone="+", message_body="Test")

    with pytest.raises(ValueError):
        twilio.send_sms(to_phone="123", message_body="Test")

    with pytest.raises(ValueError):
        twilio.send_sms(to_phone="invalid_phone_number", message_body="Test")

    # Valid E.164 numbers must succeed (in simulation)
    res_sms = twilio.send_sms(to_phone="+919820011223", message_body="Test SMS")
    assert res_sms["success"] is True
    assert res_sms["to"] == "+919820011223"

    res_wa = twilio.send_whatsapp(to_phone="+919820011223", message_body="Test WhatsApp")
    assert res_wa["success"] is True
    assert res_wa["to"] == "whatsapp:+919820011223"

    res_call = twilio.make_voice_call(to_phone="+919820011223", spoken_message="Test Call")
    assert res_call["success"] is True


# ==========================================
# 3. TIMING AVAILABILITY NEGATIVE & EDGE TESTS
# ==========================================

def test_timing_zero_overlap_produces_conflict():
    res = TimingAvailabilityEngine.evaluate_timing(
        producer_qty=5000,
        producer_frequency="monthly",
        producer_start_day=1,
        producer_end_day=3,
        receiver_demand_qty=5000,
        receiver_frequency="monthly",
        receiver_start_day=25,
        receiver_end_day=30
    )
    assert res["timing_compatible"] is False
    assert res["status"] == "Timing Conflict"
    assert res["scheduling_overlap_days"] == 0
    assert res["timing_score"] <= 30.0


def test_timing_boundary_overlap():
    res = TimingAvailabilityEngine.evaluate_timing(
        producer_qty=5000,
        producer_frequency="monthly",
        producer_start_day=1,
        producer_end_day=10,
        receiver_demand_qty=5000,
        receiver_frequency="monthly",
        receiver_start_day=10,
        receiver_end_day=20
    )
    assert res["timing_compatible"] is True
    assert res["scheduling_overlap_days"] == 1
    assert res["timing_score"] >= 80.0


def test_timing_date_conflict():
    res = TimingAvailabilityEngine.evaluate_timing(
        producer_qty=5000,
        producer_frequency="monthly",
        producer_start_day=1,
        producer_end_day=10,
        receiver_demand_qty=5000,
        receiver_frequency="monthly",
        producer_available_from="2026-10-01",
        receiver_required_until="2026-09-01"
    )
    assert res["timing_compatible"] is False
    assert res["status"] == "Timing Conflict"


# ==========================================
# 4. LOGISTICS & TRANSPORT MODE TESTS
# ==========================================

def test_logistics_transport_mode_powder_consistency():
    analyzer = MaterialPropertyAnalyzer()
    profile = analyzer.analyze_material_input("We generate 5000 kg fly ash in Mumbai")
    form = profile["physical_properties"]["form"]["value"]
    
    assert form == "powder"
    mode = LogisticsFeasibilityEngine.determine_transport_mode(5000, form, 120.0)
    assert mode == "Pneumatic Bulk Tanker / Silo Bulker"


def test_logistics_excessive_distance():
    res = LogisticsFeasibilityEngine.evaluate_logistics(
        producer_location="Mumbai",
        receiver_location="Rotterdam",
        quantity_kg=5000,
        form="solid"
    )
    assert res["distance_km"] > 400.0
    assert res["transportation_feasible"] is False
    assert res["feasibility_status"] == "Long Haul Constraint"


# ==========================================
# 5. ENVIRONMENTAL IMPACT TESTS & PROVENANCE
# ==========================================

def test_environmental_impact_known_and_default():
    # Known emission factor (Fly Ash replacing Clinker)
    res_known = EnvironmentalImpactCalculator.calculate_impact("fly ash", 10000, distance_km=100)
    assert res_known["net_co2_saved_tonnes"] > 0
    assert "IPCC 2019 Refinement" in res_known["data_source_citation"]
    assert "clinker" in res_known["replaced_virgin_material_name"].lower()

    # Default / Unknown material
    res_unknown = EnvironmentalImpactCalculator.calculate_impact("unknown_rare_byproduct_x", 10000, distance_km=100)
    assert res_unknown["net_co2_saved_tonnes"] > 0
    assert "Standard Circular Economy Benefit Baseline" in res_unknown["data_source_citation"]


def test_environmental_zero_quantity():
    res = EnvironmentalImpactCalculator.calculate_impact("fly ash", 0, distance_km=50)
    assert res["waste_diverted_tonnes"] == 0.0
    assert res["net_co2_saved_tonnes"] == 0.0


# ==========================================
# 6. OPPORTUNITY 9-FACTOR ASSESSMENT MATHEMATICS
# ==========================================

def test_opportunity_score_weights_and_bounds():
    weights = [0.22, 0.16, 0.12, 0.10, 0.10, 0.10, 0.08, 0.07, 0.05]
    assert round(sum(weights), 6) == 1.0

    eval_result = OpportunityAssessmentEngine.evaluate_opportunity(
        producer_data={"company_name": "Tata Power", "industry": "Thermal Power", "location": "Mumbai"},
        partner_data={"company_name": "UltraTech Cement", "industry_type": "Cement", "location": "Pune", "required_quantity": 5000},
        material_profile={
            "material_name": "Fly Ash",
            "quantity": 5000.0,
            "physical_properties": {"form": {"value": "powder"}, "condition": {"value": "dry"}},
            "availability_frequency": "monthly",
            "availability_window": {"start_day": 1, "end_day": 10}
        },
        transformation_pathway={
            "transformed_resource": "Portland Pozzolana Cement (PPC)",
            "transforming_process": "clinker replacement",
            "confidence": 0.95
        }
    )

    score = eval_result["opportunity_score"]
    assert 0.0 <= score <= 100.0
    assert len(eval_result["factor_breakdown"]) == 9
    assert len(eval_result["detailed_evidence"]) == 8


# ==========================================
# 7. FASTAPI API BOUNDARY & VALIDATION TESTS
# ==========================================

def test_api_zero_quantity_rejected(client):
    payload = {
        "material": "Fly Ash",
        "quantity": 0,
        "location": "Mumbai"
    }
    response = client.post("/api/symbiosis/analyze", json=payload)
    assert response.status_code == 422 or response.status_code == 400


def test_api_negative_quantity_rejected(client):
    payload = {
        "material": "Fly Ash",
        "quantity": -500,
        "location": "Mumbai"
    }
    response = client.post("/api/symbiosis/analyze", json=payload)
    assert response.status_code == 422 or response.status_code == 400


def test_api_invalid_twilio_channel_returns_400(client):
    payload = {
        "channel": "invalid_channel_xyz",
        "recipient_phone": "+919820011223",
        "partner_name": "UltraTech",
        "producer_name": "Tata Power",
        "waste_material": "Fly Ash",
        "quantity": 5000
    }
    response = client.post("/api/symbiosis/notify", json=payload)
    assert response.status_code == 400
    assert "Unsupported communication channel" in response.json()["detail"]


def test_api_invalid_twilio_phone_returns_400(client):
    payload = {
        "channel": "sms",
        "recipient_phone": "+",
        "partner_name": "UltraTech",
        "producer_name": "Tata Power",
        "waste_material": "Fly Ash",
        "quantity": 5000
    }
    response = client.post("/api/symbiosis/notify", json=payload)
    assert response.status_code == 400
    assert "Invalid phone number" in response.json()["detail"] or "Malformed" in response.json()["detail"]


def test_api_missing_material_returns_400(client):
    payload = {
        "material": "",
        "quantity": 5000
    }
    response = client.post("/api/symbiosis/analyze", json=payload)
    assert response.status_code == 400
