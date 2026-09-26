import os
import re
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class TwilioCommunicationService:
    """
    Multi-Channel Twilio Communication Service for Industrial Symbiosis.
    Supports SMS, WhatsApp, and Voice Calling with automated fallback and simulation logging.
    """
    _instance: Optional["TwilioCommunicationService"] = None

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = os.getenv("TWILIO_PHONE_NUMBER", "+15005550006")
        self.from_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER", "+14155238886")
        
        self.is_live_ready = bool(
            self.account_sid and 
            self.auth_token and 
            self.account_sid != "YOUR_TWILIO_ACCOUNT_SID" and
            self.auth_token != "YOUR_TWILIO_AUTH_TOKEN"
        )
        self._twilio_client = None

        if self.is_live_ready:
            try:
                from twilio.rest import Client
                self._twilio_client = Client(self.account_sid, self.auth_token)
                print("[Twilio] Initialized live Twilio REST client.")
            except Exception as e:
                print(f"[Twilio Warning] Could not initialize Twilio client ({e}). Operating in simulation mode.")
                self.is_live_ready = False

    @classmethod
    def get_instance(cls) -> "TwilioCommunicationService":
        if cls._instance is None:
            cls._instance = TwilioCommunicationService()
        return cls._instance

    def _normalize_phone(self, phone: str) -> str:
        """
        Sanitizes and formats phone numbers to E.164 standard.
        Validates that phone contains a valid number of digits.
        Raises ValueError on invalid or malformed numbers.
        """
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone number cannot be empty.")
        
        trimmed = phone.strip()
        if not trimmed or trimmed == "+":
            raise ValueError("Invalid phone number format.")
        
        # Check that it contains at least some digits
        digits_only = re.sub(r'\D', '', trimmed)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValueError(f"Invalid phone number length ({len(digits_only)} digits). Must be between 7 and 15 digits.")
        
        clean = "".join([c for c in trimmed if c.isdigit() or c == "+"])
        if not clean.startswith("+"):
            # Default to India country code (+91) if 10 digits
            if len(digits_only) == 10:
                clean = "+91" + digits_only
            else:
                clean = "+" + digits_only
        else:
            clean = "+" + digits_only

        # Strict E.164 pattern validation: + followed by 7 to 15 digits
        if not re.match(r'^\+[1-9]\d{6,14}$', clean):
            raise ValueError(f"Malformed E.164 phone number: {clean}")

        return clean

    def send_sms(
        self,
        to_phone: str,
        message_body: str,
        notification_type: str = "partner_discovered"
    ) -> Dict[str, Any]:
        """
        Sends SMS notification via Twilio.
        """
        target_phone = self._normalize_phone(to_phone)
        timestamp = datetime.now(timezone.utc).isoformat()

        if self.is_live_ready and self._twilio_client:
            try:
                message = self._twilio_client.messages.create(
                    body=message_body,
                    from_=self.from_phone,
                    to=target_phone
                )
                return {
                    "success": True,
                    "channel": "SMS",
                    "sid": message.sid,
                    "status": message.status,
                    "to": target_phone,
                    "from": self.from_phone,
                    "body": message_body,
                    "notification_type": notification_type,
                    "timestamp": timestamp,
                    "mode": "live"
                }
            except Exception as e:
                print(f"[Twilio Error] SMS dispatch failed: {e}")

        # Simulated delivery for development / test environments
        simulated_sid = f"SM_sim_{uuid.uuid4().hex[:16]}"
        return {
            "success": True,
            "channel": "SMS",
            "sid": simulated_sid,
            "status": "delivered_simulation",
            "to": target_phone,
            "from": self.from_phone,
            "body": message_body,
            "notification_type": notification_type,
            "timestamp": timestamp,
            "mode": "simulation",
            "note": "SMS simulated successfully. To enable live SMS delivery, provide valid TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
        }

    def send_whatsapp(
        self,
        to_phone: str,
        message_body: str,
        notification_type: str = "connection_request"
    ) -> Dict[str, Any]:
        """
        Sends WhatsApp message using Twilio WhatsApp API.
        """
        target_phone = self._normalize_phone(to_phone)
        whatsapp_to = f"whatsapp:{target_phone}"
        whatsapp_from = f"whatsapp:{self.from_whatsapp.replace('whatsapp:', '')}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Format with industrial circularity branding
        formatted_body = f"🌿 *WasteX Industrial Symbiosis Alert*\n\n{message_body}\n\n_Reply to this message to coordinate feedstock specifications._"

        if self.is_live_ready and self._twilio_client:
            try:
                message = self._twilio_client.messages.create(
                    body=formatted_body,
                    from_=whatsapp_from,
                    to=whatsapp_to
                )
                return {
                    "success": True,
                    "channel": "WhatsApp",
                    "sid": message.sid,
                    "status": message.status,
                    "to": whatsapp_to,
                    "from": whatsapp_from,
                    "body": formatted_body,
                    "notification_type": notification_type,
                    "timestamp": timestamp,
                    "mode": "live"
                }
            except Exception as e:
                print(f"[Twilio Error] WhatsApp dispatch failed: {e}")

        simulated_sid = f"WA_sim_{uuid.uuid4().hex[:16]}"
        return {
            "success": True,
            "channel": "WhatsApp",
            "sid": simulated_sid,
            "status": "delivered_simulation",
            "to": whatsapp_to,
            "from": whatsapp_from,
            "body": formatted_body,
            "notification_type": notification_type,
            "timestamp": timestamp,
            "mode": "simulation",
            "note": "WhatsApp message simulated successfully. Configure TWILIO_WHATSAPP_NUMBER for live WhatsApp dispatch."
        }

    def make_voice_call(
        self,
        to_phone: str,
        spoken_message: str,
        notification_type: str = "exchange_alert"
    ) -> Dict[str, Any]:
        """
        Initiates an automated voice call with synthesized TwiML voice alert.
        """
        target_phone = self._normalize_phone(to_phone)
        timestamp = datetime.now(timezone.utc).isoformat()

        twiml_payload = f"""<Response>
            <Say voice="Polly.Aditi" language="en-IN">
                Hello. This is an automated notification from WasteX Industrial Symbiosis Platform.
                {spoken_message}
                Please check your WasteX dashboard to review and accept the symbiosis proposal. Thank you.
            </Say>
        </Response>"""

        if self.is_live_ready and self._twilio_client:
            try:
                call = self._twilio_client.calls.create(
                    twiml=twiml_payload,
                    to=target_phone,
                    from_=self.from_phone
                )
                return {
                    "success": True,
                    "channel": "Voice Call",
                    "sid": call.sid,
                    "status": call.status,
                    "to": target_phone,
                    "from": self.from_phone,
                    "spoken_script": spoken_message,
                    "notification_type": notification_type,
                    "timestamp": timestamp,
                    "mode": "live"
                }
            except Exception as e:
                print(f"[Twilio Error] Voice call initiation failed: {e}")

        simulated_sid = f"CA_sim_{uuid.uuid4().hex[:16]}"
        return {
            "success": True,
            "channel": "Voice Call",
            "sid": simulated_sid,
            "status": "initiated_simulation",
            "to": target_phone,
            "from": self.from_phone,
            "spoken_script": spoken_message,
            "twiml": twiml_payload,
            "notification_type": notification_type,
            "timestamp": timestamp,
            "mode": "simulation",
            "note": "Automated voice call simulated with Amazon Polly TTS Indian English voice."
        }
