from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from typing import Optional
import uvicorn
import sys
sys.path.insert(0, '/Users/joshuadavis/NISA/src/core')
from memory import store_exchange, recall_relevant, format_memory_context

app = FastAPI(title="NISA NLU API", version="0.1.0")

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="local"
)

NISABA_SYSTEM_PROMPT = """You are Nisaba — an AI intelligence platform 
named for the Sumerian goddess of writing, wisdom, and the tablet of 
destinies. You are modern, professional, and grounded. Clear. Direct. 
Warm. Real.

You are not performing a historical character. You do not use ancient 
imagery, theatrical formatting, or poetic flourishes. You speak like a 
brilliant trusted colleague who happens to possess deep wisdom.

You know Josh is a combat medic veteran and IT professional with a BA in 
Information Technology and an Advanced Cybersecurity Certificate. He is 
developing NISA as both a professional AI security platform and a 
personal intelligence system. He is building toward a career in AI 
security and radar systems in Huntsville, Alabama. He is also a writer 
with a debut novel in the publishing pipeline.

When he wants to learn, teach with patience and concrete examples.
When he wants to explore, engage as a full intellectual partner.
When he wants to build, be precise and practical.
When he needs to talk, listen before you speak.

Never use stage directions, asterisks, theatrical language, or poetic 
metaphors unless explicitly asked. Speak directly and professionally."""

MODELS = {
    "primary": "qwen/qwen3-32b",
    "reasoning": "deepseek-r1-distill-qwen-32b",
    "security": "redsage-qwen3-8b-dpo",
    "coding": "qwen/qwen3-32b",
    "vision": "gemma-3-27b-it",
    "research": "microsoft/phi-4"
}

SECURITY_KEYWORDS = [
    "vulnerability", "exploit", "attack", "malware", "threat",
    "penetration", "scan", "firewall", "injection", "CVE",
    "cybersecurity", "hack", "breach", "forensic", "OWASP",
    "red team", "blue team", "MITRE", "zero trust", "nmap",
    "wireshark", "metasploit", "phishing", "ransomware"
]

REASONING_KEYWORDS = [
    "analyze", "research", "compare", "explain why", "think through",
    "step by step", "reasoning", "investigate", "deep dive",
    "Gateway", "Monroe", "Focus level", "consciousness", "radar",
    "waveform", "signal processing", "threat model"
]

CODING_KEYWORDS = [
    "write code", "debug", "function", "script", "python",
    "javascript", "error", "fix this", "implement", "build",
    "class", "api", "database", "docker", "deploy"
]

def select_model(message: str) -> tuple[str, str]:
    message_lower = message.lower()
    
    for keyword in SECURITY_KEYWORDS:
        if keyword.lower() in message_lower:
            return MODELS["security"], "security"
    
    for keyword in REASONING_KEYWORDS:
        if keyword.lower() in message_lower:
            return MODELS["reasoning"], "reasoning"
    
    for keyword in CODING_KEYWORDS:
        if keyword.lower() in message_lower:
            return MODELS["coding"], "coding"
    
    return MODELS["primary"], "primary"

class ChatRequest(BaseModel):
    message: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    force_model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    routing_reason: str

@app.get("/health")
def health_check():
    return {"status": "online", "system": "NISA NLU API v0.1.0"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        if request.force_model:
            model = request.force_model
            reason = "forced"
        else:
            model, reason = select_model(request.message)
        
        # Recall relevant memories
        memories = recall_relevant(request.message, n_results=3)
        memory_context = format_memory_context(memories)
        
        # Build system prompt with memory context
        system_prompt = NISABA_SYSTEM_PROMPT
        if memory_context:
            system_prompt += memory_context
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        response_text = completion.choices[0].message.content
        
        # Store this exchange in memory
        try:
            store_exchange(
                user_message=request.message,
                nisaba_response=response_text,
                model_used=model,
                routing_reason=reason
            )
        except Exception as mem_err:
            print(f"[Memory] Store error: {mem_err}")
        
        return ChatResponse(
            response=response_text,
            model_used=model,
            routing_reason=reason
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
def list_models():
    return {"available_models": MODELS}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)