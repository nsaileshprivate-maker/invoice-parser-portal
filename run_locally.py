#!/usr/bin/env python3
"""
Invoice & Shipment Bill Parser Portal - Simple Launcher
Run this script to start the application easily.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("  Invoice & Shipment Bill Parser Portal")
    print("  Simple Launcher")
    print("="*60 + "\n")

def check_requirements():
    """Check if requirements are installed"""
    print("Checking requirements...")
    try:
        import flask
        import pdfplumber
        import openpyxl
        print("✓ All dependencies are installed\n")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nTo install dependencies, run:")
        print("  pip install -r requirements.txt\n")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['uploads']
    for dirname in directories:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            print(f"✓ Created '{dirname}/' directory")

def initialize_database():
    """Initialize database"""
    print("\nInitializing database...")
    try:
        from app import init_db
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return False
    return True

def start_server():
    """Start Flask server"""
    print("\n" + "="*60)
    print("Starting Flask server...")
    print("="*60)
    print("\n🌐 Open your browser and go to:")
    print("   http://localhost:5000\n")
    print("To stop the server, press Ctrl+C\n")
    
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main launcher function"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == '__main__':
    main()
