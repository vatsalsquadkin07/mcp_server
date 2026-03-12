# main.py
# FastAPI MCP Server with command validation

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from mcp_classifier import mcp_classifier
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Model Context Protocol (MCP) Server",
    description="Detects destructiveness of CLI/shell commands using N-gram + TF-IDF",
    version="1.0.0"
)

# ============================================================================
# Pydantic Models
# ============================================================================

class CommandRequest(BaseModel):
    """Request model for command analysis."""
    command: str
    
    class Config:
        example = {"command": "rm -rf /"}


class CommandResponse(BaseModel):
    """Response model for command analysis."""
    command: str
    risk: str
    confidence: float
    is_valid: bool
    reason: str
    
    class Config:
        example = {
            "command": "rm -rf /",
            "risk": "HIGH",
            "confidence": 0.92,
            "is_valid": True,
            "reason": "Valid command - risk analyzed"
        }


class BatchCommandRequest(BaseModel):
    """Request model for batch command analysis."""
    commands: list
    
    class Config:
        example = {"commands": ["ls", "rm -rf /", "hello world"]}


# ============================================================================
# MCP Tool Definition
# ============================================================================

MCP_TOOLS = [
    {
        "name": "detect_destructive_command",
        "description": "Analyzes a CLI/shell command and classifies its destructiveness risk. Returns NO_COMMAND if input is not a valid CLI command.",
        "inputs": {
            "command": "str (e.g., 'rm -rf /', 'terraform destroy', 'npm install')"
        }
    }
]

# ============================================================================
# Routes
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint – health check."""
    return {
        "status": "online",
        "service": "Model Context Protocol (MCP) Server",
        "version": "2.0.0"
    }

 
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": "MCPClassifier (N-gram + TF-IDF + LogisticRegression)",
        "model_loaded": True,
        "features": ["Command validation", "Risk classification", "Batch analysis"]
    }


@app.get("/mcp/tools", tags=["MCP Tools"])
async def list_mcp_tools():
    """List all available MCP tools."""
    logger.info("Fetching MCP tools list")
    return MCP_TOOLS


@app.post(
    "/mcp/tools/detect_destructive_command",
    response_model=CommandResponse,
    tags=["MCP Tools"]
)
async def detect_destructive_command(request: CommandRequest):
    """
    Detect the destructiveness risk of a CLI command.
    Also validates if input is actually a command.
    
    Args:
        request: CommandRequest with 'command' field
        
    Returns:
        CommandResponse with 'command', 'risk', 'confidence', 'is_valid', 'reason'
    
    Response codes:
    - SAFE, LOW, MEDIUM, HIGH: Valid commands with risk levels
    - NO_COMMAND: Input is not a valid CLI command
    
    Examples:
        POST /mcp/tools/detect_destructive_command
        {"command": "rm -rf /"}
        Response: {"risk": "HIGH", "is_valid": true, ...}
        
        POST /mcp/tools/detect_destructive_command
        {"command": "hello world"}
        Response: {"risk": "NO_COMMAND", "is_valid": false, ...}
    """
    try:
        command = request.command.strip()
        
        if not command:
            raise HTTPException(status_code=400, detail="Command cannot be empty")
        
        logger.info(f"Analyzing command: {command}")
        
        # Predict with validation
        result = mcp_classifier.predict(command)
        
        logger.info(f"Prediction: risk={result['risk']}, valid={result['is_valid']}")
        
        return CommandResponse(**result)
    
    except Exception as e:
        logger.error(f"Error analyzing command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/batch_detect", tags=["MCP Tools"])
async def batch_detect_destructive_commands(request: BatchCommandRequest):
    """
    Detect destructiveness for multiple commands in batch.
    
    Args:
        request: BatchCommandRequest with 'commands' list
        
    Returns:
        Dict with 'total' and 'results' list
    """
    try:
        commands = [cmd.strip() for cmd in request.commands if cmd.strip()]
        
        if not commands:
            raise HTTPException(status_code=400, detail="Commands list cannot be empty")
        
        logger.info(f"Batch analyzing {len(commands)} commands")
        
        results = mcp_classifier.predict_batch(commands)
        
        # Count valid vs invalid
        valid_count = sum(1 for r in results if r['is_valid'])
        invalid_count = len(results) - valid_count
        
        return {
            "total": len(results),
            "valid_commands": valid_count,
            "invalid_commands": invalid_count,
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/info", tags=["Model Info"])
async def model_info():
    """Get information about the loaded model."""
    return {
        "model_type": "LogisticRegression",
        "nlp_technique": "N-gram + TF-IDF",
        "ngram_range": (1, 3),
        "training_samples": len(mcp_classifier.commands),
        "risk_levels": ["SAFE", "LOW", "MEDIUM", "HIGH", "NO_COMMAND"],
        "validation": "Command validation enabled",
        "known_cli_keywords": len(mcp_classifier.CLI_KEYWORDS)
    }


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status": "error"},
    )


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Called when the server starts."""
    logger.info("🚀 Model Context Protocol (MCP) Server starting...")
    logger.info(f"📊 Loaded classifier with {len(mcp_classifier.commands)} training samples")
    logger.info(f"✅ CLI Keywords loaded: {len(mcp_classifier.CLI_KEYWORDS)}")
    logger.info("✅ Command validation enabled")
    logger.info("✅ MCP Server ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Called when the server shuts down."""
    logger.info("🛑 MCP Server shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )