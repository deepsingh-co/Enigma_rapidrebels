import os
import re
import json
from typing import Dict, Any, Optional, List
from ..ai.ai_layer import SymbiosisAILayer
from ..knowledge_graph.kg_engine import W2RKGKnowledgeGraph


class MaterialPropertyAnalyzer:
    """
    AI-powered Material & Property Analysis Engine.
    Structures raw industrial descriptions into rich, verified material profiles
    distinguishing explicitly provided properties from inferred domain estimates.
    """

    # Industry Category mapping rules
    CATEGORY_KEYWORDS = {
        "Cement": ["fly ash", "slag", "pozzolan", "limestone", "clinker", "gypsum", "cement kiln"],
        "Construction": ["concrete", "rubble", "demolition", "aggregate", "sand", "brick", "stone", "quarry dust"],
        "Textile": ["cotton", "fabric", "yarn", "fiber", "polyester", "wool", "textile", "selvedge", "garment"],
        "Chemical": ["acid", "alkali", "solvent", "sludge", "brine", "phosphogypsum", "resin", "catalyst", "effluent"],
        "Food Processing": ["spent grain", "spent yeast", "molasses", "bagasse", "coffee grounds", "citrus peel", "whey", "food waste"],
        "Metal": ["scale", "foundry sand", "dross", "scrap metal", "swarf", "tailings", "iron scrap", "aluminum"],
        "Plastic": ["plastic", "polymer", "polyethylene", "hdpe", "ldpe", "pet", "pp", "pvc", "regrind", "film"],
        "Paper": ["pulp", "paper sludge", "cellulose", "black liquor", "cardboard scrap"],
        "Agriculture": ["biomass", "crop residue", "straw", "husk", "manure", "stalk", "leaves"],
        "Manufacturing": ["packaging", "composite", "rubber", "refractory", "insulation"]
    }

    # Standard preprocessing profiles based on waste physics
    PREPROCESSING_KNOWLEDGE = {
        "fly ash": {
            "requirements": ["Screening/sieving (<45 micron)", "Dry pneumatics conveying", "Moisture control (<1%)"],
            "storage": "Hermetic dry silo storage",
            "grade_patterns": [(r'class\s*f|siliceous|coal', "Class F (Siliceous Pozzolan)"), (r'class\s*c|calcareous', "Class C (High Calcium)")]
        },
        "slag": {
            "requirements": ["Crushing and granulation", "Magnetic iron extraction", "Fine grinding to GGBFS"],
            "storage": "Covered concrete yard or bunker",
            "grade_patterns": [(r'blast\s*furnace|gbf|ggbfs', "Granulated Blast Furnace Slag"), (r'steel|bof|eaf', "Steel Slag Aggregate")]
        },
        "cotton": {
            "requirements": ["Mechanical shredding & garnetting", "Color/blend segregation", "Baling"],
            "storage": "Dry fire-protected warehouse",
            "grade_patterns": [(r'100%|pure|virgin', "100% Virgin Cotton Scraps"), (r'blended|poly', "Poly-Cotton Blended Scraps")]
        },
        "plastic": {
            "requirements": ["Polymer type sorting", "Washing and de-inking", "Shredding and pelletizing"],
            "storage": "Baled or caged dry storage",
            "grade_patterns": [(r'hdpe|ldpe|polyethylene', "Polyethylene Regrind"), (r'pet|bottle', "PET Flakes")]
        },
        "biomass": {
            "requirements": ["Moisture reduction/drying (<15%)", "Chipping/pulverization", "Pelletizing or briquetting"],
            "storage": "Well-ventilated dry shed to avoid auto-ignition",
            "grade_patterns": [(r'bagasse', "Sugar Mill Bagasse"), (r'straw|husk', "Agro-Husk Residue")]
        },
        "concrete": {
            "requirements": ["Primary crushing", "Rebar/wire magnetic extraction", "Sieving into coarse/fine fractions"],
            "storage": "Open aggregate stockyard",
            "grade_patterns": [(r'clean|structural', "Clean Structural Recycled Aggregate"), (r'mixed|masonry', "Mixed Demolition Rubble")]
        }
    }

    def __init__(self, ai_layer: Optional[SymbiosisAILayer] = None, kg: Optional[W2RKGKnowledgeGraph] = None):
        self.ai_layer = ai_layer or SymbiosisAILayer()
        self.kg = kg or W2RKGKnowledgeGraph.get_instance()

    @staticmethod
    def format_ordinal(n: int) -> str:
        """Formats integer as English ordinal: 1st, 2nd, 3rd, 4th, 11th, 12th, 13th, 21st, etc."""
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    def analyze_material_input(
        self,
        text_prompt: str,
        provided_quantity: Optional[float] = None,
        provided_unit: str = "kg",
        provided_frequency: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts verified structured material profile with clear demarcation between
        provided and inferred properties.
        """
        provided_fields: List[str] = []
        inferred_fields: List[str] = []

        prompt_clean = text_prompt.strip()
        p_lower = prompt_clean.lower()

        # 1. Material Name Extraction
        material_name = "Industrial Byproduct"
        for mat in [
            "fly ash", "blast furnace slag", "steel slag", "cotton fabric scraps", "cotton scraps",
            "textile waste", "plastic waste", "polyethylene scrap", "sugarcane bagasse",
            "spent bleaching earth", "spent grain", "foundry sand", "concrete rubble",
            "demolition waste", "phosphogypsum", "red mud", "paper sludge", "wood sawdust"
        ]:
            if mat in p_lower:
                material_name = mat.title()
                provided_fields.append("material_name")
                break

        if material_name == "Industrial Byproduct":
            words = [w for w in p_lower.replace(",", " ").split() if len(w) > 2 and w not in ["have", "generate", "with", "monthly", "tons", "tonnes", "kg", "every", "about"]]
            if words:
                material_name = " ".join(words[:2]).title()
                inferred_fields.append("material_name")

        # 2. Material Category
        category = "Manufacturing"
        for cat, kw_list in self.CATEGORY_KEYWORDS.items():
            if any(kw in p_lower for kw in kw_list):
                category = cat
                inferred_fields.append("material_category")
                break

        # 3. Physical Properties
        physical_props: Dict[str, Any] = {}

        # Moisture extraction
        moisture_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:moisture|water|humidity)', p_lower) or re.search(r'moisture(?:\s*content)?(?:\s*of|\s*is|\s*:)?\s*(\d+(?:\.\d+)?)\s*%', p_lower)
        if moisture_match:
            physical_props["moisture_content"] = {
                "value": f"{moisture_match.group(1)}%",
                "numeric_percent": float(moisture_match.group(1)),
                "is_inferred": False
            }
            provided_fields.append("physical_properties.moisture_content")
        else:
            # Domain-inferred moisture
            if "dry" in p_lower:
                physical_props["moisture_content"] = {"value": "< 2% (Dry)", "numeric_percent": 1.5, "is_inferred": True}
                inferred_fields.append("physical_properties.moisture_content")
            elif "slurry" in p_lower or "wet" in p_lower:
                physical_props["moisture_content"] = {"value": "20% - 40% (Wet/Slurry)", "numeric_percent": 30.0, "is_inferred": True}
                inferred_fields.append("physical_properties.moisture_content")

        # Physical form extraction
        form = "solid"
        if "powder" in p_lower or "dust" in p_lower or "fine" in p_lower or "ash" in p_lower:
            form = "powder"
            provided_fields.append("physical_properties.form")
        elif "slurry" in p_lower:
            form = "slurry"
            provided_fields.append("physical_properties.form")
        elif "scraps" in p_lower or "scrap" in p_lower or "shredded" in p_lower or "fabric" in p_lower:
            form = "scraps"
            provided_fields.append("physical_properties.form")
        elif "liquid" in p_lower or "effluent" in p_lower:
            form = "liquid"
            provided_fields.append("physical_properties.form")
        else:
            inferred_fields.append("physical_properties.form")
        physical_props["form"] = {"value": form, "is_inferred": form == "solid" and "solid" not in p_lower}

        # Temperature / condition if mentioned
        condition_val = "dry"
        if "wet" in p_lower:
            condition_val = "wet"
            provided_fields.append("condition")
        elif "mixed" in p_lower or "unsegregated" in p_lower:
            condition_val = "mixed"
            provided_fields.append("condition")
        elif "pure" in p_lower or "clean" in p_lower:
            condition_val = "pure"
            provided_fields.append("condition")
        else:
            inferred_fields.append("condition")
        physical_props["condition"] = {"value": condition_val, "is_inferred": "condition" in inferred_fields}

        # 4. Chemical Properties (if provided in text or inferred domain markers)
        chemical_props: Dict[str, Any] = {}
        ph_match = re.search(r'ph(?:\s*of|\s*is|\s*:)?\s*(\d+(?:\.\d+)?)', p_lower)
        if ph_match:
            chemical_props["pH"] = {"value": float(ph_match.group(1)), "is_inferred": False}
            provided_fields.append("chemical_properties.pH")

        carbon_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:carbon|c\b|unburnt)', p_lower)
        if carbon_match:
            chemical_props["unburnt_carbon"] = {"value": f"{carbon_match.group(1)}%", "is_inferred": False}
            provided_fields.append("chemical_properties.unburnt_carbon")

        if not chemical_props:
            if "fly ash" in p_lower:
                chemical_props["primary_oxides"] = {"value": "SiO₂ + Al₂O₃ + Fe₂O₃ (> 70%)", "is_inferred": True}
                chemical_props["reactivity"] = {"value": "Pozzolanic activity index > 75%", "is_inferred": True}
                inferred_fields.append("chemical_properties")
            elif "slag" in p_lower:
                chemical_props["primary_oxides"] = {"value": "CaO + SiO₂ + Al₂O₃ + MgO", "is_inferred": True}
                chemical_props["hydraulicity"] = {"value": "Latent hydraulic binding properties", "is_inferred": True}
                inferred_fields.append("chemical_properties")

        # 5. Quality & Grade Detection
        quality_grade = "Standard Industrial Byproduct"
        matched_kg_key = None
        for key, p_data in self.PREPROCESSING_KNOWLEDGE.items():
            if key in p_lower:
                matched_kg_key = key
                for pat, g_name in p_data["grade_patterns"]:
                    if re.search(pat, p_lower):
                        quality_grade = g_name
                        provided_fields.append("quality_grade")
                        break
                if quality_grade == "Standard Industrial Byproduct" and p_data["grade_patterns"]:
                    quality_grade = p_data["grade_patterns"][0][1]
                    inferred_fields.append("quality_grade")
                break

        # 6. Quantity & Unit
        quantity = provided_quantity
        unit = provided_unit or "kg"
        if quantity is None:
            qty_match = re.search(r'(\d+[\d,.]*)\s*(kg|kgs|ton|tons|tonnes|t|mt|liters|l|m3)', p_lower)
            if qty_match:
                try:
                    quantity = float(qty_match.group(1).replace(",", ""))
                    raw_unit = qty_match.group(2).lower()
                    if raw_unit in ["t", "ton", "tons", "tonnes", "mt"]:
                        quantity = quantity * 1000.0  # Normalize to kg
                        unit = "kg"
                    else:
                        unit = "kg" if "kg" in raw_unit else raw_unit
                    provided_fields.append("quantity")
                except Exception:
                    quantity = 5000.0
                    inferred_fields.append("quantity")
            else:
                quantity = 5000.0
                inferred_fields.append("quantity")
        else:
            provided_fields.append("quantity")

        # 7. Availability Frequency & Dates
        frequency = provided_frequency or "monthly"
        if "weekly" in p_lower or "week" in p_lower:
            frequency = "weekly"
            provided_fields.append("availability_frequency")
        elif "daily" in p_lower or "day" in p_lower:
            frequency = "daily"
            provided_fields.append("availability_frequency")
        elif "one-time" in p_lower or "one time" in p_lower or "batch" in p_lower:
            frequency = "one-time"
            provided_fields.append("availability_frequency")
        elif "monthly" in p_lower or "month" in p_lower:
            frequency = "monthly"
            provided_fields.append("availability_frequency")
        else:
            inferred_fields.append("availability_frequency")

        # Availability window / recurring schedule
        dates_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*(?:to|-)\s*(\d+)(?:st|nd|rd|th)?', p_lower)
        if dates_match:
            d1 = int(dates_match.group(1))
            d2 = int(dates_match.group(2))
            avail_window = {
                "recurring_window": f"{self.format_ordinal(d1)} - {self.format_ordinal(d2)} of every cycle",
                "start_day": d1,
                "end_day": d2,
                "is_inferred": False
            }
            provided_fields.append("availability_window")
        else:
            avail_window = {
                "recurring_window": "1st - 10th of every month (Continuous dispatch)",
                "start_day": 1,
                "end_day": 10,
                "is_inferred": True
            }
            inferred_fields.append("availability_window")

        # 8. Potential Applications & Resource Uses from W2RKG
        kg_uses = self.kg.get_possible_uses_for_waste(material_name, top_k=6)
        potential_apps = [u["transformed_resource"] for u in kg_uses] if kg_uses else ["Secondary raw material substitution", "Industrial circularity"]
        potential_resources = [f"{u['transformed_resource']} (via {u['transforming_process'][:40]}...)" for u in kg_uses[:4]] if kg_uses else ["Feedstock replacement"]

        # 9. Processing Requirements & Required Storage Conditions
        preprocessing_steps = ["Standard inspection and quality assay"]
        storage_cond = "Standard industrial covered storage"

        if matched_kg_key and matched_kg_key in self.PREPROCESSING_KNOWLEDGE:
            preprocessing_steps = self.PREPROCESSING_KNOWLEDGE[matched_kg_key]["requirements"]
            storage_cond = self.PREPROCESSING_KNOWLEDGE[matched_kg_key]["storage"]

        if physical_props.get("moisture_content", {}).get("numeric_percent", 0) > 10.0:
            if "Drying or dewatering required prior to thermal usage" not in preprocessing_steps:
                preprocessing_steps.insert(0, "Thermal drying or mechanical dewatering to reduce moisture")

        return {
            "material_name": material_name,
            "material_category": category,
            "quality_grade": quality_grade,
            "physical_properties": physical_props,
            "chemical_properties": chemical_props,
            "quantity": float(quantity),
            "quantity_unit": unit,
            "availability_frequency": frequency,
            "availability_window": avail_window,
            "potential_applications": potential_apps,
            "potential_resource_uses": potential_resources,
            "processing_requirements": preprocessing_steps,
            "required_conditions": storage_cond,
            "location": location or "Industrial Zone, India",
            "metadata": {
                "provided_fields": list(set(provided_fields)),
                "inferred_fields": list(set(inferred_fields)),
                "confidence_score": round(len(provided_fields) / max(1, len(provided_fields) + len(inferred_fields)), 2)
            }
        }
