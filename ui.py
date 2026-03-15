import streamlit as st
import requests

API = "http://localhost:8000"

st.title("MCP Command Safety Analyzer")

command = st.text_input("Enter CLI command to analyze")

if st.button("Analyze"):
    if not command.strip():
        st.warning("Please enter a command.")
    else:
        try:
            res = requests.post(
                f"{API}/mcp/tools/detect_destructive_command",
                json={"command": command},
                timeout=30
            )
            if res.status_code == 200:
                st.session_state.analysis = res.json()
                st.session_state.command = command
            else:
                st.error(f"API Error {res.status_code}: {res.json().get('detail', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the FastAPI server is running on port 8000.")
        except Exception as e:
            st.error(f"Error: {e}")

if "analysis" in st.session_state:
    data = st.session_state.analysis

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Risk Level", value=data.get("risk", "N/A"))
    with col2:
        confidence = data.get("confidence", 0.0)
        st.metric(label="Confidence", value=f"{confidence:.2%}")

    reason = data.get("reason", "")
    st.info(f"**Reasoning:** {reason}")

    if data.get("confirmation_required"):
        st.warning("⚠️ HIGH RISK COMMAND DETECTED")
        if st.button("Proceed Anyway"):
            try:
                confirm = requests.post(
                    f"{API}/mcp/tools/confirm_execution",
                    json={"command": st.session_state.get("command", ""), "confirm": True},
                    timeout=30
                )
                result = confirm.json()
                if result.get("status") == "executed":
                    st.success("Command Executed")
                    st.code(result["output"].get("stdout", ""))
                    if result["output"].get("stderr"):
                        st.error(result["output"]["stderr"])
                del st.session_state.analysis
                st.rerun()
            except Exception as e:
                st.error(f"Execution failed: {e}")

    if st.button("Clear Results"):
        del st.session_state.analysis
        st.rerun()