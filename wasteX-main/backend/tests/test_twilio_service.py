import pytest
from services.communication.twilio_service import TwilioCommunicationService


def test_twilio_sms_dispatch():
    service = TwilioCommunicationService.get_instance()
    res = service.send_sms(
        to_phone="+919820011223",
        message_body="WasteX Alert: Potential partner discovered.",
        notification_type="partner_discovered"
    )

    assert res["success"] is True
    assert res["channel"] == "SMS"
    assert "sid" in res
    assert res["to"] == "+919820011223"


def test_twilio_whatsapp_dispatch():
    service = TwilioCommunicationService.get_instance()
    res = service.send_whatsapp(
        to_phone="+919820011223",
        message_body="WasteX Alert: New circular exchange request.",
        notification_type="connection_request"
    )

    assert res["success"] is True
    assert res["channel"] == "WhatsApp"
    assert "whatsapp:+919820011223" in res["to"]


def test_twilio_voice_call_dispatch():
    service = TwilioCommunicationService.get_instance()
    res = service.make_voice_call(
        to_phone="+919820011223",
        spoken_message="A new industrial partner has accepted your proposal.",
        notification_type="opportunity_accepted"
    )

    assert res["success"] is True
    assert res["channel"] == "Voice Call"
    assert "sid" in res
