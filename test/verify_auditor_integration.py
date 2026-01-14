# test/verify_auditor_integration.py
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app logic (might need to handle the demo.launch if it runs on import)
# Ideally app.py should guard the launch.
# But looking at the file content, it ends with demo.launch() which will BLOCK.
# We need to test the logic WITHOUT importing app.py directly if it blocks.
# OR we modify app.py to guard the launch.

# Let's Modify app.py to guard launch first, otherwise this test will hang.
# But I already edited app.py. Let's inspect if I can just import functionality.
# If I import app, it runs demo.launch()... that's bad.

# PLAN:
# 1. Setup App State
# Mock gradio before importing app
from unittest.mock import MagicMock
sys.modules["gradio"] = MagicMock()
sys.modules["gradio.components"] = MagicMock()

import app

def verify_integration():
    print("🧪 Verifying Auditor Integration in App...")
    
    # 1. Setup App State
    app.indexed = True
    
    # 2. Mock the RAG Engine's ask() function
    # app.ask is imported from src.ai.rag_engine
    # We need to patch it where it is used in app.py
    
    app.ask = MagicMock(return_value={
        "answer": "Revenue was $10 million but Operating Income was $20 million.",
        "note": "Extracted from Page 1."
    })
    
    # 3. Call the App's Ask Function
    print("   Invoking ask_question() with mocked faulty data...")
    answer, context = app.ask_question("Analyze profit hierarchy")
    
    print(f"   📝 Answer Received:\n{answer}")
    
    # 4. Verify Auditor Intervention
    if "Auditor Warning" in answer and "Logic Error" in answer:
        print("\n✅ SUCCESS: Auditor correctly intercepted the answer and appended a warning!")
    else:
        print("\n❌ FAILED: Auditor warning not found in answer.")
        sys.exit(1)

if __name__ == "__main__":
    verify_integration()
