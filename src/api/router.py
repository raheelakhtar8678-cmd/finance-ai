# src/api/router.py

from fastapi import APIRouter, UploadFile, File
import uuid
from pathlib import Path
import shutil
import traceback
from typing import Dict, Any

from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables

# Analysis Logic
try:
    from src.analysis.financial_reasoning import compute_metric_with_reasoning
    from src.analysis.query_controller import route_query
except ImportError as e:
    print(f"⚠️ Warning: Analysis modules not found: {e}")
    compute_metric_with_reasoning = None
    route_query = None

router = APIRouter()
user_sessions = {}

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    session_id = str(uuid.uuid4())
    user_sessions[session_id] = {"tables": [], "files": []}
    
    total_tables = 0
    for file in files:
        file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 🎯 FAST: Extract tables synchronously (required for queries)
        tables = ingest_any_file(str(file_path), auto_index_rag=False)  # Skip auto RAG for speed
        cleaned_tables = clean_all_tables(tables)

        # Add source to the already wrapped tables
        for item in cleaned_tables:
            item["source"] = file.filename
            
        user_sessions[session_id]["tables"].extend(cleaned_tables)
        user_sessions[session_id]["files"].append(str(file_path))
        total_tables += len(cleaned_tables)
        
        # 🎯 ASYNC: Index to RAG in background (non-blocking)
        import threading
        def background_index(tables_to_index, filename):
            try:
                from src.ai.rag_engine import index_dataframe_to_chroma, index_markdown_content
                
                # 🎯 NEW: Handle Markdown-based pipeline (PyMuPDF4LLM)
                # If we detect a PyMuPDF4LLM object (usually one big doc object)
                if tables_to_index and tables_to_index[0].get("method") == "pymupdf4llm":
                    md_content = tables_to_index[0].get("markdown", "")
                    if md_content:
                        index_markdown_content(md_content, filename)
                        print(f"✅ [BACKGROUND] Indexed markdown document {filename} into RAG")
                    return

                # 🎯 LEGACY: Handle DataFrame-based pipeline (CSV, Excel, old PDF)
                for table_idx, table in enumerate(tables_to_index):
                    df = table.get("df")
                    if df is not None and not df.empty:
                        index_dataframe_to_chroma(
                            df=df,
                            source_name=filename,
                            table_id=table_idx,
                            preceding_text=table.get("preceding_text", ""),
                            following_text=table.get("following_text", "")
                        )
                print(f"✅ [BACKGROUND] Indexed {len(tables_to_index)} tables from {filename} into RAG")
            except Exception as e:
                print(f"⚠️ [BACKGROUND] RAG indexing failed for {filename}: {e}")
        
        thread = threading.Thread(target=background_index, args=(cleaned_tables, file.filename))
        thread.daemon = True
        thread.start()

    return {"success": True, "session_id": session_id, "files": len(files), "tables": total_tables}

@router.post("/query")
async def query_endpoint(request: Dict[str, Any]):
    try:
        session_id = request.get("session_id")
        question = request.get("question", "")

        if not session_id or session_id not in user_sessions:
            return {"success": False, "answer": "Invalid session.", "session_id": session_id}

        tables = user_sessions[session_id]["tables"]
        q = question.lower()
        
        # ✅ UNIFIED ROUTING
        # Delegate specific metric detection and RAG fallbacks 
        # ENTIRELY to the query_controller. 
        # Do not try to pre-optimize here.
        if route_query:
            from src.visualization.chart_generator import generate_chart
            
            print(f"🚀 [ROUTER] Passing to Controller: {question}")
            
            answer, chart_path = route_query(
                question=question,
                tables=tables,
                chart_gen=generate_chart,
                session_id=session_id
            )
            return {
                "success": True,
                "answer": answer,
                "chart_path": chart_path,
                "session_id": session_id
            }
        
        return {"success": False, "answer": "Logic modules missing.", "session_id": session_id}

    except Exception as e:
        print("❌ Query error:", e)
        print(traceback.format_exc())
        return {"success": False, "answer": "Internal error.", "session_id": session_id}
