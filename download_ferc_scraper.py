#!/usr/bin/env python3
"""
Simple HTTP server to serve FERC scraper zip file for download
"""

import http.server
import socketserver
import os
import threading
import time

PORT = 8080
ZIP_FILE = "FERC_SCRAPER_COMPLETE.zip"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for web access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def start_server():
    """Start HTTP server to serve the zip file"""
    os.chdir('/workspace')
    
    # Check if zip file exists
    if not os.path.exists(ZIP_FILE):
        print(f"❌ Error: {ZIP_FILE} not found!")
        return
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 HTTP server started on port {PORT}")
        print(f"📦 Serving: {ZIP_FILE}")
        print(f"📏 File size: {os.path.getsize(ZIP_FILE)} bytes")
        print(f"🌐 Download URL: http://localhost:{PORT}/{ZIP_FILE}")
        print(f"📋 Direct link: http://localhost:{PORT}/{ZIP_FILE}")
        print("")
        print("📥 To download:")
        print(f"1. Open: http://localhost:{PORT}/{ZIP_FILE}")
        print("2. Or visit: http://localhost:8080/")
        print("3. Click on the zip file to download")
        print("")
        print("⏹️  Press Ctrl+C to stop server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    start_server()