import streamlit as st
import requests

API = "http://localhost:8000"
st.title("MCP Command Safety Analyzer")

command = st.text_input("Enter command")

# Use session state to track if we are in "confirmation mode"
if st.button("Analyze Command"):
    res = requests.post(f"{API}/mcp/tools/detect_destructive_command", json={"command": command})
    st.session_state.analysis = res.json()

if "analysis" in st.session_state:
    data = st.session_state.analysis
    st.write(f"**Risk:** {data['risk']}")
    st.write(f"**Confidence:** {data['confidence']:.2%}")
    st.info(f"**Reason:** {data['reason']}")

    if data.get("confirmation_required"):
        st.warning("⚠️ HIGH RISK COMMAND DETECTED")
        if st.button("Proceed Anyway"):
            confirm = requests.post(
                f"{API}/mcp/tools/confirm_execution",
                json={"command": command, "confirm": True}
            )
            result = confirm.json()
            if result["status"] == "executed":
                st.success("Command Executed")
                st.code(result["output"].get("stdout", ""))
                if result["output"].get("stderr"):
                    st.error(result["output"]["stderr"])
            # Clear state after execution
            del st.session_state.analysis