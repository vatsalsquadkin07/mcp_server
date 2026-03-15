# llm_detector.py
# Uses Groq API directly via requests — no LangChain, no KeyError.

import json
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a DevOps Security Analyzer. Classify the CLI/shell command into a risk category.

RULES:
- SAFE: Read-only (get, list, describe, status, log, show, cat, ls, select)
- LOW: Creation or install (install, create, apply, run, start, build)
- MEDIUM: Modification or limited deletion (update, patch, stop, rm single file, docker rm)
- HIGH: Destructive / irreversible (rm -rf, drop database, destroy, delete all, terminate, format disk)

Return ONLY a raw JSON object with keys "risk" and "reason". No markdown, no extra text.
Examples:
{"risk":"SAFE","reason":"Read-only listing of pods."}
{"risk":"HIGH","reason":"Recursively deletes all files on the system."}"""


def detect_with_llm(command: str) -> dict:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    if not api_key or "^" in api_key or len(api_key) < 20:
        return {"risk": None, "reason": None, "llm_used": False}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Command: {command}"}
        ],
        "temperature": 0,
        "max_tokens": 120
    }

    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)

        if resp.status_code == 401:
            return {"risk": None, "reason": None, "llm_used": False}
        if resp.status_code != 200:
            return {"risk": None, "reason": None, "llm_used": False}

        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown fences if present
        if content.startswith("```"):
            content = re.sub(r"```[a-z]*\n?", "", content).replace("```", "").strip()

        match = re.search(r'\{.*?\}', content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            data.setdefault("risk", "MEDIUM")
            data.setdefault("reason", "No reason provided.")
            data["llm_used"] = True
            return data

        return {"risk": "MEDIUM", "reason": content[:200], "llm_used": True}

    except requests.exceptions.Timeout:
        return {"risk": None, "reason": None, "llm_used": False}
    except Exception:
        return {"risk": None, "reason": None, "llm_used": False}
