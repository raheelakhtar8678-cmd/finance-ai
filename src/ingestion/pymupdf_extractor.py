# src/ingestion/pymupdf_extractor.py
"""
PyMuPDF-based PDF table extractor.
Alternative to pdfplumber for better handling of complex financial tables.
"""

import fitz  # PyMuPDF
import pandas as pd
import re
from typing import List, Dict, Any, Optional
import pymupdf4llm

def extract_markdown_with_pymupdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract full document content as Markdown using PyMuPDF4LLM.
    This provides the best raw material for RAG and Table Cleaning.
    
    Returns:
        List containing a single dict with the full markdown content.
        (List format to maintain compatibility with other extractors returning tables)
    """
    try:
        md_text = pymupdf4llm.to_markdown(file_path)
        
        # Return as a single "table" object representing the whole doc
        # This keeps the pipeline consistent
        return [{
            "df": None, # No DataFrame for full text
            "page": 0,
            "markdown": md_text,
            "preceding_text": "",
            "following_text": "",
            "source": file_path,
            "method": "pymupdf4llm"
        }]
    except Exception as e:
        print(f"[PyMuPDF4LLM] Extraction error: {e}")
        return []



def extract_tables_pymupdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from PDF using PyMuPDF.
    Better at handling complex financial tables with many columns.
    
    Returns:
        List of dicts with {df, page, markdown, preceding_text, following_text}
    """
    results = []
    
    try:
        doc = fitz.open(file_path)
        
        for page_num, page in enumerate(doc, start=1):
            # Method 1: Try PyMuPDF's built-in table finder (v1.23+)
            try:
                tables = page.find_tables()
                for table_idx, table in enumerate(tables.tables):
                    df = table.to_pandas()
                    if df is not None and not df.empty:
                        # Clean column names
                        df.columns = [str(c).strip() if c else f"col_{i}" for i, c in enumerate(df.columns)]
                        
                        results.append({
                            "df": df,
                            "page": page_num,
                            "markdown": df.to_markdown(index=False) if hasattr(df, 'to_markdown') else df.to_string(),
                            "preceding_text": "",  # Can enhance later
                            "following_text": "",
                            "source": file_path,
                            "method": "pymupdf_table"
                        })
            except AttributeError:
                # Older PyMuPDF version - use text extraction
                pass
            
            # Method 2: Text-based extraction for Note 10 segment data
            # This catches text tables that aren't detected as proper tables
            text = page.get_text()
            
            # Look for segment data patterns
            segment_patterns = [
                r"(Americas|Europe|Greater China|Japan|Rest of Asia Pacific)\s*\$?\s*([\d,]+)\s*\$?\s*([\d,]+)",
            ]
            
            for pattern in segment_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches and len(matches) >= 3:  # At least 3 segments found
                    # Build a DataFrame from the matches
                    data = []
                    for match in matches:
                        segment = match[0]
                        val1 = match[1].replace(",", "")
                        val2 = match[2].replace(",", "") if len(match) > 2 else ""
                        data.append({
                            "Segment": segment,
                            "Current": val1,
                            "Prior": val2
                        })
                    
                    df = pd.DataFrame(data)
                    results.append({
                        "df": df,
                        "page": page_num,
                        "markdown": df.to_markdown(index=False),
                        "preceding_text": "Segment Information (Text Extraction)",
                        "following_text": "",
                        "source": file_path,
                        "method": "pymupdf_text_regex"
                    })
                    break  # One segment table per page is enough
        
        doc.close()
        print(f"[PyMuPDF] Extracted {len(results)} tables from {file_path}")
        
    except Exception as e:
        print(f"[PyMuPDF] Extraction error: {e}")
    
    return results


