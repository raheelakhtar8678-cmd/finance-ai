
import re

def test_regex():
    # The snippet from Note 10
    text = """
    | Greater China: | | | | |
    | Net sales $ | 16,002 $ | 16,372 $ | 34,515 $ | 37,191 |
    | Operating income $ | 6,626 $ | 6,700 $ | 14,786 $ | 15,322 |
    """.strip().lower() # simulate RAG usually lowercases or normalized
    
    segment_filter = "Greater China"
    metric_name = "operating_income"
    
    # Normalize text as done in the code
    normalized = re.sub(r'\s+', ' ', text)
    print(f"Normalized Text: {normalized}")
    
    seg_words = segment_filter.split()
    seg_pattern = r'\s*'.join([re.escape(w) for w in seg_words])
    
    metric_regex = r"operating\s*income"

    regex_configs = [
        # (Name, Pattern, Val_Group, Prior_Group)
        ("Contextual", rf"({seg_pattern})(?:(?!{seg_pattern}).)*?({metric_regex}).*?([\d,]+(?:\.\d+)?)(?:[^0-9]*?([\d,]+(?:\.\d+)?))?", 3, 4),
        ("Table Row Close", rf"({seg_pattern})\s*[:\|]?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*\$?\s*([\d,]+(?:\.\d+)?)?", 2, 3),
        ("Markdown Table", rf"\|\s*({seg_pattern})\s*\|\s*([\d,\$\.]+)\s*\|\s*([\d,\$\.]+)?", 2, 3),
        ("Flexible Line", rf"({seg_pattern})[^0-9]*?([\d,]+(?:\.\d+)?)\s+(?:[\d,]+(?:\.\d+)?)\s*([\d,]+(?:\.\d+)?)?", 2, 3),
        ("Simple Proximity", rf"({seg_pattern})\D*([\d,]+(?:\.\d+)?)\D*([\d,]+(?:\.\d+)?)?", 2, 3),
    ]

    for p_name, pat, g_val, g_prior in regex_configs:
        print(f"\nTesting Pattern ({p_name}): {pat}")
        
        matches = list(re.finditer(pat, normalized, re.IGNORECASE))
        print(f"Found {len(matches)} matches.")
        
        for match in matches:
            if not match.group(g_val): continue
            
            val_str = match.group(g_val).replace(',', '').replace('$', '')
            val = float(val_str)
            
            # Check intervening text
            start_check = match.end(1)
            try:
                end_check = match.start(g_val)
                intervening = normalized[start_check:end_check]
            except:
                intervening = ""
                
            print(f"  -> Match Value: {val}")
            print(f"  -> Intervening Text: {repr(intervening)}")
            
            # Validate Intervening Text
            conflicts = ["net sales", "revenue", "gross margin"]
            if p_name != "Contextual":
                if metric_name == "operating_income" and any(c in intervening for c in conflicts):
                    print(f"     ⚠️ SKIPPING: Found conflicting metric keywords in text: {intervening}")
                    continue
            
            print(f"     ✅ VALID MATCH: {val}")
            if val == 6626:
                print("     🎉 SUCCESS: Found correct Operating Income!")
            elif val == 16002:
                print("     🚨 FAILURE: Still picking Net Sales")


if __name__ == "__main__":
    test_regex()
