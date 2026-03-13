import streamlit as st
import requests

API = "http://localhost:8000"

st.title("MCP Command Safety Analyzer")

command = st.text_input("Enter command")

if st.button("Analyze Command"):

    res = requests.post(    
        f"{API}/mcp/tools/detect_destructive_command",
        json={"command": command}
    )

    data = res.json()

    st.write("Risk:", data["risk"])
    st.write("Confidence:", data["confidence"])
    st.write("Reason:", data["reason"])

    if data.get("confirmation_required"):

        st.warning("⚠️ HIGH RISK COMMAND DETECTED")

        if st.button("Proceed Anyway"):

            confirm = requests.post(
                f"{API}/mcp/tools/confirm_execution",
                json={"command": command, "confirm": True}
            )

            result = confirm.json()

            st.success("Command Executed")

            st.write("Output:")
            st.code(result["output"]["stdout"])

            if result["output"]["stderr"]:
                st.error(result["output"]["stderr"])