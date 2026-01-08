import re
import os

# Try to import Google Generative AI library
try:
    import google.generativeai as genai
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

def extract_with_llm(text):
    """
    Uses Google Gemini (or similar) to extract entities if an API key is available.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not HAS_LLM or not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Extract all financial crime entities, sanctioned individuals, or organizations from the text below.
        Return ONLY a list of entities in the format: Name | Type (Person/Org/Vessel/etc)
        Do not include headers or markdown.
        
        Text:
        {text[:4000]}
        """
        
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        entities = []
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                entities.append({
                    'name': parts[0].strip(),
                    'type': parts[1].strip()
                })
        return entities
    except Exception as e:
        print(f"LLM Extraction failed: {e}")
        return None

def extract_entities(text):
    """
    Extracts potential entities from text using simple heuristics or LLM.
    Returns a list of dictionaries: {'name': 'Entity Name', 'type': 'Person/Org'}
    """
    if not text:
        return []
    
    # 1. Try LLM first if configured
    llm_result = extract_with_llm(text)
    if llm_result:
        return llm_result

    entities = []
    seen = set()

    # 2. Specialized Regex for "Entity Name (Country)" format
    # Found in US Treasury/OFAC releases often.
    # Ex: "Bliri S.A. de C.V. (Mexico)"
    sanction_pattern = r'([A-Z0-9][A-Za-z0-9\.\-\s]+?)\s\((Mexico|Canada|Poland|China|Russia|Iran|Korea|Venezuela|Colombia|Ecuador|Brazil)\)'
    matches_sanction = re.findall(sanction_pattern, text)
    
    for name, country in matches_sanction:
        clean_name = name.strip()
        if clean_name not in seen:
            seen.add(clean_name)
            entities.append({
                'name': clean_name,
                'type': f'Sanctioned Entity ({country})'
            })

    # 3. Fallback to Capitalized Words Sequence (Heuristic)
    # This regex looks for: Capitalized Word + (space + Capitalized Word)+
    pattern = r'[A-Z][a-z]+(?:\s[A-Z][a-z]+)+'
    matches = re.findall(pattern, text)
    
    # Filter list
    ignore_list = {
        'Press Release', 'Immediate Release', 'United States', 'Department of Justice',
        'Washington', 'New York', 'District Court', 'Attorney General', 'Homeland Security',
        'Treasury Department', 'Foreign Assets', 'Control', 'Recent Actions', 'January', 'February',
        'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'
    }
    
    for match in matches:
        clean_match = match.strip()
        if clean_match in seen:
            continue
            
        # Basic filtering to reduce noise
        if len(clean_match) < 4: continue
        if any(ignore in clean_match for ignore in ignore_list): continue
        if any(entity['name'] in clean_match for entity in entities): continue # Avoid duplicates if already found better match
        
        seen.add(clean_match)
        entities.append({
            'name': clean_match,
            'type': 'Potential Entity' # Generic type
        })
        
    return entities
