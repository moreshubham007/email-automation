from flask_sock import Sock
from flask import request
import json
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask-Sock
sock = Sock()

# Global variables
clients = set()
status_lock = threading.Lock()
email_status = {}

def init_app(app):
    """Initialize WebSocket functionality"""
    sock.init_app(app)
    
    # Add CORS headers to the WebSocket route
    @app.after_request
    def after_request(response):
        if request and 'ws' in request.path:
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', '*')
            response.headers.add('Access-Control-Allow-Methods', '*')
        return response

def send_to_all_clients(message):
    """Send message to all connected WebSocket clients"""
    dead_clients = set()
    for client in clients:
        try:
            client.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            dead_clients.add(client)
    clients.difference_update(dead_clients)

@sock.route('/ws')
def websocket(ws):
    """Handle WebSocket connections"""
    clients.add(ws)
    try:
        # Send connection confirmation
        ws.send(json.dumps({
            'type': 'connection',
            'status': 'connected'
        }))
        
        # Keep connection alive and handle ping/pong
        while True:
            try:
                message = ws.receive()
                if message == 'ping':
                    ws.send('pong')
                elif message:
                    logger.info(f"Received message: {message}")
            except Exception as e:
                logger.error(f"Error in websocket loop: {e}")
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        clients.remove(ws) 