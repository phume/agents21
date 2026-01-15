from google import genai
import os

# Load API Key
key_path = r"c:\Users\phume\Downloads\agent_S21\gemini_api.txt"
if os.path.exists(key_path):
    with open(key_path, 'r') as f:
        api_key = f.read().strip()
else:
    print("API Key file not found!")
    exit(1)

print(f"Using API Key: {api_key[:5]}...")

try:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents="is llm working?",
      config=genai.types.GenerateContentConfig(
        thinking_config=genai.types.ThinkingConfig(
          include_thoughts=True,
          thinking_budget=1024
        )
      )
    )
    
    print("Success!")
    print(response.text)
    
except Exception as e:
    print(f"Error: {e}")
