# src/analysis/enhanced_query_controller.py
"""
Enhanced Query Controller
Integrates all new accuracy components:
- Date normalization for date-specific queries
- Query decomposition for complex questions  
- Calculation auditing for step-by-step verification
- Confidence scoring for honest "I don't know" responses

This wraps the existing query_controller for backward compatibility.
"""

from typing import List, Dict, Any, Tuple, Optional

from src.analysis.date_normalizer import (
    FinancialDateNormalizer, 
    NormalizedDate,
    extract_dates_from_text
)
from src.analysis.query_decomposer import (
    QueryDecomposer, 
    DecomposedQuery, 
    StepType,
    is_complex_query
)
from src.analysis.calculation_auditor import (
    CalculationAuditor,
    SourcedValue,
    AuditedCalculation,
    create_sourced_value
)
from src.analysis.confidence_scorer import (
    ConfidenceScorer,
    ConfidenceAssessment,
    ConfidenceLevel
)
from src.analysis.statement_classifier import StatementType

# Import existing components
from src.analysis.query_controller import (
    route_query as original_route_query,
    build_rag_context,
    build_table_summary,
    format_currency
)
from src.analysis.financial_reasoning import compute_metric_with_reasoning
from src.analysis.metric_registry import METRIC_REGISTRY
from src.ai.rag_engine import retrieve_context
from src.ai.llm_narrator import LLMNarrator


