import os
import json
import re
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple

try:
    from rapidfuzz import fuzz
except ImportError:
    # Minimal fallback if rapidfuzz is unavailable
    class fuzz:
        @staticmethod
        def token_set_ratio(s1: str, s2: str) -> float:
            set1, set2 = set(s1.lower().split()), set(s2.lower().split())
            if not set1 or not set2:
                return 0.0
            intersection = set1.intersection(set2)
            return (2.0 * len(intersection) / (len(set1) + len(set2))) * 100.0


class W2RKGKnowledgeGraph:
    """
    Industrial Symbiosis Knowledge Graph Engine powered by W2RKG.
    Manages waste-to-resource transformation pathways, relationships, and queries.
    """
    _instance: Optional["W2RKGKnowledgeGraph"] = None

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Default to backend/data directory
            # __file__ is in backend/services/symbiosis/knowledge_graph/kg_engine.py
            # 4 dirnames up is backend/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            data_dir = os.path.join(base_dir, "data")
        
        self.data_dir = data_dir
        self.graph = nx.MultiDiGraph()
        self.triples: List[Dict[str, str]] = []
        
        # Indexed lookups for fast retrieval
        self.waste_to_triples: Dict[str, List[Dict[str, str]]] = {}
        self.resource_to_triples: Dict[str, List[Dict[str, str]]] = {}
        
        self._load_knowledge_graph()

    @classmethod
    def get_instance(cls, data_dir: Optional[str] = None) -> "W2RKGKnowledgeGraph":
        if cls._instance is None:
            cls._instance = W2RKGKnowledgeGraph(data_dir)
        return cls._instance

    @staticmethod
    def preprocess_text(text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def _load_knowledge_graph(self):
        triples_file = os.path.join(self.data_dir, "fused_triples_aggregated.json")
        if not os.path.exists(triples_file):
            print(f"[W2RKG Warning] Triples file not found at: {triples_file}")
            return

        try:
            with open(triples_file, "r", encoding="utf-8") as f:
                self.triples = json.load(f)

            for entry in self.triples:
                waste = entry.get("waste", "").strip()
                resource = entry.get("transformed_resource", "").strip()
                process = entry.get("transforming_process", "").strip()
                reference = entry.get("reference", "").strip()

                if not waste or not resource:
                    continue

                # Populate NetworkX graph
                self.graph.add_node(waste, type="waste")
                self.graph.add_node(resource, type="resource")
                self.graph.add_edge(
                    waste,
                    resource,
                    process=process,
                    reference=reference
                )

                # Populate fast index lookups
                norm_w = self.preprocess_text(waste)
                norm_r = self.preprocess_text(resource)

                self.waste_to_triples.setdefault(norm_w, []).append(entry)
                self.resource_to_triples.setdefault(norm_r, []).append(entry)

            print(f"[W2RKG KG] Loaded {len(self.triples)} triples into graph ({self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges)")
        except Exception as e:
            print(f"[W2RKG Error] Failed to load KG triples: {e}")

    def calculate_string_similarity(self, s1: str, s2: str) -> float:
        """
        Fast multi-tier string similarity between query and KG entity.
        Combines exact substring match, token set ratio, and word overlap.
        """
        if not s1 or not s2:
            return 0.0
        
        p1 = self.preprocess_text(s1)
        p2 = self.preprocess_text(s2)

        if not p1 or not p2:
            return 0.0

        if p1 == p2:
            return 1.0

        # Substring containment bonus
        if p1 in p2 or p2 in p1:
            ratio = min(len(p1), len(p2)) / max(len(p1), len(p2))
            return max(0.85, 0.75 + 0.25 * ratio)

        score = fuzz.token_set_ratio(p1, p2) / 100.0
        return float(score)

    def find_matching_wastes(self, query: str, threshold: float = 0.55, top_k: int = 6) -> List[Tuple[str, float]]:
        """Find matching waste nodes in the KG for a given user query."""
        if not query:
            return []
        
        query_norm = self.preprocess_text(query)
        scored: List[Tuple[str, float]] = []

        # Direct exact match check
        if query_norm in self.waste_to_triples:
            # Find original casing from graph
            for node, data in self.graph.nodes(data=True):
                if data.get("type") == "waste" and self.preprocess_text(node) == query_norm:
                    scored.append((node, 1.0))
                    break

        # Match across unique KG waste nodes
        waste_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "waste"]
        for node in waste_nodes:
            if scored and node == scored[0][0]:
                continue
            sim = self.calculate_string_similarity(query, node)
            if sim >= threshold:
                scored.append((node, sim))

        # Sort descending by similarity score
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def find_matching_resources(self, query: str, threshold: float = 0.55, top_k: int = 6) -> List[Tuple[str, float]]:
        """Find matching transformed resource nodes in the KG for a given query."""
        if not query:
            return []
        
        query_norm = self.preprocess_text(query)
        scored: List[Tuple[str, float]] = []

        resource_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "resource"]
        for node in resource_nodes:
            sim = self.calculate_string_similarity(query, node)
            if sim >= threshold:
                scored.append((node, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_possible_uses_for_waste(self, waste_name: str, threshold: float = 0.55, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Discovers all potential transformed resources and transforming processes for a waste.
        Performs direct lookups and fuzzy matching on the W2RKG.
        """
        if not waste_name:
            return []

        # Find best matching waste entities in graph
        matched_wastes = self.find_matching_wastes(waste_name, threshold=threshold, top_k=4)
        
        if not matched_wastes:
            # Fallback: check general keyword containment
            norm = self.preprocess_text(waste_name)
            words = norm.split()
            matched_wastes = []
            for w_node in [n for n, d in self.graph.nodes(data=True) if d.get("type") == "waste"]:
                w_norm = self.preprocess_text(w_node)
                if any(word in w_norm for word in words if len(word) > 3):
                    matched_wastes.append((w_node, 0.6))
                if len(matched_wastes) >= 4:
                    break

        results: List[Dict[str, Any]] = []
        seen_pairs = set()

        for matched_waste, sim_score in matched_wastes:
            if not self.graph.has_node(matched_waste):
                continue
            
            # Get outgoing edges to transformed resources
            for neighbor in self.graph.successors(matched_waste):
                if self.graph.nodes[neighbor].get("type") != "resource":
                    continue

                edge_dict = self.graph[matched_waste][neighbor]
                for key, edge_data in edge_dict.items():
                    process = edge_data.get("process", "Standard industrial conversion / recycling")
                    reference = edge_data.get("reference", "")
                    
                    pair_key = (matched_waste, neighbor, process)
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    results.append({
                        "matched_kg_waste": matched_waste,
                        "transformed_resource": neighbor,
                        "transforming_process": process if process else "Direct reuse or chemical / physical transformation",
                        "reference": reference,
                        "confidence": round(float(sim_score), 2)
                    })

        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:top_k]

    def get_subgraph_data(self, center_waste: str, top_resources: Optional[List[str]] = None, partner_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generates nodes and links for interactive network graph visualization.
        """
        nodes = []
        links = []
        added_nodes = set()

        # Producer / Waste center node
        center_id = f"waste_{self.preprocess_text(center_waste)}"
        nodes.append({
            "id": center_id,
            "name": center_waste,
            "type": "waste",
            "category": "Source Waste",
            "color": "#F59E0B"
        })
        added_nodes.add(center_id)

        # Transformed resource nodes & edges
        possible_uses = self.get_possible_uses_for_waste(center_waste, top_k=6)
        for idx, item in enumerate(possible_uses):
            res_name = item["transformed_resource"]
            res_id = f"res_{idx}_{self.preprocess_text(res_name)}"
            
            if res_id not in added_nodes:
                nodes.append({
                    "id": res_id,
                    "name": res_name,
                    "type": "resource",
                    "category": "Transformed Resource",
                    "color": "#10B981"
                })
                added_nodes.add(res_id)

            links.append({
                "source": center_id,
                "target": res_id,
                "label": "transforms into",
                "process": item["transforming_process"],
                "color": "#6B7280"
            })

        return {"nodes": nodes, "links": links}
