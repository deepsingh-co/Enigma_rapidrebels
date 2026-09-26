import pytest
from services.communication.twilio_service import TwilioCommunicationService


@pytest.fixture
def simulated_service(monkeypatch):
    """Service with no credentials -> deterministic simulation mode, no network."""
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    return TwilioCommunicationService()


class _FakeMessage:
    sid = "SM_fake1234567890"
    status = "queued"


class _FakeCall:
    sid = "CA_fake1234567890"
    status = "queued"


class _FakeClient:
    """Stands in for twilio.rest.Client so tests never touch the network."""

    def __init__(self, fail_with=None):
        self.messages = self
        self.calls = self
        self._fail_with = fail_with
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self._fail_with is not None:
            raise self._fail_with
        return _FakeCall() if "twiml" in kwargs or "url" in kwargs else _FakeMessage()


def _live_service(monkeypatch, client):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACtest00000000000000000000000000")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test_auth_token")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+17372508034")
    svc = TwilioCommunicationService()
    svc._twilio_client = client
    svc.is_live_ready = True
    return svc


# ── Simulation mode (no credentials) ────────────────────────────────────────

def test_twilio_sms_dispatch(simulated_service):
    res = simulated_service.send_sms(
        to_phone="+919820011223",
        message_body="WasteX Alert: Potential partner discovered.",
        notification_type="partner_discovered",
    )
    assert res["success"] is True
    assert res["channel"] == "SMS"
    assert res["mode"] == "simulation"
    assert res["sid"].startswith("SM_sim_")
    assert res["to"] == "+919820011223"


def test_twilio_whatsapp_dispatch(simulated_service):
    res = simulated_service.send_whatsapp(
        to_phone="+919820011223",
        message_body="WasteX Alert: New circular exchange request.",
        notification_type="connection_request",
    )
    assert res["success"] is True
    assert res["channel"] == "WhatsApp"
    assert res["mode"] == "simulation"
    assert "whatsapp:+919820011223" in res["to"]


def test_twilio_voice_call_dispatch(simulated_service):
    res = simulated_service.make_voice_call(
        to_phone="+919820011223",
        spoken_message="A new industrial partner has accepted your proposal.",
        notification_type="opportunity_accepted",
    )
    assert res["success"] is True
    assert res["channel"] == "Voice Call"
    assert res["mode"] == "simulation"
    assert res["sid"].startswith("CA_sim_")


# ── Live mode: real Twilio receipt is surfaced ──────────────────────────────

def test_live_sms_returns_real_sid(monkeypatch):
    client = _FakeClient()
    svc = _live_service(monkeypatch, client)
    res = svc.send_sms(to_phone="+919820011223", message_body="Real alert text")
    assert res["success"] is True
    assert res["mode"] == "live"
    assert res["sid"] == "SM_fake1234567890"
    assert res["status"] == "queued"
    # Without a template configured the real message text is sent.
    assert client.last_kwargs["body"] == "Real alert text"


def test_trial_template_overrides_body(monkeypatch):
    """Trial accounts reject free text, so a template name must be sent instead."""
    client = _FakeClient()
    svc = _live_service(monkeypatch, client)
    svc.sms_template = "sms_appointment_reminders"
    res = svc.send_sms(to_phone="+919820011223", message_body="Real alert text")
    assert res["success"] is True
    assert res["used_template"] is True
    assert client.last_kwargs["body"] == "sms_appointment_reminders"


def test_live_voice_uses_hosted_url_when_configured(monkeypatch):
    """Trial accounts reject inline twiml=; a hosted TwiML URL is used instead."""
    client = _FakeClient()
    svc = _live_service(monkeypatch, client)
    svc.voice_url = "https://example.com/twiml"
    res = svc.make_voice_call(to_phone="+919820011223", spoken_message="Alert")
    assert res["success"] is True
    assert res["used_hosted_twiml"] is True
    assert client.last_kwargs["url"] == "https://example.com/twiml"
    assert "twiml" not in client.last_kwargs


def test_live_voice_uses_inline_twiml_by_default(monkeypatch):
    client = _FakeClient()
    svc = _live_service(monkeypatch, client)
    res = svc.make_voice_call(to_phone="+919820011223", spoken_message="Alert")
    assert res["success"] is True
    assert "twiml" in client.last_kwargs
    assert "<Say" in client.last_kwargs["twiml"]


# ── Live failures must NOT be reported as success ───────────────────────────

def test_live_sms_failure_is_reported_honestly(monkeypatch):
    """A rejected live send must not degrade into a fake simulation receipt."""
    client = _FakeClient(fail_with=RuntimeError("Invalid template name."))
    svc = _live_service(monkeypatch, client)
    res = svc.send_sms(to_phone="+919820011223", message_body="Real alert text")
    assert res["success"] is False
    assert res["status"] == "failed"
    assert res["mode"] == "live"
    assert res["sid"] is None
    assert "Invalid template name." in res["error"]
    assert "delivered_simulation" not in res["status"]


def test_live_voice_failure_is_reported_honestly(monkeypatch):
    client = _FakeClient(fail_with=RuntimeError("trial accounts have limited parameter access"))
    svc = _live_service(monkeypatch, client)
    res = svc.make_voice_call(to_phone="+919820011223", spoken_message="Alert")
    assert res["success"] is False
    assert res["mode"] == "live"
    assert "limited parameter access" in res["error"]


# ── Phone normalization / validation ────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("+918237041129", "+918237041129"),
    ("+1 737 250 8034", "+17372508034"),
    # 10-digit national numbers are assumed to be Indian (+91).
    ("9823704112", "+919823704112"),
    # 11 digits already carries a country code, so +91 is NOT prepended.
    ("98237041129", "+98237041129"),
])
def test_normalize_phone(raw, expected):
    svc = TwilioCommunicationService()
    assert svc._normalize_phone(raw) == expected


@pytest.mark.parametrize("bad", ["", "+", "12345", "not-a-number!!"])
def test_normalize_phone_rejects_invalid(bad):
    svc = TwilioCommunicationService()
    with pytest.raises(ValueError):
        svc._normalize_phone(bad)
