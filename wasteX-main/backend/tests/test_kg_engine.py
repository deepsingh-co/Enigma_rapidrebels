import pytest
from services.symbiosis.knowledge_graph.kg_engine import W2RKGKnowledgeGraph


def test_kg_engine_loads_triples():
    kg = W2RKGKnowledgeGraph.get_instance()
    assert len(kg.triples) > 10000
    assert kg.graph.number_of_nodes() > 5000
    assert kg.graph.number_of_edges() > 10000


def test_find_matching_wastes():
    kg = W2RKGKnowledgeGraph.get_instance()
    matches = kg.find_matching_wastes("Fly Ash", threshold=0.6, top_k=5)
    assert len(matches) > 0
    matched_names = [m[0].lower() for m in matches]
    assert any("fly ash" in name for name in matched_names)


def test_get_possible_uses_for_fly_ash():
    kg = W2RKGKnowledgeGraph.get_instance()
    uses = kg.get_possible_uses_for_waste("Fly Ash", top_k=5)
    assert len(uses) > 0
    resources = [u["transformed_resource"].lower() for u in uses]
    # Fly ash transforms into concrete, aggregate, ceramics, or building materials
    assert any("concrete" in r or "aggregate" in r or "ceramic" in r or "brick" in r for r in resources)
    for u in uses:
        assert "transforming_process" in u
        assert "confidence" in u
        assert u["confidence"] > 0.4


def test_get_subgraph_data():
    kg = W2RKGKnowledgeGraph.get_instance()
    graph_data = kg.get_subgraph_data("Cotton Scraps")
    assert "nodes" in graph_data
    assert "links" in graph_data
    assert len(graph_data["nodes"]) >= 2
    assert len(graph_data["links"]) >= 1
