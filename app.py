# app.py
"""
Financial AI - Professional MVP
Premium UI with Charts, Session Isolation, and Professional Styling
"""
import os
import tempfile
import uuid
import pandas as pd
import gradio as gr

# Set cache dirs
os.environ["HF_HOME"] = os.path.abspath("data/cache/hf")
os.environ["CHROMA_DB_PATH"] = os.path.abspath("data/db/chroma")

# Import pipeline
from src.ingestion.table_ingester import ingest_any_file
from src.analysis.query_controller import route_query
from src.ai.rag_engine import index_dataframe_to_chroma
from src.processing.clean_tables import clean_all_tables
from src.visualization.chart_generator import generate_chart

# Try to import auditor
try:
    from src.ai.auditor import FinancialAuditor
    auditor = FinancialAuditor()
except:
    auditor = None


def process_files(files, session_state):
    """Process uploaded files with session isolation."""
    if not files:
        return "❌ No files uploaded.", None, session_state, None
    
    if session_state is None:
        session_state = {"tables": [], "session_id": str(uuid.uuid4()), "indexed": False}
    
    session_id = session_state["session_id"]
    total_tables = 0
    file_names = []

    for file_obj in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_obj.name)[1]) as tmp:
            if hasattr(file_obj, 'read'):
                tmp.write(file_obj.read())
            else:
                with open(file_obj.name, 'rb') as f:
                    tmp.write(f.read())
            tmp_path = tmp.name

        tables = ingest_any_file(tmp_path)
        cleaned_items = clean_all_tables(tables)
        session_state["tables"].extend(cleaned_items)
        file_names.append(os.path.basename(file_obj.name))

        for item in cleaned_items:
            source_name = f"{session_id}_{os.path.basename(file_obj.name)}"
            index_dataframe_to_chroma(
                df=item["df"], 
                source_name=source_name,
                table_id=item["page"],
                preceding_text=item.get("preceding_text", ""),
                following_text=item.get("following_text", ""),
                markdown_content=item.get("markdown")
            )
        
        total_tables += len(tables)

    session_state["indexed"] = True
    session_state["files"] = file_names
    
    status = f"""
### ✅ Documents Processed Successfully

| Metric | Value |
|--------|-------|
| Files | {len(files)} |
| Tables Extracted | {total_tables} |
| Session | `{session_id[:8]}...` |

**Files:** {', '.join(file_names)}

*Ready for analysis!*
"""
    
    print(f"📂 [SESSION {session_id[:8]}] Processed {len(files)} files, {total_tables} tables")
    
    return status, None, session_state, gr.update(interactive=True)


def ask_question(query, session_state):
    """Answer question with chart generation."""
    if session_state is None or not session_state.get("indexed"):
        return "⚠️ Please upload documents first.", None, session_state
    
    if not query or not query.strip():
        return "⚠️ Please enter a question.", None, session_state
    
    session_id = session_state["session_id"]
    tables = session_state["tables"]
    
    print(f"🔍 [SESSION {session_id[:8]}] Query: {query[:50]}...")
    
    try:
        # Get answer with chart support
        answer, chart_path = route_query(
            query, 
            tables=tables,
            chart_gen=generate_chart,
            session_id=session_id
        )
        
        # Load chart image if exists
        chart_image = None
        if chart_path and os.path.exists(chart_path):
            chart_image = chart_path
            print(f"📊 Chart generated: {chart_path}")
        
        return answer, chart_image, session_state
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return f"❌ Error processing query: {str(e)}", None, session_state


# Custom CSS for professional look
CUSTOM_CSS = """
.gradio-container {
    max-width: 1200px !important;
    margin: auto !important;
}
.main-header {
    text-align: center;
    background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 20px;
    color: white;
}
.main-header h1 {
    margin: 0;
    font-size: 2.5em;
    font-weight: 700;
}
.main-header p {
    margin: 10px 0 0 0;
    opacity: 0.9;
    font-size: 1.1em;
}
.feature-badge {
    display: inline-block;
    padding: 5px 12px;
    background: rgba(255,255,255,0.2);
    border-radius: 20px;
    margin: 5px;
    font-size: 0.85em;
}
.upload-section {
    background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    padding: 20px;
    border-radius: 12px;
    border: 2px dashed #cbd5e1;
}
.results-section {
    background: #ffffff;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}
.chart-container {
    background: #f8fafc;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}
footer {
    text-align: center;
    padding: 20px;
    color: #64748b;
    font-size: 0.9em;
}
"""

