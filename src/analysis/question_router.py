from src.analysis.metric_registry import METRIC_REGISTRY


def resolve_intent(question: str):
    q = question.lower()

    for metric, config in METRIC_REGISTRY.items():
        for kw in config["keywords"]:
            if kw in q:
                return metric, config

    return None, None