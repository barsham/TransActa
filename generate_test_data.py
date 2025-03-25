#!/usr/bin/env python3
"""
AS2805 Test Data Generator for SillyPostilion

This script generates sample AS2805 transaction data that can be used
for testing the transaction processor.
"""

import json
import random
import string
import argparse
from datetime import datetime

def generate_card_number(card_type="visa"):
    """Generate a valid card number for testing."""
    if card_type.lower() == "visa":
        prefix = "4"
        length = 16
    elif card_type.lower() == "mastercard":
        prefix = "5" + random.choice(["1", "2", "3", "4", "5"])
        length = 16
    elif card_type.lower() == "amex":
        prefix = "3" + random.choice(["4", "7"])
        length = 15
    else:
        prefix = "4"  # Default to Visa
        length = 16
    
    # Generate random digits for the rest of the card
    num_digits = length - len(prefix)
    digits = [random.choice(string.digits) for _ in range(num_digits - 1)]
    
    # Calculate Luhn check digit
    total = 0
    for i, digit in enumerate(reversed(prefix + ''.join(digits))):
        digit = int(digit)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    
    check_digit = (10 - (total % 10)) % 10
    
    return prefix + ''.join(digits) + str(check_digit)

def generate_amount(min_value=100, max_value=1000000):
    """Generate a random transaction amount formatted for AS2805."""
    amount = random.randint(min_value, max_value)  # In cents
    return f"{amount:012d}"  # 12 digits with leading zeros

def generate_stan():
    """Generate a random System Trace Audit Number (STAN)."""
    return f"{random.randint(1, 999999):06d}"  # 6 digits with leading zeros

def generate_merchant_id():
    """Generate a random merchant ID."""
    prefix = random.choice(["MERCH", "SHOP", "STORE", "VENDOR", "SELLER"])
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}{suffix}"

def generate_terminal_id():
    """Generate a random terminal ID."""
    prefix = random.choice(["TERM", "POS", "EFTPOS", "KIOSK"])
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"

def generate_transaction_datetime():
    """Generate a transaction datetime in AS2805 format."""
    now = datetime.now()
    return now.strftime("%m%d%H%M%S")  # MMDDhhmmss

def generate_authorization_request():
    """Generate an AS2805 authorization request (MTI 0100)."""
    return {
        "mti": "0100",
        "processing_code": "000000",  # Purchase
        "amount": generate_amount(),
        "transmission_datetime": generate_transaction_datetime(),
        "stan": generate_stan(),
        "terminal_id": generate_terminal_id(),
        "merchant_id": generate_merchant_id(),
        "card_number": generate_card_number()
    }

def generate_financial_request():
    """Generate an AS2805 financial request (MTI 0200)."""
    return {
        "mti": "0200",
        "processing_code": "000000",  # Purchase
        "amount": generate_amount(),
        "transmission_datetime": generate_transaction_datetime(),
        "stan": generate_stan(),
        "terminal_id": generate_terminal_id(),
        "merchant_id": generate_merchant_id(),
        "card_number": generate_card_number(),
        "rrn": ''.join(random.choices(string.digits, k=12))  # Retrieval Reference Number
    }

def generate_reversal_request():
    """Generate an AS2805 reversal request (MTI 0400)."""
    # Generate an original financial request for reference
    original = generate_financial_request()
    
    return {
        "mti": "0400",
        "processing_code": original["processing_code"],
        "amount": original["amount"],
        "transmission_datetime": generate_transaction_datetime(),
        "stan": generate_stan(),
        "terminal_id": original["terminal_id"],
        "merchant_id": original["merchant_id"],
        "card_number": original["card_number"],
        "original_data": {
            "original_mti": original["mti"],
            "original_stan": original["stan"],
            "original_datetime": original["transmission_datetime"]
        }
    }

def generate_network_management_request():
    """Generate an AS2805 network management request (MTI 0800)."""
    return {
        "mti": "0800",
        "processing_code": "990000",  # Network Management
        "transmission_datetime": generate_transaction_datetime(),
        "stan": generate_stan(),
        "network_management_code": "301"  # Echo Test
    }

def generate_financial_advice():
    """Generate an AS2805 financial advice message (MTI 0220)."""
    return {
        "mti": "0220",
        "processing_code": "000000",  # Purchase
        "amount": generate_amount(),
        "transmission_datetime": generate_transaction_datetime(),
        "stan": generate_stan(),
        "terminal_id": generate_terminal_id(),
        "merchant_id": generate_merchant_id(),
        "card_number": generate_card_number(),
        "rrn": ''.join(random.choices(string.digits, k=12))  # Retrieval Reference Number
    }

def generate_test_transaction_set(count=1):
    """Generate a set of test transactions."""
    
    # Define the transaction types and their generators
    generators = {
        "0100": generate_authorization_request,
        "0200": generate_financial_request,
        "0220": generate_financial_advice,
        "0400": generate_reversal_request,
        "0800": generate_network_management_request
    }
    
    results = []
    
    for _ in range(count):
        # Choose a random transaction type
        mti = random.choice(list(generators.keys()))
        transaction = generators[mti]()
        results.append(transaction)
    
    return results

def main():
    """Main function to generate test data based on command-line arguments."""
    parser = argparse.ArgumentParser(description='AS2805 Test Data Generator')
    parser.add_argument('--mti', help='Generate a specific message type (e.g., 0100, 0200)')
    parser.add_argument('--count', type=int, default=1, help='Number of transactions to generate')
    parser.add_argument('--output', help='Output file for generated transactions (JSON format)')
    
    args = parser.parse_args()
    
    transactions = []
    
    if args.mti:
        # Generate specific transaction type
        if args.mti == "0100":
            for _ in range(args.count):
                transactions.append(generate_authorization_request())
        elif args.mti == "0200":
            for _ in range(args.count):
                transactions.append(generate_financial_request())
        elif args.mti == "0220":
            for _ in range(args.count):
                transactions.append(generate_financial_advice())
        elif args.mti == "0400":
            for _ in range(args.count):
                transactions.append(generate_reversal_request())
        elif args.mti == "0800":
            for _ in range(args.count):
                transactions.append(generate_network_management_request())
        else:
            print(f"Unknown MTI: {args.mti}")
            print("Available MTIs: 0100, 0200, 0220, 0400, 0800")
            return
    else:
        # Generate a mix of transaction types
        transactions = generate_test_transaction_set(args.count)
    
    # Output the generated transactions
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(transactions, f, indent=2)
        print(f"Generated {len(transactions)} transaction(s) and saved to {args.output}")
    else:
        # Print to stdout
        print(json.dumps(transactions, indent=2))

if __name__ == '__main__':
    main()