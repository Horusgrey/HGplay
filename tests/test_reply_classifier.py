"""Lock reply classification + the safe auto-actions it drives."""
import reply_classifier as rc


def test_stop_detected():
    assert rc.classify("Please STOP emailing me").category == "STOP"
    assert rc.classify("unsubscribe").category == "STOP"
    assert rc.classify("take me off your list").category == "STOP"


def test_wrong_person_detected():
    assert rc.classify("you have the wrong person").category == "WRONG_PERSON"
    assert rc.classify("that's not me").category == "WRONG_PERSON"


def test_already_claimed_detected():
    assert rc.classify("I already claimed it myself").category == "ALREADY_CLAIMED"


def test_interested_detected():
    assert rc.classify("Yes, please send me the details").category == "INTERESTED"
    assert rc.classify("how do I start?").category in ("INTERESTED", "QUESTION")


def test_scam_question_detected():
    assert rc.classify("is this a scam?").category == "QUESTION"


def test_bounce_is_spam():
    assert rc.classify("Out of office until Monday").category == "SPAM"


def test_empty_and_vague_go_to_human():
    assert rc.classify("").category == "UNCLEAR"
    assert rc.classify("ok").category == "UNCLEAR"


def test_optout_precedence_over_interest():
    # A message that mentions interest AND opt-out must be treated as opt-out.
    assert rc.classify("yes but actually please remove me").category == "STOP"


def test_process_reply_autosuppresses_on_stop(crm):
    crm.add_prospect({"property_id": "R1", "name": "Stopper"})
    out = rc.process_reply(crm, "R1", "please unsubscribe me")
    assert out["action_taken"] == "suppressed"
    assert crm.get_prospect("R1")["suppression_status"] == "SUPPRESSED"


def test_process_reply_autosuppresses_wrong_person(crm):
    crm.add_prospect({"property_id": "R2", "name": "NotMe"})
    out = rc.process_reply(crm, "R2", "wrong person, don't know this")
    assert out["action_taken"] == "suppressed"


def test_process_reply_advances_interested(crm):
    crm.add_prospect({"property_id": "R3", "name": "Keen", "stage": "CONTACTED"})
    out = rc.process_reply(crm, "R3", "yes! help me claim it")
    assert out["action_taken"] == "advanced_to_responded"
    assert crm.get_prospect("R3")["stage"] == "RESPONDED"
    assert out["needs_human"] is True


def test_process_reply_question_advances_but_flags_human(crm):
    crm.add_prospect({"property_id": "R4", "name": "Asker", "stage": "CONTACTED"})
    out = rc.process_reply(crm, "R4", "is this a scam?")
    # A question IS a reply → RESPONDED, but a human must answer it (never auto-send).
    assert crm.get_prospect("R4")["stage"] == "RESPONDED"
    assert out["needs_human"] is True


def test_process_reply_spam_does_not_advance(crm):
    crm.add_prospect({"property_id": "R6", "name": "Bouncer", "stage": "CONTACTED"})
    rc.process_reply(crm, "R6", "Out of office until Monday")
    assert crm.get_prospect("R6")["stage"] == "CONTACTED"   # bounce never advances


def test_process_reply_does_not_resurrect_suppressed(crm):
    crm.add_prospect({"property_id": "R5", "name": "Gone"})
    crm.suppress("R5")
    rc.process_reply(crm, "R5", "yes send details")
    assert crm.get_prospect("R5")["stage"] == "SUPPRESSED"
