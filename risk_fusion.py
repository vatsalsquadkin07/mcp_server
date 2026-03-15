# risk_fusion.py

from mcp_classifier import mcp_classifier
from llm_detector import detect_with_llm

RISK_ORDER = ["SAFE", "LOW", "MEDIUM", "HIGH"]


def fuse_risk(llm_risk, ml_risk):
    llm_risk = str(llm_risk).upper()
    ml_risk = str(ml_risk).upper()
    try:
        if RISK_ORDER.index(llm_risk) >= RISK_ORDER.index(ml_risk):
            return llm_risk
        return ml_risk
    except ValueError:
        return ml_risk  # if LLM returned something weird, trust ML


def analyze_command(command: str):
    ml_result = mcp_classifier.predict(command)
    llm_result = detect_with_llm(command)

    llm_used = llm_result.get("llm_used", False)
    ml_no_command = ml_result["risk"] == "NO_COMMAND"

    if llm_used and llm_result.get("risk"):
        # If ML said NO_COMMAND but LLM recognises it, trust the LLM fully
        if ml_no_command:
            final_risk = llm_result["risk"]
        else:
            final_risk = fuse_risk(llm_result["risk"], ml_result["risk"])
        reason = llm_result["reason"]
        is_valid = True
    else:
        # No LLM result — if ML also says NO_COMMAND, keep that
        final_risk = ml_result["risk"]
        reason = ml_result["reason"]
        is_valid = ml_result["is_valid"]

    return {
        "command": command,
        "risk": final_risk,
        "confidence": ml_result["confidence"],
        "is_valid": is_valid,
        "reason": reason
    }
