# src/ai/answer_generator.py
"""
AI Answer Generator with LLM Narration.

Takes deterministic results and generates human-friendly explanations.
"""

from src.ai.llm_narrator import LLMNarrator
from src.ai.rag_engine import retrieve_context


def generate_answer(metric_name, result, user_question, charts=None):
    """
    Generate complete answer with LLM narration.
    
    Args:
        metric_name: Name of the metric (e.g., "burn_rate")
        result: Dictionary from compute_metric_with_reasoning() containing:
                - success: bool
                - result: calculated value
                - reasoning: explanation
                - confidence: 0-1
                - calculation: formula used
        user_question: Original user question
        charts: List of chart paths (optional)
    
    Returns:
        Complete formatted answer with LLM explanation
    """
    
    # Build computed result summary
    computed_result = format_computed_result(metric_name, result)
    
    # Get RAG context for additional insights
    try:
        rag_contexts = retrieve_context(user_question, k=3)
        rag_text = "\n\n".join([
            f"Source: {ctx.get('source', 'Document')}\n{ctx['text'][:200]}"
            for ctx in rag_contexts[:2]
        ])
    except Exception as e:
        print(f"⚠️ RAG retrieval failed: {e}")
        rag_text = "Financial data from uploaded documents"
    
    # Use LLM to generate natural explanation
    try:
        narrator = LLMNarrator()
        
        explanation = narrator.explain(
            user_question=user_question,
            rag_context=rag_text,
            computed_result=computed_result,
            charts=charts
        )
        
        return explanation
    
    except Exception as e:
        print(f"⚠️ LLM narration failed: {e}")
        
        # Fallback: Return formatted computed result without LLM
        return computed_result


def format_computed_result(metric_name, result):
    """
    Format the computed result into human-readable text.
    """
    
    if result.get("success"):
        value = result.get("result", "N/A")
        reasoning = result.get("reasoning", "")
        confidence = result.get("confidence", 0)
        calculation = result.get("calculation", "")
        
        # Format based on metric type
        if "margin" in metric_name or "growth" in metric_name:
            formatted_value = f"{value:.1f}%"
        elif "rate" in metric_name and "burn" in metric_name:
            formatted_value = f"{value:.1f} months"
        else:
            formatted_value = f"{value:,.2f}"
        
        output = f"""
**{metric_name.replace('_', ' ').title()}:** {formatted_value}

{reasoning}
"""
        
        if calculation:
            output += f"\n**Calculation:** {calculation}"
        
        output += f"\n**Confidence:** {confidence:.0%}"
        
        return output.strip()
    
    else:
        # Calculation failed
        reasoning = result.get("reasoning", "Unable to calculate")
        confidence = result.get("confidence", 0)
        
        return f"""
**{metric_name.replace('_', ' ').title()}:** Unable to calculate

{reasoning}

**Confidence:** {confidence:.0%}
""".strip()
