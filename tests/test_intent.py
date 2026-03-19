from backend.intent import classify_intent_local


def test_procurement_intent_strain():
    result = classify_intent_local("I want to buy 8-week-old C57BL/6J mice")
    assert result.intent == "procurement"
    assert result.item_type in {"strain", "unclear"}


def test_greeting_intent():
    result = classify_intent_local("Hello")
    assert result.is_greeting is True


def test_education_intent():
    result = classify_intent_local("Check literature for 5xFAD mutations")
    assert result.is_education is True or result.intent == "education"


def test_reagent_intent():
    result = classify_intent_local("Need anti-GLP-1 antibody")
    assert result.item_type == "reagent"
