from typing import Dict, Any, Optional, List
from .knowledge_graph.kg_engine import W2RKGKnowledgeGraph
from .partner_discovery.partner_engine import PartnerDiscoveryEngine
from .resource_matching.resource_matcher import ResourceMatcher
from .material_analysis.material_analyzer import MaterialPropertyAnalyzer
from .opportunity.opportunity_engine import OpportunityAssessmentEngine
from .ai.ai_layer import SymbiosisAILayer
from ..communication.twilio_service import TwilioCommunicationService


class SymbiosisService:
    """
    Unified Industrial Symbiosis Intelligence Service for WasteX.
    Coordinates Knowledge Graph querying, AI material analysis, multi-factor opportunity assessment,
    partner discovery, and Twilio multi-channel communication.
    """
    _instance: Optional["SymbiosisService"] = None

    def __init__(self, db=None):
        self.db = db
        self.kg = W2RKGKnowledgeGraph.get_instance()
        self.matcher = ResourceMatcher(self.kg)
        self.partner_engine = PartnerDiscoveryEngine(self.kg, db=db)
        self.material_analyzer = MaterialPropertyAnalyzer(kg=self.kg)
        self.ai_layer = SymbiosisAILayer()
        self.twilio_service = TwilioCommunicationService.get_instance()

    @classmethod
    def get_instance(cls, db=None) -> "SymbiosisService":
        if cls._instance is None:
            cls._instance = SymbiosisService(db=db)
        elif db is not None and cls._instance.db is None:
            cls._instance.db = db
            cls._instance.partner_engine.db = db
        return cls._instance

    def analyze_material_text(
        self,
        prompt: str,
        quantity: Optional[float] = None,
        unit: str = "kg",
        frequency: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes AI Material & Property extraction on natural text input.
        """
        return self.material_analyzer.analyze_material_input(
            text_prompt=prompt,
            provided_quantity=quantity,
            provided_unit=unit,
            provided_frequency=frequency,
            location=location
        )

    def analyze_symbiosis(
        self,
        material: str,
        quantity: float,
        location: str,
        form: str = "solid",
        condition: str = "dry",
        category: str = "Other",
        producer_name: str = "Industrial Producer",
        producer_industry: str = "Manufacturing",
        top_k: int = 5,
        raw_description: Optional[str] = None,
        unit: str = "kg"
    ) -> Dict[str, Any]:
        """
        Executes end-to-end industrial symbiosis analysis for a given waste stream.
        """
        if not material or not material.strip():
            raise ValueError("Material name is required for industrial symbiosis analysis.")

        if quantity is None or float(quantity) <= 0:
            raise ValueError("Quantity must be greater than 0.")

        qty = float(quantity)
        loc = location.strip() if location else "India"

        # 1. AI Material & Property Profiling
        material_profile = self.material_analyzer.analyze_material_input(
            text_prompt=raw_description or f"{qty} {unit} {condition} {material} ({form}) in {loc}",
            provided_quantity=qty,
            provided_unit=unit,
            location=loc
        )

        # 2. Discover partners & evaluate complete 9-factor opportunity scores
        discovery_result = self.partner_engine.discover_partners(
            material=material.strip(),
            quantity=qty,
            location=loc,
            form=form.strip() if form else "solid",
            condition=condition.strip() if condition else "dry",
            producer_name=producer_name.strip() if producer_name else "Producer",
            producer_industry=producer_industry.strip() if producer_industry else "Manufacturing",
            top_k=top_k,
            material_profile=material_profile
        )

        # 3. AI Insights & Strategic advice
        top_partner = discovery_result["potentialPartners"][0] if discovery_result["potentialPartners"] else None
        ai_insights = self.ai_layer.generate_strategic_insights(
            waste_data=discovery_result["waste"],
            top_partner=top_partner,
            possible_uses=discovery_result["possibleUses"]
        )

        discovery_result["material_profile"] = material_profile
        discovery_result["ai_insights"] = ai_insights
        return discovery_result

    def dispatch_partner_notification(
        self,
        channel: str,
        recipient_phone: str,
        partner_name: str,
        producer_name: str,
        waste_material: str,
        quantity: float,
        notification_type: str = "connection_request",
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches multi-channel notification via Twilio (SMS, WhatsApp, Voice).
        """
        body = custom_message or (
            f"New Industrial Symbiosis Match! {producer_name} has {quantity:,.0f} kg of {waste_material} available "
            f"matching {partner_name}'s secondary raw material demand."
        )

        ch = channel.lower().strip()
        if ch == "sms":
            return self.twilio_service.send_sms(to_phone=recipient_phone, message_body=body, notification_type=notification_type)
        elif ch == "whatsapp":
            return self.twilio_service.send_whatsapp(to_phone=recipient_phone, message_body=body, notification_type=notification_type)
        elif ch in ["voice", "call", "voice_call"]:
            spoken_script = f"Attention {partner_name} procurement team. A new industrial symbiosis opportunity has been matched from {producer_name} for {quantity:,.0f} kilograms of {waste_material}."
            return self.twilio_service.make_voice_call(to_phone=recipient_phone, spoken_message=spoken_script, notification_type=notification_type)
        else:
            raise ValueError(f"Unsupported communication channel: {channel}. Use 'sms', 'whatsapp', or 'voice'.")

    def query_graph_subgraph(self, waste_query: str) -> Dict[str, Any]:
        """
        Returns subgraph visualization elements for a given waste or query.
        """
        return self.kg.get_subgraph_data(waste_query)

    def get_benchmark_industries(self) -> List[Dict[str, Any]]:
        """
        Returns available registered and benchmark industrial sectors.
        """
        return PartnerDiscoveryEngine.BENCHMARK_PARTNERS
