import requests
import json
import os

def call_ollama(model_name, system_prompt, user_prompt):
    """
    Calls local Ollama instance.
    """
    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
    except Exception as e:
        raise ConnectionError(f"Failed to connect to local Ollama. Ensure Ollama is running and the model '{model_name}' is pulled. Error: {str(e)}")

def call_groq(api_key, model_name, system_prompt, user_prompt):
    """
    Calls Groq API.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise ConnectionError(f"Failed to call Groq API. Check your API key. Error: {str(e)}")

def patch_vulnerability(code_snippet, vulnerability, engine="Ollama", ollama_model="qwen2.5", groq_key=None, groq_model="llama-3.3-70b-specdec"):
    """
    Generates a secure patch for the vulnerable code snippet using the selected LLM engine.
    """
    system_prompt = (
        "You are an expert DevSecOps and Security Engineering assistant. "
        "Your task is to fix security vulnerabilities in Python code. "
        "Modify only the vulnerable function or lines. "
        "Ensure the fix is highly secure, handles errors correctly, and follows Python best practices. "
        "Return ONLY the updated, complete Python code block. Do NOT include markdown styling, explanations, or code fences."
    )
    
    user_prompt = f"""
    The following Python code snippet contains a security vulnerability:
    
    ```python
    {code_snippet}
    ```
    
    Vulnerability details:
    - Line: {vulnerability['line']}
    - Code: {vulnerability['code']}
    - Type: {vulnerability['id']}
    - Description: {vulnerability['description']}
    Remediation needed: {vulnerability['remediation']}
    
    Please provide the corrected Python code that replaces the vulnerable code. Return ONLY the code, no explanation.
    """
    
    if engine == "Ollama":
        raw_response = call_ollama(ollama_model, system_prompt, user_prompt)
    elif engine == "Groq":
        if not groq_key:
            raise ValueError("Groq API Key is required when selecting Groq engine.")
        raw_response = call_groq(groq_key, groq_model, system_prompt, user_prompt)
    else:
        raise ValueError(f"Unknown engine: {engine}")
        
    # Clean up the output in case the LLM returned markdown code blocks (e.g. ```python ... ```)
    clean_code = raw_response.strip()
    if clean_code.startswith("```python"):
        clean_code = clean_code[9:]
    elif clean_code.startswith("```"):
        clean_code = clean_code[3:]
        
    if clean_code.endswith("```"):
        clean_code = clean_code[:-3]
        
    return clean_code.strip()
