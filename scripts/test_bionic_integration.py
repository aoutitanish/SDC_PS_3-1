import sys
import os
import asyncio
import json
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from backend.main import app
from backend.app.services.llm_service import llm_service
from backend.app.core.config import settings

print(f"Current LLM_PROVIDER: {settings.LLM_PROVIDER}")
print(f"Current LLM_BASE_URL: {settings.LLM_BASE_URL}")
print(f"Current LLM_MODEL: {settings.LLM_MODEL}")

client = TestClient(app)

def test_models_endpoint():
    print("\n--- CHECK 1: Bionic Dependency Check (GET /v1/models) ---")
    r = httpx.get(f"{settings.LLM_BASE_URL}/models", timeout=10.0)
    print(f"Status Code: {r.status_code}")
    data = r.json()
    print(f"Models: {json.dumps(data, indent=2)}")
    model_ids = [m["id"] for m in data.get("data", [])]
    assert settings.LLM_MODEL in model_ids, f"Model {settings.LLM_MODEL} not found in Bionic models list!"
    print(f"SUCCESS: {settings.LLM_MODEL} is present in Bionic models.")

def test_chat_stream_case1():
    print("\n--- TEST 1: Simple farming tip for Telangana ---")
    payload = {
        "message": "Give me one simple farming tip for a farmer in Telangana.",
        "language": "en",
        "session_id": "bionic_test_sess_1"
    }
    res = client.post("/api/chat/stream", json=payload)
    print(f"Status Code: {res.status_code}")
    print("Stream output snippet:")
    lines = res.text.split("\n\n")
    tokens = []
    metadata = None
    for line in lines:
        if line.startswith("data: "):
            content = line.replace("data: ", "").strip()
            if content == '{"type": "done"}':
                continue
            try:
                parsed = json.loads(content)
                if parsed.get("type") == "token":
                    tokens.append(parsed.get("token", ""))
                elif parsed.get("type") == "metadata":
                    metadata = parsed
            except Exception:
                pass
    full_answer = "".join(tokens)
    print(f"Metadata: {json.dumps(metadata, indent=2)}")
    print(f"Full Answer:\n{full_answer}")
    assert len(full_answer.strip()) > 0, "Response answer was empty!"

def test_chat_case2():
    print("\n--- TEST 2: Agriculture / RAG Question ---")
    payload = {
        "message": "I have black soil and limited irrigation. Which crops should I consider?",
        "language": "en",
        "session_id": "bionic_test_sess_2"
    }
    res = client.post("/api/chat", json=payload)
    print(f"Status Code: {res.status_code}")
    data = res.json()
    print(f"Intent: {data.get('intent')}")
    print(f"Sources: {json.dumps(data.get('sources'), indent=2)}")
    print(f"Answer:\n{data.get('answer')}")
    assert data.get("success") is True
    assert len(data.get("answer", "")) > 0, "Response answer was empty!"

def test_chat_case3_conversation_memory():
    print("\n--- TEST 3: Multi-turn Conversation Memory ---")
    session_id = "bionic_test_memory_sess"
    
    print("\nTurn 1: 'My soil is black.'")
    res1 = client.post("/api/chat", json={
        "message": "My soil is black.",
        "language": "en",
        "session_id": session_id
    })
    data1 = res1.json()
    print(f"Turn 1 Intent: {data1.get('intent')}")
    print(f"Turn 1 Answer:\n{data1.get('answer')}")

    print("\nTurn 2: 'What crop should I consider?'")
    res2 = client.post("/api/chat", json={
        "message": "What crop should I consider?",
        "language": "en",
        "session_id": session_id
    })
    data2 = res2.json()
    print(f"Turn 2 Intent: {data2.get('intent')}")
    print(f"Turn 2 Answer:\n{data2.get('answer')}")
    assert data2.get("success") is True
    assert len(data2.get("answer", "")) > 0

if __name__ == "__main__":
    test_models_endpoint()
    test_chat_stream_case1()
    test_chat_case2()
    test_chat_case3_conversation_memory()
    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
