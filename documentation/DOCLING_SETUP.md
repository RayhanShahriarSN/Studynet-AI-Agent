# Docling Setup Guide

## ⚠️ Important: Docling Dependencies

Docling requires **PyTorch** and **OCR engines** to work properly. Follow these steps to install correctly.

---

## 🖥️ Installation by Platform

### **Option 1: CPU-Only (Recommended for most users)**

This is lighter and faster to install:

```bash
# Install PyTorch CPU version first
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Then install docling and other requirements
pip install -r requirements.txt
```

### **Option 2: GPU (CUDA) - For faster processing**

If you have NVIDIA GPU:

```bash
# Install PyTorch with CUDA support first
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Then install docling and other requirements
pip install -r requirements.txt
```

### **Option 3: macOS (Apple Silicon M1/M2/M3)**

```bash
# PyTorch for Apple Silicon
pip install torch torchvision

# Then install docling and other requirements
pip install -r requirements.txt
```

---

## 📦 What Gets Installed

When you run `pip install docling`, it automatically downloads:

1. **PyTorch** - Deep learning framework
2. **HuggingFace Models** - Downloaded automatically on first use from:
   - https://huggingface.co/ds4sd/docling-models
3. **EasyOCR** (already in requirements.txt) - For text extraction from images/scanned PDFs

---

## 🧪 Test Docling Installation

```python
# test_docling.py
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("test.pdf")
print("✅ Docling working!")
print(f"Extracted {len(result.document.export_to_markdown())} characters")
```

Run test:
```bash
python test_docling.py
```

**First run**: Will download models from HuggingFace (~500MB-1GB)
**Subsequent runs**: Uses cached models

---

## 🔧 Troubleshooting

### Error: "No module named 'torch'"
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Error: "Failed to download model from HuggingFace"
- **Check internet connection**
- **Set HuggingFace cache directory** (if needed):
  ```bash
  export HF_HOME=/path/to/cache
  ```

### Error: "CUDA not available"
- This is **OK** if you're using CPU-only version
- Docling works fine on CPU, just slightly slower

### Models downloading every time
Models are cached in:
- **Linux/Mac**: `~/.cache/huggingface/`
- **Windows**: `C:\Users\<username>\.cache\huggingface\`

Make sure this directory persists between sessions.

### Want to skip Docling temporarily?

In `api/utils.py`, the code already has a fallback:

```python
# If Docling fails, falls back to PyPDF
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
```

If Docling is not installed, it will use PyPDF instead (basic PDF extraction).

---

## 📊 Docling vs PyPDF Comparison

| Feature | Docling | PyPDF |
|---------|---------|-------|
| **PDF text extraction** | ✅ Advanced | ✅ Basic |
| **Table extraction** | ✅ Yes | ❌ No |
| **Layout preservation** | ✅ Yes | ❌ No |
| **Scanned PDFs (OCR)** | ✅ Yes | ❌ No |
| **Images in PDF** | ✅ Extracted | ❌ Ignored |
| **Installation size** | ~2-3 GB | ~10 MB |
| **Speed** | Medium | Fast |

---

## ✅ Recommended Setup Steps

```bash
# 1. Install PyTorch CPU version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 2. Install all requirements
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Load knowledge base (will download Docling models on first run)
python load_kb.py

# 5. Start server
python manage.py runserver
```

**First-time setup takes longer** (model downloads), but subsequent starts are fast.

---

## 🚀 Alternative: Skip Docling (Lightweight Setup)

If you don't need advanced PDF processing:

1. **Remove Docling from requirements.txt**:
   ```bash
   # Comment out these lines in requirements.txt
   # docling==2.9.2
   # docling-core==2.6.3
   # easyocr==1.7.2
   ```

2. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **System will automatically use PyPDF** (basic but functional)

---

## 🔍 Check What's Being Used

```bash
curl http://localhost:8000/api/knowledge-base/status/
```

Response shows which processor is active:
```json
{
  "document_processor": "docling",  // or "pypdf"
  "ocr_available": true
}
```
