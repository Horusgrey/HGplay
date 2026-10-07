"""Lock the household graph — the 'money per conversation' engine.

These tests protect two things that are easy to break and expensive if broken:
  1. the grouping itself (nicknames, estates, unit numbers, businesses);
  2. the privacy boundary — relatives are operator research, never disclosure.
"""
import household


def P(pid, name, amount, addr="", city="", zip_="", ptype="", **kw):
    d = {"property_id": pid, "name": name, "amount": amount,
         "last_known_address": addr, "city": city, "zip": zip_, "property_type": ptype}
    d.update(kw)
    return d


HERSH = [
    P("H1", "Michael Hershberger", 84979.53, "2210 Sherman Ave, Madison, WI, 53704", "Madison", "53704"),
    P("H2", "Michael Hershberger", 6140.22, "2210 Sherman Ave, Madison, WI, 53704", "Madison", "53704"),
    P("H3", "Mike Hershberger", 3180.00, "2210 Sherman Ave Apt 3, Madison, WI, 53704", "Madison", "53704"),
]
KRAUSE = [
    P("K1", "Estate of David Krause", 270934.69, "455 Forest Ave, Fond Du Lac, WI, 54935",
      "Fond Du Lac", "54935", "Proceeds Due to Beneficiaries"),
    P("K2", "Linda Krause", 8425.10, "455 Forest Ave, Fond Du Lac, WI, 54935",
      "Fond Du Lac", "54935", "Insurance Refund", phone="(920) 555-0134"),
    P("K3", "Gregory Krause", 1290.45, "455 Forest Ave, Fond Du Lac, WI, 54935",
      "Fond Du Lac", "54935", "Wages"),
]


# ── keys ────────────────────────────────────────────────────────────────────
def test_nickname_folds_into_one_person():
    keys = {household.person_key(p) for p in HERSH}
    assert len(keys) == 1, f"Mike and Michael should be one person, got {keys}"


def test_unit_number_does_not_split_a_household():
    assert household.address_key(HERSH[0]) == household.address_key(HERSH[2])


def test_estate_wrapper_does_not_hide_the_surname():
    assert household._last_of(KRAUSE[0]) == "KRAUSE"
    assert household.household_key(KRAUSE[0]) == household.household_key(KRAUSE[1])


def test_different_surname_same_address_is_a_different_household():
    a = P("A", "Jane Doe", 100, "1 Elm St, Madison, WI, 53703", "Madison", "53703")
    b = P("B", "Bob Roe", 100, "1 Elm St, Madison, WI, 53703", "Madison", "53703")
    assert household.household_key(a) != household.household_key(b)


def test_businesses_are_never_grouped_as_a_household():
    banks = [P("B1", "US BANK NA", 5000, "1 Main St, Milwaukee, WI, 53202", "Milwaukee", "53202"),
             P("B2", "US BANK NA", 9000, "1 Main St, Milwaukee, WI, 53202", "Milwaukee", "53202")]
    g = household.build_graph(banks)
    assert g["persons"] == {} and g["houses"] == {}
    assert household.same_person_clusters(g) == []


def test_blank_address_falls_back_to_city_not_to_uniqueness():
    a = P("A", "Ann Fauxname", 500, "", "Beloit")
    b = P("B", "Ann Fauxname", 700, "", "Beloit")
    g = household.build_graph([a, b])
    assert len(household.same_person_clusters(g)) == 1


def test_unmapped_nickname_prefix_still_folds_into_one_person():
    # "Bart" is in no nickname table. Surname and address already match, so the
    # prefix is enough — a missed merge means mailing the same person twice.
    recs = [P("Q1", "Bartholomew Quibbleton", 9412.55, "88 Larkspur Ln, Waunakee, WI, 53597", "Waunakee", "53597"),
            P("Q2", "Bart Quibbleton", 760.25, "88 Larkspur Ln, Waunakee, WI, 53597", "Waunakee", "53597")]
    g = household.build_graph(recs)
    [c] = household.same_person_clusters(g)
    assert len(c.members) == 2
    assert household.leverage(recs[1], g).claims == 2


def test_bare_initial_folds_into_the_full_name():
    recs = [P("I1", "Michael Hershberger", 5000, "2210 Sherman Ave, Madison, WI, 53704", "Madison", "53704"),
            P("I2", "M Hershberger", 900, "2210 Sherman Ave, Madison, WI, 53704", "Madison", "53704")]
    g = household.build_graph(recs)
    assert len(household.same_person_clusters(g)) == 1


def test_two_different_relatives_are_not_merged_into_one_person():
    # Same surname, same house, genuinely different people — must stay separate
    # or we'd disclose one person's money to another in a combined letter.
    g = household.build_graph(KRAUSE[1:])
    assert household.same_person_clusters(g) == []
    [hh] = household.households(g)
    assert len(hh.people) == 2


def test_merge_is_order_independent():
    recs = [P("Q1", "Bartholomew Quibbleton", 100, "88 Larkspur Ln, Waunakee, WI, 53597", "Waunakee", "53597"),
            P("Q2", "Bart Quibbleton", 200, "88 Larkspur Ln, Waunakee, WI, 53597", "Waunakee", "53597"),
            P("Q3", "Bartho Quibbleton", 300, "88 Larkspur Ln, Waunakee, WI, 53597", "Waunakee", "53597")]
    forward = household.same_person_clusters(household.build_graph(recs))
    backward = household.same_person_clusters(household.build_graph(list(reversed(recs))))
    assert [c.key for c in forward] == [c.key for c in backward]
    assert len(forward[0].members) == 3


