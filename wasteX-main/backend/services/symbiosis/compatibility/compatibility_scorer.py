import math
from typing import Dict, Any, Optional, Tuple
from ..logistics.geo_data import CITY_COORDINATES


class CompatibilityScorer:
    """
    Multi-criteria compatibility scoring engine for industrial symbiosis partnerships.
    Evaluates material, quantity, quality/condition, geographic distance, and industry domain synergy.
    """

    # Coordinates for key Indian & global industrial hubs for distance computation
    CITY_COORDINATES = CITY_COORDINATES

    @classmethod
    def calculate_distance_km(cls, loc1: str, loc2: str) -> float:
        """
        Calculates haversine distance between two locations using city coordinate lookup.
        Defaults to a realistic standard distance if not found.
        """
        if not loc1 or not loc2:
            return 85.0

        if loc1.lower().strip() == loc2.lower().strip():
            return 12.0  # Intra-city / local industrial zone

        coord1 = None
        coord2 = None

        loc1_norm = loc1.lower()
        loc2_norm = loc2.lower()

        for city, coord in cls.CITY_COORDINATES.items():
            if city in loc1_norm:
                coord1 = coord
            if city in loc2_norm:
                coord2 = coord

        if coord1 and coord2:
            lat1, lon1 = coord1
            lat2, lon2 = coord2
            # Haversine formula
            r = 6371.0  # Earth radius in km
            d_lat = math.radians(lat2 - lat1)
            d_lon = math.radians(lon2 - lon1)
            a = (math.sin(d_lat / 2) ** 2 +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(d_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return round(r * c, 1)

        # Realistic default based on string hash for consistency
        hash_val = abs(hash(f"{loc1_norm}_{loc2_norm}")) % 180 + 35
        return float(hash_val)

    @classmethod
    def score_material_compatibility(cls, kg_confidence: float) -> float:
        """Normalized material compatibility score (0-100)."""
        return min(100.0, max(10.0, float(kg_confidence) * 100.0))

    @classmethod
    def score_quantity_compatibility(cls, supply_qty: float, demand_qty: float) -> Tuple[float, str]:
        """
        Scores supply vs demand quantity match (0-100) and produces qualitative text.
        """
        if demand_qty <= 0 or supply_qty <= 0:
            return 80.0, "Moderate (Flexible intake batch sizes)"

        ratio = supply_qty / demand_qty
        if 0.8 <= ratio <= 1.25:
            score = 98.0
            desc = f"Excellent ({supply_qty:,.0f} kg supply closely matches {demand_qty:,.0f} kg demand - {ratio*100:.0f}% coverage)"
        elif 0.5 <= ratio < 0.8:
            score = 88.0
            desc = f"High ({supply_qty:,.0f} kg supply covers {ratio*100:.0f}% of partner's {demand_qty:,.0f} kg demand)"
        elif 1.25 < ratio <= 2.0:
            score = 85.0
            desc = f"High ({supply_qty:,.0f} kg supply fully satisfies {demand_qty:,.0f} kg demand with surplus for buffer inventory)"
        elif ratio < 0.5:
            score = 70.0 + max(0.0, ratio * 20.0)
            desc = f"Partial ({supply_qty:,.0f} kg supply covers {ratio*100:.0f}% of demand; partner can supplement with other streams)"
        else:
            score = 72.0
            desc = f"Bulk ({supply_qty:,.0f} kg supply exceeds single demand batch of {demand_qty:,.0f} kg; multi-shipment dispatch recommended)"

        return round(score, 1), desc

    @classmethod
    def score_quality_compatibility(cls, form: str, condition: str, transforming_process: str) -> Tuple[float, str]:
        """
        Evaluates physical form and condition suitability for the conversion process.
        """
        score = 85.0
        details = []

        form_lower = (form or "").lower()
        cond_lower = (condition or "").lower()
        proc_lower = (transforming_process or "").lower()

        if "dry" in cond_lower or "pure" in cond_lower or "uncontaminated" in cond_lower:
            score += 10.0
            details.append("Clean, dry condition ideal for direct conversion")
        elif "mixed" in cond_lower or "contaminated" in cond_lower:
            score -= 15.0
            details.append("Mixed condition requires pre-sorting or separation")
        elif "wet" in cond_lower or "slurry" in cond_lower:
            if "thermal" in proc_lower or "combustion" in proc_lower:
                score -= 10.0
                details.append("Requires dewatering before thermal processing")
            else:
                score += 5.0
                details.append("Moisture state suitable for wet processing")

        if "powder" in form_lower or "fine" in form_lower or "scraps" in form_lower:
            score += 5.0
            details.append("Form has favorable surface area for reaction")

        score = min(100.0, max(40.0, score))
        text_desc = "; ".join(details) if details else "Standard industrial grade suitability"
        return round(score, 1), text_desc

    @classmethod
    def score_distance_logistics(cls, distance_km: float) -> Tuple[float, str]:
        """
        Evaluates economic transport radius and logistics viability.
        """
        if distance_km <= 30.0:
            score = 98.0
            desc = f"Local ({distance_km:.1f} km) - minimal transport overhead and immediate dispatch"
        elif distance_km <= 100.0:
            score = 90.0
            desc = f"Regional ({distance_km:.1f} km) - highly viable same-day trucking"
        elif distance_km <= 250.0:
            score = 80.0
            desc = f"Inter-city ({distance_km:.1f} km) - viable via standard road freight"
        elif distance_km <= 500.0:
            score = 65.0
            desc = f"Longer haul ({distance_km:.1f} km) - bulk consolidation recommended"
        else:
            score = 45.0
            desc = f"Distant ({distance_km:.1f} km) - rail/multimodal logistics recommended"

        return round(score, 1), desc

    @classmethod
    def score_industry_synergy(cls, producer_industry: str, receiver_industry: str) -> float:
        """
        Industry domain synergy score (0-100).
        """
        p_ind = (producer_industry or "").lower()
        r_ind = (receiver_industry or "").lower()

        # Known high-synergy industrial pairs
        high_synergy = [
            ("thermal", "cement"),
            ("power", "cement"),
            ("power", "brick"),
            ("power", "construction"),
            ("steel", "cement"),
            ("steel", "construction"),
            ("steel", "road"),
            ("textile", "insulation"),
            ("textile", "automotive"),
            ("textile", "furniture"),
            ("sugar", "distillery"),
            ("agriculture", "bio"),
            ("agriculture", "fertilizer"),
            ("chemical", "refinery"),
            ("foundry", "concrete"),
            ("foundry", "brick")
        ]

        for p_syn, r_syn in high_synergy:
            if p_syn in p_ind and r_syn in r_ind:
                return 95.0
            if r_syn in p_ind and p_syn in r_ind:
                return 95.0

        return 82.0

    @classmethod
    def compute_composite_match(
        cls,
        kg_confidence: float,
        supply_qty: float,
        demand_qty: float,
        form: str,
        condition: str,
        transforming_process: str,
        producer_location: str,
        receiver_location: str,
        producer_industry: str,
        receiver_industry: str
    ) -> Dict[str, Any]:
        """
        Computes composite multi-factor compatibility evaluation.
        """
        # 1. Material compatibility
        mat_score = cls.score_material_compatibility(kg_confidence)

        # 2. Quantity compatibility
        qty_score, qty_desc = cls.score_quantity_compatibility(supply_qty, demand_qty)

        # 3. Quality compatibility
        qual_score, qual_desc = cls.score_quality_compatibility(form, condition, transforming_process)

        # 4. Logistics & Distance
        dist_km = cls.calculate_distance_km(producer_location, receiver_location)
        dist_score, dist_desc = cls.score_distance_logistics(dist_km)

        # 5. Industry synergy
        syn_score = cls.score_industry_synergy(producer_industry, receiver_industry)

        # Composite weighted score (0-100)
        composite = (
            0.38 * mat_score +
            0.24 * qty_score +
            0.15 * qual_score +
            0.13 * dist_score +
            0.10 * syn_score
        )
        composite = round(min(99.0, max(25.0, composite)), 1)

        return {
            "match_score": composite,
            "material_compatibility": round(mat_score, 1),
            "quantity_compatibility": qty_desc,
            "quantity_score": qty_score,
            "quality_compatibility": qual_desc,
            "quality_score": qual_score,
            "distance_km": dist_km,
            "distance_description": dist_desc,
            "distance_score": dist_score,
            "industry_synergy_score": syn_score
        }
