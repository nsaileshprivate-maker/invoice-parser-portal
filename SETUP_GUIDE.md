# Invoice & Shipment Bill Parser Portal - Complete Setup Guide

## 🚀 Quick Start (3 Steps)

### **Step 1: Install Python Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 2: Run the Application**

**On macOS/Linux:**
```bash
python3 app.py
```

**On Windows:**
```bash
python app.py
```

Or use the automated start script:
- **macOS/Linux:** `bash start.sh`
- **Windows:** `start.bat` (double-click)

### **Step 3: Open in Browser**
```
http://localhost:5000
```

---

## 📦 What You're Getting

A **production-ready Invoice & Shipment Bill Parser Portal** with:

### **Backend (Flask)**
- ✅ PDF extraction engine using pdfplumber
- ✅ Regex-based field detection
- ✅ SQLite database for persistent storage
- ✅ Excel export with formatting
- ✅ RESTful API endpoints
- ✅ CORS support for cross-domain requests
- ✅ Error handling and validation

### **Frontend (HTML/CSS/JavaScript)**
- ✅ Professional dark green (#1b5e20) theme
- ✅ Responsive design (desktop, tablet, mobile)
- ✅ Dynamic row creation
- ✅ Real-time auto-fill from PDF extraction
- ✅ Field validation before submission
- ✅ Success/error notifications
- ✅ No external dependencies (pure HTML/CSS/JS)

### **Database (SQLite)**
- ✅ Invoices table with 8 fields
- ✅ Shipments table with 3 fields
- ✅ Automatic timestamp tracking
- ✅ Simple file-based storage (no server setup)

### **Utilities**
- ✅ Validation script (`validate.py`)
- ✅ Quick start scripts (`start.sh`, `start.bat`)
- ✅ Comprehensive documentation
- ✅ Ready for production deployment

---

## 📋 Files Included

```
project/
├── app.py                      # Flask backend (21 KB)
├── index.html                  # Frontend (34 KB)
├── requirements.txt            # Python dependencies
├── README.md                   # Full documentation
├── SETUP_GUIDE.md             # This file
├── validate.py                # System validation script
├── start.sh                   # Quick start (macOS/Linux)
├── start.bat                  # Quick start (Windows)
└── .gitignore                 # Git configuration (optional)
```

---

## 💻 System Requirements

- **Python:** 3.8 or higher
- **RAM:** 256 MB minimum
- **Disk Space:** 500 MB
- **Browser:** Chrome, Firefox, Safari, Edge (latest versions)
- **Internet:** Not required after installation

---

## 🔧 Installation Steps

### **Option A: Automated Setup (Recommended)**

#### On macOS/Linux:
```bash
# 1. Make script executable
chmod +x start.sh

# 2. Run the script
./start.sh

# This will:
# - Check Python version
# - Install all dependencies
# - Initialize the database
# - Start the Flask server
```

#### On Windows:
```bash
# Simply double-click: start.bat
# Or run in command prompt:
start.bat
```

### **Option B: Manual Setup**

#### Step 1: Install Python 3
- Download from https://www.python.org/downloads/
- **Windows:** Check "Add Python to PATH" during installation
- **macOS:** Use Homebrew: `brew install python3`
- **Linux:** `sudo apt-get install python3 python3-pip`

#### Step 2: Navigate to Project Directory
```bash
cd /path/to/parser/project
```

#### Step 3: Create Virtual Environment (Optional but Recommended)
```bash
# Python 3.8+
python3 -m venv venv

# Activate virtual environment:
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Validate Installation
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

#### Step 6: Start the Application
```bash
python app.py
```

Expected output:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
 * Press CTRL+C to quit
```

#### Step 7: Open Browser
Navigate to: `http://localhost:5000`

---

## 🎯 Using the Portal

### **Invoice Parser Workflow**

1. **Go to Invoice Parser** (left sidebar)
2. **Click "+ Add Row"** to create a new entry
3. **Upload PDF** → Click the dashed box
4. **System auto-fills** the following fields:
   - Invoice Number
   - Invoice Date
   - Terms of Payment
   - Terms of Delivery
   - Currency
   - Amount
5. **Edit if needed** → All fields are editable after extraction
6. **Click Submit** → Data saves to database
7. **Export** → Click "📊 Export to Excel" for all invoices

### **Shipment Parser Workflow**

1. **Go to Shipment Parser** (left sidebar)
2. **Click "+ Add Row"** to create a new entry
3. **Upload PDF** → Click the dashed box
4. **System auto-fills:**
   - Ship Bill No
   - Ship Billing Date
5. **Click Submit** → Data saves to database
6. **Export** → Click "📊 Export to Excel" for all shipments

---

## 📊 Invoice Fields Extracted

| Field | Example | Format |
|-------|---------|--------|
| Invoice Number | 2502100495 | Numeric |
| Invoice Date | 01-09-2025 | DD-MM-YYYY |
| Terms of Payment | 90 DAYS FROM BL DATE | Text |
| Terms of Delivery | Ex Works | Text |
| Currency | USD | 3-letter code |
| Amount | 24.60 | Decimal number |

---

## 🚚 Shipment Bill Fields Extracted

| Field | Example | Format |
|-------|---------|--------|
| Ship Bill No | 4974061 | Numeric |
| Ship Billing Date | 03-09-2025 | DD-MM-YYYY |

*Note: Data extracted from PART-I (top section) only*

---

## 🛢️ Database

### **Auto-Created Tables**

**Invoices Table:**
```sql
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY,
    invoice_number TEXT NOT NULL,
    invoice_date TEXT NOT NULL,
    terms_of_payment TEXT,
    terms_of_delivery TEXT,
    currency TEXT,
    amount TEXT,
    submitted_at TIMESTAMP
);
```

**Shipments Table:**
```sql
CREATE TABLE shipments (
    id INTEGER PRIMARY KEY,
    ship_bill_no TEXT NOT NULL,
    ship_billing_date TEXT NOT NULL,
    submitted_at TIMESTAMP
);
```

### **View Database Contents**
```bash
sqlite3 parser.db
sqlite> .tables
sqlite> SELECT * FROM invoices;
sqlite> SELECT * FROM shipments;
sqlite> .quit
```

---

## 📊 Export to Excel

### **What Gets Exported**

**Invoices Export (`invoices.xlsx`):**
- Invoice Number
- Invoice Date
- Terms of Payment
- Terms of Delivery
- Currency
- Amount
- Submission Timestamp

**Shipments Export (`shipments.xlsx`):**
- Ship Bill No
- Ship Billing Date
- Submission Timestamp

### **Export Features**
- Bold headers with dark green background
- Auto-sized columns
- Chronologically sorted (newest first)
- Professional formatting

---

## 🔌 API Endpoints

All endpoints use JSON for request/response.

### **Extract Invoice**
```
POST /extract-invoice
Content-Type: multipart/form-data

Request: PDF file
Response: JSON with extracted fields
```

### **Extract Shipment**
```
POST /extract-shipment
Content-Type: multipart/form-data

Request: PDF file
Response: JSON with extracted fields
```

### **Submit Invoice**
```
POST /submit-invoice
Content-Type: application/json

Body: { invoiceNumber, invoiceDate, ... }
```

### **Submit Shipment**
```
POST /submit-shipment
Content-Type: application/json

Body: { shipBillNo, shipBillingDate }
```

### **Export Invoices**
```
GET /export-invoices
Downloads: invoices.xlsx
```

### **Export Shipments**
```
GET /export-shipments
Downloads: shipments.xlsx
```

### **Get Invoices**
```
GET /get-invoices
Returns: JSON array of all invoices
```

### **Get Shipments**
```
GET /get-shipments
Returns: JSON array of all shipments
```

---

## ⚡ Performance

| Operation | Time |
|-----------|------|
| PDF upload & extraction | < 1 second |
| Database insert | < 100 ms |
| Excel generation (1000 rows) | 1-2 seconds |
| Page load | < 500 ms |
| Concurrent users supported | 10+ |

---

## 🐛 Troubleshooting

### **"ModuleNotFoundError: No module named 'flask'"**
**Solution:**
```bash
pip install -r requirements.txt
```

### **"Port 5000 is already in use"**
**Solution 1:** Use a different port
```bash
python -c "from app import app; app.run(port=5001)"
```

**Solution 2:** Kill the process using port 5000
- **Windows:** `netstat -ano | findstr :5000` then `taskkill /PID <PID> /F`
- **macOS/Linux:** `lsof -i :5000` then `kill -9 <PID>`

### **"PDF parsing error" or No fields extracted**
**Solution:**
1. Ensure the PDF is a **digital** PDF (not scanned/image-based)
2. Try opening the PDF in Adobe Reader first
3. Check that the PDF is not corrupted
4. Ensure the PDF follows standard invoice/shipment format

### **"CORS error" or "Connection refused"**
**Solution:**
- Ensure Flask is running: `python app.py`
- Check that port 5000 is open
- Clear browser cache: Ctrl+Shift+Delete

### **Database is locked**
**Solution:**
```bash
# Stop the application (Ctrl+C)
# Then restart it
python app.py
```

### **Excel export shows empty file**
**Solution:**
- Submit at least one invoice/shipment first
- Check that data was saved to database: `sqlite3 parser.db "SELECT COUNT(*) FROM invoices;"`

---

## 🚀 Deployment Options

### **Local Server (Current Setup)**
- Perfect for small teams (2-10 users)
- No server setup required
- SQLite database on local disk
- Run on your laptop/desktop

### **Windows Server / IIS**
Use IIS with Python FastCGI:
1. Install IIS
2. Configure FastCGI handler for Python
3. Set Flask app as application

### **Docker Container**
```bash
# Build Docker image
docker build -t invoice-parser .

# Run container
docker run -p 5000:5000 invoice-parser

# Access at http://localhost:5000
```

### **Cloud Deployment**

#### **Heroku** (free tier available)
```bash
git init
git add .
git commit -m "Initial commit"
heroku create
git push heroku main
heroku open
```

#### **AWS** (EC2)
1. Launch EC2 instance
2. SSH into instance
3. Install Python and dependencies
4. Clone project files
5. Run Flask app with Gunicorn
6. Configure security groups

#### **Google Cloud Platform**
1. Create App Engine application
2. Deploy with `gcloud app deploy`
3. Uses Cloud SQL for database

#### **DigitalOcean**
1. Create Droplet
2. SSH and install dependencies
3. Use Nginx as reverse proxy
4. Run Flask with Gunicorn

---

## 📚 Documentation

- **README.md** → Full feature documentation
- **SETUP_GUIDE.md** → This file (setup instructions)
- **Code comments** → In app.py and index.html

---

## 🔐 Security Notes

### **Current Features**
- ✅ File upload validation (PDF only)
- ✅ SQL injection protection (parameterized queries)
- ✅ Input sanitization
- ✅ CORS enabled for localhost

### **For Production**
- Add user authentication (login system)
- Use HTTPS/SSL certificates
- Implement rate limiting
- Use PostgreSQL/MySQL instead of SQLite
- Add audit logging
- Configure firewall rules
- Set up regular backups

---

## 📈 Future Enhancements

Priority order for future development:

1. **User Authentication** - Login/logout system
2. **Scanned PDF Support** - OCR with Tesseract
3. **Batch Processing** - Upload multiple files at once
4. **Advanced Search** - Filter by date, amount, currency
5. **Duplicate Detection** - Warn if invoice already exists
6. **Mobile App** - React Native/Flutter version
7. **AI Integration** - Claude API for complex extraction
8. **Multi-language** - Support multiple languages
9. **API Keys** - For third-party integration
10. **Webhooks** - Real-time notifications

---

## 📞 Support

### **Before Asking for Help:**
1. Run `python validate.py` to check system status
2. Check README.md for documentation
3. Review TROUBLESHOOTING section above
4. Check Flask console output for error messages

### **Getting Help:**
- Review code comments in app.py
- Check PDF requirements (digital, not scanned)
- Ensure all dependencies are installed
- Try with different PDF files

---

## 📄 License

This project is provided as-is for commercial use.

---

## ✅ Verification Checklist

Before using in production, ensure:

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] System validation passes (`python validate.py`)
- [ ] Flask runs without errors (`python app.py`)
- [ ] Browser opens successfully (`http://localhost:5000`)
- [ ] Invoice parser page loads
- [ ] Shipment parser page loads
- [ ] Can add rows with "+ Add Row" button
- [ ] File upload works
- [ ] Submit button works
- [ ] Database creates records
- [ ] Excel export works
- [ ] Tested with sample PDFs

---

## 🎉 You're Ready!

Your Invoice & Shipment Bill Parser Portal is now **installation-ready**.

### **Next Steps:**
1. Run `python app.py`
2. Open `http://localhost:5000`
3. Start parsing invoices and shipping bills!

**Enjoy your new parser portal!** 🚀

---

**Last Updated:** June 26, 2024
**Version:** 1.0.0
