#!/usr/bin/env python3
"""
AS2805 Transaction Processor Simulator

This script simulates the behavior of the SillyPostilion transaction processor
for testing purposes. It listens on a specified port for incoming connections,
processes AS2805 messages, and returns appropriate responses.
"""

import socket
import json
import logging
import argparse
import threading
import time
import random
import string
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simulator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simulator')

# Default server settings
DEFAULT_HOST = '0.0.0.0'  # Listen on all interfaces
DEFAULT_PORT = 8000

# Response code probabilities (to simulate real-world scenarios)
RESPONSE_PROBABILITIES = {
    "00": 85,  # Approved (85% chance)
    "05": 5,   # Do not honor (5% chance)
    "14": 3,   # Invalid card number (3% chance)
    "51": 3,   # Insufficient funds (3% chance)
    "54": 2,   # Expired card (2% chance)
    "91": 2    # Issuer unavailable (2% chance)
}

class TransactionSimulator:
    """Simulator for the SillyPostilion transaction processor."""
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        """Initialize the simulator with connection parameters."""
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.transactions = []  # Store processed transactions
        self.last_stan = {}  # Track last STAN for each terminal ID
        
    def start(self):
        """Start the simulator server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Allow reusing the address
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"Simulator listening on {self.host}:{self.port}")
            
            # Start accepting connections
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                logger.info(f"Connection from {client_address}")
                
                # Handle the client connection in a separate thread
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down.")
        except Exception as e:
            logger.error(f"Error starting server: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the simulator server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Simulator stopped")
    
    def handle_client(self, client_socket, client_address):
        """Handle a client connection."""
        try:
            # Receive data from the client
            data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we've received a complete message
                if self._is_complete_message(data):
                    break
            
            if data:
                # Process the incoming message
                logger.info(f"Received {len(data)} bytes from {client_address}")
                
                try:
                    # Parse the incoming message
                    message = json.loads(data.decode('utf-8'))
                    logger.info(f"Parsed message: {message}")
                    
                    # Process the message and get a response
                    response = self.process_message(message)
                    logger.info(f"Generated response: {response}")
                    
                    # Send the response back to the client
                    response_data = json.dumps(response).encode('utf-8')
                    client_socket.sendall(response_data)
                    logger.info(f"Sent {len(response_data)} bytes response to {client_address}")
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message from {client_address}: {data}")
                    # Send an error response
                    error_response = {"error": "Invalid message format", "code": "96"}
                    client_socket.sendall(json.dumps(error_response).encode('utf-8'))
                
        except Exception as e:
            logger.error(f"Error handling client {client_address}: {str(e)}")
        finally:
            client_socket.close()
            logger.info(f"Closed connection from {client_address}")
    
    def _is_complete_message(self, data):
        """Check if we've received a complete message."""
        # For JSON messages, we can try to parse it
        try:
            json.loads(data.decode('utf-8'))
            return True
        except:
            return False
    
    def _generate_rrn(self):
        """Generate a unique retrieval reference number."""
        return ''.join(random.choices(string.digits, k=12))
    
    def _generate_response_code(self):
        """Generate a response code based on defined probabilities."""
        total = sum(RESPONSE_PROBABILITIES.values())
        rand_val = random.randint(1, total)
        
        cumulative = 0
        for code, probability in RESPONSE_PROBABILITIES.items():
            cumulative += probability
            if rand_val <= cumulative:
                return code
        
        return "00"  # Default to approved if something goes wrong
    
    def process_message(self, message):
        """Process an incoming message and generate a response."""
        # Extract key fields from the message
        mti = message.get("mti", "")
        
        # Create a base response with common fields
        response = {
            "mti": self._get_response_mti(mti),
            "processing_code": message.get("processing_code", ""),
            "transmission_datetime": datetime.now().strftime("%m%d%H%M%S"),
            "stan": message.get("stan", ""),
            "rrn": message.get("rrn", self._generate_rrn()),
        }
        
        # Handle specific message types
        if mti == "0100" or mti == "0200":  # Authorization or Financial Request
            # Generate a response code based on probabilities
            response_code = self._generate_response_code()
            response["response_code"] = response_code
            
            # Add message-specific fields
            response["amount"] = message.get("amount", "")
            if "terminal_id" in message:
                response["terminal_id"] = message["terminal_id"]
            if "merchant_id" in message:
                response["merchant_id"] = message["merchant_id"]
                
            # Track transaction for future reference
            transaction = {
                "original_mti": mti,
                "response_mti": response["mti"],
                "stan": message.get("stan", ""),
                "rrn": response["rrn"],
                "amount": message.get("amount", ""),
                "terminal_id": message.get("terminal_id", ""),
                "merchant_id": message.get("merchant_id", ""),
                "response_code": response_code,
                "timestamp": datetime.now().isoformat()
            }
            self.transactions.append(transaction)
            
            # Update the last STAN for this terminal
            terminal_id = message.get("terminal_id", "unknown")
            self.last_stan[terminal_id] = message.get("stan", "")
            
        elif mti == "0400":  # Reversal
            # For reversals, try to find the original transaction
            terminal_id = message.get("terminal_id", "")
            original_stan = None
            if "original_data" in message:
                original_stan = message["original_data"].get("original_stan", "")
            
            original_found = False
            for txn in self.transactions:
                if (txn["original_mti"] in ["0100", "0200"] and 
                    txn["stan"] == original_stan and 
                    txn["terminal_id"] == terminal_id):
                    original_found = True
                    break
            
            if original_found:
                response["response_code"] = "00"  # Reversal approved
            else:
                response["response_code"] = "25"  # Unable to locate original transaction
            
            # Add message-specific fields
            response["amount"] = message.get("amount", "")
            if "terminal_id" in message:
                response["terminal_id"] = message["terminal_id"]
            if "merchant_id" in message:
                response["merchant_id"] = message["merchant_id"]
            
            # Track the reversal
            transaction = {
                "original_mti": mti,
                "response_mti": response["mti"],
                "stan": message.get("stan", ""),
                "rrn": response["rrn"],
                "amount": message.get("amount", ""),
                "terminal_id": message.get("terminal_id", ""),
                "merchant_id": message.get("merchant_id", ""),
                "response_code": response["response_code"],
                "timestamp": datetime.now().isoformat()
            }
            self.transactions.append(transaction)
            
        elif mti == "0800":  # Network Management
            # For network management, just respond with success
            response["response_code"] = "00"
            if "network_management_code" in message:
                response["network_management_code"] = message["network_management_code"]
        
        elif mti == "0220":  # Financial Advice
            # For financial advice messages, usually approve
            response["response_code"] = "00"
            
            # Add message-specific fields
            response["amount"] = message.get("amount", "")
            if "terminal_id" in message:
                response["terminal_id"] = message["terminal_id"]
            if "merchant_id" in message:
                response["merchant_id"] = message["merchant_id"]
            
            # Track the advice
            transaction = {
                "original_mti": mti,
                "response_mti": response["mti"],
                "stan": message.get("stan", ""),
                "rrn": response["rrn"],
                "amount": message.get("amount", ""),
                "terminal_id": message.get("terminal_id", ""),
                "merchant_id": message.get("merchant_id", ""),
                "response_code": response["response_code"],
                "timestamp": datetime.now().isoformat()
            }
            self.transactions.append(transaction)
        
        else:
            # Unknown message type
            response["response_code"] = "12"  # Invalid transaction
        
        return response
    
    def _get_response_mti(self, request_mti):
        """Get the appropriate response MTI for a request MTI."""
        response_map = {
            "0100": "0110",
            "0200": "0210",
            "0220": "0230",
            "0400": "0410",
            "0800": "0810"
        }
        return response_map.get(request_mti, "0910")  # Default to 0910 for unknown MTIs

def main():
    """Main function to parse arguments and start the simulator."""
    parser = argparse.ArgumentParser(description='AS2805 Transaction Processor Simulator')
    parser.add_argument('--host', default=DEFAULT_HOST, help=f'Host to bind the server to (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Port to listen on (default: {DEFAULT_PORT})')
    
    args = parser.parse_args()
    
    # Create and start the simulator
    simulator = TransactionSimulator(args.host, args.port)
    
    try:
        simulator.start()
    except KeyboardInterrupt:
        print("\nSimulator interrupted by user.")
    finally:
        simulator.stop()

if __name__ == '__main__':
    main()