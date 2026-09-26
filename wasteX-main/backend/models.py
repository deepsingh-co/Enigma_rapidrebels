from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


def current_utc_time() -> datetime:
    return datetime.now(timezone.utc)


class User(BaseModel):
    company_name: str
    email: str
    role: Optional[str] = "producer"
    industry: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    firebase_uid: Optional[str] = None
    materials_demanded: Optional[List[str]] = None
    demand_quantity: Optional[float] = None
    created_at: datetime = Field(default_factory=current_utc_time)


class WasteListing(BaseModel):
    producer_id: str
    title: str
    material: str
    category: str
    form: str
    condition: str
    quantity: float
    quantity_unit: str = "kg"
    frequency: str = "monthly"
    location: str
    expected_price: float
    created_at: datetime = Field(default_factory=current_utc_time)

    @field_validator("quantity")
    @classmethod
    def validate_quantity_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v


class BuyerRequirement(BaseModel):
    consumer_id: str
    material_required: str
    quantity_required: float
    location: str

    @field_validator("quantity_required")
    @classmethod
    def validate_quantity_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity required must be greater than 0.")
        return v


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class PromptParseRequest(BaseModel):
    prompt: str
    current_data: dict = {}


class SearchRequest(BaseModel):
    query: str


class ContactMessage(BaseModel):
    listing_id: str
    buyer_name: str
    message: str
    sender_email: Optional[str] = None
    receiver_email: Optional[str] = None
    created_at: datetime = Field(default_factory=current_utc_time)


class MaterialAnalysisRequest(BaseModel):
    description: str
    quantity: Optional[float] = None
    quantity_unit: Optional[str] = "kg"
    frequency: Optional[str] = None
    location: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v


class SymbiosisAnalyzeRequest(BaseModel):
    industryId: Optional[str] = None
    wasteId: Optional[str] = None
    listing_id: Optional[str] = None
    material: Optional[str] = None
    raw_description: Optional[str] = None
    quantity: Optional[float] = 5000.0
    quantity_unit: Optional[str] = "kg"
    frequency: Optional[str] = "monthly"
    form: Optional[str] = "powder"
    condition: Optional[str] = "dry"
    category: Optional[str] = "Other"
    location: Optional[str] = "Mumbai"
    producer_name: Optional[str] = "WasteX Industrial Partner"
    producer_industry: Optional[str] = "Manufacturing"
    top_k: Optional[int] = 5

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v


class SymbiosisProposalRequest(BaseModel):
    partner_id: str
    partner_name: str
    partner_email: Optional[str] = None
    partner_phone: Optional[str] = None
    producer_name: str
    producer_email: Optional[str] = None
    producer_phone: Optional[str] = None
    waste_material: str
    quantity: float
    quantity_unit: str = "kg"
    proposed_process: Optional[str] = None
    message: str
    dispatch_sms: Optional[bool] = True
    dispatch_whatsapp: Optional[bool] = False
    created_at: datetime = Field(default_factory=current_utc_time)

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v


class TwilioNotificationRequest(BaseModel):
    channel: str = "sms"  # "sms" | "whatsapp" | "voice"
    recipient_phone: str
    partner_name: str
    producer_name: str
    waste_material: str
    quantity: float = 5000.0
    notification_type: str = "connection_request"  # "partner_discovered" | "connection_request" | "opportunity_accepted" | "meeting_pickup" | "exchange_alert"
    custom_message: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v


class QuickMatchRequest(BaseModel):
    query: str
    threshold: Optional[float] = 0.5
    top_k: Optional[int] = 6
