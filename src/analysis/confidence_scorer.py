# src/analysis/confidence_scorer.py
"""
Confidence Scoring System
Determines when to answer vs when to say "I don't know"

This is crucial for preventing hallucinations and providing honest responses.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """Discrete confidence levels for response selection."""
    
    HIGH = "high"           # >= 0.9: Direct, confident answer
    GOOD = "good"           # 0.7 - 0.9: Answer with minor caveats
    MODERATE = "moderate"   # 0.5 - 0.7: Answer with significant caveats
    LOW = "low"             # 0.3 - 0.5: Tentative answer only if user insists
    INSUFFICIENT = "insufficient"  # < 0.3: Decline to answer


@dataclass
class ConfidenceAssessment:
    """Complete confidence assessment for a query response."""
    
    # Overall score
    score: float  # 0.0 - 1.0
    level: ConfidenceLevel
    
    # Component scores
    data_availability: float  # Did we find the relevant data?
    source_quality: float     # How reliable are the sources?
    calculation_reliability: float  # How confident in our calculations?
    query_clarity: float      # How clear was the query?
    
    # Decision
    should_answer: bool
    answer_modifier: str  # Prefix/suffix to add to answer
    
    # Explanation
    explanation: str
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level.value,
            "should_answer": self.should_answer,
            "answer_modifier": self.answer_modifier,
            "explanation": self.explanation,
            "warnings": self.warnings,
            "components": {
                "data_availability": self.data_availability,
                "source_quality": self.source_quality,
                "calculation_reliability": self.calculation_reliability,
                "query_clarity": self.query_clarity
            }
        }


class ConfidenceScorer:
    """
    Scores confidence in query responses to enable honest "I don't know" answers.
    
    Usage:
        scorer = ConfidenceScorer()
        
        assessment = scorer.assess(
            query="What is Q1 2024 revenue?",
            sources_found=3,
            sources_expected=1,
            value_extracted=True,
            cross_verified=True
        )
        
        if assessment.should_answer:
            return f"{assessment.answer_modifier} {answer}"
        else:
            return "I couldn't find sufficient data to answer this question."
    """
    
    # Default thresholds (can be customized)
    THRESHOLDS = {
        ConfidenceLevel.HIGH: 0.9,
        ConfidenceLevel.GOOD: 0.7,
        ConfidenceLevel.MODERATE: 0.5,
        ConfidenceLevel.LOW: 0.3,
        ConfidenceLevel.INSUFFICIENT: 0.0
    }
    
    # Answer modifiers based on confidence level
    ANSWER_MODIFIERS = {
        ConfidenceLevel.HIGH: "",  # No modifier needed
        ConfidenceLevel.GOOD: "Based on the available data, ",
        ConfidenceLevel.MODERATE: "Based on available information (may require verification), ",
        ConfidenceLevel.LOW: "⚠️ Limited data available. Tentative answer: ",
        ConfidenceLevel.INSUFFICIENT: ""  # Won't answer
    }
    
    def __init__(self, answer_threshold: float = 0.5):
        """
        Args:
            answer_threshold: Minimum confidence to provide an answer (default 0.5)
        """
        self.answer_threshold = answer_threshold
    
    def assess(
        self,
        query: str,
        sources_found: int = 0,
        sources_expected: int = 1,
        value_extracted: bool = False,
        extraction_confidence: float = 1.0,
        cross_verified: bool = False,
        query_understood: bool = True,
        from_same_document: bool = True
    ) -> ConfidenceAssessment:
        """
        Assess confidence for a query response.
        
        Args:
            query: Original user query
            sources_found: Number of relevant sources/chunks found
            sources_expected: Number of sources we expected to find
            value_extracted: Whether we successfully extracted a value
            extraction_confidence: Confidence in the extracted value
            cross_verified: Whether the value was cross-verified
            query_understood: Whether we understood the query intent
            from_same_document: Whether all sources are from same document
            
        Returns:
            ConfidenceAssessment with scoring and decision
        """
        warnings = []
        
        # 1. Data Availability Score
        if sources_expected > 0:
            data_availability = min(sources_found / sources_expected, 1.0)
        else:
            data_availability = 1.0 if sources_found > 0 else 0.0
        
        if sources_found == 0:
            warnings.append("No relevant data sources found")
        elif sources_found < sources_expected:
            warnings.append(f"Found {sources_found} of {sources_expected} expected sources")
        
        # 2. Source Quality Score
        source_quality = 0.5  # Base score
        if value_extracted:
            source_quality += 0.3
        if cross_verified:
            source_quality += 0.2
        source_quality = min(source_quality * extraction_confidence, 1.0)
        
        if not from_same_document and sources_found > 1:
            warnings.append("Data combined from multiple documents")
        
        # 3. Calculation Reliability Score
        if value_extracted:
            calculation_reliability = extraction_confidence
            if cross_verified:
                calculation_reliability = min(calculation_reliability + 0.1, 1.0)
        else:
            calculation_reliability = 0.0
            warnings.append("Could not extract numerical value")
        
        # 4. Query Clarity Score
        query_clarity = 1.0 if query_understood else 0.5
        
        # Detect ambiguous queries
        ambiguous_patterns = ["any", "some", "maybe", "perhaps", "could be"]
        query_lower = query.lower()
        if any(p in query_lower for p in ambiguous_patterns):
            query_clarity *= 0.9
        
        # Calculate overall score (weighted average)
        weights = {
            "data_availability": 0.35,
            "source_quality": 0.25,
            "calculation_reliability": 0.30,
            "query_clarity": 0.10
        }
        
        overall = (
            data_availability * weights["data_availability"] +
            source_quality * weights["source_quality"] +
            calculation_reliability * weights["calculation_reliability"] +
            query_clarity * weights["query_clarity"]
        )
        
        # Determine confidence level
        level = self._score_to_level(overall)
        
        # Determine if we should answer
        should_answer = overall >= self.answer_threshold
        
        # Generate explanation
        explanation = self._generate_explanation(
            overall, level, data_availability, source_quality, 
            calculation_reliability, query_clarity
        )
        
        return ConfidenceAssessment(
            score=overall,
            level=level,
            data_availability=data_availability,
            source_quality=source_quality,
            calculation_reliability=calculation_reliability,
            query_clarity=query_clarity,
            should_answer=should_answer,
            answer_modifier=self.ANSWER_MODIFIERS[level],
            explanation=explanation,
            warnings=warnings
        )
    
    def _score_to_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level."""
        if score >= self.THRESHOLDS[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif score >= self.THRESHOLDS[ConfidenceLevel.GOOD]:
            return ConfidenceLevel.GOOD
        elif score >= self.THRESHOLDS[ConfidenceLevel.MODERATE]:
            return ConfidenceLevel.MODERATE
        elif score >= self.THRESHOLDS[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.INSUFFICIENT
    
    def _generate_explanation(
        self, 
        overall: float,
        level: ConfidenceLevel,
        data: float,
        quality: float,
        calc: float,
        clarity: float
    ) -> str:
        """Generate human-readable explanation of confidence."""
        if level == ConfidenceLevel.HIGH:
            return "High confidence: Found direct match in source documents."
        elif level == ConfidenceLevel.GOOD:
            return "Good confidence: Data found with minor inference required."
        elif level == ConfidenceLevel.MODERATE:
            parts = []
            if data < 0.7:
                parts.append("limited data sources")
            if quality < 0.7:
                parts.append("source quality concerns")
            if calc < 0.7:
                parts.append("extraction uncertainty")
            return f"Moderate confidence due to: {', '.join(parts) or 'general uncertainty'}."
        elif level == ConfidenceLevel.LOW:
            return "Low confidence: Significant gaps in available data."
        else:
            return "Insufficient data to provide a reliable answer."
    
    def get_decline_message(
        self, 
        query: str,
        assessment: ConfidenceAssessment
    ) -> str:
        """Generate a helpful decline message when we can't answer."""
        messages = [
            "I couldn't find sufficient data in the uploaded documents to answer this question accurately."
        ]
        
        if assessment.data_availability < 0.3:
            messages.append(
                "The specific information you're asking about doesn't appear to be in the documents. "
                "Please check if the relevant financial statement is included."
            )
        elif assessment.calculation_reliability < 0.3:
            messages.append(
                "While I found potentially relevant data, I couldn't extract the specific values needed. "
                "The data format may not be in a standard structure."
            )
        
        # Suggest what data we'd need
        if "date" in query.lower() or "march" in query.lower() or "quarter" in query.lower():
            messages.append(
                "💡 Tip: For date-specific queries, make sure the financial statements include data for that period."
            )
        
        return "\n\n".join(messages)
    
    def format_answer(
        self,
        answer: str,
        assessment: ConfidenceAssessment,
        include_warnings: bool = True
    ) -> str:
        """Format an answer with appropriate confidence modifiers."""
        parts = []
        
        # Add modifier if not high confidence
        if assessment.answer_modifier:
            parts.append(assessment.answer_modifier)
        
        parts.append(answer)
        
        # Add warnings if requested and present
        if include_warnings and assessment.warnings:
            warning_text = "\n\n⚠️ " + " | ".join(assessment.warnings)
            parts.append(warning_text)
        
        return "".join(parts)


# Convenience functions
def assess_confidence(
    sources_found: int,
    value_extracted: bool,
    extraction_confidence: float = 1.0,
    cross_verified: bool = False
) -> Tuple[float, bool, str]:
    """
    Quick confidence assessment.
    
    Returns:
        (score, should_answer, modifier)
    """
    scorer = ConfidenceScorer()
    assessment = scorer.assess(
        query="",
        sources_found=sources_found,
        sources_expected=1,
        value_extracted=value_extracted,
        extraction_confidence=extraction_confidence,
        cross_verified=cross_verified
    )
    return assessment.score, assessment.should_answer, assessment.answer_modifier


def should_decline(sources_found: int, value_extracted: bool) -> bool:
    """Quick check if we should decline to answer."""
    score, should_answer, _ = assess_confidence(sources_found, value_extracted)
    return not should_answer
