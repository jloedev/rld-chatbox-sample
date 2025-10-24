"""
Web Application Server for Customer Service Chatbot

This module provides a FastAPI-based web server with REST API endpoints
for the chatbot functionality.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from pathlib import Path

from src.chatbot import CustomerServiceChatbot

app = FastAPI(title="Customer Service Chatbot", version="1.0.0")

# Initialize chatbot
chatbot = None


class ChatMessage(BaseModel):
    """
    Model for chat message request.
    """
    message: str
    use_llm_classification: bool = False


class ChatResponse(BaseModel):
    """
    Model for chat response.
    """
    query: str
    intent: str
    answer: str


class HistoryMessage(BaseModel):
    """
    Model for conversation history message.
    """
    role: str
    content: str


@app.on_event("startup")
async def startup_event():
    """
    Initialize chatbot on server startup.
    """
    global chatbot
    print("Initializing chatbot...")
    chatbot = CustomerServiceChatbot("config.yaml")
    print("Chatbot initialized successfully!")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serve the main chat interface.
    """
    html_file = Path("static/index.html")
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return HTMLResponse(content="<h1>Chat interface not found. Please ensure static/index.html exists.</h1>")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Process a chat message and return response.

    Args:
        message: ChatMessage containing user query

    Returns:
        ChatResponse with answer and metadata
    """
    if chatbot is None:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")

    try:
        result = chatbot.process_query(
            message.message,
            use_llm_classification=message.use_llm_classification
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history", response_model=List[HistoryMessage])
async def get_history():
    """
    Get conversation history.

    Returns:
        List of conversation messages
    """
    if chatbot is None:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")

    try:
        history = chatbot.get_conversation_history()
        return [HistoryMessage(**msg) for msg in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear")
async def clear_history():
    """
    Clear conversation history.

    Returns:
        Success message
    """
    if chatbot is None:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")

    try:
        chatbot.clear_history()
        return {"status": "success", "message": "Conversation history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """
    Get system status.

    Returns:
        System status information
    """
    if chatbot is None:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")

    try:
        status = chatbot.get_system_status()
        return {"status": "operational", "components": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "chatbot_initialized": chatbot is not None}


def main():
    """
    Start the web server.
    """
    print("=" * 80)
    print("Customer Service Chatbot - Web Application")
    print("=" * 80)
    print("\nStarting server...")
    print("\nAccess the chatbot at: http://localhost:8080")
    print("API documentation at: http://localhost:8080/docs")
    print("\nPress CTRL+C to stop the server")
    print("=" * 80)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


if __name__ == "__main__":
    main()
