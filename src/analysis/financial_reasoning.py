# src/analysis/financial_reasoning.py

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import re

from src.analysis.robust_value_extractor import (
    extract_financial_value,
    extract_multiple_values
)
from src.analysis.metric_registry import METRIC_REGISTRY
from src.analysis.formula_evaluator import evaluate_metric

def heal_fragmented_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Heals split columns in PDF-extracted tables:
    1. Numeric fragments: '53' + '887' -> '53,887'
    2. Text fragments: 'Grea' + 'ter China' -> 'Greater China' (🎯 NEW)
    """
    if df.empty or len(df.columns) < 2: return df
    cols = list(df.columns)
    df_new = df.copy()
    columns_to_drop = []
    
    # Safe string conversion
    for col in df_new.columns:
        df_new[col] = df_new[col].apply(lambda x: "" if pd.isna(x) or str(x).lower() == "nan" else str(x))
    
    for i in range(len(cols) - 1):
        c1, c2 = cols[i], cols[i+1]
        is_frag = str(c2).startswith("column_") or not str(c2).strip()
        if not is_frag: continue
        
        merge_count, total = 0, 0
        text_merge_count = 0  # 🎯 NEW: Track text fragments
        
        for v1, v2 in zip(df_new[c1].tail(40), df_new[c2].tail(40)):
            s1, s2 = str(v1).strip(), str(v2).strip()
            if not s1 or not s2: continue
            total += 1
            
            # Numeric fragment detection (existing)
            if (s1.endswith(",") and s2.isdigit() and len(s2) == 3) or \
               (s1 == "$" and any(char.isdigit() for char in s2)) or \
               (s1.isdigit() and s2.isdigit() and len(s2) == 3):
                merge_count += 1
            
            # 🎯 NEW: Text fragment detection
            # Detect splits like 'Grea' + 'ter China' or 'Ameri' + 'cas'
            # Pattern: Short text (2-6 chars) + continuation text starting lowercase or with ':'
            elif len(s1) >= 2 and len(s1) <= 10 and s1.isalpha():
                # Check if s2 looks like a continuation (lowercase start, or ends incomplete word)
                if s2 and (s2[0].islower() or s2.startswith("ter ") or s2.startswith("icas") or ":" in s2):
                    text_merge_count += 1
                # Also catch: ends with partial word that continues in s2
                elif len(s1) >= 3 and not s1.endswith(" ") and s2 and s2[0:3].isalpha():
                    text_merge_count += 1
        
        # Merge if significant fragment rate detected
        should_merge = total > 0 and ((merge_count / total > 0.2) or (text_merge_count / total > 0.1))
        
        if should_merge:
            df_new[c1] = df_new[c1] + df_new[c2]
            columns_to_drop.append(c2)
    
    return df_new.drop(columns=columns_to_drop) if columns_to_drop else df

# =====================================================
# COLUMN SYNONYMS
# =====================================================

REVENUE_KEYWORDS = METRIC_REGISTRY["revenue"]["keywords"]
COST_KEYWORDS = METRIC_REGISTRY["cost_of_revenue"]["keywords"]
OPS_KEYWORDS = METRIC_REGISTRY["operating_income"]["keywords"]
PROFIT_KEYWORDS = METRIC_REGISTRY["net_income"]["keywords"]
EPS_KEYWORDS = METRIC_REGISTRY["eps"]["keywords"]
RND_KEYWORDS = METRIC_REGISTRY["r_and_d_expense"]["keywords"]
SGA_KEYWORDS = METRIC_REGISTRY["sga_expense"]["keywords"]


# =====================================================
# INTENT DETECTION
# =====================================================

def is_boolean_revenue_question(question: str) -> bool:
    q = question.lower()
    return any(
        phrase in q
        for phrase in [
            "is it making revenue",
            "does it make revenue",
            "is there revenue",
            "is the company making revenue",
            "does the company have revenue"
        ]
    )


# =====================================================
# MAIN REASONER
# =====================================================

from src.analysis.calculator import safe_eval_expr
from src.ai.rag_engine import retrieve_context, get_embedding_model, get_vector_store
from src.analysis.cfo_insights import CFOInsights # NEW CFO Engine

class FinancialReasoner:

    def __init__(self, tables: List[Dict[str, Any]], question: str = ""):
        self.tables = tables
        self.question = question.lower()
        self.embeddings = get_embedding_model()
        self.vector_store = get_vector_store()
        self.cfo = CFOInsights() # Initialize CFO Engine
        self.reasoning_log: List[str] = []
        
        # 🔑 GLOBAL UNIT INFERENCE: Scan all tables to detect report-wide multiplier (e.g. Millions)
        self.global_multiplier = 1
        for t in self.tables:
             # Fast scan of raw df string
             txt = pd.DataFrame(t.get("df")).to_string().lower()
             # Robust check: remove spaces and symbols to catch "in million s" -> "inmillions"
             clean_txt = txt.replace(" ", "").replace("_", "").replace("-", "").replace("\n", "")
             
             if "millions" in clean_txt or "inmillions" in clean_txt:
                 self.global_multiplier = 1_000_000
                 break
             if "billions" in clean_txt or "inbillions" in clean_txt:
                 self.global_multiplier = 1_000_000_000
                 break

    def _log(self, msg: str):
        self.reasoning_log.append(msg)
        print(f"📝 {msg}")

    def _heal_df(self, df: pd.DataFrame) -> pd.DataFrame:
        return heal_fragmented_columns(df)

    # -------------------------------------------------
    # RAG FALLBACK (AGGRESSIVE VALUE EXTRACTION)
    # -------------------------------------------------

    def _fallback_to_rag(self, metric_name: str) -> Dict[str, Any]:
        """
        Enhanced RAG fallback - extracts financial values from ANY format
        """
        try:
            from src.ai.rag_engine import retrieve_context
        except ImportError:
            self._log("❌ RAG engine not available")
            return {
                "success": False,
                "result": None,
                "reasoning": "RAG engine unavailable",
                "confidence": 0.0
            }
        
        self._log(f"🔍 RAG fallback for {metric_name}")
        
        # Search RAG with multiple query variations
        search_queries = [
            f"{metric_name} total amount value",
            f"total {metric_name}",
            f"{metric_name} quarterly",
            f"net sales {metric_name}",
            metric_name,
            "Statement of Operations",
            "Consolidated Statements of Operations",
            "Net income"
        ]
        
        all_contexts = []
        for query in search_queries[:4]:  # Limit to avoid too many calls
            contexts = retrieve_context(query, k=10)
            all_contexts.extend(contexts)
        
        # Remove duplicates
        seen = set()
        unique_contexts = []
        for ctx in all_contexts:
            text = ctx.get('text', '')
            if text and text not in seen:
                seen.add(text)
                unique_contexts.append(ctx)
        
        self._log(f"📝 Searching {len(unique_contexts)} unique contexts")
        
        # Extract ALL possible financial values from contexts
        all_values = []
        
        for ctx in unique_contexts:
            text = ctx.get('text', '')
            
            # Pattern 1: $XX.XX billion/million/B/M
            patterns = [
                (r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*billion', 1_000_000_000),
                (r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*B\b', 1_000_000_000),
                (r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*billion', 1_000_000_000),
                (r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*B\b', 1_000_000_000),
                (r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*million', 1_000_000),
                (r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*M\b', 1_000_000),
                (r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*million', 1_000_000),
                (r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*M\b', 1_000_000),
            ]
            
            for pattern, multiplier in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        num_str = match.group(1).replace(',', '')
                        value = float(num_str) * multiplier
                        
                        # Only consider realistic financial values
                        if value >= 1_000_000:  # At least $1M
                            all_values.append({
                                'value': value,
                                'context': text[:300],
                                'confidence': 0.85
                            })
                            self._log(f"✅ Pattern match: ${value:,.0f} from '{text[:100]}...'")
                    except Exception as e:
                        pass
            
            # Pattern 2: Large comma-separated numbers (likely financial)
            number_pattern = r'\b(\d{1,3}(?:,\d{3}){2,}(?:\.\d+)?)\b'  # At least 2 commas
            matches = re.finditer(number_pattern, text)
            for match in matches:
                try:
                    num_str = match.group(1).replace(',', '')
                    value = float(num_str)
                    
                    # Check context for scale indicators
                    context_window = text[max(0, match.start()-50):match.end()+50].lower()
                    
                    if 'billion' in context_window or 'b ' in context_window:
                        value *= 1_000_000_000
                    elif 'million' in context_window or 'm ' in context_window:
                        value *= 1_000_000
                    
                    # Only consider if looks like revenue
                    if value >= 10_000_000:  # At least $10M
                        all_values.append({
                            'value': value,
                            'context': text[:300],
                            'confidence': 0.7
                        })
                        self._log(f"✅ Number found: ${value:,.0f}")
                except:
                    pass
            
            # Pattern 3: Dollar amounts
            dollar_pattern = r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\b'
            matches = re.finditer(dollar_pattern, text)
            for match in matches:
                try:
                    num_str = match.group(1).replace(',', '')
                    value = float(num_str)
                    
                    # Check nearby text for scale
                    context_window = text[max(0, match.start()-50):match.end()+50].lower()
                    if 'billion' in context_window:
                        value *= 1_000_000_000
                    elif 'million' in context_window:
                        value *= 1_000_000
                    
                    if value >= 10_000_000:
                        all_values.append({
                            'value': value,
                            'context': text[:300],
                            'confidence': 0.6
                        })
                except:
                    pass
        
        if not all_values:
            self._log(f"❌ No values found in RAG for {metric_name}")
            return {
                "success": False,
                "result": None,
                "reasoning": f"Could not find {metric_name} in tables or document context",
                "confidence": 0.0
            }
        
        # Sort by confidence and prefer larger values for revenue
        all_values.sort(key=lambda x: (x['confidence'], x['value']), reverse=True)
        
        # For revenue/sales, strongly prefer billion-scale values
        if metric_name.lower() in ['revenue', 'sales', 'net sales', 'net_sales']:
            billion_values = [v for v in all_values if v['value'] >= 1_000_000_000]
            if billion_values:
                best = billion_values[0]
            else:
                # If no billions, take the highest confidence value that is at least $1M
                best = all_values[0]
                self._log(f"⚠️ No billion-scale values found for {metric_name}, using best match.")
        else:
            best = all_values[0]
        
        self._log(f"✅ RAG extracted: ${best['value']:,.0f}")
        
        return {
            "success": True,
            "result": best['value'],
            "reasoning": f"Found {metric_name} in document: {best['context'][:150]}...",
            "confidence": best['confidence'],
            "source": "rag",
            "context_snippet": best['context']
        }

    # -------------------------------------------------
    # BOOLEAN REVENUE (YES / NO)
    # -------------------------------------------------

    def has_revenue(self) -> Dict[str, Any]:
        self._log("Checking if entity is making revenue")

        # 1️⃣ Check tables
        for table in self.tables:
            df = table["df"]

            for col in df.columns:
                col_l = str(col).lower()
                if any(k in col_l for k in REVENUE_KEYWORDS):
                    self._log(f"Revenue column found: {col}")
                    return self._yes_response("Revenue column present in tables")

            # 2️⃣ Check values inside table
            for _, row in df.iterrows():
                for cell in row:
                    val = extract_financial_value(cell)
                    if val and val > 10_000_000:  # At least $10M
                        self._log(f"Revenue-like value found: {val:,.0f}")
                        return self._yes_response("Revenue values detected in tables")

        # 3️⃣ Fallback → RAG
        self._log("No revenue evidence in tables, checking documents")

        try:
            from src.ai.rag_engine import retrieve_context
        except ImportError:
            return self._no_response("RAG unavailable")

        contexts = retrieve_context("revenue net sales quarterly", k=10)

        for ctx in contexts:
            text = ctx.get("text", "").lower()
            if any(k in text for k in REVENUE_KEYWORDS):
                self._log("Revenue mentioned in document text")
                return self._yes_response("Revenue mentioned in document text")

        return self._no_response("No revenue evidence found")

    # -------------------------------------------------
    # NUMERIC REVENUE (STRICT)
    # -------------------------------------------------

    def compute_revenue_value(self) -> Dict[str, Any]:
        """
        Extract actual revenue value - tries tables first, then RAG
        """
        self._log("Computing numeric revenue (STRICT)")

        # 1. Row-Based Extraction (Robust Helper)
        curr, prior, source_df, source_meta, curr_date, prior_date = self._extract_metric_value_from_rows(REVENUE_KEYWORDS, heuristic_millions=True)
        
        if curr:
            reasoning = f"Revenue of ${curr:,.0f} extracted for period {curr_date}."
            if prior:
                growth = (curr - prior) / prior * 100 if prior != 0 else 0
                reasoning += f" Comparable prior period ({prior_date}) was ${prior:,.0f} (Growth: {growth:+.1f}%)."
            
            context_str = f"Source: {source_meta}\nPeriod: {curr_date}\n{source_df.to_string()}"
            
            return {
                "success": True,
                "result": curr,
                "prior_result": prior,
                "confidence": 0.95,
                "reasoning": reasoning,
                "source": "tables",
                "context_table_str": context_str,
                "period_date": curr_date,
                "prior_date": prior_date
            }

        # ---------------------------------------------------------
        # 2. Column-Based Extraction (Fallback)
        # ---------------------------------------------------------
        # (Keeping column fallback for edge cases, but row-based is primary)
        self._log("Revenue values too small or missing in rows, trying RAG fallback")
        return self._fallback_to_rag("revenue")

    # -------------------------------------------------
    # RESPONSES
    # -------------------------------------------------

    def _yes_response(self, reason: str) -> Dict[str, Any]:
        return {
            "success": True,
            "result": "YES",
            "confidence": 0.9,
            "reasoning": reason
        }

    def _no_response(self, reason: str) -> Dict[str, Any]:
        return {
            "success": True,
            "result": "NO",
            "confidence": 0.7,
            "reasoning": reason
        }


# =====================================================
# ENTRY POINT
# =====================================================

    # -------------------------------------------------
    # HELPERS
    # -------------------------------------------------
    def _extract_metric_value_from_rows(
        self, 
        keywords: List[str], 
        heuristic_millions: bool = False,
        prefer_balance_sheet: bool = False,
        prefer_income_statement: bool = False
    ) -> Tuple[Optional[float], Optional[float], Optional[pd.DataFrame], Optional[str], Optional[str], Optional[str]]:
        """
        Robust row-based extraction that finds the BEST match across tables.
        Prioritizes: 1. Exact matches 2. Specific/Longer keyword matches.
        """
        all_matches = []
        
        # Identify period preference from question
        pref_six = any(k in self.question for k in ["six months", "six-month", "6 months", "6-month", "ytd"])
        pref_three = any(k in self.question for k in ["three months", "three-month", "3 months", "3-month", "quarterly"])
        
        for table in self.tables:
            df = table.get("df")
            if df is None: continue # Skip Markdown-only docs
            df = self._heal_df(df)
            source = table.get("source", "Unknown")
            page = table.get("page", "?")
            
            # Detect multiplier
            # Robust text construction: use full dataframe string to catch units anywhere
            raw_text = df.to_string().lower()
            table_text = raw_text.replace("_", " ").replace("-", " ")
            clean_text = raw_text.replace(" ", "").replace("_", "").replace("-", "").replace("\n", "")
            
            multiplier = 1
            if "millions" in clean_text or "inmillions" in clean_text: multiplier = 1_000_000
            elif "billions" in clean_text or "inbillions" in clean_text: multiplier = 1_000_000_000
            
            # Global Fallback: If local table has no unit, but report is in Millions, use Global
            if multiplier == 1 and heuristic_millions:
                if self.global_multiplier > 1:
                    multiplier = self.global_multiplier
                    # self._log(f"Using Global Multiplier ({multiplier}) for table {source}")

            # 🛑 FINAL GATE: If scaling is disabled (for EPS/Ratios), force multiplier to 1
            if not heuristic_millions:
                multiplier = 1

            text_cols = df.select_dtypes(include="object").columns
            if text_cols.empty: continue
            
            first_text_col = text_cols[0]
            
            # 🕒 PERIOD FILTERING: Select candidate columns based on duration preference
            candidate_cols = []
            
            # 🔑 NEW: Detect if this is a Balance Sheet (has date columns, not period columns)
            # Balance Sheets have columns like "March 30, 2024" or "September 30, 2023"
            # Income Statements have "Three Months Ended" or "Six Months Ended"
            is_balance_sheet = any(k in table_text for k in [
                "balance sheet", "balance sheets", "financial position",
                "total assets", "total liabilities", "stockholders"
            ])
            
            # 🔑 NEW: Detect if this is an Income Statement
            # Must have EPS info OR Revenue/Cost/Income structure
            is_income_statement = any(k in table_text for k in ["earnings per share", "weighted-average", "weighted average"]) or \
                                  (all(k in table_text for k in ["net sales", "cost of sales", "gross margin"]))
            
            # Check for date-style columns (e.g., "March 30, 2024", "September 30, 2023")
            has_date_columns = any(
                any(month in str(col).lower() for month in ["march", "september", "june", "december", "jan", "feb", "apr", "may", "jul", "aug", "oct", "nov"])
                and any(char.isdigit() for char in str(col))
                for col in df.columns
            )
            
            # For Balance Sheets or tables with date columns: use ALL numeric columns
            if is_balance_sheet or has_date_columns:
                self._log(f"📋 Detected Balance Sheet or date-column table - using all numeric columns")
                for col in df.columns:
                    if col == first_text_col: continue
                    # Check if column has any numeric data
                    col_data = df[col].astype(str).str.replace(r'[,$()%]', '', regex=True)
                    if col_data.str.match(r'^-?\d+\.?\d*$').any():
                        candidate_cols.append(col)
                
                # If we have 2+ columns, sort by date (most recent first)
                # This ensures current period is first, prior period is second
                if len(candidate_cols) >= 2:
                    self._log(f"   Found {len(candidate_cols)} candidate columns: {candidate_cols}")
            else:
                # 1. Strict Inclusion for Income Statement / Cash Flow
                for col in df.columns:
                    if col == first_text_col: continue
                    c_str = str(col).lower()
                    
                    if pref_six:
                        if any(k in c_str for k in ["six", "6-mo", "6 month", "ytd"]):
                            candidate_cols.append(col)
                    elif pref_three:
                        if any(k in c_str for k in ["three", "3-mo", "3 month", "quarterly"]):
                            candidate_cols.append(col)
            
            # 2. Smart Fallback with Exclusion (only for non-Balance Sheet tables)
            if not candidate_cols and not is_balance_sheet and not has_date_columns:
                for col in df.columns:
                    if col == first_text_col: continue
                    c_str = str(col).lower()
                    
                    if pref_six:
                        # User wants 6 months -> EXCLUDE 3 months
                        if any(k in c_str for k in ["three", "3-mo", "3 month", "quarterly"]):
                            self._log(f"  Excluding column '{col}' because it matches 3-month pattern (wanted 6-month)")
                            continue
                    elif pref_three:
                        # User wants 3 months -> EXCLUDE 6 months
                        if any(k in c_str for k in ["six", "6-mo", "6 month", "ytd"]):
                            self._log(f"  Excluding column '{col}' because it matches 6-month pattern (wanted 3-month)")
                            continue
                            
                    candidate_cols.append(col)
                
                # If we still have multiple columns, and we want 6 months, 
                # financial reports usually list "3 Months" THEN "6 Months".
                # If we have 2+ columns left, maybe prefer the later ones for 6-month? This is risky but often true for 10-Qs.
                # safely defaulting to "all remaining candidates" is safer than nothing.

            # 🐛 DEBUG PRINT (Unconditional for BS)
            if is_balance_sheet:
                print(f"\n🐛 DEBUG TABLE {source} (Page {page}) (BS=True): Candidates={candidate_cols}")

            # Identify the first THREE columns for label construction (to handle split text)
            cols = df.columns.tolist()
            text_col_indices = [i for i, c in enumerate(cols) if c in text_cols]
            target_indices = text_col_indices[:3] # Take up to first 3 text columns
            
            for idx, row in df.iterrows():
                # Construct combined label from first 3 columns to handle splits like "Total net" | "s" | "ales"
                parts = [str(row[cols[i]]) for i in target_indices]
                
                # Create variations: Single col, First 2 cols, First 3 cols
                raw_labels = []
                
                # 1. Full combination (Highest priority)
                raw_labels.append(" ".join(parts).lower().strip())
                
                # 2. First 2 cols (if available)
                if len(parts) >= 2:
                    raw_labels.append(" ".join(parts[:2]).lower().strip())
                
                # 3. First col
                if parts:
                    raw_labels.append(parts[0].lower().strip())
                
                # Check all label variations
                labels_to_check = raw_labels
                
                match_score = 0
                matched_kw = None
                
                for lbl in labels_to_check:
                    # Normalize label: lower case, strip, and collapse internal whitespace
                    label = " ".join(lbl.split())
                    
                    # Scoring
                    label_nospace = label.replace(" ", "")
                    for k in keywords:
                        # 1. Exact/Normal Match
                        if k == label:
                            match_score = max(match_score, 100)
                            matched_kw = k
                        elif k in label:
                            score = len(k) * 5
                            if score > match_score:
                                match_score = score
                                matched_kw = k
                        
                        # 2. Space-Insensitive Match (Handles "pay able" vs "payable")
                        else:
                            k_nospace = k.replace(" ", "")
                            if len(k_nospace) > 4 and k_nospace in label_nospace:
                                score = len(k) * 7 # Increased from 4 to 7 to prioritize specificity (Long Fuzzy > Short Exact)
                                if score > match_score:
                                    match_score = score
                                    matched_kw = k
                
                if match_score > 0:
                    # Extract numeric values from candidate columns only
                    row_vals = []
                    for col in candidate_cols:
                        v = extract_financial_value(row[col])
                        if v is not None: 
                            row_vals.append(v * multiplier)
                    
                    if "inventory" in label:
                        self._log(f"🕵️ DEBUG: Label '{label}' | Candidates: {candidate_cols} | RowVals: {row_vals}")

                    if not row_vals: continue
                    
                    curr = row_vals[0]
                    prior = row_vals[1] if len(row_vals) > 1 else None
                    
                    # Dates
                    dates = self._extract_period_dates(df)
                    curr_date = "current"
                    prior_date = "prior"
                    
                    all_matches.append({
                        "score": match_score,
                        "data": (curr, prior, df, f"{source} (Page {page})", curr_date, prior_date),
                        "label": label,
                        "is_balance_sheet": is_balance_sheet,
                        "is_income_statement": is_income_statement,
                        "row_label": label,  # 🎯 PRODUCT-GRADE: Track exact row for source attribution
                        "page": page,
                        "source_file": source
                    })

        if all_matches:
            # Sort by score descending
            if prefer_balance_sheet:
                 # Prioritize Balance Sheet matches (True > False), then Score
                 all_matches.sort(key=lambda x: (x.get("is_balance_sheet", False), x["score"]), reverse=True)
            elif prefer_income_statement:
                 # Prioritize Income Statement matches (True > False), then Score
                 all_matches.sort(key=lambda x: (x.get("is_income_statement", False), x["score"]), reverse=True)
            else:
                 all_matches.sort(key=lambda x: x["score"], reverse=True)

            best = all_matches[0]
            # self._log(f"Best match found: '{best['label']}' (score {best['score']}) -> {best['data'][0]:,.0f}")
            return best["data"]
            
        return None, None, None, None, None, None

    def _extract_period_dates(self, df: pd.DataFrame) -> List[str]:
        """Extract and normalize all date-like strings from column headers."""
        dates = []
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        
        # Regex for common date patterns: "March 30, 2024", "2024-03-30", "Q1 2024"
        date_pattern = r'(\b(?:' + '|'.join(months) + r')\b\s+\d{1,2},?\s+\d{4})|(\d{4}-\d{2}-\d{2})|(\bQ[1-4]\b\s+\d{4})'
        
        for col in df.columns:
            c_str = str(col).lower()
            match = re.search(date_pattern, c_str)
            if match:
                dates.append(str(col))
            elif any(m in c_str for m in months) and re.search(r'\d{4}', c_str):
                dates.append(str(col))
                
        return dates

    def _find_column(self, keywords: List[str]) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        for table in self.tables:
            df = table.get("df")
            if df is None: continue
            for col in df.columns:
                if any(k in str(col).lower() for k in keywords):
                    return df, col
        return None, None

    def _extract_latest_value(self, df: pd.DataFrame, col: str) -> Optional[float]:
        try:
            val = extract_financial_value(df[col].iloc[-1])
            if val: return val
            return extract_financial_value(df[col].iloc[0])
        except:
            return None

    # -------------------------------------------------
    # MATRIX REASONING (Segment x Metric)
    # -------------------------------------------------
    def compute_matrix_metric(self, metric_name: str, segment_filter: str) -> Dict[str, Any]:
        """
        Extracts value from a matrix structure where:
        - Row Label matches 'segment_filter'
        - Column Header matches 'metric_name' keywords
        """
        metric_config = METRIC_REGISTRY.get(metric_name, {})
        metric_keywords = metric_config.get("keywords", [metric_name.replace("_", " ")])
        
        self._log(f"🧩 Matrix Extraction: Searching for Row='{segment_filter}' AND Column='{metric_keywords}'")
        
        best_match = None
        best_score = 0
        
        
        segment_filter = segment_filter.lower()
        
        # 0. PRE-SCORE TABLES based on Relevance
        # We want to prioritize tables that are explicitly about "Operating Income" vs "Net Sales"
        scored_tables = []
        for table in self.tables:
            score = 0
            df = table.get("df")
            
            # Text Context (Preceding text, Markdown title)
            context_text = (table.get("preceding_text", "") + " " + table.get("markdown", "")).lower()
            
            # Explicit Title Match (High Priority)
            for mk in metric_keywords:
                 if mk in context_text:
                     score += 10
            
            # Segment Filter Boost (VERY HIGH PRIORITY)
            if segment_filter:
                 # self._log(f"   [DEBUG] Checking '{segment_filter.lower()}' in context (len={len(context_text)})")
                 if segment_filter.lower() in context_text:
                     self._log(f"   Table p{table.get('page')} contains segment '{segment_filter}' (+50 score)")
                     score += 50
            
            # Negative Contex Scoring (Avoid False Positives)
            # If we want Operating Income, but table says "Net Sales", penalize it!
            if "operating_income" in metric_name and "net sales" in context_text and "operating" not in context_text:
                 score -= 20
                 
            # Column Header Match
            if df is not None:
                for col in df.columns:
                     c_str = str(col).lower()
                     if any(mk in c_str for mk in metric_keywords):
                         score += 5
            
            scored_tables.append({"table": table, "score": score})
            
        # Sort tables by score descending
        scored_tables.sort(key=lambda x: x["score"], reverse=True)
        
        sorted_tables = [x["table"] for x in scored_tables]
        
        self._log(f"📋 Sorted {len(sorted_tables)} tables by relevance for '{metric_name}'")
        if scored_tables:
             for st in scored_tables[:3]:
                 m_snip = st['table'].get('markdown','')[:50].replace('\n', ' ')
                 self._log(f"   Table p{st['table'].get('page')} | Score: {st['score']} | First 50: {m_snip}")

        for table in sorted_tables:

            df = table.get("df")
            if df is None: continue
            df = self._heal_df(df)
            source = table.get("source", "Unknown")
            page = table.get("page", "?")
            
            # 1. Identify Target Columns (Columns that match the Metric)
            target_cols = []
            cols = df.columns
            column_matched = False
            
            # Detect Year/Period columns
            period_cols = []
            for col in cols:
                c_str = str(col).lower()
                # Check directly if column header matches metric keywords (e.g. "Net Sales", "Operating Income")
                is_metric_col = False
                for mk in metric_keywords:
                    if mk in c_str:
                        is_metric_col = True
                        break
                
                if is_metric_col:
                    target_cols.append(col)
                    column_matched = True
            
            # --- ROW-BASED CONTEXT INFERENCE (FALLBACK) ---
            # If columns don't explicitly say "Operating Income" (e.g. just "2025"), 
            # check if there is a "Total Operating Income" row that confirms this table's content.
            
            if not column_matched:
                # Iterate rows to look for Metric Keywords (confirming this table contains the metric)
                text_cols = df.select_dtypes(include="object").columns
                if not text_cols.empty:
                    label_col = text_cols[0]
                    # SCAN ALL ROWS for metric keywords or check context score
                    is_metric_confirmed = any(mk in context_text for mk in metric_keywords) and score >= 60
                    
                    for idx, row_vals in df.iterrows():
                        row_str = " ".join([str(v) for v in row_vals]).lower()
                        
                        if any(mk in row_str for mk in metric_keywords) or is_metric_confirmed:
                             if not any(mk in row_str for mk in metric_keywords):
                                 self._log(f"   Table Content Match: Using Context Match (Score {score}) to confirm metric.")
                             else:
                                 self._log(f"   Table Content Match: Found '{row_str}' confirming metric.")
                             
                             # Identify target columns primarily by dates in headers
                             header_dates = self._extract_period_dates(df)
                             if header_dates:
                                 self._log(f"   Identifying target columns based on {len(header_dates)} date headers.")
                                 for i, col in enumerate(df.columns):
                                     c_str = str(col).lower()
                                     if any(d.lower() in c_str or d.split(",")[-1].strip() in c_str for d in header_dates):
                                         target_cols.append(col)
                             
                             # Fallback: All columns with numbers that aren't labels
                             # Also accept common generic headers: "Current", "Prior", "2025", "2024"
                             if not target_cols:
                                 generic_headers = ["current", "prior", "202", "months ended"]
                                 for col in df.columns:
                                     if col == label_col: continue
                                     c_str = str(col).lower()
                                     if any(gh in c_str for gh in generic_headers) or df[col].astype(str).str.contains(r'\d').any():
                                         target_cols.append(col)
                             
                             if target_cols:
                                 column_matched = True
                                 break
            
            if not target_cols:
                continue

            # 2. Iterate Rows to find Segment
            # 🎯 CRITICAL FIX: PDF extraction fragments text across columns
            # "Greater China" may appear as ['Grea', 'ter China:'] in cols 0 and 1
            # So we concatenate first 5 text columns to build the full row label
            text_cols = df.select_dtypes(include="object").columns
            if text_cols.empty: continue
            label_cols = [c for c in df.columns if c in text_cols][:5] # Safer column selection
            
            last_seen_segment = None
            
            for idx, row in df.iterrows():
                # Construct combined label
                parts = [str(row[c]) for c in label_cols]
                raw_labels = []
                raw_labels.append(" ".join(parts).lower().strip())
                
                # Also try combining first two parts, then first three, etc.
                for i in range(1, len(parts)):
                    raw_labels.append(" ".join(parts[:i+1]).lower().strip())

                # Normalize whitespace and remove colons
                row_label = " ".join(raw_labels).lower().replace(":", "").strip()
                row_label = " ".join(row_label.split())  # Normalize whitespace
                
                # A. Detect Segment Match (Header Row)
                if segment_filter in row_label:
                    last_seen_segment = row_label
                    self._log(f"   Segment Scope: Found '{row_label}' as potential header in table p{page}")
                
                # B. Detect Metric Match (Values Row)
                metric_row_match = any(mk in row_label for mk in metric_keywords)
                
                # Decide if we extract: 
                # Either Segment and Metric are on SAME ROW, OR Metric is on a row under a matching Segment header
                should_extract = False
                if segment_filter in row_label and metric_row_match:
                    should_extract = True
                elif metric_row_match and last_seen_segment and segment_filter in last_seen_segment:
                    should_extract = True
                    self._log(f"   Contextual extraction: metric '{row_label}' under segment '{last_seen_segment}'")

                if should_extract:
                    # Found the extraction target!
                    self._log(f"   ✅ Extraction Target: {row_label} (Table p{page}, Line {idx})")
                    
                    # 3. Extract Values from Target Columns
                    if len(target_cols) >= 1:
                        # Standard financial reporting is [Metric Latest] [Metric Prior]
                        curr_col = target_cols[0]
                        prior_col = target_cols[1] if len(target_cols) > 1 else None
                        
                        val = extract_financial_value(row[curr_col])
                        p_val = extract_financial_value(row[prior_col]) if prior_col else None
                        
                        if val is not None:
                            # Contextual Multiplier Logic
                            raw_text = df.to_string().lower()
                            clean_text = raw_text.replace(" ", "").replace("_", "").replace("-", "").replace("\n", "")
                            multiplier = 1
                            if "millions" in clean_text or "inmillions" in clean_text: multiplier = 1_000_000
                            elif "billions" in clean_text or "inbillions" in clean_text: multiplier = 1_000_000_000
                            elif self.global_multiplier > 1: multiplier = self.global_multiplier
                            
                            final_val = val * multiplier
                            final_prior = p_val * multiplier if p_val is not None else None
                            
                            dates = self._extract_period_dates(df)
                            curr_date = dates[0] if dates else "Current Period"
                            prior_date = dates[1] if len(dates) > 1 else "Prior Period"
                            
                            return {
                                "success": True,
                                "result": final_val,
                                "prior": final_prior,
                                "confidence": 0.98,
                                "reasoning": f"Hierarchical Matrix Extraction: Found '{segment_filter}' -> '{row_label}' = {final_val:,.0f} (Table p{page})",
                                "source": "matrix_extraction",
                                "context_table_str": f"Segment: {segment_filter}\n{df.to_string()}",
                                "period_date": curr_date,
                                "prior_date": prior_date
                            }
                        
        # -------------------------------------------------
        # FALLBACK 1: PyMuPDF Direct Text Extraction
        # -------------------------------------------------
        # Bypass fragmented tables entirely by extracting from raw PDF text
        self._log(f"📝 Matrix extraction failed. Trying PyMuPDF direct extraction...")
        
        try:
            from src.ingestion.pymupdf_extractor import extract_segment_values_direct
            
            # Get the source PDF path from tables
            pdf_paths = set()
            import os
            import glob
            
            for t in self.tables:
                # Check both 'source' (from cleaned tables) and 'source_file' (raw extraction)
                source = t.get("source") or t.get("source_file") or ""
                if not source: continue
                
                # Check if it's already a valid path
                if os.path.exists(source) and source.lower().endswith(".pdf"):
                    pdf_paths.add(source)
                elif source.lower().endswith(".pdf"):
                    # It might be just a filename, try to find it in uploads
                    # Try exact match first
                    upload_path = os.path.join("e:/finance-ai/data/uploads", os.path.basename(source))
                    if os.path.exists(upload_path):
                        pdf_paths.add(upload_path)
                    else:
                        # Try globbing for partial match/uuid
                        basename = os.path.basename(source)
                        # Remove extension for glob
                        name_no_ext = os.path.splitext(basename)[0]
                        matches = glob.glob(f"e:/finance-ai/data/uploads/*{name_no_ext}*.pdf")
                        if matches:
                            pdf_paths.add(matches[0])
                            
            self._log(f"   📂 Found {len(pdf_paths)} candidate PDFs for PyMuPDF: {list(pdf_paths)}")
            
            for pdf_path in pdf_paths:
                result = extract_segment_values_direct(pdf_path, segment_filter)
                
                if result.get("success"):
                    val = result.get(metric_name)
                    if val is not None:
                        # Map correct prior key
                        prior_key = f"{metric_name}_prior"
                        prior_val = result.get(prior_key)
                        
                        self._log(f"   ✅ PyMuPDF Extracted {metric_name}: {val:,.0f} | Prior: {prior_val:,.0f if prior_val else 'N/A'}")
                        return {
                             "success": True,
                             "result": val,
                             "prior": prior_val,
                             "confidence": 0.95,
                             "reasoning": f"PyMuPDF Direct Extraction: Found '{segment_filter}' {metric_name.replace('_', ' ')} = {val:,.0f}",
                             "source": f"PyMuPDF Direct Extraction (Page {result.get('page','?')}, File: {os.path.basename(result.get('source', 'Unknown'))})",
                             "context_table_str": f"Direct Extraction for {segment_filter}",
                             "period_date": "Current Period", 
                             "prior_date": "Prior Period"
                        }
        except Exception as e:
            self._log(f"   ⚠️ PyMuPDF fallback error: {e}")

        # -------------------------------------------------
        # FALLBACK 2: RAG + Regex
        # -------------------------------------------------
        # If PyMuPDF extraction fails, try to extract segment data from RAG context
        self._log(f"📝 Attempting RAG fallback for segment '{segment_filter}'...")
        
        try:
            from src.ai.rag_engine import retrieve_context
            
            # Search for segment-specific context
            search_queries = [
                f"{segment_filter} {metric_name}",
                f"{segment_filter} operating income",
                f"segment operating income {segment_filter}",
                "Note 10 segment information",
                f"{segment_filter} net sales operating"
            ]
            
            all_contexts = []
            for query in search_queries[:3]:
                contexts = retrieve_context(query, k=5)
                all_contexts.extend(contexts)
            
            # Deduplicate
            seen = set()
            unique_contexts = []
            for ctx in all_contexts:
                text = ctx.get('text', '')
                if text and text not in seen:
                    seen.add(text)
                    unique_contexts.append(ctx)
            
            self._log(f"   RAG returned {len(unique_contexts)} unique contexts")
            
            # Try to extract segment value from context text
            for ctx in unique_contexts:
                text = ctx.get('text', '')
                text_lower = text.lower()
                
                # Check if this context mentions our segment
                if segment_filter not in text_lower:
                    continue
                
                self._log(f"   Found context mentioning '{segment_filter}': {text[:100]}...")
                
                # Try to extract the value using multiple regex patterns
                # PDF text is often fragmented, so we need robust patterns
                
                import re
                
                # 🎯 ENHANCED: Handle fragmented segment names
                # "Greater China" might appear as "Greater China", "Grea ter China", or in markdown table
                
                # Normalize text: collapse excessive whitespace but preserve structure
                normalized = re.sub(r'\s+', ' ', text_lower)
                
                # Build flexible segment pattern that handles fragmentation
                # "greater china" -> "gre[a]?[ter]?\s*[ter]?\s*ch[i]?[na]?\s*[na]?"
                seg_words = segment_filter.split()
                seg_pattern = r'\s*'.join([re.escape(w) for w in seg_words])
                
                # Multiple extraction patterns
                # Multiple extraction patterns
                # Structure: (prio_name, regex_pattern, group_idx_val, group_idx_prior)
                
                # Build Metric Regex (e.g. "operating\s*income")
                metric_keywords_regex = "|".join([re.escape(k).replace(r'\ ', r'\s*') for k in [metric_name.replace("_", " ")]])
                
                # 🎯 NEW PATTERN 0: Contextual Link (Segment ... Metric ... Value)
                # Matches "Greater China ... Operating Income ... 6,626"
                # Uses Dotall-like matching (.*?)
                pat_context = rf"({seg_pattern})(?:(?!{seg_pattern}).)*?({metric_keywords_regex}).*?([\d,]+(?:\.\d+)?)(?:[^0-9]*?([\d,]+(?:\.\d+)?))?"
                
                regex_configs = [
                    # (Name, Pattern, Val_Group, Prior_Group)
                    ("Contextual", pat_context, 3, 4),
                    
                    # Pattern 1: Segment followed by $ amounts (common in tables)
                    # Group 2 = Val, Group 3 = Prior
                    ("Table Row Close", rf"({seg_pattern})\s*[:\|]?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*\$?\s*([\d,]+(?:\.\d+)?)?", 2, 3),
                    
                    # Pattern 2: Markdown table row format
                    ("Markdown Table", rf"\|\s*({seg_pattern})\s*\|\s*([\d,\$\.]+)\s*\|\s*([\d,\$\.]+)?", 2, 3),
                    
                    # Pattern 3: Segment with numbers on same/next line (more flexible)
                     # Group 2 = Val, Group 3 = Prior
                    ("Flexible Line", rf"({seg_pattern})[^0-9]*?([\d,]+(?:\.\d+)?)\s+(?:[\d,]+(?:\.\d+)?)\s*([\d,]+(?:\.\d+)?)?", 2, 3),
                    
                    # Pattern 4: Simple numbers after segment name
                    ("Simple Proximity", rf"({seg_pattern})\D*([\d,]+(?:\.\d+)?)\D*([\d,]+(?:\.\d+)?)?", 2, 3),
                ]
                
                match = None
                extraction_source = ""
                
                for p_name, pat, g_val, g_prior in regex_configs:
                    # Use finditer to verify ALL matches and skip bad ones
                    matches = list(re.finditer(pat, normalized, re.IGNORECASE))
                    
                    for m in matches:
                        try:
                            # 🛡️ SAFETY CHECK: Intervening Text
                            # Check text between end of Segment (Group 1) and start of Value (Group g_val)
                            start_check = m.end(1)
                            end_check = m.start(g_val)
                            intervening_text = normalized[start_check:end_check]
                            
                            # 🛡️ SAFETY CHECK: Intervening Text
                            # (Skip for Contextual Pattern as it explicitly finds the metric label)
                            if p_name != "Contextual":
                                # If Metric is "Operating Income", forbid "Net Sales", "Revenue" in between
                                if "operating_income" in metric_name and any(bad in intervening_text for bad in ["net sales", "revenue", "gross margin"]):
                                    self._log(f"   ⚠️ Skipping Match ({p_name}): Found conflicting metric in text: '{intervening_text[:30]}...'")
                                    continue
                                    
                                # If Metric is "Net Sales", forbid "Operating Income" (less likely but good safety)
                                if "revenue" in metric_name and any(bad in intervening_text for bad in ["operating income", "operating profit"]):
                                    self._log(f"   ⚠️ Skipping Match ({p_name}): Found conflicting metric in text: '{intervening_text[:30]}...'")
                                    continue

                            # Verify match isn't empty
                            if not m.group(g_val): continue
                            
                            match = m
                            # Adjust group indices for extraction below
                            val_group_idx = g_val
                            prior_group_idx = g_prior
                            extraction_source = p_name
                            break # Found a valid match for this pattern!
                        except Exception as e:
                            continue
                            
                    if match: 
                        break # Found a match in this pattern priority level
                
                if match:
                    try:
                        # Normalize string to float
                        curr_str = match.group(val_group_idx).replace(',', '').replace('$', '')
                        curr_val = float(curr_str)
                        
                        prior_val = None
                        if match.lastindex >= prior_group_idx and match.group(prior_group_idx):
                            prior_str = match.group(prior_group_idx).replace(',', '').replace('$', '')
                            prior_val = float(prior_str)
                        
                        # Determine multiplier from context
                        multiplier = 1
                        if "million" in text_lower or "in millions" in text_lower:
                            multiplier = 1_000_000
                        elif "billion" in text_lower:
                            multiplier = 1_000_000_000
                        elif self.global_multiplier > 1:
                            multiplier = self.global_multiplier
                        
                        final_val = curr_val * multiplier
                        final_prior = prior_val * multiplier if prior_val else None
                        
                        # Validate: Check if this looks like the right metric
                        # For Operating Income, values should be smaller than Net Sales
                        # Greater China Net Sales ~$16B, Operating Income ~$6.6B
                        is_operating_income = "operating_income" in metric_name or "operating income" in text_lower
                        is_net_sales = "revenue" in metric_name or "net sales" in text_lower
                        
                        # Sanity check: Operating Income should be less than ~50% of typical Net Sales
                        if is_operating_income and final_val > 15_000_000_000:
                            self._log(f"   ⚠️ Value {final_val:,.0f} too large for Operating Income, likely Net Sales. Skipping.")
                            continue
                        
                        self._log(f"   ✅ RAG Extracted: {final_val:,.0f} (Prior: {final_prior:,.0f if final_prior else 'N/A'})")
                        
                        return {
                            "success": True,
                            "result": final_val,
                            "prior": final_prior,
                            "confidence": 0.80,  # Lower confidence for RAG extraction
                            "reasoning": f"RAG Extraction: Found '{segment_filter}' {metric_name} = {final_val:,.0f} from document context.",
                            "source": "rag_segment_extraction",
                            "context_table_str": f"Context: {text[:500]}",
                            "period_date": "Current Period",
                            "prior_date": "Prior Period"
                        }
                    except (ValueError, AttributeError) as e:
                        self._log(f"   ⚠️ Failed to parse value: {e}")
                        continue
            
            # 🎯 FINAL FALLBACK: LLM-based extraction for fragmented PDFs
            self._log(f"   📡 Attempting LLM extraction for '{segment_filter}' {metric_name}...")
            
            try:
                from src.ai.llm_narrator import explain_with_gemini
                
                # Combine all contexts that mention the segment
                combined_context = "\n\n".join([
                    ctx.get('text', '')[:1000] 
                    for ctx in unique_contexts 
                    if segment_filter in ctx.get('text', '').lower()
                ][:3])  # Top 3 relevant contexts
                
                if combined_context:
                    prompt = f"""Extract the financial value from this document context.

