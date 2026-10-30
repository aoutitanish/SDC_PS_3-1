import sys
import os
import time
import json
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from backend.main import app
from backend.app.core.config import settings

client = TestClient(app)

print(f"============================================================")
print(f"LATENCY & CONVERSATIONAL STATEMENTS BENCHMARK TEST")
print(f"LLM Provider: {settings.LLM_PROVIDER}")
print(f"LLM Base URL: {settings.LLM_BASE_URL}")
print(f"LLM Model: {settings.LLM_MODEL}")
print(f"Max Output Tokens Setting: {settings.LLM_MAX_TOKENS}")
print(f"============================================================\n")

results = []

def run_latency_test_case(test_num: int, title: str, query: str, session_id: str, endpoint: str = "/api/chat"):
    print(f"--- TEST {test_num}: {title} ---")
    print(f"Query: '{query}'")
    t0 = time.time()
    
    if endpoint == "/api/chat/stream":
        res = client.post("/api/chat/stream", json={"message": query, "language": "en", "session_id": session_id})
        t1 = time.time()
        elapsed = round(t1 - t0, 2)
        lines = res.text.split("\n\n")
        tokens = []
        meta = None
        for line in lines:
            if line.startswith("data: "):
                c = line[6:].strip()
                if c == '{"type": "done"}':
                    continue
                try:
                    p = json.loads(c)
                    if p.get("type") == "token":
                        tokens.append(p.get("token", ""))
                    elif p.get("type") == "metadata":
                        meta = p
                except Exception:
                    pass
        answer = "".join(tokens)
        intent = meta.get("intent") if meta else "unknown"
    else:
        res = client.post("/api/chat", json={"message": query, "language": "en", "session_id": session_id})
        t1 = time.time()
        elapsed = round(t1 - t0, 2)
        data = res.json()
        answer = data.get("answer", "")
        intent = data.get("intent", "")

    word_count = len(answer.split())
    approx_tokens = int(word_count * 1.3)
    
    print(f"Status Code: {res.status_code}")
    print(f"Response Time: {elapsed} seconds")
    print(f"Intent Detected: {intent}")
    print(f"Answer Word Count: {word_count} words (~{approx_tokens} tokens)")
    print(f"Answer Preview:\n{answer}\n")
    
    results.append({
        "test_num": test_num,
        "title": title,
        "query": query,
        "elapsed_sec": elapsed,
        "intent": intent,
        "word_count": word_count,
        "approx_tokens": approx_tokens,
        "answer": answer
    })

if __name__ == "__main__":
    # Test 1: Simple farming tip
    run_latency_test_case(1, "Simple Farming Tip (Telangana)", "Give me one simple farming tip for a farmer in Telangana.", "latency_sess_1", "/api/chat/stream")

    # Test 2: Recommendation question
    run_latency_test_case(2, "Crop Recommendation Question", "I have black soil and moderate water availability. Which crops should I consider?", "latency_sess_2", "/api/chat")

    # Multi-turn session for Test 3 & 4
    session_id_multi = "latency_multi_sess"

    # Test 3: Statement only
    run_latency_test_case(3, "Conversational Statement Only", "My soil is black and I have moderate water availability.", session_id_multi, "/api/chat")

    # Test 4: Follow-up question
    run_latency_test_case(4, "Follow-up Question using Context", "What crop should I consider?", session_id_multi, "/api/chat")

    print("\n============================================================")
    print("SUMMARY OF BENCHMARK RESULTS")
    print("============================================================")
    for r in results:
        print(f"Test {r['test_num']} ({r['title']}): {r['elapsed_sec']}s | Intent: {r['intent']} | ~{r['approx_tokens']} tokens")
