#!/usr/bin/env python3.11
"""
NISA Fine-tuning Dataset Builder
Converts SSD knowledge library documents into MLX-LM LoRA training format
Output: train.jsonl, valid.jsonl, test.jsonl
"""
import os
import json
import random
from pathlib import Path

SSD_BASE = "/Volumes/Share Drive/NISA/knowledge"
OUTPUT_DIR = "/Users/joshuadavis/NISA/finetune/datasets/combined"

DOMAIN_SYSTEM_PROMPTS = {
    "security": "You are Nisaba, an expert AI security analyst. Answer questions about cybersecurity, vulnerabilities, threat detection, and defensive techniques with precision and depth.",
    "radar_ew": "You are Nisaba, an expert in radar systems and electronic warfare. Answer questions about radar principles, waveform design, EW techniques, and signal processing with technical accuracy.",
    "general": "You are Nisaba, an intelligent AI assistant. Answer questions clearly and helpfully.",
    "programs": "You are Nisaba, an expert software engineer and security researcher. Help with code, explain implementations, and provide technical guidance.",
}

DOMAIN_QA_TEMPLATES = {
    "security": [
        ("What is {topic} and how does it work?", "Explain the concept in detail"),
        ("How do you defend against {topic}?", "Provide defensive strategies"),
        ("What are the indicators of compromise for {topic}?", "List IOCs and detection methods"),
        ("Explain the OWASP guidelines for {topic}", "Reference OWASP standards"),
    ],
    "radar_ew": [
        ("Explain how {topic} works in radar systems", "Technical explanation"),
        ("What are the advantages of {topic} in electronic warfare?", "EW application"),
        ("How does {topic} improve radar performance?", "Performance analysis"),
        ("Describe the signal processing for {topic}", "DSP details"),
    ],
}

def chunk_text(text: str, chunk_size: int = 512) -> list:
    """Split text into chunks for training"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        if len(chunk.strip()) > 100:
            chunks.append(chunk.strip())
    return chunks

def text_to_training_examples(text: str, domain: str) -> list:
    """Convert document text to instruction-response training pairs"""
    examples = []
    system_prompt = DOMAIN_SYSTEM_PROMPTS.get(domain, DOMAIN_SYSTEM_PROMPTS["general"])
    chunks = chunk_text(text, 400)
    
    for chunk in chunks:
        # Format 1: Direct knowledge as assistant response
        example = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Tell me about: {chunk[:100]}..."},
                {"role": "assistant", "content": chunk}
            ]
        }
        examples.append(example)
        
        # Format 2: Q&A style
        if len(chunk) > 200:
            sentences = chunk.split(". ")
            if len(sentences) > 2:
                question_context = sentences[0]
                answer = ". ".join(sentences[1:])
                example2 = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Explain: {question_context}"},
                        {"role": "assistant", "content": answer}
                    ]
                }
                examples.append(example2)
    
    return examples

def load_domain_documents(domain: str) -> list:
    """Load all documents from a knowledge domain"""
    domain_path = os.path.join(SSD_BASE, domain)
    documents = []
    
    supported = {".txt", ".md", ".py", ".json"}
    
    seen_filenames = set()
    for root, dirs, files in os.walk(domain_path):
        dirs[:] = [d for d in dirs if d not in ["output", "cache", "logs", "prompts"]]
        for fname in files:
            if fname.startswith("."):
                continue
            if fname in seen_filenames:
                print(f"  Skip duplicate: {fname}")
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in supported:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if len(content.strip()) > 100:
                    seen_filenames.add(fname)
                    documents.append({"content": content, "source": fname, "domain": domain})
                    print(f"  Loaded: {fname} ({len(content)} chars)")
            except Exception as e:
                print(f"  Error loading {fname}: {e}")
    
    return documents

def build_dataset():
    """Build the complete training dataset"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_examples = []
    domains = ["security", "radar_ew", "programs", "general", "nisa_docs"]
    
    for domain in domains:
        print(f"\nProcessing domain: {domain}")
        docs = load_domain_documents(domain)
        print(f"  Found {len(docs)} documents")
        
        for doc in docs:
            examples = text_to_training_examples(doc["content"], domain)
            all_examples.extend(examples)
            print(f"  Generated {len(examples)} examples from {doc['source']}")
    
    print(f"\nTotal examples: {len(all_examples)}")
    
    # Shuffle and split
    random.shuffle(all_examples)
    n = len(all_examples)
    train_n = int(n * 0.85)
    val_n = int(n * 0.10)
    
    train_data = all_examples[:train_n]
    val_data = all_examples[train_n:train_n+val_n]
    test_data = all_examples[train_n+val_n:]
    
    # Write JSONL files
    for split, data, fname in [
        ("train", train_data, "train.jsonl"),
        ("valid", val_data, "valid.jsonl"),
        ("test", test_data, "test.jsonl"),
    ]:
        out_path = os.path.join(OUTPUT_DIR, fname)
        with open(out_path, "w") as f:
            for ex in data:
                f.write(json.dumps(ex) + "\n")
        print(f"Written {len(data)} {split} examples to {out_path}")
    
    print("\nDataset build complete!")
    print(f"Train: {len(train_data)} | Val: {len(val_data)} | Test: {len(test_data)}")

if __name__ == "__main__":
    build_dataset()
