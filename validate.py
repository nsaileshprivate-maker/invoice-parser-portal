#!/usr/bin/env python3
"""
Invoice & Shipment Bill Parser Portal - System Validation Script

This script verifies that all dependencies are installed and the system
is ready to run. It performs basic tests to ensure everything works correctly.
"""

import sys
import os
import sqlite3
import json
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*50)
    print(f"  {text}")
    print("="*50)

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    print_header("Python Version Check")
    
    version = sys.version_info
    version_string = f"Python {version.major}.{version.minor}.{version.micro}"
    
    print(f"Current: {version_string}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✓ Python version is compatible")
        return True
    else:
        print("✗ Error: Python 3.8 or higher required")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    print_header("Dependency Check")
    
    dependencies = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'pdfplumber': 'pdfplumber',
        'openpyxl': 'openpyxl',
        'werkzeug': 'Werkzeug'
    }
    
    all_installed = True
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {name} is installed")
        except ImportError:
            print(f"✗ {name} is NOT installed")
            all_installed = False
    
    if not all_installed:
        print("\n⚠ To install missing dependencies, run:")
        print("  pip install -r requirements.txt")
    
    return all_installed

def check_file_structure():
    """Check if all required files exist"""
    print_header("File Structure Check")
    
    required_files = {
        'app.py': 'Flask backend application',
        'index.html': 'Frontend HTML file',
        'requirements.txt': 'Python dependencies',
        'README.md': 'Documentation'
    }
    
    all_exist = True
    
    for filename, description in required_files.items():
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"✓ {filename} ({file_size:,} bytes) - {description}")
        else:
            print(f"✗ {filename} - {description} - MISSING")
            all_exist = False
    
    return all_exist

def check_directories():
    """Check and create required directories"""
    print_header("Directory Check")
    
    directories = ['uploads']
    all_exist = True
    
    for dirname in directories:
        if os.path.exists(dirname):
            print(f"✓ {dirname}/ directory exists")
        else:
            print(f"⚠ {dirname}/ directory does NOT exist (will be created on first run)")
            all_exist = False
    
    return True  # Not critical if missing

def check_database():
    """Check database initialization"""
    print_header("Database Check")
    
    db_file = 'parser.db'
    
    if os.path.exists(db_file):
        print(f"✓ {db_file} exists ({os.path.getsize(db_file):,} bytes)")
        
        # Try to connect and check tables
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            
            # Check invoices table
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices';")
            if c.fetchone():
                c.execute("SELECT COUNT(*) FROM invoices;")
                count = c.fetchone()[0]
                print(f"  ✓ invoices table exists ({count} records)")
            else:
                print(f"  ✗ invoices table does NOT exist")
            
            # Check shipments table
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shipments';")
            if c.fetchone():
                c.execute("SELECT COUNT(*) FROM shipments;")
                count = c.fetchone()[0]
                print(f"  ✓ shipments table exists ({count} records)")
            else:
                print(f"  ✗ shipments table does NOT exist")
            
            conn.close()
            return True
        except Exception as e:
            print(f"  ✗ Error connecting to database: {e}")
            return False
    else:
        print(f"⚠ {db_file} does NOT exist (will be created on first run)")
        print("  ✓ This is normal for a fresh installation")
        return True  # Not critical if missing on first run

def test_imports():
    """Test that key modules can be imported"""
    print_header("Import Test")
    
    all_ok = True
    
    # Try importing Flask
    try:
        from flask import Flask
        print("✓ Flask import successful")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        all_ok = False
    
    # Try importing pdfplumber
    try:
        import pdfplumber
        print("✓ pdfplumber import successful")
    except ImportError as e:
        print(f"✗ pdfplumber import failed: {e}")
        all_ok = False
    
    # Try importing openpyxl
    try:
        from openpyxl import Workbook
        print("✓ openpyxl import successful")
    except ImportError as e:
        print(f"✗ openpyxl import failed: {e}")
        all_ok = False
    
    # Try importing the app
    try:
        import app
        print("✓ app module import successful")
    except Exception as e:
        print(f"✗ app module import failed: {e}")
        all_ok = False
    
    return all_ok

def check_ports():
    """Check if port 5000 is available"""
    print_header("Port Availability Check")
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("⚠ Port 5000 is currently in use")
            print("  If you want to use a different port, modify app.py or use:")
            print("  python -c \"from app import app; app.run(port=5001)\"")
            return False
        else:
            print("✓ Port 5000 is available")
            return True
    except Exception as e:
        print(f"⚠ Could not check port availability: {e}")
        return True  # Not critical

def main():
    """Run all validation checks"""
    print("\n")
    print("╔════════════════════════════════════════════════════╗")
    print("║   Invoice & Shipment Bill Parser Portal            ║")
    print("║   System Validation Script                         ║")
    print("╚════════════════════════════════════════════════════╝")
    
    results = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'File Structure': check_file_structure(),
        'Directories': check_directories(),
        'Database': check_database(),
        'Import Tests': test_imports(),
        'Port Availability': check_ports()
    }
    
    # Print summary
    print_header("Validation Summary")
    
    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:7} - {check_name}")
    
    all_passed = all(results.values())
    
    print("\n")
    if all_passed:
        print("✓ All checks passed! System is ready to run.")
        print("\nTo start the application, run:")
        print("  python app.py")
        print("\nThen open your browser to:")
        print("  http://localhost:5000")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nFor help, see README.md or the TROUBLESHOOTING section.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
