"""
NISA Mixture of Agents (MoA) Pipeline
Two-pass approach: analytical reasoning -> synthesis
When memory allows: DeepSeek R1 reasons -> Qwen 3 synthesizes
When memory constrained: Qwen 3 reasons -> Qwen 3 synthesizes
"""
from openai import OpenAI
import time

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="local"
)

PRIMARY_MODEL = "qwen/qwen3-32b"
REASONING_MODEL = "deepseek-r1-distill-qwen-32b"

REASONING_PROMPT = """You are a precise analytical reasoner. Think through
this problem step by step. Identify key considerations, risks, trade-offs,
and implications. Be systematic and comprehensive. Provide only your
analysis and reasoning — not a final answer."""

SYNTHESIS_PROMPT = """You are Nisaba — an AI intelligence platform named
for the Sumerian goddess of writing, wisdom, and the tablet of destinies.
You are modern, professional, and grounded. Clear. Direct. Warm. Real.

You have received a detailed analysis. Synthesize it into a clear,
direct, genuinely helpful response. Speak in your own voice. Do not
mention the reasoning process or analysis. Just give the best answer."""

def get_available_models() -> list:
    """Check which models are currently loaded"""
    try:
        models = client.models.list()
        return [m.id for m in models.data]
    except Exception:
        return []

def run_moa(query: str, verbose: bool = False) -> dict:
    """
    Run two-pass MoA pipeline.
    Uses DeepSeek R1 for reasoning if available, else Qwen 3.
    Always uses Qwen 3 for synthesis.
    """
    start_time = time.time()
    available = get_available_models()
    
    # Choose reasoning model based on availability
    if REASONING_MODEL in available:
        reasoning_model = REASONING_MODEL
        mode = "full_moa"
    else:
        reasoning_model = PRIMARY_MODEL
        mode = "single_model_moa"
    
    if verbose:
        print(f"[MoA] Mode: {mode}")
        print(f"[MoA] Reasoning with: {reasoning_model}")
    
    # Pass 1: Analytical reasoning
    r1 = client.chat.completions.create(
        model=reasoning_model,
        messages=[
            {"role": "system", "content": REASONING_PROMPT},
            {"role": "user", "content": f"Analyze thoroughly: {query}"}
        ],
        temperature=0.2,
        max_tokens=1024
    )
    reasoning = r1.choices[0].message.content
    reasoning_time = time.time() - start_time
    
    if verbose:
        print(f"[MoA] Reasoning complete ({reasoning_time:.1f}s)")
        print(f"[MoA] Synthesizing with: {PRIMARY_MODEL}")
    
    # Pass 2: Synthesis
    r2 = client.chat.completions.create(
        model=PRIMARY_MODEL,
        messages=[
            {"role": "system", "content": SYNTHESIS_PROMPT},
            {"role": "user", "content": f"""Question: {query}

Analysis:
{reasoning}

Synthesized response:"""}
        ],
        temperature=0.7,
        max_tokens=1024
    )
    
    response = r2.choices[0].message.content
    total_time = time.time() - start_time
    
    if verbose:
        print(f"[MoA] Complete ({total_time:.1f}s)")
    
    return {
        "query": query,
        "reasoning": reasoning,
        "response": response,
        "reasoning_model": reasoning_model,
        "synthesis_model": PRIMARY_MODEL,
        "mode": mode,
        "total_time": total_time
    }

def should_use_moa(query: str) -> bool:
    """Determine if a query warrants MoA processing"""
    moa_triggers = [
        "analyze", "explain why", "compare", "evaluate",
        "what should i", "help me decide", "think through",
        "best approach", "recommend", "strategy",
        "how do i", "implications", "pros and cons",
        "trade-offs", "deep dive", "assess", "review"
    ]
    return any(t in query.lower() for t in moa_triggers)

if __name__ == "__main__":
    print("Testing NISA MoA pipeline...")
    query = "What is the best strategy for building an AI security portfolio to get hired at a defense contractor in Huntsville Alabama?"
    
    result = run_moa(query, verbose=True)
    print()
    print("=" * 60)
    print("NISABA:")
    print(result["response"])
    print()
    print(f"Mode: {result['mode']}")
    print(f"Time: {result['total_time']:.1f}s")