def extract_segment_values_direct(file_path: str, segment_name: str) -> Dict[str, Any]:
    """
    Direct extraction of segment values using PyMuPDF text search.
    Bypasses table parsing entirely - useful for fragmented PDFs.
    
    Args:
        file_path: Path to PDF
        segment_name: e.g., "Greater China"
    
    Returns:
        Dict with {net_sales, operating_income, success}
    """
    result = {
        "net_sales": None,
        "operating_income": None,
        "success": False,
        "source": file_path
    }
    
    try:
        doc = fitz.open(file_path)
        
        
        candidates = []
        
        for page in doc:
            text = page.get_text()
            text_lower = text.lower()
            
            # Check if this page mentions the segment
            if segment_name.lower() not in text_lower:
                continue
            
            # Score this page's relevance
            score = 0
            if "segment" in text_lower: score += 10
            if "note 10" in text_lower: score += 20
            if "operating income" in text_lower: score += 5
            
            page_result = {
                "net_sales": None,
                "operating_income": None,
                "page": page.number + 1,
                "score": score
            }
            
            print(f"[PyMuPDF] Found '{segment_name}' on page {page.number + 1} (Score: {score})")
            
            # Strategy 1: Labeled Vertical Search
            idx = text_lower.find(segment_name.lower())
            if idx != -1:
                window = text[idx:idx+800] # Increased window
                print(f"   Strategy 1 Window from Page {page.number+1}:\n{window[:200]}...")
                
                # 🔑 FIXED REGEX v3: Find ALL comma-separated numbers after keyword
                # PDF text: "Net sales\n$\n16,002\n$\n16,372\n..."
                # Strategy: Extract all numbers, take first 2 as current and prior
                
                def extract_numbers_after(keyword, text, count=2):
                    """Find all comma-separated numbers after a keyword."""
                    # Find keyword position
                    idx = text.lower().find(keyword.lower())
                    if idx == -1:
                        return []
                    # Get text after keyword
                    after_text = text[idx:]
                    # Find all numbers with commas (like 16,002)
                    numbers = re.findall(r'(\d{1,3}(?:,\d{3})+)', after_text)
                    return numbers[:count]
                
                # Extract Net Sales
                ns_numbers = extract_numbers_after("net sales", window)
                if ns_numbers:
                    val = float(ns_numbers[0].replace(",", ""))
                    page_result["net_sales"] = val * 1_000_000
                    if len(ns_numbers) > 1:
                        pval = float(ns_numbers[1].replace(",", ""))
                        page_result["net_sales_prior"] = pval * 1_000_000
                        print(f"   ✅ NS: {val:,.0f} | Prior: {pval:,.0f}")
                
                # Extract Operating Income
                oi_numbers = extract_numbers_after("operating income", window)
                if oi_numbers:
                    val = float(oi_numbers[0].replace(",", ""))
                    page_result["operating_income"] = val * 1_000_000
                    if len(oi_numbers) > 1:
                        pval = float(oi_numbers[1].replace(",", ""))
                        page_result["operating_income_prior"] = pval * 1_000_000
                        print(f"   ✅ OI: {val:,.0f} | Prior: {pval:,.0f}")

            # Strategy 2: Horizontal/Adjacent Search (Fallback)
            if not page_result["net_sales"] and not page_result["operating_income"]:
                try:
                    segment_pattern = rf"{re.escape(segment_name)}[:\s]*\$?\s*([\d,]+)[.\s]*\$?\s*([\d,]+)?"
                    match = re.search(segment_pattern, text, re.IGNORECASE)
                    if match and match.group(1):
                        val1 = float(match.group(1).replace(",", ""))
                        val2 = float(match.group(2).replace(",", "")) if match.group(2) else None
                        if val2 and val1 > val2:
                            page_result["net_sales"] = val1 * 1_000_000
                            page_result["operating_income"] = val2 * 1_000_000
                        elif val2:
                            page_result["net_sales"] = val2 * 1_000_000
                            page_result["operating_income"] = val1 * 1_000_000
                        else:
                            if "net sales" in text_lower[:text_lower.find(segment_name.lower()) + 100]:
                                page_result["net_sales"] = val1 * 1_000_000
                            else:
                                page_result["operating_income"] = val1 * 1_000_000
                except (ValueError, AttributeError):
                    pass  # Continue to next page if this one fails
            
            if page_result["net_sales"] or page_result["operating_income"]:
                if page_result["net_sales"] and page_result["operating_income"]:
                    page_result["score"] += 50 # Big bonus for finding both
                candidates.append(page_result)

        doc.close()
        
        # Pick the best candidate
        if candidates:
            best = max(candidates, key=lambda x: x["score"])
            result["net_sales"] = best["net_sales"]
            result["net_sales_prior"] = best.get("net_sales_prior")
            result["operating_income"] = best["operating_income"]
            result["operating_income_prior"] = best.get("operating_income_prior")
            result["success"] = True
            f_cur = lambda x: f"{x:,.0f}" if x is not None else "N/A"
            print(f"   Selected Best Candidate from Page {best['page']} (Score: {best['score']})")
            print(f"   Net Sales: {f_cur(result['net_sales'])} | Prior: {f_cur(result.get('net_sales_prior'))}")
            print(f"   Operating Income: {f_cur(result['operating_income'])} | Prior: {f_cur(result.get('operating_income_prior'))}")

        
    except Exception as e:
        print(f"[PyMuPDF] Direct extraction error: {e}")
    
    return result
