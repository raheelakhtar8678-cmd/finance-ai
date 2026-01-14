import os
import sys
import logging
import shutil
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("docling_setup_test")

# 1. Configure Environment Variables for Custom Storage (E: drive)
# CRITICAL: These must be set BEFORE importing docling/transformers
cache_root = Path(r"E:\finance-ai\cache")
hf_home = cache_root / "huggingface"
docling_home = cache_root / "docling"

os.environ["HF_HOME"] = str(hf_home)
os.environ["DOCLING_HOME"] = str(docling_home)
# some libs use TORCH_HOME or XDG_CACHE_HOME
os.environ["TORCH_HOME"] = str(cache_root / "torch")
os.environ["XDG_CACHE_HOME"] = str(cache_root / "xdg")

logger.info(f"HF_HOME set to: {os.environ['HF_HOME']}")
logger.info(f"DOCLING_HOME set to: {os.environ['DOCLING_HOME']}")

if not cache_root.exists():
    cache_root.mkdir(parents=True, exist_ok=True)

# 2. Import Docling
logger.info("Importing Docling (this may trigger initial setup)...")
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
except ImportError as e:
    logger.error(f"Failed to import docling: {e}")
    sys.exit(1)

# 3. Validation Run
logger.info("Initializing DocumentConverter...")

# Configure options for functionality and potential memory constraints
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False # Disable OCR for speed test
pipeline_options.do_table_structure = False # Disable table structure for minimal resource test
# pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

# Force CPU usage if necessary (though usually auto-detected)
# pipeline_options.accelerator_options.device = "cpu"

try:
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
except Exception as e:
    logger.error(f"Failed to initialize converter: {e}")
    sys.exit(1)

# Use a sample PDF from the user's data
# 4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf seems to be small (~338KB)
sample_pdf = Path(r"E:\finance-ai\data\raw\4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf")

if not sample_pdf.exists():
    logger.error(f"Sample PDF not found at {sample_pdf}")
    # Try finding any pdf
    raw_dir = Path(r"E:\finance-ai\data\raw")
    pdfs = list(raw_dir.glob("*.pdf"))
    if pdfs:
        sample_pdf = pdfs[0]
        logger.info(f"Falling back to {sample_pdf}")
    else:
        sys.exit(1)

logger.info(f"Converting {sample_pdf}...")

try:
    # First run will trigger model download
    logger.info("Starting conversion (models will download to E: drive if missing)...")
    result = converter.convert(sample_pdf)
    logger.info("Conversion successful!")
    
    # Check output
    markdown_output = result.document.export_to_markdown()
    logger.info(f"Generated Markdown length: {len(markdown_output)}")
    # logger.info("Preview:\n" + markdown_output[:500])
    
    # Verify Storage Usage
    logger.info("Verifying storage usage on E: drive...")
    
    def get_dir_size(path):
        total = 0
        if path.exists():
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        return total

    hf_size = get_dir_size(hf_home)
    docling_size = get_dir_size(docling_home)
    
    logger.info(f"HuggingFace Cache Size: {hf_size / 1024 / 1024:.2f} MB")
    logger.info(f"Docling Cache Size: {docling_size / 1024 / 1024:.2f} MB")
    
    if hf_size == 0 and docling_size == 0:
        logger.warning("Cache dirs are empty! Models might have gone to default location or were already cached elsewhere.")
    else:
        logger.info("Storage redirection successful.")

except Exception as e:
    logger.error(f"Conversion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

logger.info("Test complete.")
