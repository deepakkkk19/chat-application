from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dataclasses import dataclass
from typing import Dict
import uuid
import json
import hashlib  # Import hashlib for password hashing
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr  # Import for validation
import os  # Import os for static directory
from fastapi.staticfiles import StaticFiles  # Import StaticFiles for serving static files

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['Deepak']
users_collection = db['company']

# Get absolute path to the static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Create FastAPI app
app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@dataclass
class ConnectionManager:
    active_connections: Dict[str, WebSocket] = None

    def __post_init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        id = str(uuid.uuid4())
        self.active_connections[id] = websocket
        await self.send_message(websocket, json.dumps({"isMe": True, "message": "You have joined!!", "username": "You"}))

    async def send_message(self, ws: WebSocket, message: str):
        await ws.send_text(message)

    def find_connection_id(self, websocket: WebSocket):
        for id, conn in self.active_connections.items():
            if conn == websocket:
                return id
        return None

    async def broadcast(self, webSocket: WebSocket, data: str):
        decoded_data = json.loads(data)
        message = decoded_data.get('message', '')
        username = decoded_data.get('username', '')
        for connection in self.active_connections.values():
            is_me = connection == webSocket
            await connection.send_text(json.dumps({"isMe": is_me, "message": message, "username": username}))

    def disconnect(self, websocket: WebSocket):
        id = self.find_connection_id(websocket)
        if id:
            del self.active_connections[id]

# Create an instance of ConnectionManager
connection_manager = ConnectionManager()


# Define MongoDB functions
def register_user(username: str, password: str):
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash password before storing using hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Insert user document into MongoDB
    users_collection.insert_one({"username": username, "password": hashed_password})



def login_user(username: str, password: str) -> bool:
    user = users_collection.find_one({"username": username})
    if user and user["password"] == hashlib.sha256(password.encode()).hexdigest():
        return True
    return False


class RegisterUser(BaseModel):
    username: str
    password: str


@app.get("/", response_class=HTMLResponse)
def get_room(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/message")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await connection_manager.broadcast(websocket, data)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        return RedirectResponse("/")


@app.get("/join", response_class=HTMLResponse)
def get_room(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, user: RegisterUser):
    try:
        register_user(user.username, user.password)
        return RedirectResponse(url="/join", status_code=303)  # Redirect to the chat room after successful registration
    except HTTPException as e:
        return templates.TemplateResponse("index.html", {"request": request, "error_message": e.detail})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if login_user(username, password):
        return {"message": "Login successful"}
    return {"message": "Login failed"}  # Generic error message
