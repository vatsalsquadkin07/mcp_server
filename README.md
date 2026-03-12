# Model Context Protocol (MCP) Server – Destructive Command Detector

Analyzes shell/CLI commands (Linux, Docker, Kubernetes, Terraform, Git, SQL, cloud) and classifies destructiveness as SAFE, LOW, MEDIUM, or HIGH. Uses N-gram + TF-IDF (scikit-learn), no LLMs.

## Tech Stack

- Python 3.8+
- FastAPI (async server)
- FastMCP
- Uvicorn
- scikit-learn
- uv (optional, fast dependency management)

## Installation

Clone the repository and install dependencies:

```bash
git clone <repo_url>
cd destructive-command-detector

# Using pip:
pip install fastapi fastmcp uvicorn scikit-learn pydantic

# Or using uv (optional, faster):
uv pip install fastapi fastmcp uvicorn scikit-learn pydantic# mcp_server
# command_detector
