from typing import List, Dict, Any, Optional
from ..knowledge_graph.kg_engine import W2RKGKnowledgeGraph


class ResourceMatcher:
    """
    Identifies high-value resource transformations and industrial use cases
    for incoming waste products using the W2RKG Knowledge Graph.
    """
    def __init__(self, kg: Optional[W2RKGKnowledgeGraph] = None):
        self.kg = kg or W2RKGKnowledgeGraph.get_instance()

    def discover_possible_uses(self, material: str, form: Optional[str] = None, condition: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discovers possible transformed resources from W2RKG.
        Enriches results with condition / form applicability.
        """
        if not material:
            return []

        # Query KG
        uses = self.kg.get_possible_uses_for_waste(material, threshold=0.5, top_k=12)

        # If primary query returned few results, expand query with form/category
        if len(uses) < 3 and form:
            combined_query = f"{material} {form}"
            extra_uses = self.kg.get_possible_uses_for_waste(combined_query, threshold=0.45, top_k=6)
            for u in extra_uses:
                if not any(existing["transformed_resource"] == u["transformed_resource"] for existing in uses):
                    uses.append(u)

        # Enrich and structure results
        enriched = []
        for item in uses:
            transformed = item["transformed_resource"]
            process = item["transforming_process"]
            confidence = item["confidence"]

            # Estimate technical feasibility adjustment based on condition
            feasibility_note = "High technical feasibility"
            if condition:
                cond_lower = condition.lower()
                if "mixed" in cond_lower or "contaminated" in cond_lower:
                    feasibility_note = "Requires pre-sorting or purification prior to conversion"
                    confidence = round(confidence * 0.9, 2)
                elif "wet" in cond_lower or "slurry" in cond_lower:
                    if "thermal" in process.lower() or "calcination" in process.lower() or "pyrolysis" in process.lower():
                        feasibility_note = "Requires dewatering or drying stage for thermal processing"
                    elif "anaerobic" in process.lower() or "digestion" in process.lower() or "aqueous" in process.lower():
                        feasibility_note = "Optimal moisture content for wet/biological processing"

            enriched.append({
                "transformed_resource": transformed,
                "transforming_process": process,
                "confidence": confidence,
                "feasibility_note": feasibility_note,
                "reference": item.get("reference", ""),
                "matched_kg_waste": item.get("matched_kg_waste", material)
            })

        return enriched
