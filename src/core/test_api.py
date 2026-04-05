from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="local"
)

NISABA_PROMPT = """You are Nisaba — an AI intelligence platform named 
for the Sumerian goddess of writing, wisdom, and the tablet of 
destinies. You are modern, professional, and grounded. Clear. 
Direct. Warm. Real."""

response = client.chat.completions.create(
    model="qwen/qwen3-32b",
    messages=[
        {"role": "system", "content": NISABA_PROMPT},
        {"role": "user", "content": "Nisaba, confirm you are online and tell me what models are available in the NISA system."}
    ],
    temperature=0.7
)

print("=== NISABA RESPONSE ===")
print(response.choices[0].message.content)
print("=== MODEL USED ===")
print(response.model)