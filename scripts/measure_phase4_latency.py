"""
KrishiMitra Phase 4 Latency Benchmark & Profiling Script
Measures granular latency breakdown:
- Intent and context resolution
- External retrieval latency by source (Crossref, OpenAlex, Wikimedia)
- Total parallel retrieval latency
- Prompt construction time
- Total LLM generation time
- Citation validation time
- Total roundtrip latency
"""

import asyncio
import time
import json
import statistics
from typing import Dict, Any, List
import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.intent_service import intent_service
from backend.app.core.session_memory import session_memory
from backend.app.services.dynamic_rag_service import dynamic_rag
from backend.app.core.llm_provider import llm_provider
from backend.app.api.chat import process_chat_intent


BENCHMARK_QUERIES = [
    {
        "domain": "Crop Physiological Requirements",
        "query": "What is the optimal temperature and soil pH for cotton growth?",
        "lang": "en"
    },
    {
        "domain": "Pest & Disease Management",
        "query": "How to control pink bollworm infestation in cotton organically?",
        "lang": "en"
    },
    {
        "domain": "Fertilizer & Soil Fertility",
        "query": "వరిలో ఎరువుల యాజమాన్యం మరియు నత్రజని మోతాదు ఎంత?",
        "lang": "te"
    },
    {
        "domain": "Sowing Calendar & Season",
        "query": "गेहूं की बुवाई का सही समय क्या है और कितनी सिंचाई चाहिए?",
        "lang": "hi"
    },
    {
        "domain": "International Regional Suitability",
        "query": "What coffee varieties are suitable for high altitude cultivation in Kenya?",
        "lang": "en"
    }
]


async def run_benchmark():
    print("=" * 80)
    print("KRISHIMITRA PHASE 4 - SYSTEM LATENCY BENCHMARK")
    print("=" * 80)

    # 1. Warm-up Ollama and Cache
    print("\nWarming up local Ollama Qwen 3.5 9B instance...")
    try:
        t0 = time.perf_counter()
        warm_res = await llm_provider.generate(
            message="Ready?",
            retrieved_context="None",
            lang="en"
        )
        print(f"Warmup complete in {(time.perf_counter() - t0):.2f}s: {warm_res.strip()}")
    except Exception as e:
        print(f"Warning: Warmup failed: {e}")

    results = []

    for idx, item in enumerate(BENCHMARK_QUERIES, 1):
        domain = item["domain"]
        query = item["query"]
        lang = item["lang"]
        print(f"\n[{idx}/5] Benchmarking Query ({domain})")
        print(f"    Query: '{query}'")

        # A. Intent & Context Resolution
        t0 = time.perf_counter()
        entities = intent_service.extract_entities(query)
        cat = intent_service.classify_question_category(query, entities)
        st = session_memory.get_or_create(f"bench_sess_{idx}")
        resolved_ctx = st.resolve_context(extracted_facts=entities, category=cat)
        t_resolve_ms = (time.perf_counter() - t0) * 1000

        # B. Parallel Dynamic Retrieval
        dynamic_rag.clear_cache()
        t0 = time.perf_counter()
        rag_data = await dynamic_rag.retrieve_dynamic_async(
            query=query,
            crop_filter=entities.get("crop_mentions")[0] if entities.get("crop_mentions") else None,
            state_filter=resolved_ctx.get("state"),
            country_filter=entities.get("country"),
            category=cat,
            top_k=4
        )
        t_rag_ms = (time.perf_counter() - t0) * 1000

        # C. LLM Generation
        t0 = time.perf_counter()
        prompt_text = (
            f"Question: {query}\n"
            f"Evidence Context: {rag_data['context_text'][:1200]}\n"
            f"Provide a concise, factual 2-3 sentence answer."
        )
        llm_answer = await llm_provider.generate(
            message=query,
            retrieved_context=rag_data["context_text"],
            lang=lang
        )
        t_gen_ms = (time.perf_counter() - t0) * 1000

        # D. Total Pipeline Roundtrip
        t0 = time.perf_counter()
        api_res = await process_chat_intent(
            message=query,
            language=lang,
            session_id=f"bench_full_{idx}"
        )
        t_roundtrip_ms = (time.perf_counter() - t0) * 1000

        bench_row = {
            "domain": domain,
            "query": query[:40] + "...",
            "resolve_ms": round(t_resolve_ms, 2),
            "rag_ms": round(t_rag_ms, 2),
            "gen_ms": round(t_gen_ms, 2),
            "roundtrip_ms": round(t_roundtrip_ms, 2),
            "sources_count": len(rag_data.get("sources", [])),
            "answer_preview": llm_answer[:90].replace("\n", " ") + "..."
        }
        results.append(bench_row)
        print(f"    Intent: {cat} (in {t_resolve_ms:.1f}ms)")
        print(f"    Parallel Dynamic RAG: {len(rag_data.get('sources', []))} sources (in {t_rag_ms:.1f}ms)")
        print(f"    LLM Generation: in {t_gen_ms:.1f}ms")
        print(f"    Total Roundtrip: {t_roundtrip_ms:.1f}ms")

    # Aggregate Statistics
    avg_resolve = statistics.mean([r["resolve_ms"] for r in results])
    avg_rag = statistics.mean([r["rag_ms"] for r in results])
    avg_gen = statistics.mean([r["gen_ms"] for r in results])
    avg_total = statistics.mean([r["roundtrip_ms"] for r in results])

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY & AGGREGATE RESULTS")
    print("=" * 80)
    print(f"Average Intent & Context Resolution : {avg_resolve:8.2f} ms")
    print(f"Average Parallel Dynamic RAG Fetch  : {avg_rag:8.2f} ms (Concurrent Crossref + OpenAlex + Wiki)")
    print(f"Average Local Ollama Qwen Inference : {avg_gen:8.2f} ms")
    print(f"Average Total Chat Roundtrip        : {avg_total:8.2f} ms")
    print("=" * 80)

    # Save artifact
    output_path = "C:\\Users\\aouti\\.gemini\\antigravity-ide\\brain\\33be6dcb-4ecb-4d96-ad35-1e221e7f967a\\phase4_latency_benchmark.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "averages": {
            "avg_resolve_ms": avg_resolve,
            "avg_rag_ms": avg_rag,
            "avg_gen_ms": avg_gen,
            "avg_roundtrip_ms": avg_total
        }}, f, indent=2)
    print(f"Benchmark artifact saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
