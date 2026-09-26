import math
from typing import Dict, Any, Optional, Tuple
from .geo_data import CITY_COORDINATES


class LogisticsFeasibilityEngine:
    """
    Logistics & Transportation Feasibility Engine for Industrial Symbiosis.
    Calculates transport modes, freight tariffs, delivery duration, and economic viability.
    """

    # Shared coordinates database for industrial zones and cities
    CITY_COORDS = CITY_COORDINATES

    # Standard Road Freight Tariffs (INR per metric tonne per km + base loading)
    FREIGHT_CONFIG = {
        "base_loading_fee_inr": 1200.0,
        "rate_per_tonne_km_inr": 2.85,
        "min_charge_inr": 2500.0,
        "avg_truck_speed_kmh": 42.0,  # Average commercial heavy vehicle speed in India/highways
        "loading_unloading_hours": 2.5
    }

    @classmethod
    def calculate_distance(cls, loc1: str, loc2: str) -> Tuple[float, bool]:
        """
        Calculates distance in km between two locations using coordinate haversine formula
        with road winding factor (1.25x). Returns (distance_km, is_estimated).
        """
        if not loc1 or not loc2:
            return 85.0, True

        l1 = loc1.lower().strip()
        l2 = loc2.lower().strip()

        if l1 == l2:
            return 12.0, True  # Same city/industrial corridor

        coord1 = None
        coord2 = None

        for city, c in cls.CITY_COORDS.items():
            if city in l1: coord1 = c
            if city in l2: coord2 = c

        if coord1 and coord2:
            lat1, lon1 = coord1
            lat2, lon2 = coord2
            r = 6371.0
            d_lat = math.radians(lat2 - lat1)
            d_lon = math.radians(lon2 - lon1)
            a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            air_dist = r * c
            road_dist = air_dist * 1.25  # Road routing winding factor
            return round(road_dist, 1), False

        # Fallback estimation
        h = abs(hash(f"{l1}_{l2}")) % 160 + 40
        return float(h), True

    @classmethod
    def determine_transport_mode(cls, quantity_kg: float, form: str, distance_km: float) -> str:
        """Determines the most optimal commercial transport vehicle mode."""
        qty_tonnes = quantity_kg / 1000.0
        form_lower = (form or "").lower()

        if "powder" in form_lower or "ash" in form_lower:
            return "Pneumatic Bulk Tanker / Silo Bulker"
        elif "liquid" in form_lower or "slurry" in form_lower:
            return "Chemical/Liquid Road Tanker"
        elif "solid" in form_lower or "rubble" in form_lower or "slag" in form_lower:
            return "Heavy Hydraulic Tipper (16-32 Tonne)"
        elif qty_tonnes <= 3.5:
            return "Light Commercial Vehicle (LCV / 4-Wheeler)"
        elif qty_tonnes <= 10.0:
            return "Medium Commercial Truck (6-Wheeler 10T)"
        elif distance_km > 600.0:
            return "Multimodal Rail Freight Container"
        else:
            return "Multi-Axle Heavy Freight Truck (24-32 Tonne)"

    @classmethod
    def evaluate_logistics(
        cls,
        producer_location: str,
        receiver_location: str,
        quantity_kg: float,
        form: str = "solid",
        expected_material_value_inr: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Computes complete transportation feasibility, cost breakdown, and transit duration.
        """
        distance_km, is_dist_estimated = cls.calculate_distance(producer_location, receiver_location)
        qty_tonnes = max(0.1, quantity_kg / 1000.0)

        transport_mode = cls.determine_transport_mode(quantity_kg, form, distance_km)

        # Cost Calculation
        base_fee = cls.FREIGHT_CONFIG["base_loading_fee_inr"]
        per_ton_km = cls.FREIGHT_CONFIG["rate_per_tonne_km_inr"]
        variable_freight = qty_tonnes * distance_km * per_ton_km
        total_transport_cost = max(cls.FREIGHT_CONFIG["min_charge_inr"], base_fee + variable_freight)

        # Delivery Duration
        transit_hours = (distance_km / cls.FREIGHT_CONFIG["avg_truck_speed_kmh"]) + cls.FREIGHT_CONFIG["loading_unloading_hours"]

        # Logistics Feasibility Evaluation
        # Standard rule: Transport cost should not exceed 35% of material value or distance > 450 km for low value bulk
        is_feasible = True
        feasibility_status = "High Feasibility"
        warnings = []

        if distance_km > 400.0:
            is_feasible = False
            feasibility_status = "Long Haul Constraint"
            warnings.append(f"Distance ({distance_km:.1f} km) exceeds standard 300 km regional circularity radius.")
        elif distance_km > 250.0:
            feasibility_status = "Moderate Feasibility"
            warnings.append(f"Inter-city haul ({distance_km:.1f} km); consider full-truckload (FTL) batch consolidation.")

        if expected_material_value_inr and expected_material_value_inr > 0:
            freight_ratio = total_transport_cost / expected_material_value_inr
            if freight_ratio > 0.40:
                is_feasible = False
                feasibility_status = "Economically Constrained"
                warnings.append(f"Estimated transport cost (₹{total_transport_cost:,.0f}) is {freight_ratio*100:.0f}% of total material value.")

        # Logistics Score (0-100)
        if distance_km <= 50.0:
            logistics_score = 98.0
        elif distance_km <= 150.0:
            logistics_score = 90.0
        elif distance_km <= 300.0:
            logistics_score = 78.0
        elif distance_km <= 500.0:
            logistics_score = 60.0
        else:
            logistics_score = 40.0

        return {
            "producer_location": producer_location,
            "receiver_location": receiver_location,
            "distance_km": distance_km,
            "is_distance_estimated": is_dist_estimated,
            "transport_mode": transport_mode,
            "quantity_transported_kg": float(quantity_kg),
            "quantity_transported_tonnes": round(qty_tonnes, 2),
            "estimated_transport_cost_inr": round(total_transport_cost, 0),
            "cost_per_kg_inr": round(total_transport_cost / max(1.0, quantity_kg), 2),
            "estimated_transit_hours": round(transit_hours, 1),
            "transportation_feasible": is_feasible,
            "feasibility_status": feasibility_status,
            "logistics_score": round(logistics_score, 1),
            "warnings": warnings
        }
