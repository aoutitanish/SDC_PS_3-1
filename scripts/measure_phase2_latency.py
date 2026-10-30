import asyncio
import time
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.api.chat import process_chat_intent
from backend.app.core.session_memory import session_memory
from backend.app.data_engine.schemas import FarmProfileInput, LocationInput

QUERIES = [
    {
        "query": "What is the ideal soil pH for cotton?",
        "desc": "General crop fact query with saved farm profile (should not force farm profile)",
        "farm": FarmProfileInput(state="Telangana", district="Warangal", soil_type="Black Soil")
    },
    {
        "query": "What crops suit Kashmir?",
        "desc": "Explicit Kashmir query with saved Telangana farm (should use Kashmir only)",
        "farm": FarmProfileInput(state="Telangana", district="Warangal", soil_type="Black Soil")
    },
    {
        "query": "Which crop should I grow for my farm in Kurnool with black soil?",
        "desc": "Farm recommendation with missing irrigation/season (should ask single follow-up)",
        "farm": None
    }
]

async def run_benchmark():
    results = []
    print("=" * 70)
    print("KRISHIMITRA PHASE 2 - LIVE INFERENCE LATENCY BENCHMARK (Ollama qwen3.5:9b)")
    print("=" * 70)
    
    for item in QUERIES:
        q = item["query"]
        desc = item["desc"]
        farm = item["farm"]
        
        session_memory._sessions.clear()
        sess_id = f"bench_{int(time.time()*1000)}"
        
        print(f"\nEvaluating: '{q}'")
        print(f"Scenario: {desc}")
        
        t0 = time.perf_counter()
        res = await process_chat_intent(
            message=q,
            language="en",
            session_id=sess_id,
            req_farm_profile=farm
        )
        total_wall_s = time.perf_counter() - t0
        
        answer = res[0]
        sources = res[1]
        follow_up = getattr(res, "follow_up", None)
        chips = getattr(res, "quick_replies", None)
        metrics = getattr(res, "latency_metrics", {})
        
        print(f"Total Wall Clock Time: {total_wall_s:.2f}s")
        print(f"Metrics: {metrics}")
        print(f"Answer Length: {len(answer)} chars")
        print(f"Sources Count: {len(sources)}")
        print(f"Follow-up: {follow_up}")
        print(f"Quick-reply chips: {chips}")
        print("-" * 50)
        print("Generated Answer Preview:")
        print(answer[:350] + ("..." if len(answer) > 350 else ""))
        
        results.append({
            "query": q,
            "wall_clock_s": round(total_wall_s, 2),
            "chars": len(answer),
            "metrics": metrics,
            "follow_up": follow_up,
            "chips": chips,
            "sources": len(sources)
        })
        
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY:")
    for r in results:
        print(f"- '{r['query'][:40]}...': {r['wall_clock_s']}s (Length: {r['chars']} chars, Follow-up: {'Yes' if r['follow_up'] else 'No'})")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
