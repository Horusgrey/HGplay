"""Lock the outbox guarantees: no send without approval, never to suppressed, cap held."""
import pytest

from outbox import Outbox, DryRunSender
from outreach_generator import SuppressedProspectError


class CountingSender:
    """Test sender that records every send so we can assert what actually went out."""
    name = "counting"

    def __init__(self):
        self.sent = []

    def send(self, to, channel, subject, body):
        self.sent.append((to, channel))
        return "recorded"


def _prospect(crm, pid="P1", email="p@example.com"):
    crm.add_prospect({"property_id": pid, "name": "Out Test", "amount": 40000,
                      "holder": "EXAMPLE BANK", "email": email})


def test_queue_draft_refuses_suppressed(crm):
    _prospect(crm)
    crm.suppress("P1")
    ob = Outbox(crm)
    with pytest.raises(SuppressedProspectError):
        ob.queue_draft("P1", "email")


def test_draft_does_not_send_without_approval(crm):
    _prospect(crm)
    ob = Outbox(crm)
    ob.queue_draft("P1", "email")
    sender = CountingSender()
    result = ob.send_approved(sender=sender)
    assert result["sent"] == 0
    assert sender.sent == []          # nothing left the building


def test_approve_then_send(crm):
    _prospect(crm)
    ob = Outbox(crm)
    i = ob.queue_draft("P1", "email")
    assert ob.approve(i, "zack") is True
    sender = CountingSender()
    result = ob.send_approved(sender=sender)
    assert result["sent"] == 1
    assert sender.sent == [("p@example.com", "email")]


def test_suppressed_after_approval_is_held_not_sent(crm):
    _prospect(crm)
    ob = Outbox(crm)
    i = ob.queue_draft("P1", "email")
    ob.approve(i, "zack")
    crm.suppress("P1", "changed mind")     # opt-out AFTER approval
    sender = CountingSender()
    result = ob.send_approved(sender=sender)
    assert result["sent"] == 0 and result["held"] == 1
    assert sender.sent == []
    assert ob.list_outbox()[0]["status"] == "HELD"


def test_daily_cap_enforced(crm):
    for n in range(3):
        _prospect(crm, pid=f"P{n}", email=f"p{n}@example.com")
    ob = Outbox(crm)
    for n in range(3):
        i = ob.queue_draft(f"P{n}", "email")
        ob.approve(i, "zack")
    result = ob.send_approved(sender=CountingSender(), daily_cap=2)
    assert result["sent"] == 2 and result["capped"] == 1


def test_dry_run_sender_sends_nothing_real(crm):
    _prospect(crm)
    ob = Outbox(crm)
    i = ob.queue_draft("P1", "email")
    ob.approve(i, "zack")
    result = ob.send_approved(sender=DryRunSender())
    assert result["sent"] == 1
    row = ob.list_outbox()[0]
    assert "DRY-RUN" in row["send_result"]
