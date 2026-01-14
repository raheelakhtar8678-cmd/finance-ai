import re
from pathlib import Path

# Paths to the cleaned markdown files
path_2024 = Path(r"E:\finance-ai\data\raw\4b7fbf86-37be-4e59-bed7-fda7ec8404ef.md")
path_2025 = Path(r"E:\finance-ai\data\raw\618374cc-0b7e-4007-8f49-da55758e5811.md")

def extract_greater_china_oi(md_text, year_label):
    # Regex to find the Segment Information table row for Greater China
    # Pattern: | Greater China | Sales | Sales | Change | Sales | Sales | Change |
    # followed by | Operating income | Value | Value | ...
    
    # Actually, based on my previous inspection:
    # | Greater China: | | | | ...
    # | Net sales $ | ...
    # | Operating income $ | 6,626 $ | 6,700 $ ...
    
    # We need to find the "Greater China" section first, then the "Operating income" line within it.
    
    # Simplified parser:
    # 1. Split into lines
    lines = md_text.split('\n')
    found_china = False
    
    for i, line in enumerate(lines):
        if "Greater China" in line and "**" in line: # Header usually bolded in my cleaner
             found_china = True
             continue
        
        if found_china:
            if "Operating income" in line:
                # Extract numbers
                # | Operating income $ | 6,626 $ | 6,700 $ ...
                nums = re.findall(r'[\d,]+', line)
                # Filter out small single digits that might be flags? No, just grab big numbers.
                # Remove commas
                values = [int(n.replace(',', '')) for n in nums if n.replace(',','').isdigit()]
                
                # In Q2 reports, usually: [Current Q, Prev Q, Current 6M, Prev 6M]
                # We want "Three Months Ended". Usually the first column.
                if len(values) >= 1:
                    return values[0]
            
            # If we hit another segment header, stop (e.g. "Japan")
            if "Japan" in line or "Rest of Asia Pacific" in line:
                break
                
    return None

def answer_question():
    print("--- Question Answering Simulation ---")
    print("Q: What was the operating income for 'Greater China' in Q2 2024 vs Q2 2025?")
    
    # 1. Extract 2024 Value from 2024 Report
    # Note: The 2024 report contains Q2 2024 data (Current) and Q2 2023 (Prior)
    text_2024 = path_2024.read_text(encoding='utf-8')
    val_2024_report = extract_greater_china_oi(text_2024, "2024")
    
    # 2. Extract 2025 Value from 2025 Report
    # Note: The 2025 report contains Q2 2025 data (Current) AND Q2 2024 data (Prior)
    text_2025 = path_2025.read_text(encoding='utf-8')
    val_2025_report = extract_greater_china_oi(text_2025, "2025")
    
    print(f"\n[Extraction]")
    print(f"2024 Report (Q2 2024): ${val_2024_report} million (Found in 2024 file)")
    print(f"2025 Report (Q2 2025): ${val_2025_report} million (Found in 2025 file)")
    
    # Special Check: Does 2025 report also list 2024 as prior year?
    # val_2025_report is likely the first column (2025). 
    # Let's see if we can get the second column from 2025 report which should be 2024.
    
    if val_2024_report and val_2025_report:
        diff = val_2025_report - val_2024_report
        print(f"\n[Analysis]")
        print(f"2024 Value: {val_2024_report}")
        print(f"2025 Value: {val_2025_report}")
        print(f"Change: {diff}")
        
        print(f"\n[Final Answer]")
        print(f"The operating income for Greater China in the three months ended March 30, 2024 was ${val_2024_report:,} million.")
        print(f"In the same period for 2025 (ended March 29, 2025), it was ${val_2025_report:,} million.")
        if diff < 0:
             print(f"This represents a decrease of ${abs(diff)} million.")
        else:
             print(f"This represents an increase of ${diff} million.")

if __name__ == "__main__":
    answer_question()
