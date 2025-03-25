#!/usr/bin/env python3
"""
AS2805 Transaction Testing Tool for SillyPostilion

This script provides a way to test the transaction processor by sending
various AS2805 messages and analyzing the responses.
"""

import socket
import sys
import time
import logging
import argparse
import binascii
import json
from datetime import datetime
import random
import string
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("transaction_tests.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('transaction_tester')

# Default connection settings
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8000
DEFAULT_TIMEOUT = 30

# AS2805 message templates
TEMPLATES = {
    "0100": {  # Authorization Request
        "description": "Financial Purchase Authorization",
        "template": {
            "mti": "0100",
            "processing_code": "000000",  # Purchase
            "amount": "000000001000",     # $10.00
            "transmission_datetime": "",  # Will be filled in dynamically
            "stan": "",                   # Will be filled in dynamically
            "terminal_id": "TERM0001",
            "merchant_id": "MERCH001",
            "card_number": "4111111111111111"
        }
    },
    "0200": {  # Financial Request
        "description": "Financial Purchase Transaction",
        "template": {
            "mti": "0200",
            "processing_code": "000000",  # Purchase
            "amount": "000000005000",     # $50.00
            "transmission_datetime": "",  # Will be filled in dynamically
            "stan": "",                   # Will be filled in dynamically
            "terminal_id": "TERM0001",
            "merchant_id": "MERCH001",
            "card_number": "5555555555554444"
        }
    },
    "0220": {  # Financial Advice
        "description": "Financial Advice Message",
        "template": {
            "mti": "0220",
            "processing_code": "000000",  # Purchase
            "amount": "000000002500",     # $25.00
            "transmission_datetime": "",  # Will be filled in dynamically
            "stan": "",                   # Will be filled in dynamically
            "terminal_id": "TERM0001",
            "merchant_id": "MERCH001",
            "card_number": "4111111111111111"
        }
    },
    "0400": {  # Reversal
        "description": "Reversal Message",
        "template": {
            "mti": "0400",
            "processing_code": "000000",  # Purchase
            "amount": "000000001000",     # $10.00
            "transmission_datetime": "",  # Will be filled in dynamically
            "stan": "",                   # Will be filled in dynamically
            "terminal_id": "TERM0001",
            "merchant_id": "MERCH001",
            "card_number": "4111111111111111",
            "original_data": {
                "original_mti": "0200",
                "original_stan": "123456",  # Will be filled with a prior transaction
                "original_datetime": "0601083542"  # Will be filled with a prior transaction
            }
        }
    },
    "0800": {  # Network Management
        "description": "Echo Test / Network Management",
        "template": {
            "mti": "0800",
            "processing_code": "990000",  # Network Management
            "transmission_datetime": "",  # Will be filled in dynamically
            "stan": "",                   # Will be filled in dynamically
            "network_management_code": "301"  # Echo Test
        }
    },
}

class AS2805Formatter:
    """Utility class to format AS2805 messages from JSON to binary format and vice versa."""
    
    @staticmethod
    def format_message(template):
        """
        Convert a template dictionary into an AS2805 message format.
        This is a simplified implementation - a real AS2805 formatter would be more complex.
        """
        # In a real implementation, this would properly encode the AS2805 format
        # For this test, we'll just convert the template to a JSON string as a placeholder
        return json.dumps(template).encode('utf-8')
    
    @staticmethod
    def parse_response(response_bytes):
        """
        Parse a response from the AS2805 binary format to a Python dictionary.
        This is a simplified implementation.
        """
        # In a real implementation, this would properly decode the AS2805 format
        # For this test, we'll assume the response is a JSON string
        if not response_bytes:
            return None
        try:
            return json.loads(response_bytes.decode('utf-8'))
        except:
            return {"raw": binascii.hexlify(response_bytes).decode('utf-8')}

class TransactionTester:
    """Main class for testing transactions against the SillyPostilion processor."""
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT):
        """Initialize the tester with connection parameters."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.last_stan = 0
        self.test_results = []
        
    def _get_next_stan(self):
        """Generate a unique System Trace Audit Number (STAN)."""
        self.last_stan = (self.last_stan % 999999) + 1
        return f"{self.last_stan:06d}"
    
    def _get_transmission_datetime(self):
        """Generate the current date and time in the format expected by AS2805."""
        return datetime.now().strftime("%m%d%H%M%S")  # MMDDhhmmss
    
    def _prepare_message(self, template_name):
        """Prepare a message from a template by filling in dynamic fields."""
        if template_name not in TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = TEMPLATES[template_name]["template"].copy()
        # Fill in dynamic fields
        template["transmission_datetime"] = self._get_transmission_datetime()
        template["stan"] = self._get_next_stan()
        
        return template
    
    def send_message(self, message):
        """Send a prepared message to the transaction processor and return the response."""
        # Format the message as per AS2805 standard
        formatted_message = AS2805Formatter.format_message(message)
        
        response = None
        try:
            # Create a socket connection to the transaction processor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                logger.info(f"Connecting to {self.host}:{self.port}")
                sock.connect((self.host, self.port))
                
                # Send the message
                logger.info(f"Sending message: {message}")
                sock.sendall(formatted_message)
                
                # Receive the response
                response_data = sock.recv(4096)
                logger.info(f"Received response: {len(response_data)} bytes")
                
                # Parse the response
                response = AS2805Formatter.parse_response(response_data)
                logger.info(f"Parsed response: {response}")
                
        except socket.timeout:
            logger.error("Connection timed out")
        except ConnectionRefusedError:
            logger.error(f"Connection refused to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            
        return response
    
    def test_transaction(self, template_name):
        """Test a specific transaction type and record the results."""
        message = self._prepare_message(template_name)
        description = TEMPLATES[template_name]["description"]
        
        logger.info(f"Testing transaction: {description} (MTI: {template_name})")
        start_time = time.time()
        response = self.send_message(message)
        end_time = time.time()
        
        # Determine the result
        success = False
        response_time = end_time - start_time
        response_code = "Error"
        details = "No response"
        
        if response:
            if isinstance(response, dict):
                response_code = response.get("response_code", "Unknown")
                if response_code in ("00", "000", "0000"):  # Approval codes
                    success = True
                    details = "Approved"
                else:
                    details = "Declined"
            else:
                details = "Invalid response format"
        
        # Record the test result
        result = {
            "mti": template_name,
            "description": description,
            "success": success,
            "response_code": response_code,
            "response_time": response_time,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response
        }
        
        self.test_results.append(result)
        return result
    
    def run_all_tests(self):
        """Run tests for all available transaction types."""
        for template_name in TEMPLATES:
            try:
                self.test_transaction(template_name)
            except Exception as e:
                logger.error(f"Error testing {template_name}: {str(e)}")
        
        return self.test_results
    
    def print_results(self):
        """Print a formatted table of test results."""
        if not self.test_results:
            print("No test results available.")
            return
        
        # Format results for tabulation
        table_data = []
        for result in self.test_results:
            status = "✅ Pass" if result["success"] else "❌ Fail"
            table_data.append([
                result["mti"],
                result["description"],
                status,
                result["response_code"],
                f"{result['response_time']:.3f}s",
                result["details"]
            ])
        
        # Print the table
        headers = ["MTI", "Description", "Status", "Response", "Time", "Details"]
        print("\nTransaction Test Results:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Print summary
        success_count = sum(1 for r in self.test_results if r["success"])
        total_count = len(self.test_results)
        print(f"\nSummary: {success_count}/{total_count} tests passed "
              f"({success_count/total_count*100:.1f}%)")

def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='AS2805 Transaction Testing Tool')
    parser.add_argument('--host', default=DEFAULT_HOST, help=f'Host to connect to (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Port to connect to (default: {DEFAULT_PORT})')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, 
                        help=f'Connection timeout in seconds (default: {DEFAULT_TIMEOUT})')
    parser.add_argument('--mti', help='Test a specific message type (e.g., 0100, 0200)')
    
    args = parser.parse_args()
    
    # Create the tester
    tester = TransactionTester(args.host, args.port, args.timeout)
    
    try:
        # Run the tests
        if args.mti:
            if args.mti in TEMPLATES:
                result = tester.test_transaction(args.mti)
                tester.print_results()
            else:
                print(f"Unknown MTI: {args.mti}")
                print(f"Available MTIs: {', '.join(TEMPLATES.keys())}")
        else:
            tester.run_all_tests()
            tester.print_results()
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        tester.print_results()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()