def test_same_length_different_names_never_merge():
    assert not household._same_human("JOHN", "JEAN")
    assert not household._same_human("MARY", "MARK")


# ── same-person consolidation ───────────────────────────────────────────────
def test_same_person_cluster_totals_all_their_claims():
    g = household.build_graph(HERSH)
    [c] = household.same_person_clusters(g)
    assert len(c.members) == 3
    assert round(c.total, 2) == 94299.75
    assert c.members[0]["property_id"] == "H1"          # biggest claim anchors the letter
    assert round(c.fee_potential, 2) == round(94299.75 * 0.10, 2)


def test_single_claim_person_is_not_a_cluster():
    g = household.build_graph([HERSH[0]])
    assert household.same_person_clusters(g) == []


def test_suppressed_records_drop_out_of_clusters():
    recs = [dict(HERSH[0]), dict(HERSH[1]), dict(HERSH[2])]
    recs[1]["suppression_status"] = "SUPPRESSED"
    recs[2]["suppression_status"] = "SUPPRESSED"
    g = household.build_graph(recs)
    # Only one active claim left → no combined letter, nothing to consolidate.
    assert household.same_person_clusters(g) == []


# ── leverage ────────────────────────────────────────────────────────────────
def test_leverage_reports_claims_and_siblings():
    g = household.build_graph(HERSH)
    lev = household.leverage(HERSH[1], g)
    assert lev.claims == 3
    assert set(lev.siblings) == {"H1", "H3"}
    assert lev.multiplier > 1.0


def test_leverage_multiplier_is_capped():
    many = [P(f"M{i}", "Ann Manyclaims", 1000, "9 Oak St, Madison, WI, 53703", "Madison", "53703")
            for i in range(20)]
    g = household.build_graph(many)
    assert household.leverage(many[0], g).multiplier == 1 + household.LEVERAGE_CAP


def test_single_claim_leverage_is_neutral():
    g = household.build_graph([HERSH[0]])
    assert household.leverage(HERSH[0], g).multiplier == 1.0


# ── heir bridges ────────────────────────────────────────────────────────────
def test_heir_bridge_finds_living_family_for_an_estate():
    g = household.build_graph(KRAUSE)
    [b] = household.heir_bridges(g)
    assert b.estate["property_id"] == "K1"
    assert [c["property_id"] for c in b.candidates] == ["K2", "K3"]   # reachable first
    assert round(b.unlock, 2) == round(270934.69 * 0.10, 2)


def test_no_bridge_without_a_deceased_owner():
    g = household.build_graph(KRAUSE[1:])
    assert household.heir_bridges(g) == []


def test_no_bridge_without_living_family():
    g = household.build_graph([KRAUSE[0]])
    assert household.heir_bridges(g) == []


def test_suppressed_relative_is_never_offered_as_an_heir_lead():
    recs = [dict(KRAUSE[0]), dict(KRAUSE[1]), dict(KRAUSE[2])]
    recs[1]["suppression_status"] = "SUPPRESSED"
    g = household.build_graph(recs)
    [b] = household.heir_bridges(g)
    assert [c["property_id"] for c in b.candidates] == ["K3"]


def test_suppressed_estate_produces_no_bridge():
    recs = [dict(KRAUSE[0]), dict(KRAUSE[1])]
    recs[0]["suppression_status"] = "SUPPRESSED"
    g = household.build_graph(recs)
    assert household.heir_bridges(g) == []


def test_beneficiary_property_type_counts_as_deceased():
    assert household.is_deceased(P("X", "Plain Person", 1,
                                   ptype="Proceeds Due to Beneficiaries"))
    assert not household.is_deceased(P("Y", "Plain Person", 1, ptype="Checking Accounts"))


# ── households ──────────────────────────────────────────────────────────────
def test_household_groups_people_and_totals():
    g = household.build_graph(KRAUSE + HERSH)
    hh = household.households(g)
    labels = {h.label for h in hh}
    assert "Krause household" in labels and "Hershberger household" in labels
    krause = next(h for h in hh if h.label == "Krause household")
    assert krause.claims == 3 and len(krause.people) == 3    # 3 distinct people
    assert krause.has_estate and krause.reachable
    hersh = next(h for h in hh if h.label == "Hershberger household")
    assert len(hersh.people) == 1 and hersh.claims == 3      # 1 person, 3 claims
    assert not hersh.has_estate


def test_households_rank_by_total_value():
    g = household.build_graph(KRAUSE + HERSH)
    assert household.households(g)[0].label == "Krause household"


# ── summary ─────────────────────────────────────────────────────────────────
def test_summary_counts_conversations_saved():
    s = household.summary(KRAUSE + HERSH)
    assert s["multi_claim_people"] == 1
    assert s["claims_in_clusters"] == 3
    assert s["conversations_saved"] == 2      # 3 claims reachable in 1 call
    assert s["heir_bridges"] == 1
    assert s["households"] == 2
