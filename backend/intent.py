from dataclasses import dataclass
from typing import Optional


@dataclass
class IntentResult:
    intent: str
    item_type: str
    is_procurement: bool
    is_education: bool
    is_greeting: bool
    needs_clarification: bool
    user_is_novice: bool
    extracted_strain_or_item: Optional[str] = None


def classify_intent_local(message: str) -> IntentResult:
    text = message.lower().strip()

    is_greeting = text in {"hi", "hello", "hey"} or text.startswith("hello")
    is_education = "explain" in text or "what is" in text or "mutation" in text
    is_procurement = any(keyword in text for keyword in ["buy", "order", "quote", "rfq", "need", "purchase"])

    if "antibody" in text or "reagent" in text or "glp-1" in text:
        item_type = "reagent"
    elif any(token in text for token in ["jax", "stock", "strain", "mouse", "rat", "c57", "balb", "fad", "transgenic"]):
        item_type = "strain"
    else:
        item_type = "unclear"

    needs_clarification = item_type == "unclear" and not is_greeting
    intent = "education" if is_education else "procurement" if is_procurement else "greeting" if is_greeting else "procurement"

    user_is_novice = "first time" in text or "new" in text or "novice" in text

    return IntentResult(
        intent=intent,
        item_type=item_type,
        is_procurement=is_procurement or intent == "procurement",
        is_education=is_education,
        is_greeting=is_greeting,
        needs_clarification=needs_clarification,
        user_is_novice=user_is_novice,
        extracted_strain_or_item=None,
    )
