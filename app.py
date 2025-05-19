from fastapi import FastAPI, HTTPException, Depends, status, Body, Query, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import uuid
import json
import requests
from datetime import datetime, timedelta
import jwt
import hashlib
import shutil
from pathlib import Path

# Document extraction
import docx
from PyPDF2 import PdfReader

# Constants
SECRET_KEY = "your-secret-key-for-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
UPLOAD_DIR = "uploads"
LM_STUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"

# Ensure uploads directory exists
Path(UPLOAD_DIR).mkdir(exist_ok=True)

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 password bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatMessage(BaseModel):
    message: str
    document_ids: List[str] = []

class ChatResponse(BaseModel):
    response: str
    source_documents: List[str] = []

# Database connection
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_file(file_path):
    file_extension = file_path.split(".")[-1].lower()
    
    if file_extension == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_extension in ["docx", "doc"]:
        return extract_text_from_docx(file_path)
    elif file_extension == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return ""

def query_lm_studio(prompt, max_tokens=2000):
    try:
        payload = {
            "model": "mistral-nemo-instruct-2407",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        response = requests.post(LM_STUDIO_API_URL, json=payload)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"LM Studio API error: {response.status_code} {response.text}")
            return "Error communicating with LM Studio API"
    except Exception as e:
        print(f"Error querying LM Studio: {e}")
        return "Error communicating with LM Studio"

# API endpoints
@app.get("/")
def health_check():
    """Check if API and dependencies are healthy"""
    health_status = {"status": "healthy"}
    
    # Check LM Studio connection
    try:
        test_prompt = "Hello, are you there?"
        response = query_lm_studio(test_prompt, max_tokens=10)
        health_status["lm_studio"] = "connected"
    except:
        health_status["lm_studio"] = "disconnected"
    
    # Check database connection
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        health_status["database"] = "connected"
    except:
        health_status["database"] = "disconnected"
    
    return health_status

@app.post("/register")
def register(user: User):
    """Register a new user"""
    try:
        conn = get_db_connection()
        
        # Check if username already exists
        existing_user = conn.execute(
            "SELECT username FROM users WHERE username = ?", 
            (user.username,)
        ).fetchone()
        
        if existing_user:
            conn.close()
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Hash the password before storing
        hashed_password = hash_password(user.password)
        
        # Insert new user
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user.username, hashed_password)
        )
        conn.commit()
        conn.close()
        
        return {"message": "User registered successfully"}
    except Exception as e:
        # Log the actual error for debugging
        print(f"Registration error: {str(e)}")
        # Return a generic error to the client
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login to get access token"""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT username, password FROM users WHERE username = ?", 
        (form_data.username,)
    ).fetchone()
    conn.close()
    
    if not user or hash_password(form_data.password) != user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": form_data.username}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload")
def upload_documents(
    files: List[UploadFile] = File(...),
    username: str = Depends(verify_token)
):
    """Upload documents for processing"""
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed")
    
    uploaded_docs = []
    for file in files:
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        
        # Get file extension
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ["pdf", "docx", "doc", "txt"]:
            continue
        
        # Create user directory if it doesn't exist
        user_dir = os.path.join(UPLOAD_DIR, username)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(user_dir, f"{doc_id}.{file_extension}")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Extract text from file
        text = extract_text_from_file(file_path)
        
        # Store document metadata in database
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO documents (id, username, filename, file_path, upload_date) VALUES (?, ?, ?, ?, ?)",
            (doc_id, username, file.filename, file_path, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        
        uploaded_docs.append({
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(text)
        })
    
    return {"uploaded_documents": uploaded_docs}

@app.post("/chat", response_model=ChatResponse)
def chat(
    message: ChatMessage,
    username: str = Depends(verify_token)
):
    """Chat with documents"""
    # Get document contents
    document_texts = []
    document_names = []
    
    if message.document_ids:
        conn = get_db_connection()
        for doc_id in message.document_ids:
            doc = conn.execute(
                "SELECT filename, file_path FROM documents WHERE id = ? AND username = ?", 
                (doc_id, username)
            ).fetchone()
            
            if not doc:
                continue
                
            text = extract_text_from_file(doc["file_path"])
            if text:
                document_texts.append(text)
                document_names.append(doc["filename"])
        conn.close()
    
    # Create prompt for LM Studio
    prompt = f"""
    You are a document analysis assistant focused on helping users understand paper and research documents,
    especially those related to Universitas Negeri Semarang (UNNES).
    
    User's question: {message.message}
    
    {'Documents provided:' if document_texts else 'No documents provided.'}
    """
    
    for i, (text, name) in enumerate(zip(document_texts, document_names)):
        prompt += f"\n\nDocument {i+1} ({name}):\n{text[:5000]}"  # Limit text size
    
    prompt += "\n\nPlease provide a clear, concise answer based on the documents provided."
    
    # Get response from LM Studio
    response = query_lm_studio(prompt)
    
    # Store chat history
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO chat_history (username, message, response, timestamp) VALUES (?, ?, ?, ?)",
        (username, message.message, response, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    
    return {"response": response, "source_documents": document_names}

@app.get("/documents")
def get_documents(username: str = Depends(verify_token)):
    """Get list of user's documents"""
    conn = get_db_connection()
    documents = conn.execute(
        "SELECT id, filename, upload_date FROM documents WHERE username = ?",
        (username,)
    ).fetchall()
    conn.close()
    
    return {"documents": [dict(doc) for doc in documents]}

@app.get("/history")
def get_chat_history(username: str = Depends(verify_token)):
    """Get user's chat history"""
    conn = get_db_connection()
    history = conn.execute(
        "SELECT message, response, timestamp FROM chat_history WHERE username = ? ORDER BY timestamp DESC",
        (username,)
    ).fetchall()
    conn.close()
    
    return {"history": [dict(item) for item in history]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)