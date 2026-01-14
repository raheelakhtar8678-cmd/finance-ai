# src/analysis/question_router.py

from src.analysis.metric_registry import METRIC_REGISTRY

def resolve_intent(question: str):
    q = question.lower()

    # 1. Global Exclusion for Complex/Agentic Queries
    # If the user asks for breakdowns, products, or segments, we MUST use RAG
    exclusions = ["which", "product", "segment", "breakdown", "mix", "share", "geo", "region", "most", "top", "highest"]
    
    if any(ex in q for ex in exclusions):
        print(f"🚫 Complex intent detected (found exclusion keyword). Skipping predefined metrics.")
        return []

    # 2. Check Predefined Metrics
    all_matches = []
    for metric, config in METRIC_REGISTRY.items():
        for kw in config["keywords"]:
            if kw in q:
                all_matches.append((len(kw), metric, config))
    
    if all_matches:
        # Sort by keyword length descending (precision)
        all_matches.sort(key=lambda x: x[0], reverse=True)
        
        unique_results = []
        seen = set()
        for _, metric, config in all_matches:
            if metric not in seen:
                unique_results.append((metric, config))
                seen.add(metric)
        
        if len(unique_results) > 1:
            print(f"⚖️ Multi-metric query detected: {[r[0] for r in unique_results]}")
        else:
            print(f"🎯 Matched specific metric: {unique_results[0][0]}")
            
        return unique_results

    return []

KNOWN_SEGMENTS = [
    "americas", "europe", "greater china", "japan", "rest of asia pacific", "asia pacific", 
    "china", "united states", "u.s.", "international",
    "iphone", "mac", "ipad", "wearables", "services", "home", "accessories"
]

def detect_segment_filter(question: str):
    """Detect if the user is asking about a specific business segment or region."""
    q = question.lower()
    
    # Sort by length to match "Greater China" before "China"
    sorted_segments = sorted(KNOWN_SEGMENTS, key=len, reverse=True)
    
    for seg in sorted_segments:
        if seg in q:
            return seg
            
    return None