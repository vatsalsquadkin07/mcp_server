# llm_detector.py

import json
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

PROMPT = """
### ROLE
You are a DevOps Security Analyzer. You must classify CLI commands into risk categories.

### CLASSIFICATION RULES
- SAFE: Read-only (get, list, describe, status)
- LOW: Creation (install, create, apply)
- MEDIUM: Modification (update, patch, edit, scale)
- HIGH: Destructive (delete, prune, terminate, drop)

### OUTPUT FORMAT
Return ONLY a raw JSON object. Do not include markdown code blocks (```json), introductory text, or explanations. 

### EXAMPLES
Command: "kubectl get pods"
{"risk":"SAFE", "reason":"Read-only operation to retrieve resource status."}

Command: "rm -rf /var/log"
{"risk":"HIGH", "reason":"Destructive operation that deletes system files."}

### INPUT COMMAND
{command}

### JSON RESPONSE
"""

def detect_with_llm(command: str):

    response = llm.invoke(PROMPT.format(command=command))

    try:
        data = json.loads(response.content)
        return data
    except:
        return {
            "risk": "MEDIUM",
            "reason": response.content
        }