#!/bin/bash
# Example script for testing SillyPostilion transaction processor

# Step 1: Start the simulator in the background
echo "Starting transaction processor simulator..."
python3 simulator.py --port 8000 > simulator_output.log 2>&1 &
SIMULATOR_PID=$!

# Give the simulator time to start up
sleep 2
echo "Simulator started with PID: $SIMULATOR_PID"

# Step 2: Generate some test transaction data
echo -e "\nGenerating test transaction data..."
python3 generate_test_data.py --count 5 --output test_transactions.json

# Step 3: Run tests for each message type
echo -e "\nTesting Authorization Requests (MTI 0100)..."
python3 transaction_tester.py --mti 0100

echo -e "\nTesting Financial Requests (MTI 0200)..."
python3 transaction_tester.py --mti 0200

echo -e "\nTesting Reversal Messages (MTI 0400)..."
python3 transaction_tester.py --mti 0400

echo -e "\nTesting Network Management Messages (MTI 0800)..."
python3 transaction_tester.py --mti 0800

# Step 4: Clean up - stop the simulator
echo -e "\nStopping the simulator..."
kill $SIMULATOR_PID
wait $SIMULATOR_PID 2>/dev/null  # Wait for the process to exit

# Step 5: Generate a consolidated report
echo -e "\nGenerating test report..."
# Find all log files
echo "Test logs can be found in:"
find . -name "*.log" | sed 's/^/- /'

echo -e "\nTest transaction data: test_transactions.json"

echo -e "\nTest completed successfully!"