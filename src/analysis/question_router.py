# src/analysis/question_router.py

from src.analysis.metric_registry import METRIC_METADATA

def resolve_intent(question: str):
    q = question.lower()

    # Iterate over the correct dictionary: METRIC_METADATA
    for metric, config in METRIC_METADATA.items():
        for kw in config["keywords"]:
            if kw in q:
                return metric, config

    return None, None