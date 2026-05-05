#!/bin/bash
set -e

# Configuration
PYTHON_VERSION="3.9.18"
RELEASE_TAG="20240224"
PYTHON_ARCHIVE="cpython-${PYTHON_VERSION}+${RELEASE_TAG}-x86_64-unknown-linux-gnu-install_only.tar.gz"
PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${RELEASE_TAG}/${PYTHON_ARCHIVE}"

# Persistent download directory in project root
DOWNLOADS_DIR="downloads"
mkdir -p "$DOWNLOADS_DIR"

# OCR Models Configuration
# For old systems (like BCLinux 8.2), we MUST use Python 3.9 to get a compatible paddlepaddle wheel.
ENABLE_OCR_BUNDLE="${ENABLE_OCR_BUNDLE:-1}"
# If set to 0, local PaddleOCR libraries (400MB+) will be EXCLUDED.
# The app will fallback to Multimodal LLM (Vision) if available via API.
PRELOAD_OCR_MODELS="${PRELOAD_OCR_MODELS:-0}"
MODELS_DIR="models/ocr"
mkdir -p "$MODELS_DIR"
PADDLEX_CACHE_DIR="models/paddlex_cache"
mkdir -p "$PADDLEX_CACHE_DIR"

BUILD_DIR="build_env"
PYTHON_DIR="$BUILD_DIR/python"
VENV_DIR="$BUILD_DIR/venv"

echo "Starting build process (Backend Only) with Portable Python ${PYTHON_VERSION}..."

# Optional Fast Mode (skip pip install if venv is ready)
FAST_MODE="${FAST_MODE:-0}"

# 0. Build Frontend (SKIP per user request: "只打后台包")
# echo "Building Frontend..."
# ... (skipping actual build)

