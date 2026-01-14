
import pandas as pd
from typing import Dict, List, Any, Optional

class CFOInsights:
    """
    Acts as a Virtual CFO, analyzing financial variances and generating strategic advice.
    This module is responsible for the 'Why' and 'What Next' layers of the analysis.
    """
    
    def __init__(self):
        self.positive_metrics = [
            "revenue", "sales", "net sales", "income", "profit", "operating income", 
            "net income", "gross margin", "cash", "cash flow", "eps", "earnings"
        ]
        self.negative_metrics = [
            "expense", "cost", "cost of sales", "debt", "liabilities", "loss", 
            "operating expenses", "interest expense"
        ]

    def generate_cfo_commentary(self, metric_name: str, segment: str, current_val: float, prior_val: float, period_label: str) -> str:
        """
        Generates a CFO-style strategic commentary based on the variance between current and prior periods.
        """
        if current_val is None or prior_val is None:
            return ""

        # Calculate Variance
        change_dollars = current_val - prior_val
        if prior_val != 0:
            change_pct = (change_dollars / prior_val) * 100
        else:
            change_pct = 0.0

        is_good = self._evaluate_performance(metric_name, change_pct)
        metric_display = metric_name.replace("_", " ").title()

        # Generate "Voice of CFO"
        commentary = []
        
        # 1. Magnitude & Direction
        abs_pct = abs(change_pct)
        direction = "increase" if change_pct > 0 else "decrease"
        
        if abs_pct < 1.0:
            adverb = "remained essentially flat"
            sentiment = "Stable"
        elif abs_pct < 5.0:
            adverb = f"showed a moderate {direction}"
            sentiment = "Moderate Shift"
        elif abs_pct < 15.0:
            adverb = f"posted a solid {direction}"
            sentiment = "Significant Movement"
        else:
            adverb = f"experienced a dramatic {direction}"
            sentiment = "Major Variance"

        # 2. Strategic Advice / Recommendation
        advice = self._generate_strategic_advice(metric_name, change_pct, is_good, segment)

        # Format output
        # Using Markdown for structure
        header = f"### 💼 CFO Perspective: {segment} {metric_display}"
        
        # Format dollar impact (Billion or Million)
        impact_val = abs(change_dollars)
        if impact_val >= 1000:
            impact_str = f"${impact_val/1000:.2f}B"
        else:
            impact_str = f"${impact_val:.0f}M"

        trend_line = (
            f"**Observation:** {segment} {metric_display} {adverb} of **{change_pct:+.1f}%** "
            f"({impact_str} impact) compared to the prior period."
        )
        
        # Construct the block
        block = f"{header}\n\n{trend_line}\n\n{advice}"
        return block

    def _evaluate_performance(self, metric_name: str, change_pct: float) -> bool:
        """Determine if the movement is financially 'good'."""
        metric_lower = metric_name.lower()
        
        if any(x in metric_lower for x in self.positive_metrics):
            return change_pct > 0
        elif any(x in metric_lower for x in self.negative_metrics):
            return change_pct < 0
            
        # Default fallback: Increase is usually expansion (neutral/good)
        return change_pct > 0

    def _generate_strategic_advice(self, metric_name: str, change_pct: float, is_good: bool, segment: str) -> str:
        """Selects the appropriate strategic advice snippet."""
        metric_lower = metric_name.lower()
        abs_pct = abs(change_pct)
        
        if abs_pct < 2.0:
            return "ℹ️ **Status Quo:** Performance is stable. Monitor for any emerging deviations in the coming quarters."

        if not is_good:
            # NEGATIVE SCENARIOS
            if "sales" in metric_lower or "revenue" in metric_lower:
                return (
                    "⚠️ **Action Required:** Top-line contraction is concerning. "
                    "**recommendation:** Immediately evaluate sales funnel health, competitive pricing pressures, "
                    "and consider targeted marketing interventions to reverse this trend."
                )
            elif "income" in metric_lower or "profit" in metric_lower or "margin" in metric_lower:
                return (
                    "⚠️ **Margin Alert:** Profitability is under pressure. "
                    "**Recommendation:** Conduct a granular line-item audit of Cost of Goods Sold (COGS) and OpEx. "
                    "Focus on identifying inefficiencies or pricing power erosion."
                )
            elif "expense" in metric_lower or "cost" in metric_lower:
                return (
                    "⚠️ **Cost Oversight:** Expenses are rising independently of revenue growth. "
                    "**Recommendation:** Implement stricter discretionary spending controls and review vendor contracts for renegotiation opportunities."
                )
            elif "cash" in metric_lower:
                return (
                    "⚠️ **Liquidity Check:** Cash position has deteriorated. "
                    "**Recommendation:** Review working capital cycles (AR/AP) and delay non-essential CapEx to preserve runway."
                )
        
        else:
            # POSITIVE SCENARIOS
            if "sales" in metric_lower or "revenue" in metric_lower:
                return (
                    "✅ **Growth Signal:** Strong revenue momentum. "
                    "**Recommendation:** Double down on capital allocation to this high-performing segment to capture further market share."
                )
            elif "income" in metric_lower or "profit" in metric_lower:
                return (
                    "✅ **Performance Excellence:** Margin expansion demonstrates strong operational leverage. "
                    "**Recommendation:** Reinvest a portion of excess profits into R&D or critical infrastructure to sustain this competitive advantage."
                )
            elif "expense" in metric_lower:
                return (
                    "✅ **Efficiency Win:** Successful cost containment. "
                    "**Recommendation:** Validate that cost cuts are not impacting product quality or customer churn."
                )
        
        # Generic Advice
        return f"💡 **Insight:** This {abs_pct:.1f}% variance warrants a deeper dive into the specific drivers within {segment} operations."
