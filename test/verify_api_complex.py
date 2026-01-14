import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    # 1. Upload Files
    files = [
        ("files", ("2024_report.pdf", open(r"E:\finance-ai\data\raw\4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf", "rb"), "application/pdf")),
        ("files", ("2025_report.pdf", open(r"E:\finance-ai\data\raw\618374cc-0b7e-4007-8f49-da55758e5811.pdf", "rb"), "application/pdf"))
    ]
    
    print("📤 Uploading files...")
    resp = requests.post(f"{BASE_URL}/upload", files=files)
    if resp.status_code != 200:
        print(f"❌ Upload failed: {resp.text}")
        return
        
    session_id = resp.json()["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # 2. Query
    question = "What was the operating income for 'Greater China' in the three months ended March 30, 2024, and how much did it change in the same period for 2025?"
    print(f"❓ Asking: {question}")
    
    q_resp = requests.post(f"{BASE_URL}/query", json={
        "session_id": session_id,
        "question": question
    })
    
    print(f"📥 Response Code: {q_resp.status_code}")
    json_resp = q_resp.json()
    print(f"📄 Response Body: {json_resp}")
    
    answer = json_resp.get("answer", "")
    reasoning = json_resp.get("reasoning", "") # If exposed
    
    if "6,626" in answer or "6626" in answer:
        print("🎉 SUCCESS: Found correct Operating Income ($6,626)!")
    elif "16,002" in answer or "16002" in answer:
        print("🚨 FAILURE: Returned Net Sales ($16,002) instead of Operating Income!")
    else:
        print(f"⚠️ Value check inconclusive. Check full answer: {answer}")


if __name__ == "__main__":
    test_api()
