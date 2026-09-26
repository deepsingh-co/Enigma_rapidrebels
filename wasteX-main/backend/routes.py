import os
from fastapi import APIRouter, HTTPException, Query
from models import (
    WasteListing, User, BuyerRequirement, ChatRequest,
    PromptParseRequest, SearchRequest, ContactMessage,
    SymbiosisAnalyzeRequest, SymbiosisProposalRequest, QuickMatchRequest,
    MaterialAnalysisRequest, TwilioNotificationRequest
)
from database import database
from bson import ObjectId
from serpapi import GoogleSearch
from services.symbiosis.symbiosis_service import SymbiosisService

router = APIRouter()

def serialize_doc(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# ─────────────────────────────────────────────────────────────
# Core WasteX Endpoints (Preserved & Enhanced)
# ─────────────────────────────────────────────────────────────

@router.post("/auth/google")
def google_login(user: User):
    existing_user = database.users.find_one({"email": user.email})
    if existing_user:
        if user.firebase_uid and not existing_user.get("firebase_uid"):
            database.users.update_one({"_id": existing_user["_id"]}, {"$set": {"firebase_uid": user.firebase_uid}})
        return {"id": str(existing_user["_id"]), "message": "Login successful"}
    else:
        result = database.users.insert_one(user.dict())
        return {"id": str(result.inserted_id), "message": "User registered successfully"}

@router.post("/users")
def create_user(user: User):
    result = database.users.insert_one(user.dict())
    return {"id": str(result.inserted_id)}

@router.post("/listings")
def create_listing(listing: WasteListing):
    listing_dict = listing.dict()
    material = listing_dict.get("material", "").lower()
    if "cotton" in material or "fabric" in material:
        listing_dict["category"] = "Textile"
    elif "plastic" in material:
        listing_dict["category"] = "Plastic"
    elif any(k in material for k in ["ash", "slag", "concrete", "sand", "brick"]):
        listing_dict["category"] = "Mineral"
    elif any(k in material for k in ["bio", "wood", "bagasse", "food", "husk"]):
        listing_dict["category"] = "Biomass"
    elif any(k in material for k in ["acid", "solvent", "sludge", "chemical"]):
        listing_dict["category"] = "Chemical"
    else:
        listing_dict["category"] = "Other"

    result = database.listings.insert_one(listing_dict)
    return {"id": str(result.inserted_id), "message": "Listing created"}

@router.get("/listings")
def get_listings():
    cursor = database.listings.find()
    return [serialize_doc(doc) for doc in cursor]

@router.get("/listings/{listing_id}")
def get_single_listing(listing_id: str):
    try:
        listing = database.listings.find_one({"_id": ObjectId(listing_id)})
    except Exception:
        listing = database.listings.find_one({"_id": listing_id})

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return serialize_doc(listing)

@router.get("/match/{listing_id}")
def match_buyers(listing_id: str):
    try:
        listing = database.listings.find_one({"_id": ObjectId(listing_id)})
    except Exception:
        listing = database.listings.find_one({"_id": listing_id})

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    material = listing.get("material", "")
    location = listing.get("location", "")
    
    internal_buyers = []
    cursor = database.users.find({"role": {"$in": ["consumer", "buyer", "recycler"]}})
    for consumer in cursor:
        internal_buyers.append({
            "name": consumer.get("company_name", "Industrial Consumer"),
            "distance": "120 km",
            "compatibility": "85%",
            "internal": True
        })
    if not internal_buyers:
        internal_buyers = [
            {"name": "GreenThreads Recyclers", "distance": "80 km", "compatibility": "92%", "internal": True},
            {"name": "EcoFibre Processing", "distance": "150 km", "compatibility": "88%", "internal": True}
        ]

    external_buyers = []
    api_key = os.getenv("SERPAPI_KEY")
    if api_key and api_key != "YOUR_SERPAPI_KEY_HERE":
        try:
            search = GoogleSearch({
                "q": f"{material} recycling buyers near {location}",
                "location": "India",
                "api_key": api_key
            })
            results = search.get_dict()
            organic = results.get("organic_results", [])
            for res in organic[:3]:
                external_buyers.append({
                    "name": res.get("title"),
                    "link": res.get("link"),
                    "snippet": res.get("snippet"),
                    "internal": False
                })
        except Exception as e:
            print("SerpApi Error:", e)
    else:
        external_buyers = [
            {"name": "Global Industrial Recovery", "link": "#", "snippet": "Leading processors and buyers of industrial waste and byproducts.", "internal": False},
            {"name": "National Circular Scrap Exchange", "link": "#", "snippet": "B2B clearinghouse for raw material secondary resources.", "internal": False}
        ]

    market_price = "₹6-₹14/kg"

    return {
        "listing": serialize_doc(listing),
        "internal_matches": internal_buyers,
        "external_leads": external_buyers,
        "market_intelligence": {
            "estimated_price": market_price
        }
    }

@router.post("/chat")
def chat_with_bot(request: ChatRequest):
    from huggingface_hub import InferenceClient
    
    api_key = os.getenv("HF_TOKEN")
    model = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct")
    
    if not api_key or api_key == "YOUR_HF_TOKEN_HERE":
        return {
            "reply": "WasteX is India's premier B2B circular economy platform. We connect industrial waste producers with specialized recycling and cross-sector industrial symbiosis partners. How can I help you valorize your by-products today?"
        }
    
    try:
        client = InferenceClient(api_key=api_key)
        system_prompt = "You are a helpful AI assistant for WasteX. WasteX is a platform dedicated to reducing waste, promoting recycling, and connecting people with waste management resources. Your purpose is to explain the work, purpose, and objectives of WasteX clearly and concisely to users. Keep your answers brief and helpful."
        
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in request.messages:
            if msg.role == 'assistant' and msg.content == '': continue
            formatted_messages.append({"role": msg.role, "content": msg.content})
            
        res = client.chat_completion(
            messages=formatted_messages, 
            model=model,
            max_tokens=250,
            temperature=0.7
        )
        
        bot_reply = "Sorry, I couldn't generate a response."
        if res and res.choices and len(res.choices) > 0:
            bot_reply = res.choices[0].message.content.strip()
            
        return {"reply": bot_reply}
        
    except Exception as e:
        return {
            "reply": "WasteX connects industrial facilities to convert waste into secondary resources. Explore listings or run our Industrial Symbiosis intelligence engine to find matches."
        }

@router.post("/parse-listing")
def parse_listing_prompt(request: PromptParseRequest):
    import json
    api_key = os.getenv("HF_TOKEN")
    model = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct")
    
    if api_key and api_key != "YOUR_HF_TOKEN_HERE":
        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(api_key=api_key)
            system_prompt = f"""
            You are a conversational AI assistant helping a user list industrial waste on the WasteX platform.
            Current extracted data: {json.dumps(request.current_data)}
            Return ONLY a JSON object with:
            {{
              "parsed_data": {{"title": "...", "material": "...", "quantity": 500, "form": "...", "condition": "...", "location": "...", "expected_price": 10, "frequency": "monthly"}},
              "message": "Conversational response"
            }}
            """
            res = client.chat_completion(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": request.prompt}],
                model=model,
                max_tokens=500,
                temperature=0.3
            )
            content = res.choices[0].message.content.strip()
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            return json.loads(content.strip())
        except Exception:
            pass

    p = request.prompt.lower()
    parsed = dict(request.current_data)
    
    for mat in ["cotton", "plastic", "fly ash", "slag", "concrete", "foundry sand", "bagasse", "spent grains", "wood scrap", "textile"]:
        if mat in p:
            parsed["material"] = mat.title()
            break
            
    import re
    qty_match = re.search(r'(\d+[\d,.]*)\s*(kg|tons|tonnes|t|mt)?', p)
    if qty_match:
        try:
            val = float(qty_match.group(1).replace(",", ""))
            parsed["quantity"] = val
        except Exception:
            pass

    if "dry" in p: parsed["condition"] = "dry"
    elif "wet" in p: parsed["condition"] = "wet"
    elif "mixed" in p: parsed["condition"] = "mixed"

    if "powder" in p: parsed["form"] = "powder"
    elif "scraps" in p or "scrap" in p: parsed["form"] = "scraps"
    elif "slurry" in p: parsed["form"] = "slurry"
    elif "solid" in p: parsed["form"] = "solid"

    for loc in ["mumbai", "pune", "delhi", "surat", "ahmedabad", "indore", "bhopal", "chennai", "bengaluru", "kolkata", "nagpur"]:
        if loc in p:
            parsed["location"] = loc.title()
            break

    price_match = re.search(r'(?:₹|rs\.?|inr)\s*(\d+[\d,.]*)', p) or re.search(r'(\d+[\d,.]*)\s*(?:₹|rs|inr|per kg|/kg)', p)
    if price_match:
        try:
            parsed["expected_price"] = float(price_match.group(1).replace(",", ""))
        except Exception:
            pass

    return {
        "parsed_data": parsed,
        "message": "Extracted available waste parameters. Review and confirm details below."
    }

@router.post("/search/semantic")
def semantic_search(request: SearchRequest):
    cursor = database.listings.find()
    listings = [serialize_doc(doc) for doc in cursor]
    if not listings or not request.query.strip():
        return listings

    q = request.query.lower().strip()
    return [
        l for l in listings
        if q in l.get('title', '').lower()
        or q in l.get('material', '').lower()
        or q in l.get('category', '').lower()
        or q in l.get('location', '').lower()
    ]

@router.post("/messages")
def send_message(message: ContactMessage):
    result = database.messages.insert_one(message.dict())
    return {"id": str(result.inserted_id), "message": "Message sent successfully"}

@router.get("/nearby-buyers/{user_id}")
def get_nearby_buyers(user_id: str):
    from bson.errors import InvalidId
    try:
        user = database.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = database.users.find_one({"_id": user_id})
    
    location = user.get("location", "Mumbai, India") if user else "Mumbai, India"
    buyers = []
    
    cursor = database.users.find({"role": {"$in": ["consumer", "buyer", "recycler"]}})
    for consumer in cursor:
        if str(consumer.get("_id")) == user_id:
            continue
        buyers.append({
            "id": str(consumer.get("_id")),
            "name": consumer.get("company_name", "Registered Circular Partner"),
            "location": consumer.get("location", "Nearby Industrial Area"),
            "distance": "45 km",
            "compatibility": "88%",
        })
        
    if not buyers:
        buyers = [
            {"id": "buyer_01", "name": "UltraTech Circular Raw Materials", "location": "Pune, Maharashtra", "distance": "116 km", "compatibility": "96%"},
            {"id": "buyer_02", "name": "EcoBricks Infrastructure Corp", "location": "Indore, Madhya Pradesh", "distance": "85 km", "compatibility": "92%"},
            {"id": "buyer_03", "name": "ThermaShield Acoustic Fiber Ltd", "location": "Surat, Gujarat", "distance": "140 km", "compatibility": "90%"}
        ]
        
    return {"user_location": location, "buyers": buyers}

# ─────────────────────────────────────────────────────────────
# W2RKG Industrial Symbiosis Intelligence APIs (Problem Statement 1)
# ─────────────────────────────────────────────────────────────

@router.post("/api/symbiosis/material-analysis")
@router.post("/symbiosis/material-analysis")
def analyze_material_endpoint(request: MaterialAnalysisRequest):
    """
    AI Material & Property Analysis Endpoint.
    Extracts structured properties, physical/chemical states, and potential resource uses
    while explicitly distinguishing provided vs inferred properties.
    """
    service = SymbiosisService.get_instance(db=database)
    return service.analyze_material_text(
        prompt=request.description,
        quantity=request.quantity,
        unit=request.quantity_unit or "kg",
        frequency=request.frequency,
        location=request.location
    )

@router.post("/api/symbiosis/analyze")
@router.post("/symbiosis/analyze")
def analyze_industrial_symbiosis(request: SymbiosisAnalyzeRequest):
    """
    Unified Industrial Symbiosis Discovery API.
    Executes full pipeline: AI Material Analysis → W2RKG Graph Traversal →
    9-Factor Opportunity Assessment → Environmental Impact → Transparent Reasoning.
    """
    service = SymbiosisService.get_instance(db=database)

    material = request.material
    raw_desc = request.raw_description
    quantity = request.quantity or 5000.0
    location = request.location or "Mumbai"
    form = request.form or "solid"
    condition = request.condition or "dry"
    category = request.category or "Other"
    producer_name = request.producer_name or "Industrial Producer"
    producer_industry = request.producer_industry or "Manufacturing"

    listing_id = request.listing_id or request.wasteId
    if listing_id:
        try:
            listing = database.listings.find_one({"_id": ObjectId(listing_id)})
        except Exception:
            listing = database.listings.find_one({"_id": listing_id})

        if listing:
            material = listing.get("material", material)
            quantity = float(listing.get("quantity", quantity))
            location = listing.get("location", location)
            form = listing.get("form", form)
            condition = listing.get("condition", condition)
            category = listing.get("category", category)
            producer_name = listing.get("title", producer_name)

    if request.industryId:
        try:
            ind_user = database.users.find_one({"_id": ObjectId(request.industryId)})
        except Exception:
            ind_user = database.users.find_one({"_id": request.industryId})
        if ind_user:
            producer_name = ind_user.get("company_name", producer_name)
            producer_industry = ind_user.get("industry", producer_industry)
            if not location:
                location = ind_user.get("location", "India")

    if not material and raw_desc:
        # Run material analyzer on raw description
        mat_struct = service.analyze_material_text(raw_desc, quantity=quantity, location=location)
        material = mat_struct["material_name"]
        form = mat_struct.get("physical_properties", {}).get("form", {}).get("value", form)
        condition = mat_struct.get("physical_properties", {}).get("condition", {}).get("value", condition)
        quantity = mat_struct.get("quantity", quantity)

    if not material:
        raise HTTPException(
            status_code=400,
            detail="Material name or raw description is required for industrial symbiosis analysis."
        )

    try:
        result = service.analyze_symbiosis(
            material=material,
            quantity=quantity,
            location=location,
            form=form,
            condition=condition,
            category=category,
            producer_name=producer_name,
            producer_industry=producer_industry,
            top_k=request.top_k or 5,
            raw_description=raw_desc,
            unit=request.quantity_unit or "kg"
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[Symbiosis API Error] {e}")
        raise HTTPException(status_code=500, detail=f"Symbiosis intelligence analysis error: {str(e)}")

@router.post("/api/symbiosis/notify")
@router.post("/symbiosis/notify")
def send_twilio_notification(request: TwilioNotificationRequest):
    """
    Dispatches direct Twilio notification (SMS, WhatsApp, or Voice Call) to an industrial partner.
    """
    service = SymbiosisService.get_instance(db=database)
    try:
        result = service.dispatch_partner_notification(
            channel=request.channel,
            recipient_phone=request.recipient_phone,
            partner_name=request.partner_name,
            producer_name=request.producer_name,
            waste_material=request.waste_material,
            quantity=request.quantity,
            notification_type=request.notification_type,
            custom_message=request.custom_message
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twilio communication dispatch failed: {str(e)}")

@router.get("/api/symbiosis/graph")
@router.get("/symbiosis/graph")
def get_symbiosis_graph(waste: str = Query(..., description="Waste material name")):
    """
    Returns NetworkX subgraph elements for interactive visualization of W2RKG pathways.
    """
    service = SymbiosisService.get_instance(db=database)
    return service.query_graph_subgraph(waste)

@router.get("/api/symbiosis/industries")
@router.get("/symbiosis/industries")
def get_symbiosis_industries():
    """
    Returns list of registered and benchmark industrial sectors for symbiosis planning.
    """
    service = SymbiosisService.get_instance(db=database)
    return service.get_benchmark_industries()

@router.post("/api/symbiosis/quick-match")
@router.post("/symbiosis/quick-match")
def quick_match_wastes(request: QuickMatchRequest):
    """
    Fast autocompletion / suggestions for waste materials and transformed resources.
    """
    service = SymbiosisService.get_instance(db=database)
    matches = service.kg.find_matching_wastes(request.query, threshold=request.threshold or 0.45, top_k=request.top_k or 6)
    possible_uses = service.matcher.discover_possible_uses(request.query)[:4] if matches else []
    return {
        "matched_wastes": [{"name": m[0], "confidence": round(m[1], 2)} for m in matches],
        "top_transformations": possible_uses
    }

@router.post("/api/symbiosis/propose")
@router.post("/symbiosis/propose")
def send_symbiosis_proposal(proposal: SymbiosisProposalRequest):
    """
    Records an industrial symbiosis exchange proposal and optionally dispatches Twilio SMS/WhatsApp alerts.
    """
    result = database.symbiosis_proposals.insert_one(proposal.dict())
    
    # Also log in messages collection
    database.messages.insert_one({
        "listing_id": f"symbiosis_{proposal.partner_id}",
        "buyer_name": proposal.partner_name,
        "sender_email": proposal.producer_email,
        "message": f"[Industrial Symbiosis Proposal] From {proposal.producer_name}: {proposal.message} ({proposal.quantity} {proposal.quantity_unit} of {proposal.waste_material})"
    })

    # Trigger Twilio SMS / WhatsApp if requested
    service = SymbiosisService.get_instance(db=database)
    comm_receipts = []
    if proposal.partner_phone:
        if proposal.dispatch_sms:
            receipt = service.dispatch_partner_notification(
                channel="sms",
                recipient_phone=proposal.partner_phone,
                partner_name=proposal.partner_name,
                producer_name=proposal.producer_name,
                waste_material=proposal.waste_material,
                quantity=proposal.quantity,
                notification_type="connection_request",
                custom_message=f"WasteX Match: {proposal.producer_name} has proposed an industrial symbiosis exchange for {proposal.quantity:,.0f} {proposal.quantity_unit} of {proposal.waste_material}. Check WasteX dashboard."
            )
            comm_receipts.append(receipt)
        if proposal.dispatch_whatsapp:
            receipt = service.dispatch_partner_notification(
                channel="whatsapp",
                recipient_phone=proposal.partner_phone,
                partner_name=proposal.partner_name,
                producer_name=proposal.producer_name,
                waste_material=proposal.waste_material,
                quantity=proposal.quantity,
                notification_type="connection_request",
                custom_message=f"{proposal.producer_name} sent you a circular partnership proposal for {proposal.quantity:,.0f} {proposal.quantity_unit} of {proposal.waste_material} via {proposal.proposed_process or 'valorization'}."
            )
            comm_receipts.append(receipt)

    return {
        "id": str(result.inserted_id),
        "message": f"Industrial symbiosis proposal dispatched to {proposal.partner_name} successfully!",
        "communication_receipts": comm_receipts
    }
