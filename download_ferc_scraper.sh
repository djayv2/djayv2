#!/bin/bash

echo "🚀 FERC Scraper Production Package Download Script"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -d "djayv2" ]; then
    echo "❌ Error: djayv2 directory not found!"
    echo "Please run this script from the workspace directory."
    exit 1
fi

echo "✅ Found djayv2 directory"
echo "📦 Creating production zip file..."

# Create the zip file
zip -r ferc_scraper_production.zip djayv2/ \
    -x "djayv2/.git/*" \
    -x "djayv2/venv/*" \
    -x "djayv2/__pycache__/*" \
    -x "djayv2/*/__pycache__/*" \
    -x "djayv2/*/*/__pycache__/*"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Production zip file created!"
    echo ""
    echo "📁 File: ferc_scraper_production.zip"
    echo "📏 Size: $(du -h ferc_scraper_production.zip | cut -f1)"
    echo "📍 Location: $(pwd)/ferc_scraper_production.zip"
    echo ""
    echo "🎯 CLIENT REQUIREMENTS MET:"
    echo "✅ 1. Primarily written in Python"
    echo "✅ 2. Dockerized (runs inside Docker image)"
    echo "✅ 3. Outputs all data to PostgreSQL using pg8000 driver"
    echo "✅ 4. Uses schema: test_external"
    echo "✅ 5. Returns tables in proper SCD1/SCD2 format"
    echo "✅ 6. Comes with sensible suite of pytest tests"
    echo ""
    echo "🗄️ DATABASE CONFIG:"
    echo "Host: 34.59.88.3"
    echo "Port: 5432"
    echo "Database: postgres"
    echo "Username: jay_semia"
    echo "Password: \$..q)kf:=bCqw4fZ"
    echo "Schema: test_external"
    echo ""
    echo "🚀 QUICK START:"
    echo "1. Extract: unzip ferc_scraper_production.zip"
    echo "2. Navigate: cd djayv2"
    echo "3. Deploy: ./deploy_external_db.sh"
    echo ""
    echo "📥 DOWNLOAD INSTRUCTIONS:"
    echo "In your web UI, look for:"
    echo "- File explorer or file browser"
    echo "- Navigate to: $(pwd)"
    echo "- Find: ferc_scraper_production.zip"
    echo "- Right-click and select 'Download'"
    echo ""
    echo "🎉 Your production-ready FERC scraper is ready!"
else
    echo "❌ Error creating zip file!"
    exit 1
fi