# risk_fusion.py

from mcp_classifier import mcp_classifier
from llm_detector import detect_with_llm

RISK_ORDER = ["SAFE", "LOW", "MEDIUM", "HIGH"]


RISK_ORDER = ["SAFE", "LOW", "MEDIUM", "HIGH"]

def fuse_risk(llm_risk, ml_risk):
    # Convert to uppercase to match RISK_ORDER
    llm_risk = str(llm_risk).upper()
    ml_risk = str(ml_risk).upper()

    try:
        # Check if LLM risk is higher or equal to ML risk
        if RISK_ORDER.index(llm_risk) >= RISK_ORDER.index(ml_risk):
            return llm_risk
        return ml_risk
    except ValueError:
        # Fallback if a model returns something weird like "UNKNOWN" or "ERROR"
        return "HIGH" # Default to safest/highest risk if unsure

def analyze_command(command: str):

    ml_result = mcp_classifier.predict(command)

    llm_result = detect_with_llm(command)

    final_risk = fuse_risk(llm_result["risk"], ml_result["risk"])

    return {
        "command": command,
        "risk": final_risk,
        "confidence": ml_result["confidence"],
        "is_valid": ml_result["is_valid"],
        "reason": f"LLM: {llm_result['reason']} | ML: {ml_result['reason']}"
    }