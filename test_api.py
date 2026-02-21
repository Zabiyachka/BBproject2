#!/usr/bin/env python
"""Test OpenAI API key"""
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {API_KEY[:20]}..." if API_KEY else "No API key found!")

if not API_KEY:
    print("ERROR: No API key in .env")
    exit(1)

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY)
    
    print("Testing OpenAI API call...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello"}
        ],
        timeout=10
    )
    
    print("✓ API call successful!")
    print(f"Response: {response.choices[0].message.content[:100]}")
    
except Exception as e:
    print(f"✗ API call failed: {e}")
    import traceback
    traceback.print_exc()
