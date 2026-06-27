#!/bin/bash

# Invoice & Shipment Bill Parser Portal - Quick Start Script
# Run this script to set up and start the application

echo "========================================="
echo "Invoice & Shipment Bill Parser Portal"
echo "Quick Start Setup"
echo "========================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    echo "  Found: $python_version"
else
    echo "✗ Error: Python 3 is not installed"
    echo "  Please install Python 3.8 or higher from https://www.python.org"
    exit 1
fi

# Check pip
echo ""
echo "✓ Checking pip..."
if command -v pip3 &> /dev/null; then
    echo "  pip3 is available"
else
    echo "✗ Error: pip3 is not installed"
    exit 1
fi

# Install dependencies
echo ""
echo "✓ Installing Python dependencies..."
echo "  This may take a few minutes..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "  ✓ Dependencies installed successfully"
else
    echo "  ✗ Error installing dependencies"
    exit 1
fi

# Create uploads directory
echo ""
echo "✓ Creating uploads directory..."
mkdir -p uploads

# Initialize database
echo ""
echo "✓ Initializing database..."
python3 -c "from app import init_db; init_db(); print('  ✓ Database initialized')"

# Run the application
echo ""
echo "========================================="
echo "✓ Setup complete!"
echo ""
echo "Starting Flask server..."
echo "========================================="
echo ""
echo "🌐 Open your browser and go to:"
echo "   http://localhost:5000"
echo ""
echo "To stop the server, press Ctrl+C"
echo "========================================="
echo ""

python3 app.py
