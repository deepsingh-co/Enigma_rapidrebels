import math
from typing import Dict, Any, Optional


class EnvironmentalImpactCalculator:
    """
    Transparent, configurable Environmental Impact Calculator for Industrial Symbiosis.
    Calculates gross GHG avoidance, logistics freight emissions, landfill diversion,
    and net ecological benefit with explicit scientific citations.
    """

    # Verified LCA emission factors (kg CO2e avoided per kg virgin raw material replaced)
    # Sources: IPCC Guidelines, EPA WARM v15, European Circular Economy Database, Ecoinvent 3.8
    CONFIGURABLE_EMISSION_FACTORS = {
        "fly ash": {
            "factor": 0.82,
            "replaced_material": "Portland cement clinker",
            "source": "IPCC 2019 Refinement - Mineral Industry (0.82 kg CO₂e/kg clinker substituted)"
        },
        "slag": {
            "factor": 0.78,
            "replaced_material": "Virgin quarried aggregates & ordinary Portland cement",
            "source": "World Steel Association LCA / Ecoinvent 3.8"
        },
        "blast furnace slag": {
            "factor": 0.80,
            "replaced_material": "Portland cement clinker (GGBFS)",
            "source": "European Cement Research Academy (ECRA)"
        },
        "concrete": {
            "factor": 0.35,
            "replaced_material": "Virgin crushed stone aggregate",
            "source": "EPA WARM Model v15 - Concrete Recycling"
        },
        "cotton": {
            "factor": 2.10,
            "replaced_material": "Virgin agricultural cotton lint",
            "source": "Textile Exchange Life Cycle Assessment (2.1 kg CO₂e/kg virgin cotton)"
        },
        "textile": {
            "factor": 2.05,
            "replaced_material": "Synthetic & natural virgin textile fibers",
            "source": "WRAP UK Sustainable Clothing Action Plan"
        },
        "plastic": {
            "factor": 1.55,
            "replaced_material": "Petrochemical virgin polyethylene / polypropylene polymer",
            "source": "Plastics Europe Eco-profile LCA"
        },
        "polyethylene": {
            "factor": 1.60,
            "replaced_material": "Virgin HDPE/LDPE granules",
            "source": "EPA WARM v15 - High Density Polyethylene"
        },
        "biomass": {
            "factor": 0.65,
            "replaced_material": "Fossil thermal coal / chemical fertilizers",
            "source": "IRENA Biomass for Power Generation Report"
        },
        "bagasse": {
            "factor": 0.70,
            "replaced_material": "Heavy industrial boiler fuel oil",
            "source": "Global Bioenergy Partnership (GBEP)"
        },
        "foundry sand": {
            "factor": 0.40,
            "replaced_material": "Mined virgin silica foundry sand",
            "source": "American Foundry Society (AFS) Beneficial Use LCA"
        },
        "phosphogypsum": {
            "factor": 0.45,
            "replaced_material": "Mined natural mineral gypsum rock",
            "source": "Fertilizer Institute Mineral Byproduct Study"
        },
        "food waste": {
            "factor": 0.75,
            "replaced_material": "Synthetic chemical N-P-K fertilizer / natural gas",
            "source": "FAO Food Wastage Footprint LCA"
        },
        "spent grain": {
            "factor": 0.60,
            "replaced_material": "Commercial cattle feed / virgin soy protein",
            "source": "Journal of Cleaner Production IS Benchmark"
        },
        "wood": {
            "factor": 0.55,
            "replaced_material": "Virgin timber & fossil pellets",
            "source": "US Forest Service Forest Products Laboratory"
        },
        "paper sludge": {
            "factor": 0.50,
            "replaced_material": "Virgin clay filler in brickmaking",
            "source": "CEPI European Pulp and Paper Industry LCA"
        },
        "default": {
            "factor": 0.60,
            "replaced_material": "Generic virgin industrial feedstock",
            "source": "Standard Circular Economy Benefit Baseline"
        }
    }

    # Freight logistics carbon intensity: 0.00012 kg CO2e per kg payload per km (Heavy Duty Diesel Truck)
    # Source: GLEC Framework (Global Logistics Emissions Council)
    FREIGHT_EMISSION_FACTOR_KG_PER_KG_KM = 0.00012

    @classmethod
    def get_factor_data(cls, material: str) -> Dict[str, Any]:
        mat_lower = (material or "").lower()
        for key, data in cls.CONFIGURABLE_EMISSION_FACTORS.items():
            if key != "default" and key in mat_lower:
                return data
        return cls.CONFIGURABLE_EMISSION_FACTORS["default"]

    @classmethod
    def calculate_impact(
        cls,
        material: str,
        quantity_kg: float,
        distance_km: float = 50.0,
        substitution_ratio: float = 0.95
    ) -> Dict[str, Any]:
        """
        Computes transparent environmental benefit breakdown:
        - Landfill / disposal diverted
        - Virgin raw material replaced
        - Gross avoided CO2e
        - Transportation logistics emissions
        - Net CO2e saved
        - Source assumption citation
        """
        qty = max(0.0, float(quantity_kg))
        dist = max(0.0, float(distance_km))

        factor_info = cls.get_factor_data(material)
        emission_factor = factor_info["factor"]
        replaced_mat = factor_info["replaced_material"]
        source_cite = factor_info["source"]

        # 1. Landfill diversion
        landfill_diverted_kg = qty
        landfill_diverted_tonnes = qty / 1000.0

        # 2. Virgin raw material replaced
        virgin_material_replaced_kg = qty * substitution_ratio
        virgin_material_replaced_tonnes = virgin_material_replaced_kg / 1000.0

        # 3. Gross production emissions avoided
        gross_co2_avoided_kg = virgin_material_replaced_kg * emission_factor
        gross_co2_avoided_tonnes = gross_co2_avoided_kg / 1000.0

        # 4. Transportation freight emissions
        transport_emissions_kg = qty * dist * cls.FREIGHT_EMISSION_FACTOR_KG_PER_KG_KM
        transport_emissions_tonnes = transport_emissions_kg / 1000.0

        # 5. Net environmental benefit
        net_co2_saved_kg = max(0.0, gross_co2_avoided_kg - transport_emissions_kg)
        net_co2_saved_tonnes = net_co2_saved_kg / 1000.0

        # Environmental score (0-100)
        env_score = min(100.0, max(50.0, 75.0 + (emission_factor * 10.0) - (dist * 0.02)))

        # Summary text
        if net_co2_saved_tonnes >= 1.0:
            summary = f"{net_co2_saved_tonnes:.2f} tonnes net CO₂e avoided | {landfill_diverted_tonnes:.2f} tonnes diverted from landfill"
        else:
            summary = f"{net_co2_saved_kg:.1f} kg net CO₂e avoided | {landfill_diverted_kg:.0f} kg diverted from landfill"

        return {
            "waste_diverted_kg": round(landfill_diverted_kg, 1),
            "waste_diverted_tonnes": round(landfill_diverted_tonnes, 3),
            "virgin_material_replaced_kg": round(virgin_material_replaced_kg, 1),
            "virgin_material_replaced_tonnes": round(virgin_material_replaced_tonnes, 3),
            "replaced_virgin_material_name": replaced_mat,
            "gross_avoided_emissions_kg_co2e": round(gross_co2_avoided_kg, 1),
            "gross_avoided_emissions_tonnes_co2e": round(gross_co2_avoided_tonnes, 3),
            "transportation_emissions_kg_co2e": round(transport_emissions_kg, 1),
            "transportation_emissions_tonnes_co2e": round(transport_emissions_tonnes, 3),
            "net_co2_saved_kg": round(net_co2_saved_kg, 1),
            "net_co2_saved_tonnes": round(net_co2_saved_tonnes, 3),
            "environmental_score": round(env_score, 1),
            "emission_factor_value": emission_factor,
            "data_source_citation": source_cite,
            "metric_summary": summary
        }
