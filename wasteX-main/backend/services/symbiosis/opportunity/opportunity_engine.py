from typing import Dict, Any, List, Optional
from ..timing.timing_engine import TimingAvailabilityEngine
from ..logistics.logistics_engine import LogisticsFeasibilityEngine
from ..processing.processing_engine import ProcessingRequirementEngine
from ..environmental.impact_calculator import EnvironmentalImpactCalculator


class OpportunityAssessmentEngine:
    """
    Dedicated Industrial Symbiosis Opportunity Assessment Engine.
    Evaluates 9 transparent opportunity factors and synthesizes an explainable Opportunity Score.
    """

    # Industry Domain Synergy Matrix across 10 major industrial sectors
    INDUSTRY_SYNERGIES = {
        ("Thermal Power", "Cement"): 96.0,
        ("Thermal Power", "Construction"): 94.0,
        ("Thermal Power", "Bricks"): 95.0,
        ("Metal", "Cement"): 92.0,
        ("Metal", "Construction"): 90.0,
        ("Metal", "Foundry"): 95.0,
        ("Textile", "Insulation"): 94.0,
        ("Textile", "Automotive"): 91.0,
        ("Textile", "Recycling"): 96.0,
        ("Chemical", "Refinery"): 90.0,
        ("Chemical", "Fertilizer"): 93.0,
        ("Food Processing", "Bio-Energy"): 95.0,
        ("Food Processing", "Agriculture"): 94.0,
        ("Food Processing", "Distillery"): 96.0,
        ("Plastic", "Manufacturing"): 92.0,
        ("Plastic", "Automotive"): 90.0,
        ("Construction", "Road Infrastructure"): 95.0,
        ("Paper", "Cement"): 88.0,
        ("Paper", "Packaging"): 94.0,
        ("Agriculture", "Bio-Energy"): 95.0,
        ("Agriculture", "Organic Fertilizer"): 96.0
    }

    @classmethod
    def get_industry_synergy(cls, producer_ind: str, receiver_ind: str) -> float:
        p_norm = (producer_ind or "").lower()
        r_norm = (receiver_ind or "").lower()

        for (p_key, r_key), score in cls.INDUSTRY_SYNERGIES.items():
            if (p_key.lower() in p_norm and r_key.lower() in r_norm) or (r_key.lower() in p_norm and p_key.lower() in r_norm):
                return score
        return 82.0

    @classmethod
    def evaluate_opportunity(
        cls,
        producer_data: Dict[str, Any],
        partner_data: Dict[str, Any],
        material_profile: Dict[str, Any],
        transformation_pathway: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates all 9 individual factors and the overall Opportunity Score with full transparent explanations.
        """
        material = material_profile.get("material_name", "Industrial Waste")
        quantity_kg = float(material_profile.get("quantity", 5000.0))
        # Use physical form from normalized material profile if present, else fallback
        phys_form_profile = material_profile.get("physical_properties", {}).get("form", {})
        if isinstance(phys_form_profile, dict):
            form = phys_form_profile.get("value", "solid")
        else:
            form = str(phys_form_profile or "solid")

        phys_cond_profile = material_profile.get("physical_properties", {}).get("condition", {})
        if isinstance(phys_cond_profile, dict):
            condition = phys_cond_profile.get("value", "dry")
        else:
            condition = str(phys_cond_profile or "dry")

        producer_loc = producer_data.get("location", "Mumbai, Maharashtra")
        producer_ind = producer_data.get("industry", "Manufacturing")
        producer_name = producer_data.get("company_name", "Waste Producer")

        partner_ind_type = partner_data.get("industry_type", "Manufacturing")
        partner_loc = partner_data.get("location", "Pune, Maharashtra")
        partner_demand_qty = float(partner_data.get("required_quantity", quantity_kg))
        partner_name = partner_data.get("company_name", "Industrial Partner")

        target_resource = transformation_pathway.get("transformed_resource", partner_ind_type)
        trans_process = transformation_pathway.get("transforming_process", "Direct recycling")
        kg_conf = float(transformation_pathway.get("confidence", 0.90))

        # 1. Material Compatibility (0-100)
        material_score = round(min(100.0, max(20.0, kg_conf * 100.0)), 1)

        # 2. Timing & Availability Analysis (0-100)
        timing_eval = TimingAvailabilityEngine.evaluate_timing(
            producer_qty=quantity_kg,
            producer_frequency=material_profile.get("availability_frequency", "monthly"),
            producer_start_day=material_profile.get("availability_window", {}).get("start_day", 1),
            producer_end_day=material_profile.get("availability_window", {}).get("end_day", 10),
            receiver_demand_qty=partner_demand_qty,
            receiver_frequency=partner_data.get("intake_frequency", "monthly"),
            receiver_start_day=1,
            receiver_end_day=15
        )
        timing_score = timing_eval["timing_score"]

        # 3. Quantity Compatibility (0-100)
        qty_ratio = quantity_kg / max(1.0, partner_demand_qty)
        if 0.8 <= qty_ratio <= 1.25:
            qty_score = 96.0
            qty_reason = f"Optimal volume match: Available {quantity_kg:,.0f} kg matches {qty_ratio*100:.0f}% of partner's {partner_demand_qty:,.0f} kg demand."
        elif 0.5 <= qty_ratio < 0.8:
            qty_score = 88.0
            qty_reason = f"High demand coverage: Available {quantity_kg:,.0f} kg covers {qty_ratio*100:.0f}% of monthly demand."
        elif 1.25 < qty_ratio <= 2.0:
            qty_score = 86.0
            qty_reason = f"Surplus capacity: Available {quantity_kg:,.0f} kg fully satisfies demand with buffer inventory."
        else:
            qty_score = 72.0
            qty_reason = f"Partial batch match ({qty_ratio*100:.0f}% demand covered); multi-source feed aggregation recommended."

        # 4. Quality & Physical State Compatibility (0-100)
        quality_score = 88.0
        qual_reasons = []
        if "dry" in condition or "pure" in condition:
            quality_score += 8.0
            qual_reasons.append("Clean dry condition suitable for immediate process intake")
        elif "mixed" in condition or "contaminated" in condition:
            quality_score -= 15.0
            qual_reasons.append("Mixed stream requires upfront quality assay or pre-sorting")
        elif "wet" in condition or "slurry" in condition:
            quality_score -= 6.0
            qual_reasons.append("Moisture state requires dewatering or wet process adaptation")
        quality_score = round(min(100.0, max(40.0, quality_score)), 1)
        quality_reason = "; ".join(qual_reasons) if qual_reasons else "Standard industrial quality grade matching receiver specs"

        # 5. Logistics & Transportation Feasibility (0-100)
        logistics_eval = LogisticsFeasibilityEngine.evaluate_logistics(
            producer_location=producer_loc,
            receiver_location=partner_loc,
            quantity_kg=quantity_kg,
            form=form
        )
        location_score = logistics_eval["logistics_score"]
        transportation_score = round(92.0 if logistics_eval["transportation_feasible"] else 55.0, 1)

        # 6. Processing Requirements & Technical Complexity (0-100)
        processing_eval = ProcessingRequirementEngine.evaluate_processing(
            material=material,
            target_resource=target_resource,
            condition=condition,
            form=form,
            transforming_process=trans_process
        )
        processing_score = processing_eval["processing_score"]

        # 7. Environmental Benefit (0-100)
        env_eval = EnvironmentalImpactCalculator.calculate_impact(
            material=material,
            quantity_kg=quantity_kg,
            distance_km=logistics_eval["distance_km"]
        )
        env_score = env_eval["environmental_score"]

        # 8. Industry Domain Compatibility (0-100)
        industry_score = cls.get_industry_synergy(producer_ind, partner_ind_type)

        # 9. OVERALL OPPORTUNITY SCORE (Weighted Composite 0-100)
        overall_opportunity_score = (
            0.22 * material_score +
            0.16 * qty_score +
            0.12 * quality_score +
            0.10 * location_score +
            0.10 * timing_score +
            0.10 * transportation_score +
            0.08 * processing_score +
            0.07 * env_score +
            0.05 * industry_score
        )
        overall_opportunity_score = round(min(99.0, max(30.0, overall_opportunity_score)), 1)

        # Synthesize Human-Readable Transparent Reasoning
        summary_reasoning = (
            f"High potential industrial symbiosis ({overall_opportunity_score}% score) because "
            f"{partner_name}'s demand for '{target_resource}' matches {timing_eval['demand_coverage_percent']:.0f}% of available quantity, "
            f"the material properties ({form}, {condition}) are technically compatible via {trans_process[:60]}, "
            f"and estimated transport distance is {logistics_eval['distance_km']:.1f} km ({logistics_eval['transport_mode']})."
        )

        detailed_evidence_points = [
            f"Material Compatibility ({material_score}/100): W2RKG Knowledge Graph verifies that {material} transforms into {target_resource} via {trans_process}.",
            f"Quantity Compatibility ({qty_score}/100): {qty_reason}",
            f"Quality & Physical Form ({quality_score}/100): {quality_reason}.",
            f"Location & Logistics ({location_score}/100): {logistics_eval['distance_km']:.1f} km transit via {logistics_eval['transport_mode']} (Est. ₹{logistics_eval['estimated_transport_cost_inr']:,.0f} freight, {logistics_eval['estimated_transit_hours']} hrs delivery).",
            f"Timing & Availability ({timing_score}/100): {timing_eval['status']} — {timing_eval['explanation']}",
            f"Processing Feasibility ({processing_score}/100): Preprocessing complexity is {processing_eval['processing_complexity']}. Receiver direct intake: {'Yes' if processing_eval['receiver_can_accept_directly'] else 'Requires intermediate stage'}.",
            f"Environmental Benefit ({env_score}/100): Net avoidance of {env_eval['net_co2_saved_tonnes']} tonnes CO₂e and {env_eval['waste_diverted_tonnes']} tonnes diverted from landfill.",
            f"Cross-Industry Domain Synergy ({industry_score}/100): High operational complementarity between {producer_ind} and {partner_ind_type}."
        ]

        return {
            "opportunity_score": overall_opportunity_score,
            "factor_breakdown": {
                "material_compatibility": material_score,
                "quantity_compatibility": qty_score,
                "quality_compatibility": quality_score,
                "location_distance": location_score,
                "timing_compatibility": timing_score,
                "transportation_feasibility": transportation_score,
                "processing_feasibility": processing_score,
                "environmental_benefit": env_score,
                "industry_compatibility": industry_score
            },
            "timing_analysis": timing_eval,
            "logistics_analysis": logistics_eval,
            "processing_analysis": processing_eval,
            "environmental_analysis": env_eval,
            "summary_reasoning": summary_reasoning,
            "detailed_evidence": detailed_evidence_points
        }
