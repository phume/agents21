import re
import os
import json

# Try to import Google GenAI library (New SDK)
try:
    from google import genai
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

def extract_with_llm(text):
    """
    Uses Google GenAI SDK to extract entities.
    """
    # Try to get key from file first (User provided)
    key_path = r"c:\Users\phume\Downloads\agent_S21\gemini_api.txt"
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            api_key = f.read().strip()
    else:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not HAS_LLM or not api_key:
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Analyze the following text from a government press release (AML/Financial Crime context).
        Identify any individuals, companies, or organizations that are being sanctioned, charged, prosecuted, or identified as involved in financial crimes.
        
        For each entity, determine a "Risk Level" and "Risk Type":
        - Risk Level: High, Medium, Low
        - Risk Type: Sanction, Money Laundering, Fraud, Drug Trafficking, Cybercrime, Terrorist Financing, Accomplice, Prosecuted, Settlement, etc.

        Return strictly a JSON array of objects with keys: "name", "type" (Person/Org), "risk_level", "risk_type".
        Do NOT generic government bodies (e.g. "Department of Justice", "Office of Foreign Assets Control", "District Court") unless they are the specific defendant/target.
        
        Text:
        {text[:8000]}
        
        JSON Response:
        """
        
        # Using gemini-2.5-flash as authenticated by user test
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt,
        )
        
        # Robust JSON extraction using regex
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Fallback: try to clean raw text
            json_str = response.text.replace('```json', '').replace('```', '').strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Last ditch: sometimes it returns single quotes
            # print(f"  [DEBUG] JSON Parse Failed. Raw: {json_str[:100]}...")
            return None
        
        # Flatten for the simpler app structure (Name | Type/Risk)
        entities = []
        for item in data:
            name = item.get('name')
            risk = f"{item.get('risk_level', 'Unknown')} - {item.get('risk_type', 'General')}"
            entities.append({
                'name': name,
                'type': risk
            })
        return entities
    except Exception as e:
        print(f"LLM Extraction failed: {e}")
        return None

def extract_entities(text):
    """
    Extracts entities using ONLY the LLM. 
    If LLM fails or is not configured, returns empty list (or raises error if strictly required).
    User explicitly requested NO REGEX fallback.
    """
    if not text:
        return []
    
    # 1. Try LLM
    llm_result = extract_with_llm(text)
    
    if llm_result:
        return llm_result
    
    # If LLM failed or returned None, do NOT fallback to regex.
    # Return empty to avoid "shit" data on dashboard.
    print("  [WARN] LLM extraction returned no results or failed. Skipping entity extraction.")
    return []
