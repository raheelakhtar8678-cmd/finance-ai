# src/ingestion/table_ingester.py
from pathlib import Path
import pandas as pd

# Changed read_csv -> extract_tables_from_csv and read_excel -> extract_tables_from_excel
from src.ingestion.csv_extractor import extract_tables_from_csv
from src.ingestion.excel_extractor import extract_tables_from_excel
# from src.ingestion.table_extractor import extract_tables # LEGACY (pdfplumber)
from src.ingestion.pymupdf_extractor import extract_markdown_with_pymupdf # NEW (pymupdf4llm)


def index_tables_to_rag(tables: list, source_name: str) -> int:
    """
    🎯 PRODUCT-GRADE: Index extracted tables into RAG vector store.
    This enables semantic search across all uploaded documents.
    
    Returns: Number of tables successfully indexed
    """
    indexed_count = 0
    try:
        from src.ai.rag_engine import index_dataframe_to_chroma
        
        for table_idx, table in enumerate(tables):
            df = table.get("df")
            if df is not None and not df.empty:
                index_dataframe_to_chroma(
                    df=df,
                    source_name=source_name,
                    table_id=table_idx,
                    preceding_text=table.get("preceding_text", ""),
                    following_text=table.get("following_text", "")
                )
                indexed_count += 1
        
        print(f"✅ [RAG] Indexed {indexed_count}/{len(tables)} tables from {source_name}")
        
    except Exception as e:
        print(f"⚠️ [RAG] Indexing failed for {source_name}: {e}")
    
    return indexed_count


def ingest_any_file(file_path: str, auto_index_rag: bool = True):
    """
    Unified ingestion entry point.
    
    Args:
        file_path: Path to the file
        auto_index_rag: If True, automatically index tables into RAG vector store
    
    Returns:
        List of extracted tables
    """
    suffix = Path(file_path).suffix.lower()
    source_name = Path(file_path).name

    if suffix == ".pdf":
        tables = extract_markdown_with_pymupdf(file_path)
    elif suffix == ".csv":
        tables = extract_tables_from_csv(file_path)
    elif suffix in [".xls", ".xlsx"]:
        tables = extract_tables_from_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    
    # 🎯 PRODUCT-GRADE: Auto-index into RAG for semantic search
    if auto_index_rag and tables:
        index_tables_to_rag(tables, source_name)
    
    return tables
