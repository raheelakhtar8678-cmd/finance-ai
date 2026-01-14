# 💼 Financial AI Analyst

> **Enterprise-Grade Financial Document Analysis with AI**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/raheelakhtar8678-cmd/finance-ai)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🚀 Features

- **📄 Multi-format Support** - PDF, Excel (.xlsx/.xls), and CSV files
- **🤖 AI-Powered Analysis** - RAG pipeline with LLM integration (Gemini + OpenRouter fallback)
- **📊 Auto Chart Generation** - Automatic visualization for financial data
- **🔒 Session Isolation** - Each user session is fully isolated
- **⚡ Real-time Processing** - Fast table extraction and analysis
- **✅ Financial Auditor** - Built-in verification for data accuracy

## 📸 Demo

Upload your financial documents (10-K, 10-Q, earnings reports) and ask questions like:
- "What is the revenue trend?"
- "Compare gross margin vs operating margin"
- "Operating income by geographic segment"
- "Year-over-year growth analysis"

## 🛠️ Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/raheelakhtar8678-cmd/finance-ai.git
cd finance-ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (GEMINI_API_KEY, OPENROUTER_API_KEY)

# Run the application
python app.py
```

### 🌐 Deploy to Render (Free)

1. Fork this repository
2. Go to [Render.com](https://render.com) and sign up
3. Click "New" → "Web Service"
4. Connect your GitHub repo
5. Use these settings:
   - **Runtime**: Python
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `python app.py`
6. Add environment variables:
   - `GEMINI_API_KEY` - Your Google Gemini API key
   - `OPENROUTER_API_KEY` - (Optional) Fallback LLM

## 📁 Project Structure

```
finance-ai/
├── app.py                 # Main Gradio application
├── src/
│   ├── ai/               # RAG engine, embeddings, auditor
│   ├── analysis/         # Query routing, financial formulas
│   ├── ingestion/        # PDF, Excel, CSV extractors
│   ├── processing/       # Table cleaning
│   └── visualization/    # Chart generation
├── requirements.txt      # Python dependencies
└── render.yaml          # Render deployment config
```

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for LLM |
| `OPENROUTER_API_KEY` | No | Fallback LLM via OpenRouter |

## 📊 Supported Document Types

- **SEC Filings**: 10-K, 10-Q, 8-K
- **Financial Statements**: Income Statement, Balance Sheet, Cash Flow
- **Excel Reports**: Any structured financial data
- **CSV Files**: Tabular financial data

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - feel free to use for personal or commercial projects.

---

**Built with ❤️ using Python, Gradio, ChromaDB, and Google Gemini**