# 0.1 Prepare Backend Static Directory (Use existing dist if available)
echo "Preparing backend/static..."
rm -rf backend/static
mkdir -p backend/static
if [ -d "frontend/dist" ]; then
    if [ -z "$(ls -A frontend/dist)" ]; then
        echo "Error: frontend/dist exists but is empty!"
        echo "Please run 'bash build_frontend_package.sh' first to build frontend assets."
        exit 1
    fi
    cp -r frontend/dist/* backend/static/
    echo "Existing frontend assets copied to backend/static."
else
    echo "Error: frontend/dist not found!"
    echo "Please run 'bash build_frontend_package.sh' first to build frontend assets."
    exit 1
fi

# 1. Prepare Build Directory
mkdir -p "$BUILD_DIR"

# 2. Download Portable Python (Persistent storage)
if [ ! -d "$PYTHON_DIR" ]; then
    ARCHIVE_PATH="$DOWNLOADS_DIR/$PYTHON_ARCHIVE"
    if [ ! -f "$ARCHIVE_PATH" ]; then
        echo "Downloading Portable Python to $ARCHIVE_PATH..."
        curl -L -C - --retry 5 --retry-delay 5 -o "$ARCHIVE_PATH" "$PYTHON_URL"
    else
        echo "Archive found in $DOWNLOADS_DIR, checking integrity..."
        if ! tar -tzf "$ARCHIVE_PATH" >/dev/null 2>&1; then
            echo "Archive corrupted. Redownloading..."
            rm "$ARCHIVE_PATH"
            curl -L -C - --retry 5 --retry-delay 5 -o "$ARCHIVE_PATH" "$PYTHON_URL"
        else
             echo "Archive is good."
        fi
    fi

    echo "Extracting Python..."
    tar -xzf "$ARCHIVE_PATH" -C "$BUILD_DIR"
    
    if [ ! -f "$PYTHON_DIR/bin/python3" ]; then
        echo "Error: Python binary not found at $PYTHON_DIR/bin/python3"
        exit 1
    fi
    echo "Portable Python installed."
else
    echo "Portable Python already exists in $PYTHON_DIR."
fi

# 2.1 Download and Prepare OCR Models (Offline support)
if [ "$ENABLE_OCR_BUNDLE" = "1" ]; then
    echo "Preparing OCR cache directory..."
    mkdir -p "$PADDLEX_CACHE_DIR"
else
    echo "OCR bundle disabled (ENABLE_OCR_BUNDLE=0), skip OCR cache preparation."
fi

# 3. Create Virtual Environment (Reuse if exists)
if [ ! -f "$VENV_DIR/bin/python3" ]; then
    echo "Creating virtual environment..."
    rm -rf "$VENV_DIR"
    "$PYTHON_DIR/bin/python3" -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists. Reusing..."
fi

# 4. Install Dependencies
if [ "$FAST_MODE" = "1" ] && [ -f "$VENV_DIR/bin/pyinstaller" ]; then
    echo "FAST_MODE=1: Skipping dependency installation."
    PIP="$VENV_DIR/bin/pip"
else
    echo "Installing dependencies..."
    PIP="$VENV_DIR/bin/pip"
    "$PIP" install --upgrade pip
    if [ -f "backend/requirements.txt" ]; then
        "$PIP" install -r backend/requirements.txt
    else
        "$PIP" install -r requirements.txt
    fi
    "$PIP" install captcha passlib "bcrypt==4.0.1" pyyaml requests cffi python-dotenv python-jose jinja2 markupsafe pandas openpyxl python-docx
    if [ "$ENABLE_OCR_BUNDLE" = "1" ]; then
        echo "Installing legacy PaddleOCR for better compatibility..."
        "$PIP" cache purge
        # Ensure standard opencv with GUI dependencies is NOT installed
        "$PIP" uninstall -y opencv-python opencv-contrib-python opencv-contrib-python-headless
        
        # Force reinstall a headless OpenCV wheel. The non-headless and headless
        # wheels share cv2 files, so uninstalling opencv-python can remove cv2
        # even when pip thinks opencv-python-headless is already satisfied.
        "$PIP" install "opencv-python-headless==4.10.0.84" --force-reinstall --no-deps
        
        # Install rapidocr WITHOUT its dependencies to prevent it from pulling the wrong opencv
        "$PIP" install "rapidocr-onnxruntime>=1.3.0" --no-deps
        
        # Manually install rapidocr's other required dependencies (excluding opencv)
        "$PIP" install pyclipper Shapely PyYAML Pillow onnxruntime tqdm
    else
        echo "Skipping paddleocr/paddlepaddle install (OCR disabled)."
    fi
    "$PIP" install "patchelf==0.17.2"
    "$PIP" install pyinstaller staticx scons

    # Force numpy downgrade to fix ABI compatibility with older OpenCV/PaddleOCR
    echo "Forcing numpy downgrade to fix ABI compatibility..."
    "$PIP" install "numpy<2.0.0" --force-reinstall
    "$PIP" install "opencv-python-headless==4.10.0.84" --force-reinstall --no-deps

    echo "Forcing legacy bcrypt wheel for old glibc compatibility..."
    "$PIP" install "bcrypt==4.0.1" --force-reinstall
fi

# 5. Locate Dependencies
PYTHON_BIN="$VENV_DIR/bin/python3"
CAPTCHA_DIR=$("$PYTHON_BIN" -c "import captcha; import os; print(os.path.dirname(captcha.__file__))")
echo "Found captcha at: $CAPTCHA_DIR"
if [ "$ENABLE_OCR_BUNDLE" = "1" ]; then
    RAPIDOCR_DIR=$("$PYTHON_BIN" -c "import rapidocr_onnxruntime; import os; print(os.path.dirname(rapidocr_onnxruntime.__file__))")
    echo "Found rapidocr at: $RAPIDOCR_DIR"
fi

# 5.1 Validate Imports
echo "Validating imports..."
if [ -f "validate_imports.py" ]; then
    "$PYTHON_BIN" validate_imports.py
else
    "$PYTHON_BIN" <<'EOF'
imports = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "psycopg2",
    "pgvector",
    "pandas",
    "openpyxl",
    "docx",
    "requests",
    "jinja2",
    "markupsafe",
    "captcha",
    "jose",
    "bcrypt",
]
failed = []
for name in imports:
    try:
        __import__(name)
    except Exception as exc:
        failed.append((name, str(exc)))
if failed:
    for name, error in failed:
        print(f"[import failed] {name}: {error}")
    raise SystemExit(1)
EOF
fi
echo "Imports validated successfully."

# 6. Generate Spec File
echo "Generating PyInstaller Spec file..."
PYI_MAKESPEC="$VENV_DIR/bin/pyi-makespec"

# CLEAR PYINSTALLER CACHE COMPLETELY
rm -rf ~/.cache/pyinstaller

# Generate basic spec
# Note: We include backend/static as 'static' so it's bundled at the root of the extract dir or _MEIPASS
OCR_PYI_ARGS=()
if [ "$ENABLE_OCR_BUNDLE" = "1" ]; then
    OCR_PYI_ARGS=(
        --hidden-import rapidocr_onnxruntime
        --hidden-import onnxruntime
        --add-data "$RAPIDOCR_DIR:rapidocr_onnxruntime"
    )
fi

"$PYI_MAKESPEC" --onefile --name ops-agent --noupx \
    --paths backend \
    --hidden-import requests \
    --hidden-import rag \
    --hidden-import rag.qa \
    --hidden-import rag.retriever \
    --hidden-import rag.loader \
    --hidden-import rag.splitter \
    --hidden-import llm \
    --hidden-import llm.factory \
    --hidden-import llm.mock_client \
    --hidden-import llm.ollama_client \
    --hidden-import llm.zhipu_client \
    --hidden-import llm.openai_client \
    --hidden-import openai \
    --hidden-import db \
    --hidden-import auth \
    --hidden-import uvicorn \
    --hidden-import passlib.handlers.bcrypt \
    --hidden-import _cffi_backend \
    --hidden-import pgvector.sqlalchemy \
    --hidden-import psycopg2 \
    --hidden-import pandas \
    --hidden-import openpyxl \
    --hidden-import docx \
    --hidden-import docx.oxml \
    --hidden-import docx.shared \
    --hidden-import docx.enum.text \
    --hidden-import docx_converter \
    --hidden-import tiktoken \
    --hidden-import jinja2 \
    --hidden-import markupsafe \
    --add-data "$CAPTCHA_DIR/data:captcha/data" \
    "${OCR_PYI_ARGS[@]}" \
    --add-data "backend/static:static" \
    backend/main.py

# 7. Modify Spec File to Exclude Incompatible System Libraries
echo "Modifying Spec file to exclude system libraries..."
"$PYTHON_BIN" <<EOF
import sys

spec_file = 'ops-agent.spec'
with open(spec_file, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if 'a = Analysis(' in line:
        pass
    # Insert filtering logic after Analysis is done, usually before PYZ
    if 'pyz = PYZ(' in line:
        # Insert before this line
        new_lines.pop() # Remove the PYZ line momentarily
        new_lines.append("# Filter out incompatible system libraries (libgcc_s, libstdc++)\n")
        new_lines.append("a.binaries = [x for x in a.binaries if 'libgcc_s' not in x[0] and 'libstdc++' not in x[0]]\n")
        new_lines.append(line) # Put PYZ line back

with open(spec_file, 'w') as f:
    f.writelines(new_lines)
EOF

# 8. Build from Spec
echo "Building from Spec..."
PYINSTALLER="$VENV_DIR/bin/pyinstaller"
"$PYINSTALLER" --clean --noconfirm ops-agent.spec

# 9. Final Packaging (Intranet Binary Package)
RM_DIR="ops-agent-package"
rm -rf "$RM_DIR"
mkdir -p "$RM_DIR"

echo "Copying binary and intranet config..."
cp "dist/ops-agent" "$RM_DIR/ops-agent"

# Use the checked-in intranet config template when available.
if [ -f "config.ollama.local.yaml" ]; then
    cp "config.ollama.local.yaml" "$RM_DIR/config.yaml"
elif [ -f "backend/config.ollama.local.yaml" ]; then
    cp "backend/config.ollama.local.yaml" "$RM_DIR/config.yaml"
else
    cat > "$RM_DIR/config.yaml" <<EOF
database:
  host: "127.0.0.1"
  port: 5432
  user: "ops_user"
  password: "ops_password"
  dbname: "ops_agent"

llm:
  provider: "ollama"
  ollama_base_url: "http://127.0.0.1:11434"
  model: "qwen2.5:3b"
  embedding_model: "nomic-embed-text:latest"
  embedding_dimension: 768
  timeout: 120
  embedding_timeout: 120

retrieval:
  vector_top_k: 12
  keyword_top_k: 20
  bm25_top_k: 20
  bm25_max_docs: 50000
  fusion_top_k: 20
  final_top_k: 5
  rrf_k: 60
  rerank_enabled: true
  rerank_provider: "local"
  rerank_endpoint: ""
  rerank_timeout: 30
  context_expand_window: 1
  create_vector_index: true

server:
  host: "0.0.0.0"
  port: 9020
EOF
fi

# Create simple README for binary
cat > "$RM_DIR/README.txt" <<EOF
智能运维问答机器人 (内网单文件版)
================================

启动步骤:
1. 赋予执行权限:
   chmod +x ops-agent
2. 启动程序:
   ./ops-agent

注意:
- 本程序已内置前端静态资源，无需额外的 templates 或 static 文件夹。
- 如果需要修改配置，请编辑 'config.yaml'。
EOF

# Create ZIP archive
echo "Creating ZIP archive..."
"$PYTHON_BIN" <<EOF
import shutil
shutil.make_archive('ops-agent-linux-x64', 'zip', 'ops-agent-package')
EOF

# 10. (Optional) Cleanup Frontend archives - Skip per user request "只需要输出ops-agent二进制文件"
# ... existing frontend packaging code will be removed or commented out ...

echo "Build complete! Output: ops-agent-linux-x64.zip"

# Cleanup intermediate artifacts. Keep build_env by default because deleting a
# large Linux venv on a Windows-mounted Docker volume can take a very long time.
echo "Cleaning up generated packaging artifacts..."
rm -rf "$RM_DIR"
rm -rf dist build ops-agent.spec
if [ "${CLEAN_BUILD_ENV:-0}" = "1" ]; then
    echo "CLEAN_BUILD_ENV=1: removing build_env..."
    rm -rf "$BUILD_DIR"
else
    echo "Keeping build_env cache. Set CLEAN_BUILD_ENV=1 to remove it."
fi
exit 0
