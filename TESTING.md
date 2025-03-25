# SillyPostilion Transaction Testing Tools

This directory contains several tools for testing the SillyPostilion transaction processor with AS2805 messages.

## Available Tools

### 1. Transaction Tester (`transaction_tester.py`)

A command-line tool that sends test transactions to the transaction processor and analyzes the responses.

**Usage:**
```
./transaction_tester.py [--host HOST] [--port PORT] [--timeout TIMEOUT] [--mti MTI]
```

**Options:**
- `--host`: Host to connect to (default: localhost)
- `--port`: Port to connect to (default: 8000)
- `--timeout`: Connection timeout in seconds (default: 30)
- `--mti`: Test a specific message type (e.g., 0100, 0200)

**Examples:**
```
# Test all transaction types
./transaction_tester.py

# Test only authorization requests (MTI 0100)
./transaction_tester.py --mti 0100

# Test against a specific host and port
./transaction_tester.py --host 192.168.1.100 --port 9000
```

### 2. Test Data Generator (`generate_test_data.py`)

A tool for generating sample AS2805 transaction data for testing purposes.

**Usage:**
```
./generate_test_data.py [--mti MTI] [--count COUNT] [--output OUTPUT]
```

**Options:**
- `--mti`: Generate a specific message type (e.g., 0100, 0200)
- `--count`: Number of transactions to generate (default: 1)
- `--output`: Output file for generated transactions (JSON format)

**Examples:**
```
# Generate one random transaction and print to stdout
./generate_test_data.py

# Generate 10 authorization requests (MTI 0100) and save to a file
./generate_test_data.py --mti 0100 --count 10 --output authorization_tests.json
```

### 3. Transaction Processor Simulator (`simulator.py`)

A simulator that behaves like the SillyPostilion transaction processor, accepting AS2805 messages and returning appropriate responses.

**Usage:**
```
./simulator.py [--host HOST] [--port PORT]
```

**Options:**
- `--host`: Host to bind the server to (default: 0.0.0.0)
- `--port`: Port to listen on (default: 8000)

**Examples:**
```
# Start the simulator with default settings
./simulator.py

# Start the simulator on a specific port
./simulator.py --port 9000
```

### 4. Batch Test Runner (`run_tests.py`)

A comprehensive tool that coordinates the testing process by starting the simulator, running test transactions, and generating a report.

**Usage:**
```
./run_tests.py [--host HOST] [--port PORT] [--count COUNT] [--report REPORT]
```

**Options:**
- `--host`: Host to connect to (default: localhost)
- `--port`: Port to connect to (default: 8000)
- `--count`: Number of test transactions to generate (default: 5)
- `--report`: Output file for the test report (default: test_report_TIMESTAMP.md)

**Examples:**
```
# Run a complete test cycle with default settings
./run_tests.py

# Generate 20 test transactions and specify the report file
./run_tests.py --count 20 --report my_test_report.md
```

## Testing Process

The typical testing process involves:

1. Make sure the SillyPostilion transaction processor backend is running or use the provided simulator.
2. Generate test transaction data with `generate_test_data.py` if needed.
3. Run individual tests with `transaction_tester.py` or run a complete test cycle with `run_tests.py`.
4. Review the test results and reports.

## Transaction Types

The testing tools support the following AS2805 message types:

| MTI  | Description                  |
|------|------------------------------|
| 0100 | Authorization Request        |
| 0200 | Financial Request            |
| 0220 | Financial Advice Message     |
| 0400 | Reversal Message             |
| 0800 | Network Management Message   |

## Test Reports

The `run_tests.py` tool generates comprehensive test reports in Markdown format, including:

- Test environment details
- Summary of test results
- Detailed transaction logs
- Recommendations based on the test results

These reports can be used to track testing progress and identify issues in the transaction processor implementation.

## Logging

All tools generate detailed logs that can be used for debugging and analysis:

- `transaction_tests.log`: Logs from the transaction tester
- `simulator.log`: Logs from the transaction processor simulator
- `test_runner.log`: Logs from the batch test runner

## Requirements

The testing tools require:

- Python 3.7 or higher
- The `tabulate` package for formatted output
- Network access to the transaction processor or simulator

## License

These testing tools are provided under the same license as the SillyPostilion project. See the LICENSE file for details.