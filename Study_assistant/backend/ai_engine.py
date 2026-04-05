import requests
import json
import config

def ask_ai(prompt):
    """
    Unified AI Gateway. Supports OpenAI, Gemini, and DeepSeek.
    Configuration is read from config.py.
    """
    provider = config.AI_PROVIDER.lower()

    try:
        if provider == "openai":
            return _call_openai(prompt)
        elif provider == "gemini":
            return _call_gemini(prompt)
        elif provider == "deepseek":
            return _call_deepseek(prompt)
        else:
            return f"Error: Unknown AI Provider '{provider}' in config.py"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

def _call_openai(prompt):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": config.OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    return _process_openai_compatible(api_url, headers, data)

def _call_deepseek(prompt):
    # DeepSeek uses OpenAI-compatible headers and payload structure
    api_url = f"{config.DEEPSEEK_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": config.DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    return _process_openai_compatible(api_url, headers, data)

def _call_gemini(prompt):
    model = config.GEMINI_MODEL
    api_key = config.GEMINI_API_KEY
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    r = requests.post(url, headers=headers, json=payload, timeout=20)
    
    if r.status_code != 200:
        try:
            err_json = r.json()
            msg = err_json.get("error", {}).get("message", "API Error")
            return f"Gemini Error ({r.status_code}): {msg}"
        except:
            return f"Gemini Error ({r.status_code}): {r.text}"

    data = r.json()
    try:
        return data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        return f"Gemini Error: Unexpected response format: {json.dumps(data)}"

def _process_openai_compatible(api_url, headers, data):
    """Common helper for OpenAI and DeepSeek"""
    r = requests.post(api_url, headers=headers, json=data, timeout=20)
    
    if r.status_code != 200:
        try:
            err_json = r.json()
            msg = err_json.get("error", {}).get("message", "API Error")
            return f"API Error ({r.status_code}): {msg}"
        except:
            return f"API Error ({r.status_code}): {r.text}"

    response_json = r.json()
    if "choices" in response_json and len(response_json["choices"]) > 0:
        return response_json["choices"][0]["message"]["content"]
    else:
        return f"Error: Unexpected response format: {response_json}"