#!/usr/bin/env python3
"""
Fake Printer Server - Simulates a network printer for testing direct_print module.
Listens on port 9100 and saves any received PDF data to a test folder.

Usage:
    python test_printer_server.py
    
Then configure a printer in Odoo with:
    - IP: 127.0.0.1 (localhost)
    - Port: 9100
    - Protocol: Raw (port 9100 - JetDirect)
"""

import socket
import os
import threading
from datetime import datetime

# Create test output directory
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_output')
if not os.path.exists(TEST_OUTPUT_DIR):
    os.makedirs(TEST_OUTPUT_DIR)

def handle_client(client_socket, addr):
    """Handle incoming print job from Odoo"""
    print(f"[{datetime.now()}] Connection from {addr[0]}:{addr[1]}")
    
    try:
        # Receive data
        data = b''
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            data += chunk
        
        # Save received data as PDF
        if data:
            filename = f"print_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(TEST_OUTPUT_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(data)
            
            print(f"✓ Received {len(data)} bytes")
            print(f"✓ Saved to: {filepath}")
            print(f"✓ Check the test_output folder for your PDF!\n")
        
        client_socket.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        client_socket.close()

def start_server(host='127.0.0.1', port=9100):
    """Start the fake printer server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    
    print(f"=" * 60)
    print(f"Fake Printer Server Started")
    print(f"=" * 60)
    print(f"Listening on: {host}:{port}")
    print(f"Test output folder: {TEST_OUTPUT_DIR}")
    print(f"\nConfigure this in Odoo:")
    print(f"  - IP/Host: {host}")
    print(f"  - Port: {port}")
    print(f"  - Protocol: Raw (port 9100 - JetDirect)")
    print(f"\nWaiting for print jobs... (Ctrl+C to stop)")
    print(f"=" * 60 + "\n")
    
    try:
        while True:
            client_socket, addr = server.accept()
            # Handle each client in a separate thread
            client_thread = threading.Thread(
                target=handle_client, 
                args=(client_socket, addr),
                daemon=True
            )
            client_thread.start()
    
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.close()
        print("Server stopped.")

if __name__ == '__main__':
    start_server()
