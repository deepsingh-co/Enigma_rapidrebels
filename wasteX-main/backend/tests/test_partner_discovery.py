import pytest
from services.symbiosis.partner_discovery.partner_engine import PartnerDiscoveryEngine


def test_fly_ash_partner_discovery():
    engine = PartnerDiscoveryEngine()
    result = engine.discover_partners(
        material="Fly Ash",
        quantity=5000.0,
        location="Mumbai, Maharashtra",
        form="powder",
        condition="dry",
        producer_name="Tata Thermal Power",
        producer_industry="Thermal Power"
    )

    assert result["total_partners_discovered"] > 0
    top_partner = result["potentialPartners"][0]
    assert "Cement" in top_partner["industry"]["industry_type"] or "Construction" in top_partner["industry"]["industry_type"]
    assert top_partner["opportunityScore"] >= 80.0
    assert len(top_partner["reasons"]) >= 3
    assert "networkGraph" in result
    assert len(result["networkGraph"]["nodes"]) >= 3


def test_cotton_textile_partner_discovery():
    engine = PartnerDiscoveryEngine()
    result = engine.discover_partners(
        material="Cotton Fabric Scraps",
        quantity=2500.0,
        location="Surat, Gujarat",
        form="scraps",
        condition="dry",
        producer_name="Surat TexFab Mills",
        producer_industry="Textile"
    )

    assert result["total_partners_discovered"] > 0
    partner_types = [p["industry"]["industry_type"] for p in result["potentialPartners"]]
    assert any("Textile" in pt or "Paper" in pt or "Plastic" in pt for pt in partner_types)
