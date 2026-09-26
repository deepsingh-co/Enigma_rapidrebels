import pytest

from services.communication.twilio_service import TwilioCommunicationService


TWILIO_ENV_VARS = [
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_PHONE_NUMBER",
    "TWILIO_WHATSAPP_NUMBER",
    "TWILIO_SMS_TEMPLATE",
    "TWILIO_VOICE_URL",
]


@pytest.fixture(autouse=True)
def isolate_twilio(monkeypatch):
    """
    Force every test into deterministic simulation mode with no network access.

    Without this, a developer's real credentials in backend/.env leak into the
    suite: tests call the live Twilio API (sending real SMS/calls) and assert on
    results that depend on account tier, verified recipients, and account credit.
    Live-mode behaviour is covered explicitly in test_twilio_service.py using an
    injected fake client.
    """
    for var in TWILIO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    # Reset the cached singleton so it is rebuilt from the cleared environment.
    TwilioCommunicationService._instance = None
    yield
    TwilioCommunicationService._instance = None
