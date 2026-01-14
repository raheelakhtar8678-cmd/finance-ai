import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TableCleaner:
    def __init__(self):
        pass

    def is_table_row(self, line: str) -> bool:
        """
        Heuristic: line contains at least 2 distinct numbers or currency symbols.
        Refined to avoid false positives on sentences with years (e.g. "ended 2023 ... 2024")
        """
        # Exclude common sentence structures? 
        # For now, strict number pattern: $?d,ddd.dd
        # Count numbers.
        numbers = re.findall(r'[\(\$]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?', line)
        
        # Additional filter: if line is very long and mostly text, it might not be a table row.
        # But financial table rows can be long "Net income per share...".
        # Let's trust the number count for now, maybe increase to 3 if many false positives?
        # PyMuPDF4LLM output usually isolates these well.
        return len(numbers) >= 2

    def clean_text(self, text: str) -> str:
        lines = text.split('\n')
        cleaned_lines = []
        in_table = False
        
        # Pre-process: tag lines as 'row' or 'text'
        tagged_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                 if not tagged_lines or tagged_lines[-1]['type'] != 'empty':
                     tagged_lines.append({'text': '', 'type': 'empty'})
                 continue
            
            is_row = self.is_table_row(stripped)
            tagged_lines.append({'text': stripped, 'type': 'row' if is_row else 'text'})

        i = 0
        while i < len(tagged_lines):
            line = tagged_lines[i]
            
            if line['type'] == 'row':
                if not in_table:
                    in_table = True
                    cleaned_lines.append("<!-- TABLE START -->")
                
                # Formatter
                # Split by number lookahead
                parts = re.split(r'(?=\s+[\(\$]?\d)', line['text'])
                parts = [p.strip() for p in parts if p.strip()]
                cleaned_lines.append("| " + " | ".join(parts) + " |")
            
            elif line['type'] == 'text':
                 if in_table:
                     # Lookahead for subheader validity
                     is_sub_header = False
                     for k in range(i + 1, len(tagged_lines)):
                         if tagged_lines[k]['type'] == 'empty':
                             continue
                         if tagged_lines[k]['type'] == 'row':
                             is_sub_header = True
                         break # Stop at first non-empty
                     
                     if is_sub_header:
                         # Sub-header row
                         cleaned_lines.append(f"| **{line['text']}** | | | | |") 
                     else:
                         # End of table
                         in_table = False
                         cleaned_lines.append("<!-- TABLE END -->")
                         cleaned_lines.append(line['text'])
                 else:
                     cleaned_lines.append(line['text'])
                     
            else: # empty
                 if in_table:
                     should_close = True
                     for k in range(i + 1, len(tagged_lines)):
                         if tagged_lines[k]['type'] == 'empty': continue
                         
                         if tagged_lines[k]['type'] == 'row': 
                             should_close = False 
                         elif tagged_lines[k]['type'] == 'text':
                             # valid subheader check
                             is_sub = False
                             for m in range(k + 1, len(tagged_lines)):
                                 if tagged_lines[m]['type'] == 'empty': continue
                                 if tagged_lines[m]['type'] == 'row':
                                     is_sub = True
                                 break
                             
                             if is_sub:
                                 should_close = False
                                 
                         break 
                     
                     if should_close:
                         in_table = False
                         cleaned_lines.append("<!-- TABLE END -->")
                 else:
                     cleaned_lines.append("")
            
            i += 1

        if in_table:
            cleaned_lines.append("<!-- TABLE END -->")

        return "\n".join(cleaned_lines)


def clean_all_tables(tables: list) -> list:
    """
    Apply TableCleaner to a list of table dictionaries.
    """
    cleaner = TableCleaner()
    cleaned_tables = []
    
    for table in tables:
        # If the table has raw markdown content, clean it
        # We flag it coming from pymupdf4llm to be sure
        if "markdown" in table and table.get("method") == "pymupdf4llm":
            raw_text = table["markdown"]
            cleaned_text = cleaner.clean_text(raw_text)
            table["markdown"] = cleaned_text
            cleaned_tables.append(table)
        else:
            # Pass through existing tables
            cleaned_tables.append(table)
            
    return cleaned_tables