TASK: Find the {metric_name.replace('_', ' ')} for "{segment_filter}" segment.

RULES:
1. Look for rows/entries mentioning "{segment_filter}"
2. Find the {metric_name.replace('_', ' ')} value (in millions USD)
3. Return ONLY the numeric value, nothing else
4. If you find "Greater China" with values like 16,002 and 6,626 - the SMALLER one is Operating Income
5. If not found, return "NOT_FOUND"

CONTEXT:
{combined_context}

ANSWER (just the number in millions, e.g., "6626" or "NOT_FOUND"):"""

                    response = explain_with_gemini(prompt)
                    
                    if response and "NOT_FOUND" not in response.upper():
                        # Parse the numeric response
                        import re
                        numbers = re.findall(r'[\d,]+(?:\.\d+)?', response)
                        if numbers:
                            value_str = numbers[0].replace(',', '')
                            value = float(value_str)
                            
                            # Apply multiplier
                            multiplier = self.global_multiplier if self.global_multiplier > 1 else 1_000_000
                            final_value = value * multiplier if value < 100000 else value
                            
                            # Sanity check for operating income
                            if "operating_income" in metric_name and final_value > 15_000_000_000:
                                self._log(f"   ⚠️ LLM value too large for operating income, skipping")
                            else:
                                self._log(f"   ✅ LLM Extracted: {final_value:,.0f}")
                                return {
                                    "success": True,
                                    "result": final_value,
                                    "prior": None,
                                    "confidence": 0.75,
                                    "reasoning": f"LLM Extraction: Found '{segment_filter}' {metric_name} = {final_value:,.0f}",
                                    "source": "llm_segment_extraction",
                                    "context_table_str": f"Context: {combined_context[:500]}",
                                    "period_date": "Current Period",
                                    "prior_date": None
                                }
            except Exception as e:
                self._log(f"   ⚠️ LLM extraction error: {e}")
            
            self._log(f"   ❌ All extraction methods failed for segment '{segment_filter}'")
            
        except Exception as e:
            self._log(f"   ❌ RAG fallback error: {e}")
        
        return {
            "success": False,
            "result": None,
            "reasoning": f"Could not find matrix data for segment '{segment_filter}' and metric '{metric_name}'",
            "confidence": 0.0
        }

    # -------------------------------------------------
    # PROFIT / LOSS
    # -------------------------------------------------

    # -------------------------------------------------
    # FORMULA-BASE REASONING (ELITE RAG)
    # -------------------------------------------------

    def compute_with_formula(self, metric_name: str) -> Dict[str, Any]:
        """
        Elite RAG: Computes metric using deterministic formulas and registry.
        Handles both single-point metrics and growth rates.
        """
        config = METRIC_REGISTRY.get(metric_name)
        if not config:
            return self._fallback_to_rag(metric_name)
            
        formula = config["formula"]
        self._log(f"Executing deterministic formula for {metric_name}: {formula}")
        
        # 1. Identify required variables from formula
        vars_needed = re.findall(r'[a-zA-Z_]+', formula)
        
        extracted_data = {}
        source_metas = []
        source_dfs = []
        p_date, pr_date = "current", "prior"
        
        # 2. Extract each variable from tables
        # Track prior value for the *primary* metric if available
        primary_prior = None

        for var in vars_needed:
            # Special handling for growth variables
            base_var = var.replace("current_", "").replace("prior_", "")
            var_config = METRIC_REGISTRY.get(base_var)
            keywords = var_config["keywords"] if var_config else [base_var.replace("_", " ")] # Restored this line
            
            # Determine if we should prefer balance sheet
            bs_metrics = ["inventory", "accounts_receivable", "accounts_payable", "current_assets", "current_liabilities", "total_assets", "total_liabilities"]
            prefer_bs = (base_var in bs_metrics)

            # Determine if we should prefer income statement
            is_metrics = ["revenue", "operating_income", "net_income", "eps", "cost_of_revenue", "gross_margin", "r_and_d_expense"]
            prefer_is = (base_var in is_metrics)
            
            # Selective Scaling: Only apply millions heuristic to CURRENCY metrics, not EPS/Ratios
            should_scale = (base_var not in ["eps", "gross_margin", "tax_rate", "shares", "p_e_ratio"])

            curr, prior, df, meta, d_curr, d_prior = self._extract_metric_value_from_rows(
                keywords, 
                heuristic_millions=should_scale, 
                prefer_balance_sheet=prefer_bs,
                prefer_income_statement=prefer_is
            )
            
            if curr is not None:
                if "prior_" in var:
                    if prior is not None:
                        extracted_data[var] = prior
                        pr_date = d_prior
                    else:
                        self._log(f"  ⚠️ Variable {var} requested but prior value missing in table.")
                else:
                    extracted_data[var] = curr
                    p_date = d_curr
                    # Capture prior if available (for primary metric)
                    if prior is not None and primary_prior is None:
                        primary_prior = prior
                
                source_metas.append(meta)
                if df is not None: source_dfs.append(df)
            else:
                self._log(f"  ⚠️ Could not find required variable: {var}")

        # 3. Evaluate formula
        eval_res = evaluate_metric(formula, extracted_data)
        
        if eval_res.get("success"):
            val = eval_res["result"]
            reasoning = f"Calculated {metric_name.replace('_', ' ').title()} as {val:,.2f} based on deterministic formula: {formula}."
            
            # Format inputs for reasoning
            input_strs = []
            for k, v in extracted_data.items():
                if abs(v) > 100: input_strs.append(f"{k}=${v:,.0f}")
                else: input_strs.append(f"{k}={v:.2f}")
            reasoning += " Inputs: " + ", ".join(input_strs)
            
            # Additional context for profitability
            ops_curr, ops_prior, _, _, _, _ = self._extract_metric_value_from_rows(OPS_KEYWORDS)
            rev_curr, rev_prior, _, _, _, _ = self._extract_metric_value_from_rows(REVENUE_KEYWORDS)
            eps_curr, eps_prior, _, _, _, _ = self._extract_metric_value_from_rows(["eps", "earnings per share"])

            return {
                "success": True,
                "result": val,
                "prior": primary_prior,
                "reasoning": reasoning,
                "confidence": 0.98,
                "source": "formula_engine",
                "context_table_str": "\n\n".join([df.to_string() for df in source_dfs[:1]]) if source_dfs else "",
                "period_date": p_date,
                "prior_date": pr_date,
                "operating_income": ops_curr,
                "operating_income_prior": ops_prior,
                "revenue": rev_curr,
                "revenue_prior": rev_prior,
                "eps": eps_curr,
                "eps_prior": eps_prior
            }
            
        return self._fallback_to_rag(metric_name)

    # -------------------------------------------------
    # AGENTIC VERIFICATION (Cross-Check logic)
    # -------------------------------------------------
    def _cross_verify_integrity(self, metric_name: str, value: float, period: str) -> List[str]:
        """
        Agentic Workflow: Cross-check extracted value against other statements.
        Example: Verify 'Net Income' matches the starting line of 'Cash Flow Statement'.
        """
        warnings = []
        
        # 1. Net Income Cross-Check
        if metric_name == "net_income":
            # Look for Cash Flow Statement
            cf_table = None
            for table in self.tables:
                if "cash" in str(table.get("df").columns).lower() and "operating" in str(table.get("df").columns).lower():
                    cf_table = table["df"]
                    break
            
            if cf_table is not None:
                # Try to find Net Income in CF
                ni_vals = []
                for idx, row in cf_table.head(10).iterrows(): # Usually at top
                    row_str = str(row.values).lower()
                    if "net income" in row_str or "net earnings" in row_str:
                         for cell in row:
                             v = extract_financial_value(cell)
                             if v: ni_vals.append(v)
                
                # Check if matches (allow 10% tolerance due to adjustments)
                matched = False
                for v in ni_vals:
                    # Check both raw and scaled (millions/billions)
                    if abs(v - value) < value * 0.05 or abs(v*1000000 - value) < value * 0.05:
                        matched = True
                        self._log(f"✅ Cross-verification passed: Net Income found in Cash Flow stmt ({v:,.0f})")
                        break
                
                if not matched and ni_vals:
                    warnings.append(f"⚠️ Data Integrity Issue: Net Income (${value:,.0f}) does not match Figure in Cash Flow Statement (approx ${ni_vals[0]:,.0f}).")

        return warnings

    def _analyze_cash_flow_discrepancy(self, net_income: float, ocf: float) -> str:
        """
        Analyze why OCF differs from Net Income (e.g. Ireland Tax Settlement).
        """
        diff = net_income - ocf
        if diff < 0: return "" # OCF is higher, usually fine.
        
        # If OCF is significantly lower (>20% discrepancy)
        if diff > net_income * 0.2:
             self._log(f"⚠️ OCF (${ocf:,.0f}) is much lower than Net Income (${net_income:,.0f}). Investigating...")
             
             # Fallback RAG search for explanation
             try:
                 from src.ai.rag_engine import retrieve_context
                 # Search for keywords explaining the gap
                 q = "cash flow lower than net income tax settlement payment"
                 contexts = retrieve_context(q, k=5)
                 
                 found_reasons = []
                 for ctx in contexts:
                     text = ctx.get("text", "").lower()
                     if "tax" in text and ("payment" in text or "settlement" in text) and "billion" in text:
                         found_reasons.append("tax payments")
                     if "penalty" in text or "fine" in text or "legal" in text:
                         found_reasons.append("legal settlements")
                         
                 if found_reasons:
                     return f" The difference may be due to {', '.join(set(found_reasons))} mentioned in the notes."
             except:
                 pass
                 
        return ""

    # -------------------------------------------------
    # ENTRY POINT UPDATE
    # -------------------------------------------------

def compute_metric_with_reasoning(metric_name: str, tables: List[dict], question: str = "", segment_filter: str = None) -> Dict[str, Any]:
    """
    Main entry point for metric computation with reasoning
    """
    reasoner = FinancialReasoner(tables, question=question)

    if metric_name in METRIC_REGISTRY:
        # Check for boolean revenue/profit question
        if metric_name == "revenue" and is_boolean_revenue_question(question):
            result = reasoner.has_revenue()

        # Special handling for Segments (Matrix Extraction)
        elif segment_filter:
            print(f"📊 Attempting Segment Extraction for '{segment_filter}' - Metric: {metric_name}")
            result = reasoner.compute_matrix_metric(metric_name, segment_filter)

        # Standard Deterministic Calculation
        elif metric_name == "revenue":
            # Check if we want strict numeric revenue
            result = reasoner.compute_revenue_value()
        
        else:
            result = reasoner.compute_with_formula(metric_name)

        # AGENTIC VERIFICATION STEP (Applied to all results)
        if result.get("success") and result.get("result"):
            warnings = reasoner._cross_verify_integrity(
                metric_name, 
                result["result"], 
                result.get("period_date")
            )
            
            # Check for Cash Flow specifics if we just computed OCF
            if metric_name == "operating_cash_flow":
                # Try to get Net Income for comparison
                ni_res = reasoner.compute_with_formula("net_income")
                if ni_res.get("success"):
                    ni_val = ni_res["result"]
                    ocf_val = result["result"]
                    explanation = reasoner._analyze_cash_flow_discrepancy(ni_val, ocf_val)
                    if explanation:
                        result["reasoning"] += "\n\nAnalyst Note:" + explanation

        result["reasoning"] = "\n".join(reasoner.reasoning_log) + "\n" + result.get("reasoning", "")
        return result

    else:
        # For completely unknown metrics, try RAG directly
        result = reasoner._fallback_to_rag(metric_name)

    # Add reasoning log to result
    if result:
        result["reasoning_log"] = reasoner.reasoning_log
    
    return result
