"""Lock the follow-up cadence: exactly one nudge, then silence.

The second letter tells the recipient it is the last one they'll get. These
tests are what make that sentence true.
"""
from datetime import datetime, timedelta

import followup_engine as fu


def mailed(days_ago, **kw):
    p = {"property_id": "P1", "name": "Ada Fauxname", "amount": 5000, "stage": "CONTACTED",
         "mailed_on": (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
         "mailed_count": 1}
    p.update(kw)
    return p


def test_not_due_before_the_window():
    assert fu.followup_due(mailed(20)) is False


def test_due_on_the_window():
    assert fu.followup_due(mailed(fu.FOLLOWUP_DAYS)) is True
    assert fu.followup_due(mailed(40)) is True


def test_second_letter_ends_the_sequence():
    assert fu.followup_due(mailed(60, mailed_count=2)) is False


def test_a_reply_stops_the_chaser():
    # Any stage past CONTACTED means they answered. Never chase an answered letter.
    for stage in ("RESPONDED", "AGREEMENT_SENT", "SIGNED", "PAID", "CLOSED"):
        assert fu.followup_due(mailed(40, stage=stage)) is False, stage


def test_suppressed_is_never_followed_up():
    assert fu.followup_due(mailed(90, suppression_status="SUPPRESSED")) is False


def test_never_mailed_is_not_due():
    assert fu.followup_due({"stage": "CONTACTED", "mailed_count": 0}) is False


def test_unreadable_date_is_not_due():
    assert fu.followup_due(mailed(30, mailed_on="last spring")) is False


def test_queue_puts_the_longest_silence_first():
    a, b, c = mailed(22), mailed(60), mailed(35)
    a["property_id"], b["property_id"], c["property_id"] = "a", "b", "c"
    assert [p["property_id"] for p in fu.followups_due([a, b, c])] == ["b", "c", "a"]


def test_record_letter_sets_the_clock_and_advances_the_stage():
    p = fu.record_letter({"property_id": "X", "stage": "ENRICHED"}, "FIRST", on="2026-01-01")
    assert p["mailed_on"] == "2026-01-01" and p["mailed_count"] == 1
    assert p["stage"] == "CONTACTED"


def test_recording_a_first_letter_twice_keeps_the_original_date():
    # Reprinting a letter is not mailing a second one; the clock must not reset.
    p = fu.record_letter({"property_id": "X", "stage": "ENRICHED"}, "FIRST", on="2026-01-01")
    fu.record_letter(p, "FIRST", on="2026-03-01")
    assert p["mailed_on"] == "2026-01-01" and p["mailed_count"] == 1


def test_followup_increments_and_closes_the_sequence():
    p = fu.record_letter({"property_id": "X", "stage": "ENRICHED"}, "FIRST", on="2026-01-01")
    fu.record_letter(p, "FOLLOWUP", on="2026-01-22")
    assert p["mailed_count"] == fu.MAX_LETTERS and p["followup_on"] == "2026-01-22"
    assert fu.followup_due(p) is False


def test_max_letters_is_two():
    # If this ever rises, the letter's "this is the last letter I'll send" lies.
    assert fu.MAX_LETTERS == 2
