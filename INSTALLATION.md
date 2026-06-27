# Installation Guide - Invoice & Shipment Bill Parser Portal

Complete step-by-step installation instructions for all operating systems.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Windows Installation](#windows-installation)
3. [macOS Installation](#macos-installation)
4. [Linux Installation](#linux-installation)
5. [Docker Installation](#docker-installation)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Windows (Fastest)
1. Extract ZIP file
2. Double-click `start.bat`
3. Open http://localhost:5000

### macOS/Linux (Fastest)
1. Extract ZIP file
2. Open terminal in folder
3. Run: `bash start.sh`
4. Open http://localhost:5000

---

## Windows Installation

### Option 1: Automated (Recommended)
```bash
# 1. Extract the ZIP file
# 2. Double-click: start.bat
# Done! Browser opens automatically
```

### Option 2: Manual Installation

#### Step 1: Install Python 3
1. Visit https://www.python.org/downloads/
2. Download Python 3.11 or higher
3. **Important:** Check "Add Python to PATH"
4. Click "Install Now"

#### Step 2: Open Command Prompt
- Press `Win + R`
- Type: `cmd`
- Press Enter

#### Step 3: Navigate to Project Folder
```bash
cd C:\Users\YourName\Downloads\invoice-parser-app
```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Run the Application
```bash
python app.py
```

#### Step 6: Open Browser
Go to: `http://localhost:5000`

#### Step 7: Stop Server
Press `Ctrl + C` in command prompt

---

## macOS Installation

### Option 1: Automated (Recommended)
```bash
# 1. Extract the ZIP file
# 2. Open Terminal (Cmd + Space, type "Terminal")
# 3. Drag the folder into Terminal, then type:
bash start.sh
# Done!
```

### Option 2: Manual Installation

#### Step 1: Install Python 3
Using Homebrew (recommended):
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3
```

Or download from: https://www.python.org/downloads/

#### Step 2: Open Terminal
- Press `Cmd + Space`
- Type: `Terminal`
- Press Enter

#### Step 3: Navigate to Project Folder
```bash
cd ~/Downloads/invoice-parser-app
```

#### Step 4: Create Virtual Environment (Optional but Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 5: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 6: Run the Application
```bash
python3 app.py
```

#### Step 7: Open Browser
Go to: `http://localhost:5000`

#### Step 8: Stop Server
Press `Ctrl + C` in terminal

#### Step 9: Deactivate Virtual Environment (if used)
```bash
deactivate
```

---

## Linux Installation

### Ubuntu/Debian

#### Step 1: Install Python 3 and pip
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

#### Step 2: Navigate to Project Folder
```bash
cd ~/Downloads/invoice-parser-app
```

#### Step 3: Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Run the Application
```bash
python3 app.py
```

#### Step 6: Open Browser
Go to: `http://localhost:5000`

#### Step 7: Stop Server
Press `Ctrl + C` in terminal

### Fedora/CentOS/RHEL
```bash
sudo dnf install python3 python3-pip
# Then follow steps 2-7 above
```

### Arch Linux
```bash
sudo pacman -S python python-pip
# Then follow steps 2-7 above
```

---

## Docker Installation

### Option 1: Docker Desktop (All Platforms)

#### Step 1: Install Docker Desktop
- Windows: https://www.docker.com/products/docker-desktop
- macOS: https://www.docker.com/products/docker-desktop
- Linux: https://docs.docker.com/engine/install/

#### Step 2: Extract ZIP and Open Terminal
```bash
cd invoice-parser-app
```

#### Step 3: Run with Docker Compose (Easiest)
```bash
docker-compose up
```

Or manually with Docker:
```bash
# Build image
docker build -t invoice-parser .

# Run container
docker run -p 5000:5000 invoice-parser
```

#### Step 4: Open Browser
Go to: `http://localhost:5000`

#### Step 5: Stop Container
Press `Ctrl + C` in terminal

### Option 2: Using Docker CLI

```bash
# Build the image
docker build -t invoice-parser-app .

# Run the container
docker run -d \
  --name invoice-app \
  -p 5000:5000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/parser.db:/app/parser.db \
  invoice-parser-app

# View logs
docker logs -f invoice-app

# Stop container
docker stop invoice-app

# Remove container
docker rm invoice-app
```

---

## Python Virtual Environment (Recommended)

Virtual environments isolate your project dependencies.

### Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Deactivate Virtual Environment
```bash
# Windows
venv\Scripts\deactivate

# macOS/Linux
deactivate
```

---

## Verify Installation

Run the validation script:
```bash
python validate.py
```

Expected output:
```
✓ PASS - Python Version
✓ PASS - Dependencies
✓ PASS - File Structure
✓ PASS - Directories
✓ PASS - Database
✓ PASS - Import Tests
✓ PASS - Port Availability

✓ All checks passed! System is ready to run.
```

---

## Troubleshooting

### "Python is not installed"
**Windows:**
- Download from https://www.python.org/downloads/
- **Must check:** "Add Python to PATH"

**macOS:**
```bash
brew install python3
```

**Linux:**
```bash
sudo apt-get install python3 python3-pip
```

### "pip: command not found"
Try using `pip3` instead:
```bash
pip3 install -r requirements.txt
```

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### "Port 5000 already in use"
Use a different port:
```bash
python -c "from app import app; app.run(port=5001)"
```

Or kill the process using port 5000:

**Windows:**
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
lsof -i :5000
kill -9 <PID>
```

### "Permission denied" on macOS/Linux
Make scripts executable:
```bash
chmod +x start.sh
chmod +x run_locally.py
```

### "PDF extraction not working"
- Ensure PDF is digital (not scanned)
- Try opening PDF in Adobe Reader first
- Check that PDF is not corrupted

### "Excel export shows empty file"
- Submit at least one invoice/shipment first
- Check database: `sqlite3 parser.db "SELECT COUNT(*) FROM invoices;"`

### Virtual environment issues
Delete and recreate:
```bash
rm -rf venv  # or rmdir venv on Windows
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.8+ |
| RAM | 256 MB minimum |
| Disk Space | 500 MB |
| Browser | Chrome, Firefox, Safari, Edge |
| Internet | Not required (local only) |

---

## Next Steps

1. ✅ Install Python
2. ✅ Extract ZIP file
3. ✅ Install dependencies: `pip install -r requirements.txt`
4. ✅ Run: `python app.py` or `bash start.sh`
5. ✅ Open: http://localhost:5000
6. ✅ Start parsing PDFs!

---

## Getting Help

1. Check TROUBLESHOOTING section above
2. Review README.md
3. Run: `python validate.py`
4. Check Flask console output for errors

---

**Installation Complete!** 🎉

Your Invoice & Shipment Bill Parser Portal is ready to use.
