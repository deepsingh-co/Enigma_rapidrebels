import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_material_analysis_endpoint(client):
    payload = {
        "description": "We generate 5000 kg of fly ash every month with 8% moisture in Mumbai.",
        "quantity": 5000,
        "quantity_unit": "kg"
    }
    response = client.post("/api/symbiosis/material-analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["material_name"] == "Fly Ash"
    assert data["physical_properties"]["moisture_content"]["numeric_percent"] == 8.0
    assert "material_name" in data["metadata"]["provided_fields"]


def test_api_symbiosis_analyze(client):
    payload = {
        "material": "Fly Ash",
        "quantity": 5000,
        "location": "Mumbai",
        "form": "powder",
        "condition": "dry",
        "producer_name": "Tata Thermal Power",
        "producer_industry": "Thermal Power & Energy"
    }
    response = client.post("/api/symbiosis/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "waste" in data
    assert "possibleUses" in data
    assert "potentialPartners" in data
    assert len(data["potentialPartners"]) > 0

    top_partner = data["potentialPartners"][0]
    assert "opportunityScore" in top_partner
    assert "factor_breakdown" in top_partner
    assert "timing_analysis" in top_partner
    assert "logistics_analysis" in top_partner
    assert "processing_analysis" in top_partner
    assert "summary_reasoning" in top_partner


def test_api_symbiosis_notify_twilio(client):
    payload = {
        "channel": "sms",
        "recipient_phone": "+919820011223",
        "partner_name": "UltraTech Cement Corp.",
        "producer_name": "Tata Thermal Energy",
        "waste_material": "Fly Ash",
        "quantity": 5000
    }
    response = client.post("/api/symbiosis/notify", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_api_symbiosis_quick_match(client):
    response = client.post("/api/symbiosis/quick-match", json={"query": "slag"})
    assert response.status_code == 200
    data = response.json()
    assert "matched_wastes" in data
    assert len(data["matched_wastes"]) > 0


def test_api_symbiosis_graph(client):
    response = client.get("/api/symbiosis/graph?waste=Fly%20Ash")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "links" in data
