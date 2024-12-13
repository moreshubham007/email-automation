from flask_sock import Sock
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
        
        # Keep connection alive
        while True:
            try:
                # Handle incoming messages
                message = ws.receive()
                if message:
                    logger.info(f"Received message: {message}")
            except Exception as e:
                logger.error(f"Error in websocket loop: {e}")
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        clients.remove(ws) 