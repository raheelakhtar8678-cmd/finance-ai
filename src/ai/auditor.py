# src/ai/auditor.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re

@dataclass
class AuditResult:
    passed: bool
    score: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)
    correction_hint: str = ""

class FinancialAuditor:
    """
    Agentic Auditor that verifies RAG responses against accounting rules 
    and document facts before showing them to the user.
    """
    
    def verify(self, rag_response: Dict[str, Any]) -> AuditResult:
        """
        Main entry point for verification.
        """
        # 1. Skip if error
        if "error" in rag_response:
            return AuditResult(passed=True, score=1.0) # Pass errors through
            
        answer = rag_response.get("answer", "")
        # If answering about insufficient data, skip audit
        if "Insufficient data" in str(answer):
            return AuditResult(passed=True, score=1.0)
            
        issues = []
        
        # 2. Extract Numbers & Terms
        # Simple extraction of financial figures from the answer string
        # mapping: "Revenue": 100000.0, "Net Income": 5000.0
        metrics = self._extract_metrics_from_text(str(answer))
        
        # 3. Running Checks
        self._check_hierarchy(metrics, issues)
        self._check_consistency(str(answer), metrics, issues)
        
        # 4. Score
        score = 1.0 - (len(issues) * 0.2)
        passed = len(issues) == 0
        
        hint = ""
        if not passed:
            hint = f"⚠ Auditor Warning: {'; '.join(issues)}"
            
        return AuditResult(
            passed=passed, 
            score=max(0.0, score), 
            issues=issues, 
            correction_hint=hint
        )

    def _extract_metrics_from_text(self, text: str) -> Dict[str, float]:
        """
        Heuristic extraction of labeled numbers from text.
        e.g. "Revenue was $50 million" -> {"revenue": 50000000}
        """
        # Simplified for now: just looking for keywords near format $XX.X billion/million
        extracted = {}
        
        # Normalize
        lower_text = text.lower()
        
        # Define patterns
        # map generic key -> list of synonyms
        taxonomy = {
            "revenue": ["revenue", "net sales", "turnover", "sales"],
            "operating_income": ["operating income", "operating profit", "income from operations"],
            "net_income": ["net income", "net profit", "net earnings", "net loss"],
            "gross_margin": ["gross margin", "gross profit"]
        }
        
        # Regex for values: $123.45 million, 12,345, etc.
        # This is hard to do perfectly on unstructured answer text, 
        # but the RAG usually outputs: "**Total Net Sales**: $90,753 million"
        
        for key, synonyms in taxonomy.items():
            for term in synonyms:
                # Look for TERM followed by strictly format checks or rely on RAG structure
                # Searching: term... value
                # Using a wide window (50 chars)
                matches = list(re.finditer(re.escape(term), lower_text))
                for m in matches:
                    start = m.end()
                    window = lower_text[start:start+50]
                    
                    # Parse number
                    # Support: $10B, $10 Million, 10,000,000
                    value_match = re.search(r"(\$?)(\d[\d,\.]*)\s*(billion|million|thousand|b|m|k)?", window)
                    if value_match:
                        raw_num = value_match.group(2).replace(",", "")
                        scale = value_match.group(3)
                        
                        try:
                            val = float(raw_num)
                            if scale:
                                s = scale.lower()
                                if s.startswith("b"): val *= 1_000_000_000
                                elif s.startswith("m"): val *= 1_000_000
                                elif s.startswith("k") or s.startswith("t"): val *= 1_000
                            
                            # Existing logic often extracts in Millions, so let's stick to raw if huge, 
                            # or just compare relative magnitudes. 
                            # Hierarchy checks work regardless of scale IF units are consistent.
                            # But here we might get mixed units.
                            
                            extracted[key] = val
                            break # Found one instance of this metric
                        except:
                            continue
                if key in extracted: break
        
        return extracted

    def _check_hierarchy(self, metrics: Dict[str, float], issues: List[str]):
        """
        Accounting Hierarchy:
        Revenue >= Gross Margin (usually)
        Revenue >= Operating Income
        Operating Income >= Net Income (usually, unless non-op gains)
        """
        rev = metrics.get("revenue")
        op_inc = metrics.get("operating_income")
        net_inc = metrics.get("net_income")
        
        if rev and op_inc:
            if op_inc > rev:
                issues.append(f"Logic Error: Operating Income (${op_inc:,.0f}) > Revenue (${rev:,.0f})")
        
        if rev and net_inc:
             if net_inc > rev:
                 issues.append(f"Logic Error: Net Income (${net_inc:,.0f}) > Revenue (${rev:,.0f})")

    def _check_consistency(self, text: str, metrics: Dict[str, float], issues: List[str]):
        """
        Text vs Number Consistency.
        e.g. Text says "loss" but Net Income is positive, or vice versa?
        """
        lower = text.lower()
        net_inc = metrics.get("net_income")
        
        # 1. "Loss" Check
        if "net loss" in lower or "operating loss" in lower:
            # We expect negative numbers or explicit notes
            # But the extraction might return positive absolute value.
            # This is tricky without more sophisticated NLP.
            # Skipping for now to avoid false positives.
            pass
            
        # 2. Year consistency? (Hard without knowing the question year)
        pass
