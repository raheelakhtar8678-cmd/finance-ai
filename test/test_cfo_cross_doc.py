
from src.analysis.comparison_engine import MultiTableComparator

# Mock tables don't matter as much because we are testing _generate_summary directly
# But we need to instantiate the class
comparator = MultiTableComparator([])

def test_cross_doc_cfo():
    print("\n🧐 Testing CFO Cross-Doc Advisory...")
    
    # Mock Results from compare_metric
    results = [
        {
            "source": "Report_2024.pdf",
            "value": 100,
            "period": "March 30, 2024",
            "confidence": 1.0
        },
        {
            "source": "Report_2025.pdf",
            "value": 150, # Growth!
            "period": "March 29, 2025",
            "confidence": 1.0
        }
    ]
    
    summary = comparator._generate_summary("revenue", results)
    
    print("-" * 50)
    print(summary)
    print("-" * 50)
    
    if "CFO STRATEGIC ADVISORY" in summary:
        print("✅ SUCCESS: CFO Advisory section present.")
    else:
        print("❌ FAILURE: CFO Advisory section missing.")
        
    if "Growth Signal" in summary:
        print("✅ SUCCESS: Correct 'Growth Signal' advice (100 -> 150).")
    else:
        print("❌ FAILURE: Incorrect advice text.")

if __name__ == "__main__":
    test_cross_doc_cfo()