class EnhancedQueryController:
    """
    Enhanced query controller with improved accuracy for complex financial queries.
    
    Key improvements:
    1. Date-specific queries (e.g., "March 29 burn rate")
    2. Complex query decomposition
    3. Calculation auditing with provenance
    4. Confidence-based "I don't know" responses
    """
    
    def __init__(
        self, 
        confidence_threshold: float = 0.5,
        enable_decomposition: bool = True,
        enable_auditing: bool = True
    ):
        """
        Args:
            confidence_threshold: Minimum confidence to provide an answer
            enable_decomposition: Whether to decompose complex queries
            enable_auditing: Whether to track calculation provenance
        """
        self.date_normalizer = FinancialDateNormalizer()
        self.query_decomposer = QueryDecomposer()
        self.auditor = CalculationAuditor()
        self.confidence_scorer = ConfidenceScorer(answer_threshold=confidence_threshold)
        self.narrator = LLMNarrator()
        
        self.enable_decomposition = enable_decomposition
        self.enable_auditing = enable_auditing
    
    def route_query(
        self, 
        question: str, 
        tables: List[Dict],
        chart_gen: Any = None,
        session_id: str = None
    ) -> Tuple[str, Optional[str]]:
        """
        Enhanced query routing with date filtering and confidence scoring.
        
        Args:
            question: User's question
            tables: List of extracted tables
            chart_gen: Optional chart generator function
            session_id: Optional session ID for tracking
            
        Returns:
            (answer, chart_path) tuple
        """
        print(f"\n🎯 [ENHANCED] Processing: {question}")
        
        # Step 1: Extract dates from query
        dates = self.date_normalizer.extract_all_dates(question)
        if dates:
            print(f"📅 Found dates in query: {[str(d) for d in dates]}")
        
        # Step 2: Check if this is a complex query that needs decomposition
        if self.enable_decomposition and is_complex_query(question):
            print("🔀 Complex query detected - attempting decomposition")
            return self._handle_complex_query(question, tables, dates, chart_gen)
        
        # Step 3: For simple queries with dates, apply date filtering
        if dates:
            return self._handle_date_filtered_query(question, tables, dates, chart_gen)
        
        # Step 4: Fall back to original controller for simple queries
        return self._handle_simple_query(question, tables, chart_gen)
    
    def _handle_complex_query(
        self,
        question: str,
        tables: List[Dict],
        dates: List[NormalizedDate],
        chart_gen: Any
    ) -> Tuple[str, Optional[str]]:
        """Handle complex queries through decomposition and step-by-step execution."""
        
        # Decompose the query
        decomposed = self.query_decomposer.decompose(question)
        print(f"📊 Decomposed into {len(decomposed.steps)} steps")
        
        if self.enable_auditing:
            audit = self.auditor.start_calculation(f"query_{decomposed.primary_intent}")
        
        # Track results for each step
        step_results = {}
        sources_found = 0
        values_extracted = []
        
        # Execute steps in order
        for step_id in decomposed.get_execution_order():
            step = next(s for s in decomposed.steps if s.step_id == step_id)
            
            if step.step_type == StepType.EXTRACT_DATE:
                step.result = step.date_filter
                step_results[step_id] = step.result
                
            elif step.step_type == StepType.LOOKUP_METRIC:
                # Look up metric with optional date filtering
                result = self._lookup_metric_with_date(
                    step.metric_name or "",
                    tables,
                    step.date_filter
                )
                if result:
                    step.result = result["value"]
                    step.confidence = result.get("confidence", 0.8)
                    sources_found += 1
                    values_extracted.append(result["value"])
                    
                    # Record in audit trail
                    if self.enable_auditing:
                        sourced = create_sourced_value(
                            value=result["value"],
                            source_file=result.get("source_file", "unknown"),
                            page=result.get("page", 0),
                            row=result.get("row_label", step.metric_name),
                            col=result.get("col_label", ""),
                            raw=result.get("raw_text", "")
                        )
                        self.auditor.record_lookup(audit, sourced)
                    
                step_results[step_id] = step.result
                
            elif step.step_type == StepType.CALCULATE_CHANGE:
                # Calculate burn rate or similar change
                deps = [step_results.get(d) for d in step.depends_on if step_results.get(d)]
                if len(deps) >= 2:
                    step.result = deps[0] - deps[1]
                    step_results[step_id] = step.result
                    
            elif step.step_type == StepType.CALCULATE_GROWTH:
                deps = [step_results.get(d) for d in step.depends_on if step_results.get(d)]
                if len(deps) >= 2 and deps[1] != 0:
                    step.result = ((deps[0] - deps[1]) / abs(deps[1])) * 100
                    step_results[step_id] = step.result
                    
            elif step.step_type == StepType.AVERAGE:
                deps = [step_results.get(d) for d in step.depends_on if step_results.get(d)]
                if deps:
                    step.result = sum(deps) / len(deps)
                    step_results[step_id] = step.result
                    
            elif step.step_type == StepType.SUM:
                deps = [step_results.get(d) for d in step.depends_on if step_results.get(d)]
                if deps:
                    step.result = sum(deps)
                    step_results[step_id] = step.result
        
        # Assess confidence
        assessment = self.confidence_scorer.assess(
            query=question,
            sources_found=sources_found,
            sources_expected=max(len(decomposed.metrics_mentioned), 1),
            value_extracted=len(values_extracted) > 0,
            extraction_confidence=0.9 if values_extracted else 0.0
        )
        
        # Generate response based on confidence
        if not assessment.should_answer:
            decline_msg = self.confidence_scorer.get_decline_message(question, assessment)
            return decline_msg, None
        
        # Build answer from step results
        answer = self._build_answer_from_steps(decomposed, step_results, assessment)
        
        return answer, None
    
    def _handle_date_filtered_query(
        self,
        question: str,
        tables: List[Dict],
        dates: List[NormalizedDate],
        chart_gen: Any
    ) -> Tuple[str, Optional[str]]:
        """Handle queries with specific date references."""
        
        # Filter tables to those matching the date
        filtered_tables = self._filter_tables_by_date(tables, dates[0])
        
        if not filtered_tables:
            print(f"⚠️ No tables found for date: {dates[0]}")
            # Try original query without date filtering
            filtered_tables = tables
        else:
            print(f"📅 Found {len(filtered_tables)} tables matching date {dates[0]}")
        
        # Try deterministic metric extraction first
        from src.analysis.question_router import resolve_intent
        matched_metrics = resolve_intent(question)
        
        if matched_metrics:
            for m_name, m_config in matched_metrics:
                result = self._lookup_metric_with_date(m_name, filtered_tables, dates[0])
                if result and result.get("value") is not None:
                    # Format the answer
                    formatted_value = format_currency(result["value"])
                    
                    # Assess confidence
                    assessment = self.confidence_scorer.assess(
                        query=question,
                        sources_found=1,
                        value_extracted=True,
                        extraction_confidence=result.get("confidence", 0.9)
                    )
                    
                    answer = self.confidence_scorer.format_answer(
                        f"**{m_name.replace('_', ' ').title()}** for {dates[0]}: {formatted_value}\n\n"
                        f"Source: {result.get('source_file', 'document')}, Page {result.get('page', '?')}\n"
                        f"Row: {result.get('row_label', 'N/A')}",
                        assessment
                    )
                    return answer, None
        
        # Fall back to original controller
        return original_route_query(question, tables, chart_gen)
    
    def _handle_simple_query(
        self,
        question: str,
        tables: List[Dict],
        chart_gen: Any
    ) -> Tuple[str, Optional[str]]:
        """Handle simple queries with confidence assessment."""
        
        # Use original route_query but add confidence wrapper
        answer, chart = original_route_query(question, tables, chart_gen)
        
        # Simple heuristic: if answer contains "could not" or is very short, low confidence
        confidence = 0.9  # Default high
        if "could not" in answer.lower() or "unable to" in answer.lower():
            confidence = 0.3
        elif len(answer) < 50:
            confidence = 0.5
        
        # We don't modify the original answer to maintain compatibility
        return answer, chart
    
    def _lookup_metric_with_date(
        self,
        metric_name: str,
        tables: List[Dict],
        target_date: NormalizedDate = None
    ) -> Optional[Dict]:
        """
        Look up a metric value, optionally filtered by date.
        
        Returns dict with: value, confidence, source_file, page, row_label, col_label, raw_text
        """
        # Get keywords for this metric
        keywords = []
        for m_name, config in METRIC_REGISTRY.items():
            if metric_name.lower() in m_name or m_name in metric_name.lower():
                keywords.extend(config.get("keywords", []))
        
        if not keywords:
            # Treat metric_name itself as a keyword
            keywords = [metric_name.lower()]
        
        # Search tables
        for table in tables:
            df = table.get("df")
            if df is None or df.empty:
                continue
            
            # Check if table period matches target date
            if target_date:
                table_periods = table.get("periods", [])
                date_columns = table.get("date_columns", {})
                
                # Find matching column
                matching_col = None
                for col_name, col_date_str in date_columns.items():
                    # Parse the stored date string
                    col_date = self.date_normalizer.parse(col_date_str)
                    if col_date and target_date.overlaps(col_date):
                        matching_col = col_name
                        break
            else:
                matching_col = None
            
            # Search rows for keywords
            row_labels = table.get("row_labels", [])
            for idx, label in enumerate(row_labels):
                label_lower = label.lower()
                
                for kw in keywords:
                    if kw in label_lower:
                        # Found matching row
                        if matching_col and matching_col in df.columns:
                            col_idx = list(df.columns).index(matching_col)
                        else:
                            # Use last numeric column
                            col_idx = len(df.columns) - 1
                        
                        try:
                            raw_value = df.iloc[idx, col_idx]
                            # Parse the value
                            from src.analysis.robust_value_extractor import extract_financial_value
                            value = extract_financial_value(raw_value)
                            
                            if value is not None:
                                return {
                                    "value": value,
                                    "confidence": 0.9,
                                    "source_file": table.get("source_file", "unknown"),
                                    "page": table.get("page", 0),
                                    "row_label": label,
                                    "col_label": str(df.columns[col_idx]),
                                    "raw_text": str(raw_value)
                                }
                        except Exception as e:
                            print(f"⚠️ Error extracting value: {e}")
                            continue
        
        return None
    
    def _filter_tables_by_date(
        self,
        tables: List[Dict],
        target_date: NormalizedDate
    ) -> List[Dict]:
        """Filter tables to those containing data for the target date."""
        matching = []
        
        for table in tables:
            # Check periods
            periods = table.get("periods", [])
            for period_str in periods:
                period = self.date_normalizer.parse(period_str)
                if period and target_date.overlaps(period):
                    matching.append(table)
                    break
            
            # Also check date_columns
            date_columns = table.get("date_columns", {})
            for col_date_str in date_columns.values():
                col_date = self.date_normalizer.parse(col_date_str)
                if col_date and target_date.overlaps(col_date):
                    if table not in matching:
                        matching.append(table)
                    break
        
        return matching
    
    def _build_answer_from_steps(
        self,
        decomposed: DecomposedQuery,
        step_results: Dict[int, Any],
        assessment: ConfidenceAssessment
    ) -> str:
        """Build a natural language answer from step results."""
        
        parts = []
        
        # Add confidence modifier
        if assessment.answer_modifier:
            parts.append(assessment.answer_modifier)
        
        # Format results
        for step in decomposed.steps:
            if step.result is not None and step.step_type != StepType.FORMAT_ANSWER:
                if isinstance(step.result, (int, float)):
                    # Try to infer metric name from description or step details
                    metric_name = step.metric_name if hasattr(step, "metric_name") else None
                    formatted = format_currency(step.result, metric_name=metric_name)
                    parts.append(f"**{step.description}**: {formatted}")
                elif step.step_type == StepType.EXTRACT_DATE:
                    pass  # Don't include date parsing in output
                else:
                    parts.append(f"**{step.description}**: {step.result}")
        
        # Add confidence note if not high
        if assessment.level != ConfidenceLevel.HIGH:
            parts.append(f"\n*Confidence: {assessment.level.value}*")
        
        # Add warnings
        if assessment.warnings:
            parts.append(f"\n⚠️ Notes: {', '.join(assessment.warnings)}")
        
        return "\n".join(parts)


# Public interface functions
def enhanced_route_query(
    question: str,
    tables: List[Dict],
    chart_gen: Any = None,
    session_id: str = None,
    confidence_threshold: float = 0.5
) -> Tuple[str, Optional[str]]:
    """
    Enhanced query routing with all accuracy improvements.
    
    This is the main entry point for the enhanced query controller.
    """
    controller = EnhancedQueryController(confidence_threshold=confidence_threshold)
    return controller.route_query(question, tables, chart_gen, session_id)


def get_query_confidence(question: str, tables: List[Dict]) -> ConfidenceAssessment:
    """
    Get confidence assessment for a query without generating the answer.
    
    Useful for determining if we should attempt the query.
    """
    controller = EnhancedQueryController()
    
    # Quick assessment based on available data
    dates = controller.date_normalizer.extract_all_dates(question)
    
    if dates:
        matching_tables = controller._filter_tables_by_date(tables, dates[0])
        sources_found = len(matching_tables)
    else:
        sources_found = len(tables)
    
    return controller.confidence_scorer.assess(
        query=question,
        sources_found=sources_found,
        sources_expected=1,
        value_extracted=sources_found > 0
    )
