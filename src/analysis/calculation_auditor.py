# src/analysis/calculation_auditor.py
"""
Calculation Auditor
Tracks every calculation step with source provenance for verification.

Enables:
- Full audit trail for any computed value
- Step-by-step calculation visualization
- Source verification (which cell in which document)
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SourcedValue:
    """A value with complete provenance."""
    
    value: float
    source_file: str
    source_page: int
    row_label: str          # e.g., "Total Revenue"
    column_label: str       # e.g., "Q1 2024" or "March 29, 2025"
    raw_text: str           # Original text before parsing
    confidence: float = 1.0  # 1.0 = extracted directly, <1.0 = inferred/calculated
    
    def __str__(self) -> str:
        return f"{self.value:,.2f} (from {self.source_file}, p.{self.source_page}, {self.row_label})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "source_file": self.source_file,
            "source_page": self.source_page,
            "row_label": self.row_label,
            "column_label": self.column_label,
            "raw_text": self.raw_text,
            "confidence": self.confidence
        }


@dataclass
class CalculationStep:
    """A single step in a calculation."""
    
    step_number: int
    operation: str          # e.g., "lookup", "divide", "subtract", "multiply"
    description: str        # Human-readable description
    inputs: List['SourcedValue']
    output: Optional['SourcedValue'] = None
    formula_used: str = ""  # e.g., "profit_margin = net_income / revenue * 100"
    
    def __str__(self) -> str:
        return f"Step {self.step_number}: {self.description}"


@dataclass
class AuditedCalculation:
    """Complete audit trail for a calculated result."""
    
    # Result
    final_value: float
    metric_name: str
    unit: str = ""          # e.g., "%", "$", "USD"
    
    # Audit trail
    steps: List[CalculationStep] = field(default_factory=list)
    
    # Confidence scoring
    overall_confidence: float = 1.0
    confidence_factors: Dict[str, float] = field(default_factory=dict)
    
    # Timing
    computed_at: datetime = field(default_factory=datetime.now)
    
    # Warnings/Notes
    warnings: List[str] = field(default_factory=list)
    
    def add_step(self, step: CalculationStep):
        """Add a calculation step."""
        self.steps.append(step)
    
    def add_warning(self, warning: str):
        """Add a warning about the calculation."""
        self.warnings.append(warning)
    
    def get_all_sources(self) -> List[SourcedValue]:
        """Get all source values used in this calculation."""
        sources = []
        for step in self.steps:
            sources.extend(step.inputs)
        return sources
    
    def explain(self, verbose: bool = False) -> str:
        """Generate human-readable explanation of the calculation."""
        lines = [
            f"📊 **{self.metric_name}**: {self.final_value:,.2f}{self.unit}",
            f"   Confidence: {self.overall_confidence:.0%}",
            ""
        ]
        
        if self.warnings:
            lines.append("⚠️ Warnings:")
            for w in self.warnings:
                lines.append(f"   - {w}")
            lines.append("")
        
        if verbose:
            lines.append("📝 Calculation Steps:")
            for step in self.steps:
                lines.append(f"   {step.step_number}. {step.description}")
                if step.formula_used:
                    lines.append(f"      Formula: {step.formula_used}")
                if step.inputs:
                    lines.append(f"      Inputs: {[str(i) for i in step.inputs]}")
                if step.output:
                    lines.append(f"      Output: {step.output.value:,.2f}")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "final_value": self.final_value,
            "metric_name": self.metric_name,
            "unit": self.unit,
            "overall_confidence": self.overall_confidence,
            "confidence_factors": self.confidence_factors,
            "warnings": self.warnings,
            "steps": [
                {
                    "step_number": s.step_number,
                    "operation": s.operation,
                    "description": s.description,
                    "formula_used": s.formula_used,
                    "inputs": [i.to_dict() for i in s.inputs],
                    "output": s.output.to_dict() if s.output else None
                }
                for s in self.steps
            ]
        }


class CalculationAuditor:
    """
    Tracks and audits all calculations performed by the system.
    
    Usage:
        auditor = CalculationAuditor()
        
        # Start a new calculation
        calc = auditor.start_calculation("profit_margin")
        
        # Record each step
        revenue = SourcedValue(123000000, "report.pdf", 3, "Total Revenue", "Q1 2024", "123,000")
        profit = SourcedValue(15000000, "report.pdf", 3, "Net Income", "Q1 2024", "15,000")
        
        auditor.record_lookup(calc, revenue)
        auditor.record_lookup(calc, profit)
        auditor.record_division(calc, profit, revenue, result=12.195)
        
        # Finalize
        auditor.finalize(calc, final_value=12.195, unit="%")
    """
    
    def __init__(self):
        self.calculations: Dict[str, AuditedCalculation] = {}
        self._current_step = 0
    
    def start_calculation(self, metric_name: str) -> AuditedCalculation:
        """Start tracking a new calculation."""
        calc = AuditedCalculation(
            final_value=0.0,
            metric_name=metric_name
        )
        self._current_step = 0
        self.calculations[metric_name] = calc
        return calc
    
    def record_lookup(
        self, 
        calc: AuditedCalculation, 
        value: SourcedValue,
        description: str = None
    ) -> CalculationStep:
        """Record a value lookup step."""
        self._current_step += 1
        
        step = CalculationStep(
            step_number=self._current_step,
            operation="lookup",
            description=description or f"Retrieved {value.row_label}: {value.value:,.2f}",
            inputs=[value],
            output=value
        )
        calc.add_step(step)
        return step
    
    def record_calculation(
        self,
        calc: AuditedCalculation,
        operation: str,
        inputs: List[SourcedValue],
        result_value: float,
        formula: str = "",
        description: str = ""
    ) -> CalculationStep:
        """Record a calculation step."""
        self._current_step += 1
        
        # Create output sourced value (derived, so lower confidence)
        output = SourcedValue(
            value=result_value,
            source_file="calculated",
            source_page=0,
            row_label=calc.metric_name,
            column_label="derived",
            raw_text=f"{result_value:,.2f}",
            confidence=0.9  # Slightly lower since it's calculated
        )
        
        step = CalculationStep(
            step_number=self._current_step,
            operation=operation,
            description=description or f"Calculated {operation}: {result_value:,.2f}",
            inputs=inputs,
            output=output,
            formula_used=formula
        )
        calc.add_step(step)
        return step
    
    def record_division(
        self,
        calc: AuditedCalculation,
        numerator: SourcedValue,
        denominator: SourcedValue,
        result: float,
        multiply_100: bool = False
    ) -> CalculationStep:
        """Record a division calculation."""
        formula = f"{numerator.row_label} / {denominator.row_label}"
        if multiply_100:
            formula += " × 100"
        
        return self.record_calculation(
            calc=calc,
            operation="divide",
            inputs=[numerator, denominator],
            result_value=result,
            formula=formula,
            description=f"Divided {numerator.row_label} by {denominator.row_label}"
        )
    
    def record_subtraction(
        self,
        calc: AuditedCalculation,
        value1: SourcedValue,
        value2: SourcedValue,
        result: float
    ) -> CalculationStep:
        """Record a subtraction calculation."""
        return self.record_calculation(
            calc=calc,
            operation="subtract",
            inputs=[value1, value2],
            result_value=result,
            formula=f"{value1.row_label} - {value2.row_label}",
            description=f"Subtracted {value2.row_label} from {value1.row_label}"
        )
    
    def record_growth(
        self,
        calc: AuditedCalculation,
        current: SourcedValue,
        prior: SourcedValue,
        result: float
    ) -> CalculationStep:
        """Record a growth rate calculation."""
        return self.record_calculation(
            calc=calc,
            operation="growth",
            inputs=[current, prior],
            result_value=result,
            formula=f"({current.row_label} - {prior.row_label}) / {prior.row_label} × 100",
            description=f"Calculated growth from {prior.column_label} to {current.column_label}"
        )
    
    def finalize(
        self,
        calc: AuditedCalculation,
        final_value: float,
        unit: str = ""
    ) -> AuditedCalculation:
        """Finalize a calculation with the final result."""
        calc.final_value = final_value
        calc.unit = unit
        calc.computed_at = datetime.now()
        
        # Calculate overall confidence based on sources
        if calc.steps:
            source_confidences = [
                inp.confidence 
                for step in calc.steps 
                for inp in step.inputs
            ]
            if source_confidences:
                calc.overall_confidence = sum(source_confidences) / len(source_confidences)
            
            # Add confidence factors
            calc.confidence_factors = {
                "source_quality": calc.overall_confidence,
                "num_sources": min(len(source_confidences) / 3, 1.0),  # Normalize to max 1.0
                "direct_extraction": 1.0 if len(calc.steps) <= 2 else 0.8
            }
        
        return calc
    
    def calculate_confidence(
        self,
        sources_found: int,
        sources_expected: int,
        all_from_same_doc: bool = True,
        cross_verified: bool = False
    ) -> float:
        """
        Calculate confidence score for a result.
        
        Args:
            sources_found: Number of source values found
            sources_expected: Number of source values expected
            all_from_same_doc: Whether all sources are from one document
            cross_verified: Whether result was verified against another statement
            
        Returns:
            Confidence score 0.0 - 1.0
        """
        # Base confidence from completeness
        completeness = min(sources_found / max(sources_expected, 1), 1.0)
        
        # Bonus for same document (more reliable context)
        doc_bonus = 0.1 if all_from_same_doc else 0.0
        
        # Bonus for cross-verification
        verify_bonus = 0.15 if cross_verified else 0.0
        
        return min(completeness + doc_bonus + verify_bonus, 1.0)
    
    def should_answer(self, confidence: float, threshold: float = 0.5) -> Tuple[bool, str]:
        """
        Determine if we should provide an answer based on confidence.
        
        Returns:
            (should_answer, explanation)
        """
        if confidence >= 0.9:
            return True, "High confidence - direct match found"
        elif confidence >= 0.7:
            return True, "Good confidence - some inference applied"
        elif confidence >= threshold:
            return True, "Moderate confidence - result may need verification"
        else:
            return False, f"Low confidence ({confidence:.0%}) - insufficient data to provide reliable answer"


# Singleton auditor for easy access
_global_auditor = None


def get_auditor() -> CalculationAuditor:
    """Get the global calculation auditor."""
    global _global_auditor
    if _global_auditor is None:
        _global_auditor = CalculationAuditor()
    return _global_auditor


def create_sourced_value(
    value: float,
    source_file: str,
    page: int,
    row: str,
    col: str,
    raw: str = ""
) -> SourcedValue:
    """Convenience function to create a SourcedValue."""
    return SourcedValue(
        value=value,
        source_file=source_file,
        source_page=page,
        row_label=row,
        column_label=col,
        raw_text=raw or str(value)
    )
