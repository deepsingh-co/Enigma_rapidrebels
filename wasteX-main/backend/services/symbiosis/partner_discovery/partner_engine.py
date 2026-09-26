import os
import json
from typing import List, Dict, Any, Optional
from ..knowledge_graph.kg_engine import W2RKGKnowledgeGraph
from ..resource_matching.resource_matcher import ResourceMatcher
from ..opportunity.opportunity_engine import OpportunityAssessmentEngine


class PartnerDiscoveryEngine:
    """
    Industrial Symbiosis Partner Discovery Engine.
    Discovers previously unknown industrial partners who can utilize a producer's waste stream
    as valuable input resources via knowledge graph pathways and multi-factor opportunity assessment.
    """

    # Comprehensive benchmark industrial symbiosis entities across 10 major industrial sectors
    BENCHMARK_PARTNERS = [
        {
            "id": "partner_cement_01",
            "company_name": "UltraTech Cement Corp.",
            "industry_type": "Cement",
            "location": "Pune, Maharashtra",
            "contact_email": "procurement@ultratech-circular.com",
            "contact_phone": "+919820011223",
            "demanded_resources": ["Raw material for Cement production", "concrete", "aggregate", "clinker substitute", "pozzolanic additive"],
            "target_wastes": ["fly ash", "slag", "blast furnace slag", "red mud", "silica fume", "limestone dust"],
            "typical_demand_kg": 6000.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["dry", "powder", "granules", "pure", "mixed"],
            "description": "Leading cement producer incorporating industrial byproducts into Portland Pozzolana Cement (PPC) and green concrete formulations."
        },
        {
            "id": "partner_brick_02",
            "company_name": "EcoBricks & Advanced Ceramics",
            "industry_type": "Construction",
            "location": "Indore, Madhya Pradesh",
            "contact_email": "supply@ecobricks-tech.in",
            "contact_phone": "+919820022334",
            "demanded_resources": ["Raw material for Production of bricks", "ceramics", "building material", "aggregate"],
            "target_wastes": ["fly ash", "bottom ash", "foundry sand", "quarry dust", "clay residue", "ceramic scrap"],
            "typical_demand_kg": 4500.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["dry", "moist", "powder", "scraps"],
            "description": "Manufacturer of high-strength autoclaved aerated concrete (AAC) and non-fired eco-bricks using mineral industrial waste."
        },
        {
            "id": "partner_road_03",
            "company_name": "National Infrastructure & Paving Corp",
            "industry_type": "Construction",
            "location": "Ahmedabad, Gujarat",
            "contact_email": "materials@infra-paving.com",
            "contact_phone": "+919820033445",
            "demanded_resources": ["Raw material for Road construction", "Road foundations", "Paving", "aggregate", "bitumen modifier"],
            "target_wastes": ["slag", "demolition rubble", "concrete rubble", "crushed stone", "plastic waste", "steel slag"],
            "typical_demand_kg": 10000.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["solid", "scraps", "crushed", "dry", "coarse"],
            "description": "Major highway contractor utilizing recycled aggregates and polymer-modified bitumen for sustainable road foundations."
        },
        {
            "id": "partner_insul_04",
            "company_name": "ThermaShield Acoustic & Insulation Ltd",
            "industry_type": "Textile",
            "location": "Surat, Gujarat",
            "contact_email": "partners@thermashield.in",
            "contact_phone": "+919820044556",
            "demanded_resources": ["thermal insulation", "acoustic panels", "insoluble polymer", "fiber composite"],
            "target_wastes": ["cotton", "fabric scraps", "textile waste", "polyester", "wool scrap", "cellulose fiber"],
            "typical_demand_kg": 3000.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["dry", "scraps", "shredded", "pure", "mixed"],
            "description": "Produces thermal and sound dampening insulation pads for the automotive and building industries from regenerated textile fibers."
        },
        {
            "id": "partner_bio_05",
            "company_name": "AeroBiofuels & Green Energy Ltd",
            "industry_type": "Food Processing",
            "location": "Vadodara, Gujarat",
            "contact_email": "feedstock@aerobiofuels.org",
            "contact_phone": "+919820055667",
            "demanded_resources": ["bio-oil", "biogas", "syngas", "activated carbon", "process energy"],
            "target_wastes": ["biomass", "crop residues", "bagasse", "spent grains", "wood waste", "agricultural residue", "organic sludge"],
            "typical_demand_kg": 8000.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["dry", "moist", "organic", "solid", "crushed"],
            "description": "Next-generation biorefinery producing advanced drop-in biofuels, pyrolysis bio-oil, and carbon pellets from agro-industrial residues."
        },
        {
            "id": "partner_poly_06",
            "company_name": "PolyReclaim Composites",
            "industry_type": "Plastic",
            "location": "Mumbai, Maharashtra",
            "contact_email": "intake@polyreclaim.com",
            "contact_phone": "+919820066778",
            "demanded_resources": ["recycled polymer", "flame retardant materials", "composite materials", "injection pellets"],
            "target_wastes": ["plastic waste", "polyethylene", "polypropylene", "pet scraps", "film scrap"],
            "typical_demand_kg": 5000.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["shredded", "baled", "clean", "mixed"],
            "description": "Industrial plastics re-granulation facility compounding post-industrial polymer scraps into automotive-grade composite resin."
        },
        {
            "id": "partner_foundry_07",
            "company_name": "Apex Metallurgical & Foundry Works",
            "industry_type": "Metal",
            "location": "Nagpur, Maharashtra",
            "contact_email": "recycling@apexmetals.in",
            "contact_phone": "+919820077889",
            "demanded_resources": ["Raw material for Production of refractories", "silica sand", "foundry flux", "metallurgical additive"],
            "target_wastes": ["mill scales", "foundry slag", "spent sand", "metal scrap", "refractories"],
            "typical_demand_kg": 6000.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["dry", "granular", "solid"],
            "description": "Refractory and metal casting firm recycling spent sands, slag flux, and mill scale into refractory furnace linings."
        },
        {
            "id": "partner_agri_08",
            "company_name": "TerraFert Organic Agritech",
            "industry_type": "Agriculture",
            "location": "Bhopal, Madhya Pradesh",
            "contact_email": "procurement@terrafert.co",
            "contact_phone": "+919820088990",
            "demanded_resources": ["Fertiliser", "Soil quality improvement and fertiliser", "soil amendment", "compost activator"],
            "target_wastes": ["food waste", "distillery spent wash", "ash", "press mud", "lignin residue", "spent grounds"],
            "typical_demand_kg": 4000.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["slurry", "moist", "organic", "solid"],
            "description": "Manufacturer of bio-enriched soil conditioners and organic micro-nutrient fertilizers utilizing agro-industrial waste streams."
        },
        {
            "id": "partner_chem_09",
            "company_name": "Gujarat Speciality Syntheses & Chlor-Alkali",
            "industry_type": "Chemical",
            "location": "Surat, Gujarat",
            "contact_email": "feedstock@gujaratsynth.com",
            "contact_phone": "+919820099001",
            "demanded_resources": ["chemical feedstock", "solvent recovery", "calcium sulfate", "acid neutralizer"],
            "target_wastes": ["phosphogypsum", "acid waste", "spent caustic", "brine", "chemical sludge"],
            "typical_demand_kg": 7500.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["liquid", "slurry", "solid"],
            "description": "Industrial chemical complex valorizing inorganic gypsum, spent acids, and chlor-alkali byproducts into industrial salts."
        },
        {
            "id": "partner_paper_10",
            "company_name": "GreenPulp Board & Packaging Mills",
            "industry_type": "Paper",
            "location": "Coimbatore, Tamil Nadu",
            "contact_email": "recycling@greenpulp.in",
            "contact_phone": "+919820100112",
            "demanded_resources": ["cellulose fiber", "corrugated medium", "pulp substitute", "filler clay"],
            "target_wastes": ["paper sludge", "cotton linters", "bagasse", "cardboard cuttings", "textile fiber"],
            "typical_demand_kg": 8500.0,
            "intake_frequency": "monthly",
            "accepted_conditions": ["dry", "baled", "shredded"],
            "description": "Eco-friendly duplex paperboard and packaging manufacturer using non-wood fibers and textile cuttings for pulp blending."
        }
    ]

    def __init__(self, kg: Optional[W2RKGKnowledgeGraph] = None, db=None):
        self.kg = kg or W2RKGKnowledgeGraph.get_instance()
        self.matcher = ResourceMatcher(self.kg)
        self.db = db

    def _get_platform_consumers(self) -> List[Dict[str, Any]]:
        """Fetch registered consumer / buyer businesses from MongoDB."""
        consumers = []
        if self.db is not None:
            try:
                cursor = self.db.users.find({"role": {"$in": ["consumer", "buyer", "recycler", "manufacturer"]}})
                for user in cursor:
                    consumers.append({
                        "id": str(user.get("_id")),
                        "company_name": user.get("company_name", "Registered Industrial Buyer"),
                        "industry_type": user.get("industry", "Manufacturing"),
                        "location": user.get("location", "India"),
                        "contact_email": user.get("email", ""),
                        "contact_phone": user.get("phone", "+919820011223"),
                        "demanded_resources": user.get("materials_demanded", [user.get("demanded_material", "")]),
                        "typical_demand_kg": float(user.get("demand_quantity", 5000)),
                        "intake_frequency": "monthly",
                        "is_platform_registered": True
                    })
            except Exception as e:
                print(f"[W2RKG Warning] Could not query platform users: {e}")

        return consumers

    def discover_partners(
        self,
        material: str,
        quantity: float,
        location: str,
        form: str = "solid",
        condition: str = "dry",
        producer_name: str = "Industrial Producer",
        producer_industry: str = "Manufacturing",
        top_k: int = 5,
        material_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main industrial symbiosis partner discovery engine.
        Returns ranked matching partners, transformation pathways, match scores, reasoning, and network graph.
        """
        # 1. Discover possible resource uses from Knowledge Graph
        possible_uses = self.matcher.discover_possible_uses(material, form=form, condition=condition)
        
        # 2. Gather candidates: Platform registered consumers + benchmark cross-industry partners
        candidates = self._get_platform_consumers() + self.BENCHMARK_PARTNERS

        potential_partners = []
        material_lower = material.lower().strip()

        # Build default material profile if not passed
        if not material_profile:
            material_profile = {
                "material_name": material,
                "quantity": quantity,
                "physical_properties": {
                    "form": {"value": form},
                    "condition": {"value": condition}
                },
                "availability_frequency": "monthly",
                "availability_window": {"start_day": 1, "end_day": 10}
            }

        producer_info = {
            "company_name": producer_name,
            "industry": producer_industry,
            "location": location
        }

        for candidate in candidates:
            demanded = candidate.get("demanded_resources", [])
            if isinstance(demanded, str):
                demanded = [demanded]
            
            target_wastes = candidate.get("target_wastes", [])

            best_transformation = None
            best_sim = 0.0

            # Direct waste match
            for tw in target_wastes:
                sim = self.kg.calculate_string_similarity(material_lower, tw)
                if sim > best_sim:
                    best_sim = sim
                    best_transformation = {
                        "transformed_resource": candidate.get("industry_type", "Direct utilization"),
                        "transforming_process": "Direct material recycling / feed intake",
                        "confidence": sim
                    }

            # Transformed resource matches via W2RKG
            for use in possible_uses:
                t_res = use["transformed_resource"].lower()
                for dem in demanded:
                    sim = self.kg.calculate_string_similarity(t_res, dem.lower()) * use["confidence"]
                    if sim > best_sim:
                        best_sim = sim
                        best_transformation = use

            # If match is above threshold
            if best_sim >= 0.45 or (not potential_partners and best_sim >= 0.35):
                trans_process = best_transformation["transforming_process"] if best_transformation else "Industrial transformation & valorization"
                target_resource = best_transformation["transformed_resource"] if best_transformation else candidate.get("industry_type", "Feedstock")

                transformation_data = {
                    "transformed_resource": target_resource,
                    "transforming_process": trans_process,
                    "confidence": best_sim,
                    "reference": best_transformation.get("reference", "") if best_transformation else ""
                }

                candidate_data = {
                    "id": candidate["id"],
                    "company_name": candidate["company_name"],
                    "industry_type": candidate.get("industry_type", "Manufacturing"),
                    "location": candidate.get("location", location),
                    "contact_email": candidate.get("contact_email", "procurement@wastesymbiosis.org"),
                    "contact_phone": candidate.get("contact_phone", "+919820011223"),
                    "required_quantity": float(candidate.get("typical_demand_kg", quantity)),
                    "intake_frequency": candidate.get("intake_frequency", "monthly"),
                    "is_platform_registered": candidate.get("is_platform_registered", False),
                    "description": candidate.get("description", "")
                }

                # Evaluate Complete 9-Factor Opportunity Assessment
                opportunity_assessment = OpportunityAssessmentEngine.evaluate_opportunity(
                    producer_data=producer_info,
                    partner_data=candidate_data,
                    material_profile=material_profile,
                    transformation_pathway=transformation_data
                )

                potential_partners.append({
                    "industry": candidate_data,
                    "matchScore": opportunity_assessment["opportunity_score"],
                    "opportunityScore": opportunity_assessment["opportunity_score"],
                    "materialCompatibility": opportunity_assessment["factor_breakdown"]["material_compatibility"],
                    "quantityCompatibility": opportunity_assessment["timing_analysis"]["frequency_alignment"],
                    "qualityCompatibility": f"Quality Score: {opportunity_assessment['factor_breakdown']['quality_compatibility']}%",
                    "distance": opportunity_assessment["logistics_analysis"]["distance_km"],
                    "distanceDescription": f"{opportunity_assessment['logistics_analysis']['distance_km']:.1f} km via {opportunity_assessment['logistics_analysis']['transport_mode']}",
                    "transformationPathway": transformation_data,
                    "factor_breakdown": opportunity_assessment["factor_breakdown"],
                    "timing_analysis": opportunity_assessment["timing_analysis"],
                    "logistics_analysis": opportunity_assessment["logistics_analysis"],
                    "processing_analysis": opportunity_assessment["processing_analysis"],
                    "environmentalImpact": opportunity_assessment["environmental_analysis"],
                    "reasons": opportunity_assessment["detailed_evidence"],
                    "summary_reasoning": opportunity_assessment["summary_reasoning"]
                })

        # Rank potential partners by overall opportunity score
        potential_partners.sort(key=lambda x: x["opportunityScore"], reverse=True)
        top_partners = potential_partners[:top_k]

        # Build Network Graph representation
        network_graph = self._build_network_graph(
            producer_name=producer_name,
            material=material,
            location=location,
            top_partners=top_partners,
            possible_uses=possible_uses
        )

        return {
            "waste": {
                "title": f"{quantity:,.0f} kg {condition} {material} {form}".strip(),
                "material": material,
                "quantity": quantity,
                "quantity_unit": "kg",
                "frequency": "monthly",
                "form": form,
                "condition": condition,
                "location": location,
                "industry_type": producer_industry,
                "producer_name": producer_name
            },
            "possibleUses": possible_uses[:8],
            "potentialPartners": top_partners,
            "networkGraph": network_graph,
            "total_partners_discovered": len(top_partners)
        }

    def _build_network_graph(
        self,
        producer_name: str,
        material: str,
        location: str,
        top_partners: List[Dict[str, Any]],
        possible_uses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Builds graph elements (nodes and links) for interactive network visualization.
        """
        nodes = []
        links = []
        added_node_ids = set()

        # Producer Node
        prod_id = "node_producer"
        nodes.append({
            "id": prod_id,
            "name": producer_name,
            "type": "producer",
            "category": "Waste Producer",
            "color": "#3B82F6",
            "details": f"Location: {location}"
        })
        added_node_ids.add(prod_id)

        # Waste Node
        waste_id = "node_waste"
        nodes.append({
            "id": waste_id,
            "name": material,
            "type": "waste",
            "category": "Waste Stream",
            "color": "#F59E0B",
            "details": f"Source Material: {material}"
        })
        added_node_ids.add(waste_id)

        links.append({
            "source": prod_id,
            "target": waste_id,
            "label": "generates",
            "color": "#3B82F6"
        })

        # Process & Resource Nodes + Partner Connections
        for idx, partner_data in enumerate(top_partners):
            partner = partner_data["industry"]
            pathway = partner_data["transformationPathway"]
            res_name = pathway["transformed_resource"]
            proc_name = pathway["transforming_process"]

            res_id = f"node_res_{idx}"
            if res_id not in added_node_ids:
                nodes.append({
                    "id": res_id,
                    "name": res_name,
                    "type": "resource",
                    "category": "Transformed Resource",
                    "color": "#10B981",
                    "details": f"Process: {proc_name[:60]}..."
                })
                added_node_ids.add(res_id)

            links.append({
                "source": waste_id,
                "target": res_id,
                "label": "transforms into",
                "process": proc_name,
                "color": "#10B981"
            })

            partner_id = f"node_partner_{partner['id']}"
            if partner_id not in added_node_ids:
                nodes.append({
                    "id": partner_id,
                    "name": partner["company_name"],
                    "type": "partner",
                    "category": partner["industry_type"],
                    "color": "#8B5CF6",
                    "matchScore": partner_data["opportunityScore"],
                    "details": f"{partner['industry_type']} ({partner['location']})"
                })
                added_node_ids.add(partner_id)

            links.append({
                "source": res_id,
                "target": partner_id,
                "label": "supplies to",
                "matchScore": f"{partner_data['opportunityScore']}%",
                "color": "#8B5CF6"
            })

        return {"nodes": nodes, "links": links}
