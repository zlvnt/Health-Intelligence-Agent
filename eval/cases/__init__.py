from eval.cases.coordination_cases import COORDINATION_CASES
from eval.cases.intervention_cases import INTERVENTION_CASES
from eval.cases.logging_cases import LOGGING_CASES
from eval.cases.rag_cases import RAG_CASES
from eval.cases.routing_cases import ROUTING_CASES

ALL_CASES = LOGGING_CASES + ROUTING_CASES + INTERVENTION_CASES + COORDINATION_CASES + RAG_CASES


def user_id_to_telegram_id(user_id: str) -> int:
    """Map 'eval_test_N' → 90000+N for DB isolation."""
    n = int(user_id.split("_")[-1])
    return 90000 + n