# Build Professional UI
with gr.Blocks(
    title="Financial AI Analyst",
    css=CUSTOM_CSS,
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter")
    )
) as demo:
    
    # Session State
    session_state = gr.State(value=None)
    
    # Header
    gr.HTML("""
    <div class="main-header">
        <h1>💼 Financial AI Analyst</h1>
        <p>Enterprise-Grade Financial Document Analysis with AI</p>
        <div style="margin-top: 15px;">
            <span class="feature-badge">📄 PDF/Excel/CSV</span>
            <span class="feature-badge">📊 Auto Charts</span>
            <span class="feature-badge">🔒 Session Isolated</span>
            <span class="feature-badge">⚡ Real-time Analysis</span>
        </div>
    </div>
    """)
    
    with gr.Row():
        # Left Column - Upload
        with gr.Column(scale=1):
            gr.Markdown("### 📁 Upload Documents")
            file_input = gr.File(
                label="Drop financial documents here",
                file_count="multiple",
                file_types=[".pdf", ".xlsx", ".xls", ".csv"],
                elem_classes=["upload-section"]
            )
            upload_btn = gr.Button("🚀 Process Documents", variant="primary", size="lg")
            status = gr.Markdown(value="*Upload files to begin analysis*")
        
        # Right Column - Query
        with gr.Column(scale=2):
            gr.Markdown("### 💬 Ask Questions")
            query = gr.Textbox(
                label="Your Question",
                placeholder="e.g., What was the revenue growth YoY? Compare operating margins across segments...",
                lines=2
            )
            ask_btn = gr.Button("🔍 Analyze", variant="primary", size="lg", interactive=False)
            
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### 📝 Analysis Results")
                    answer = gr.Markdown(
                        value="*Results will appear here after you ask a question*",
                        elem_classes=["results-section"]
                    )
                with gr.Column(scale=1):
                    gr.Markdown("### 📊 Visualization")
                    chart_output = gr.Image(
                        label="Generated Chart",
                        elem_classes=["chart-container"],
                        show_label=False
                    )
    
    # Example Queries
    gr.Markdown("### 💡 Example Questions")
    with gr.Row():
        ex1 = gr.Button("📈 What is the revenue trend?", size="sm", variant="secondary")
        ex2 = gr.Button("💰 Compare profit margins", size="sm", variant="secondary")
        ex3 = gr.Button("📊 Operating income by segment", size="sm", variant="secondary")
        ex4 = gr.Button("📉 YoY growth analysis", size="sm", variant="secondary")
    
    # Footer
    gr.HTML("""
    <footer>
        <p>🔒 Your documents are processed securely and isolated per session</p>
        <p>Powered by RAG + LLM Technology | Built for Enterprise Financial Analysis</p>
    </footer>
    """)
    
    # Event Handlers
    upload_btn.click(
        process_files,
        inputs=[file_input, session_state],
        outputs=[status, query, session_state, ask_btn]
    )
    
    ask_btn.click(
        ask_question,
        inputs=[query, session_state],
        outputs=[answer, chart_output, session_state]
    )
    
    # Example query handlers
    ex1.click(lambda: "What is the revenue trend over the reported periods?", outputs=query)
    ex2.click(lambda: "Compare gross profit margin and operating profit margin", outputs=query)
    ex3.click(lambda: "What is the operating income breakdown by geographic segment?", outputs=query)
    ex4.click(lambda: "Analyze the year-over-year growth in key financial metrics", outputs=query)


if __name__ == "__main__":
    # Support Render.com deployment
    port = int(os.environ.get("PORT", 7860))
    server_name = os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1")
    demo.launch(
        server_name=server_name,
        server_port=port,
        share=False
    )