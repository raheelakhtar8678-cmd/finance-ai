# app.py
import os
import tempfile
import pandas as pd
from gradio import components
import gradio as gr

# Set cache dirs to /tmp (required for Spaces)
os.environ["HF_HOME"] = "/tmp/hf_cache"
os.environ["CHROMA_DB_PATH"] = "/tmp/chroma_db"

# Import your pipeline
from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_table
from src.ai.rag_engine import index_dataframe_to_chroma, ask

# Global state: keep ChromaDB in memory
indexed = False

def process_file(file):
    global indexed
    if indexed:
        return "✅ Already indexed. Ask your question!", None

    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    # Ingest → Clean → Index
    tables = ingest_any_file(tmp_path)
    cleaned_tables = [clean_table(df) for df in tables]

    for i, df in enumerate(cleaned_tables):
        index_dataframe_to_chroma(df, file.name, i)

    indexed = True
    return f"✅ Processed {len(tables)} tables. Ready for questions!", None

def ask_question(query):
    if not indexed:
        return "❗ Please upload a file first.", "", []
    result = ask(query)
    
    # Format answer
    if "answer" in result:
        answer = str(result["answer"])
        note = result.get("note", "")
        if note:
            answer += f"\n\n💡 {note}"
    elif "error" in result:
        answer = f"⚠️ {result.get('message', 'RAG failed')}"
    else:
        answer = "❓ Could not parse response."

    # Show retrieved context
    retrieved_text = ""
    if "retrieved" in result:
        for doc in result["retrieved"]:
            retrieved_text += f"[{doc['meta']['source']}] {doc['text']}\n\n"

    return answer, retrieved_text

# Gradio UI
with gr.Blocks(title="Financial AI") as demo:
    gr.Markdown("## 💰 Financial AI: Upload PDF/Excel/CSV → Ask Questions")
    with gr.Row():
        with gr.Column():
            file_input = gr.File(label="Upload Financial Document (PDF, XLSX, CSV)")
            upload_btn = gr.Button("Process File")
            status = gr.Textbox(label="Status", interactive=False)
        with gr.Column():
            query = gr.Textbox(label="Ask a financial question", placeholder="What is the YoY revenue growth?")
            ask_btn = gr.Button("Ask")
            answer = gr.Textbox(label="AI Answer", interactive=False)
            context = gr.Textbox(label="Retrieved Context", lines=10, interactive=False)

    upload_btn.click(process_file, inputs=file_input, outputs=[status, query])
    ask_btn.click(ask_question, inputs=query, outputs=[answer, context])

demo.launch()