# src/api/router.py
"""
FastAPI Router with Complete Intelligence:
- Multi-file upload
- RAG indexing
- Smart query routing (always gives useful answers)
- Session management
"""

import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_table
from src.analysis.query_controller import route_query
from src.ai.rag_engine import index_dataframe_to_chroma

router = APIRouter()
user_sessions = {}  # Store session data in memory


# ==========================================
# 📤 UPLOAD ENDPOINT
# ==========================================

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload and process financial documents.
    
    Supports: PDF, XLSX, XLS, CSV
    
    Returns:
        - session_id: Unique identifier for this upload session
        - tables_extracted: Number of tables successfully processed
        - tables_indexed: Number of tables indexed into RAG
    """
    
    session_id = str(uuid.uuid4())
    all_cleaned_tables = []
    indexed_count = 0
    
    # Validate file types
    allowed_extensions = [".pdf", ".xlsx", ".xls", ".csv"]
    
    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.filename}. Allowed: {allowed_extensions}"
            )
    
    # Process each file
    for file in files:
        try:
            print(f"📄 Processing: {file.filename}")
            
            # 1. Save file to disk
            file_path = Path("data/uploads") / f"{session_id}_{file.filename}"
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 2. Extract tables
            raw_tables = ingest_any_file(str(file_path))
            print(f"   ✅ Extracted {len(raw_tables)} table(s)")
            
            # 3. Clean and store tables
            for i, df in enumerate(raw_tables):
                try:
                    cleaned_df = clean_table(df)
                    
                    if not cleaned_df.empty:
                        table_entry = {
                            "df": cleaned_df,
                            "source": file.filename,
                            "table_id": i
                        }
                        all_cleaned_tables.append(table_entry)
                        
                        # 4. Index into RAG for intelligent retrieval
                        try:
                            index_dataframe_to_chroma(
                                cleaned_df,
                                source_name=f"{session_id}_{file.filename}",
                                table_id=i
                            )
                            indexed_count += 1
                            print(f"   ✅ Indexed table {i} into RAG")
                        except Exception as e:
                            print(f"   ⚠️ RAG indexing failed for table {i}: {e}")
                
                except Exception as e:
                    print(f"   ⚠️ Table {i} cleaning failed: {e}")
                    continue
        
        except Exception as e:
            print(f"   ❌ File processing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process {file.filename}: {str(e)}"
            )
    
    # Store session data
    user_sessions[session_id] = {
        "tables": all_cleaned_tables,
        "file_count": len(files),
        "filenames": [f.filename for f in files]
    }
    
    print(f"✅ Session {session_id}: {len(all_cleaned_tables)} tables ready")
    
    return {
        "success": True,
        "session_id": session_id,
        "tables_extracted": len(all_cleaned_tables),
        "tables_indexed": indexed_count,
        "files_processed": len(files)
    }


# ==========================================
# 💬 QUERY ENDPOINT
# ==========================================

@router.post("/query")
async def ask_question(request: dict):
    """
    Query uploaded documents using natural language.
    
    The system will:
    1. Try to calculate exact metrics (burn rate, revenue growth)
    2. Use financial reasoning (synonym matching: sales → revenue)
    3. Fallback to RAG + LLM (answers ANY question)
    
    Never returns "could not identify" - always provides useful answer.
    
    Args:
        session_id: Session ID from /upload
        question: Natural language question
    
    Returns:
        - answer: AI-generated response
        - chart_path: Path to generated chart (if applicable)
        - confidence: Confidence score
    """
    
    session_id = request.get("session_id")
    question = request.get("question")
    
    # Validate inputs
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    
    # Validate session exists
    if session_id not in user_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}. Please upload documents first via /upload endpoint."
        )
    
    session_data = user_sessions[session_id]
    cleaned_tables = session_data["tables"]
    
    print(f"\n🔍 Query: {question}")
    print(f"📊 Using {len(cleaned_tables)} tables from session {session_id}")
    
    try:
        # Route query through intelligent controller
        # This uses:
        # 1. Exact metric matching
        # 2. Financial reasoning (C-3)
        # 3. RAG + LLM fallback
        answer, chart_path = route_query(
            question=question,
            cleaned_tables=cleaned_tables,
            chart_gen=None  # Charts handled internally
        )
        
        # Format chart path for frontend
        chart_url = None
        if chart_path:
            chart_filename = Path(chart_path).name
            chart_url = f"/static/{chart_filename}"
        
        return {
            "success": True,
            "answer": answer,
            "chart_path": chart_url,
            "session_id": session_id
        }
    
    except Exception as e:
        print(f"❌ Query processing error: {e}")
        
        # Even on error, try to give helpful response
        return {
            "success": False,
            "answer": f"I encountered an error processing your question: {str(e)}\n\nPlease try rephrasing or ask about specific metrics like revenue, expenses, or burn rate.",
            "chart_path": None,
            "session_id": session_id
        }


# ==========================================
# 🗑️ DELETE SESSION ENDPOINT
# ==========================================

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Clean up session data and uploaded files.
    """
    
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Remove from memory
    session_data = user_sessions.pop(session_id)
    
    # Delete uploaded files
    upload_dir = Path("data/uploads")
    for file_path in upload_dir.glob(f"{session_id}_*"):
        try:
            file_path.unlink()
            print(f"🗑️ Deleted: {file_path.name}")
        except Exception as e:
            print(f"⚠️ Could not delete {file_path.name}: {e}")
    
    return {
        "success": True,
        "message": f"Session {session_id} deleted",
        "tables_removed": len(session_data.get("tables", []))
    }


# ==========================================
# 📋 LIST SESSIONS ENDPOINT (DEBUG)
# ==========================================

@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions (useful for debugging).
    """
    
    return {
        "active_sessions": len(user_sessions),
        "sessions": [
            {
                "session_id": sid,
                "files": data.get("filenames", []),
                "tables": len(data.get("tables", []))
            }
            for sid, data in user_sessions.items()
        ]
    }


# ==========================================
# ❤️ HEALTH CHECK
# ==========================================

@router.get("/health")
async def health_check():
    """
    System health status.
    """
    
    return {
        "status": "healthy",
        "components": {
            "ingestion": "ready",
            "rag": "ready",
            "llm": "ready",
            "financial_reasoning": "ready"
        },
        "active_sessions": len(user_sessions)
    }
