"""
Simple HTTP health check server for Railway deployment
"""
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
from datetime import datetime

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "telegram-solana-alert-bot",
                "version": "2.0.0"
            }
            
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

class HealthCheckServer:
    def __init__(self, port=8000):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the health check server in a separate thread"""
        def run_server():
            self.server = HTTPServer(('0.0.0.0', self.port), HealthCheckHandler)
            self.server.serve_forever()
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        print(f"🏥 Health check server started on port {self.port}")
    
    def stop(self):
        """Stop the health check server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)
