from fastapi import FastAPI, Query, Path, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime, timezone

app = FastAPI(
    title="Simple Messages API",
    description="Task 02 — Build a Simple Messages API"
)

# In-memory storage using a dictionary for O(1) lookups
messages_db: Dict[int, dict] = {}
message_id_counter = 1

# Custom Exception for 404 to return a custom JSON format
class MessageNotFoundException(Exception):
    def __init__(self, message_id: int):
        self.message_id = message_id

@app.exception_handler(MessageNotFoundException)
async def not_found_exception_handler(request, exc: MessageNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"error": "Message not found", "requested_id": exc.message_id}
    )

# Data Models
class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"

class MessageCreate(BaseModel):
    role: RoleEnum
    content: str = Field(min_length=1, max_length=2000, strip_whitespace=True)

class MessageUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000, strip_whitespace=True)

class MessageResponse(BaseModel):
    id: int
    role: RoleEnum
    content: str
    created_at: datetime

# API Endpoints
@app.post("/api/v1/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message: MessageCreate):
    global message_id_counter
    new_msg = {
        "id": message_id_counter,
        "role": message.role,
        "content": message.content,
        "created_at": datetime.now(timezone.utc)
    }
    messages_db[message_id_counter] = new_msg
    message_id_counter += 1
    return new_msg

@app.get("/api/v1/messages", response_model=List[MessageResponse])
def list_messages(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    role: Optional[RoleEnum] = Query(None)
):
    filtered_messages = list(messages_db.values())
    if role:
        filtered_messages = [msg for msg in filtered_messages if msg["role"] == role.value]
    
    return filtered_messages[offset : offset + limit]

@app.get("/api/v1/messages/{message_id}", response_model=MessageResponse)
def get_message(message_id: int = Path(...)):
    if message_id not in messages_db:
        raise MessageNotFoundException(message_id=message_id)
    return messages_db[message_id]

@app.patch("/api/v1/messages/{message_id}", response_model=MessageResponse)
def update_message(message_id: int, message_update: MessageUpdate):
    if message_id not in messages_db:
        raise MessageNotFoundException(message_id=message_id)
    
    messages_db[message_id]["content"] = message_update.content
    return messages_db[message_id]

@app.delete("/api/v1/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int):
    if message_id not in messages_db:
        raise MessageNotFoundException(message_id=message_id)
    del messages_db[message_id]
    return None