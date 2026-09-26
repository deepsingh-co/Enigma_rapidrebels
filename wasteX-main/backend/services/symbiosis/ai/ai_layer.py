import os
import json
import httpx
from typing import Dict, Any, Optional, List


class SymbiosisAILayer:
    """
    AI Abstraction Layer for Industrial Symbiosis Intelligence.
    Supports Hugging Face, OpenAI-compatible APIs, and local W2RKG graph-based intelligence.
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "huggingface").lower()
        self.hf_token = os.getenv("HF_TOKEN")
        self.hf_model = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 400) -> Optional[str]:
        """Calls the configured LLM provider or returns None if unavailable."""
        if self.provider == "openai" and self.openai_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.openai_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": max_tokens
                }
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(f"{self.openai_base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"[AILayer Warning] OpenAI provider error: {e}")

        # Default Hugging Face provider
        if self.hf_token and self.hf_token != "YOUR_HF_TOKEN_HERE":
            try:
                from huggingface_hub import InferenceClient
                client = InferenceClient(api_key=self.hf_token)
                res = client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.hf_model,
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                if res and res.choices and len(res.choices) > 0:
                    return res.choices[0].message.content.strip()
            except Exception as e:
                print(f"[AILayer Warning] HuggingFace provider error: {e}")

        return None

    def understand_waste_stream(self, description: str) -> Dict[str, Any]:
        """
        Extracts structured waste stream metadata, properties, and classification.
        """
        system_prompt = """
        You are an industrial waste specialist. Extract structured properties from the user's description.
        Return ONLY valid JSON matching this schema:
        {
          "material": "string",
          "category": "string (Textile|Mineral|Plastic|Chemical|Biomass|Metal|Other)",
          "form": "string (powder|slurry|solid|scraps|liquid|granular)",
          "condition": "string (dry|wet|mixed|pure|treated)",
          "estimated_quantity": number or null,
          "potential_applications": ["string"]
        }
        """
        
        response_text = self._call_llm(system_prompt, description, max_tokens=300)
        if response_text:
            try:
                cleaned = response_text
                if "```json" in cleaned:
                    cleaned = cleaned.split("```json")[1].split("```")[0]
                elif "```" in cleaned:
                    cleaned = cleaned.split("```")[1].split("```")[0]
                return json.loads(cleaned.strip())
            except Exception:
                pass

        # Robust local fallback classification
        desc_lower = description.lower()
        category = "Other"
        form = "solid"
        condition = "dry"

        if any(w in desc_lower for w in ["ash", "slag", "concrete", "sand", "brick", "stone", "dust"]):
            category = "Mineral"
            form = "powder" if "ash" in desc_lower or "dust" in desc_lower else "solid"
        elif any(w in desc_lower for w in ["cotton", "fabric", "textile", "yarn", "fiber"]):
            category = "Textile"
            form = "scraps"
        elif any(w in desc_lower for w in ["plastic", "polymer", "polyethylene", "pet", "pp", "pvc"]):
            category = "Plastic"
            form = "scraps"
        elif any(w in desc_lower for w in ["bio", "biomass", "bagasse", "wood", "grain", "husk", "organic"]):
            category = "Biomass"
        elif any(w in desc_lower for w in ["acid", "solvent", "sludge", "chemical", "brine"]):
            category = "Chemical"
            form = "liquid" if "sludge" not in desc_lower else "slurry"

        if "wet" in desc_lower or "slurry" in desc_lower or "moist" in desc_lower:
            condition = "wet"
        elif "mixed" in desc_lower or "contaminated" in desc_lower:
            condition = "mixed"

        # Extract material keyword
        words = [w for w in desc_lower.replace(",", " ").split() if len(w) > 2 and w not in ["have", "with", "from", "tons", "month", "kg"]]
        material_guess = " ".join(words[:2]).title() if words else "Industrial Byproduct"

        return {
            "material": material_guess,
            "category": category,
            "form": form,
            "condition": condition,
            "estimated_quantity": None,
            "potential_applications": ["Raw material replacement", "Industrial circularity"]
        }

    def generate_strategic_insights(
        self,
        waste_data: Dict[str, Any],
        top_partner: Optional[Dict[str, Any]],
        possible_uses: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generates executive summary and next recommended actions for industrial circularity.
        """
        material = waste_data.get("material", "Industrial Waste")
        qty = waste_data.get("quantity", 0)

        if not top_partner:
            return {
                "summary": f"Identified {len(possible_uses)} potential technical transformation pathways for {material} across regional industries.",
                "recommended_action": "Expand search radius or list waste stream publicly on the WasteX marketplace for broader buyer discovery."
            }

        p_name = top_partner["industry"]["company_name"]
        p_type = top_partner["industry"]["industry_type"]
        score = top_partner["matchScore"]
        pathway = top_partner.get("transformationPathway", {})
        proc = pathway.get("transforming_process", "Valorization")
        res = pathway.get("transformed_resource", "Secondary Raw Material")
        co2_saved = top_partner.get("environmentalImpact", {}).get("co2_saved_tonnes", 0.0)

        # Build prompt for LLM summary if key is present
        system_prompt = "You are a chief industrial sustainability advisor. Write a 2-sentence executive briefing summarizing the symbiosis match and key action step."
        user_prompt = f"Producer has {qty} kg {material}. Top matched partner is {p_name} ({p_type}) with {score}% compatibility score. The waste transforms into {res} via {proc}. Avoids ~{co2_saved} tonnes CO2."

        llm_response = self._call_llm(system_prompt, user_prompt, max_tokens=150)
        if llm_response and len(llm_response) > 20:
            return {
                "summary": llm_response,
                "recommended_action": f"Initiate a bilateral bilateral exchange proposal with {p_name} to verify sample specifications."
            }

        # Deterministic executive summary
        summary = (
            f"Discovered a high-compatibility ({score}%) symbiosis opportunity with {p_name} ({p_type}). "
            f"Your {material} can directly substitute primary {res} through {proc[:80]}, "
            f"avoiding ~{co2_saved:.2f} tonnes of net GHG emissions monthly."
        )

        recommended_action = (
            f"Submit a direct connection request to {p_name}'s procurement team with your latest material batch assay "
            f"to establish a recurring feedstock agreement."
        )

        return {
            "summary": summary,
            "recommended_action": recommended_action
        }
