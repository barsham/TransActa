#!/usr/bin/env python3
"""
AS2805 Transaction Batch Test Runner

This script coordinates the transaction testing process by:
1. Starting the transaction processor simulator
2. Running a series of test transactions
3. Generating a comprehensive test report
"""

import os
import sys
import subprocess
import time
import argparse
import threading
import json
import logging
from datetime import datetime
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_runner.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_runner')

class TestRunner:
    """Coordinates the transaction testing process."""
    
    def __init__(self, host='localhost', port=8000, simulator_host='0.0.0.0'):
        """Initialize the test runner with connection parameters."""
        self.host = host
        self.port = port
        self.simulator_host = simulator_host
        self.simulator_process = None
        self.simulator_thread = None
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def start_simulator(self):
        """Start the transaction processor simulator."""
        logger.info(f"Starting transaction processor simulator on {self.simulator_host}:{self.port}")
        
        def run_simulator():
            try:
                self.simulator_process = subprocess.Popen(
                    [sys.executable, 'simulator.py', '--host', self.simulator_host, '--port', str(self.port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = self.simulator_process.communicate()
                if stdout:
                    logger.info(f"Simulator stdout: {stdout.decode('utf-8')}")
                if stderr:
                    logger.error(f"Simulator stderr: {stderr.decode('utf-8')}")
            except Exception as e:
                logger.error(f"Error running simulator: {str(e)}")
        
        self.simulator_thread = threading.Thread(target=run_simulator)
        self.simulator_thread.daemon = True
        self.simulator_thread.start()
        
        # Give the simulator time to start up
        time.sleep(2)
        logger.info("Simulator started")
    
    def stop_simulator(self):
        """Stop the transaction processor simulator."""
        if self.simulator_process:
            logger.info("Stopping simulator")
            self.simulator_process.terminate()
            try:
                self.simulator_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.simulator_process.kill()
            logger.info("Simulator stopped")
    
    def run_test(self, mti=None):
        """Run a single test with a specific MTI or all tests if not specified."""
        logger.info(f"Running {'all tests' if mti is None else f'test for MTI {mti}'}")
        
        cmd = [sys.executable, 'transaction_tester.py', '--host', self.host, '--port', str(self.port)]
        if mti:
            cmd.extend(['--mti', mti])
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Test process failed with code {process.returncode}")
                if stderr:
                    logger.error(f"Test stderr: {stderr.decode('utf-8')}")
                return False
            
            # Parse the output to find the results table
            output = stdout.decode('utf-8')
            logger.info(f"Test output: {output}")
            
            return True
        except Exception as e:
            logger.error(f"Error running test: {str(e)}")
            return False
    
    def generate_test_data(self, count=5, output_file=None):
        """Generate test transaction data."""
        output_file = output_file or f"test_data_{self.timestamp}.json"
        
        logger.info(f"Generating {count} test transactions to {output_file}")
        
        cmd = [sys.executable, 'generate_test_data.py', '--count', str(count), '--output', output_file]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Data generation process failed with code {process.returncode}")
                if stderr:
                    logger.error(f"Data generation stderr: {stderr.decode('utf-8')}")
                return None
            
            logger.info(f"Test data generated: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error generating test data: {str(e)}")
            return None
    
    def run_batch_test(self, test_file=None, count=5):
        """Run a batch test with generated or provided test data."""
        if not test_file:
            test_file = self.generate_test_data(count)
            if not test_file:
                logger.error("Failed to generate test data")
                return False
        
        logger.info(f"Running batch test with data from {test_file}")
        
        # Now run tests for each MTI type
        mti_types = ['0100', '0200', '0220', '0400', '0800']
        results = []
        
        for mti in mti_types:
            logger.info(f"Testing MTI {mti}")
            success = self.run_test(mti)
            results.append({
                'mti': mti,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
        
        self.results = results
        return all(r['success'] for r in results)
    
    def generate_report(self, report_file=None):
        """Generate a test report based on the results."""
        report_file = report_file or f"test_report_{self.timestamp}.md"
        
        logger.info(f"Generating test report to {report_file}")
        
        # Create a markdown report
        with open(report_file, 'w') as f:
            f.write("# AS2805 Transaction Test Report\n\n")
            f.write(f"**Date/Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Test environment details
            f.write("## Test Environment\n\n")
            f.write(f"- **Host:** {self.host}\n")
            f.write(f"- **Port:** {self.port}\n")
            f.write(f"- **Python Version:** {sys.version.split()[0]}\n\n")
            
            # Test results summary
            f.write("## Test Results Summary\n\n")
            
            if self.results:
                table_data = []
                for result in self.results:
                    status = "✅ Pass" if result["success"] else "❌ Fail"
                    table_data.append([
                        result["mti"],
                        self._get_mti_description(result["mti"]),
                        status,
                        result["timestamp"]
                    ])
                
                # Generate a markdown table
                f.write("| MTI | Description | Status | Timestamp |\n")
                f.write("|-----|-------------|--------|----------|\n")
                for row in table_data:
                    f.write(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n")
                
                # Overall result
                success_count = sum(1 for r in self.results if r["success"])
                total_count = len(self.results)
                f.write(f"\n**Overall Result:** {success_count}/{total_count} tests passed ")
                f.write(f"({success_count/total_count*100:.1f}%)\n\n")
            else:
                f.write("No test results available.\n\n")
            
            # Detailed results from log files
            f.write("## Detailed Transaction Logs\n\n")
            f.write("See the following log files for detailed transaction information:\n\n")
            f.write("- `transaction_tests.log`: Detailed transaction test logs\n")
            f.write("- `simulator.log`: Transaction processor simulator logs\n")
            f.write("- `test_runner.log`: Test orchestration logs\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            f.write("Based on the test results, the following actions are recommended:\n\n")
            
            if not self.results:
                f.write("- Re-run the tests to gather test results\n")
            elif all(r["success"] for r in self.results):
                f.write("- All tests passed! The transaction processor is functioning correctly.\n")
                f.write("- Consider expanding the test suite with more edge cases and load testing.\n")
            else:
                f.write("- Review the failed tests and fix the underlying issues:\n")
                for result in self.results:
                    if not result["success"]:
                        f.write(f"  - Fix issues with {result['mti']} ({self._get_mti_description(result['mti'])}) transactions\n")
        
        logger.info(f"Test report generated: {report_file}")
        return report_file
    
    def _get_mti_description(self, mti):
        """Get a description for an MTI."""
        descriptions = {
            "0100": "Authorization Request",
            "0110": "Authorization Response",
            "0200": "Financial Request",
            "0210": "Financial Response",
            "0220": "Financial Advice",
            "0230": "Financial Advice Response",
            "0400": "Reversal Request",
            "0410": "Reversal Response",
            "0800": "Network Management Request",
            "0810": "Network Management Response"
        }
        return descriptions.get(mti, "Unknown Message Type")
    
    def run_complete_test(self, count=5):
        """Run a complete test cycle and generate a report."""
        try:
            # Start the simulator
            self.start_simulator()
            
            # Run the batch test
            success = self.run_batch_test(count=count)
            
            # Generate the report
            report_file = self.generate_report()
            
            logger.info(f"Complete test {'succeeded' if success else 'failed'}")
            logger.info(f"Report generated: {report_file}")
            
            return success, report_file
        finally:
            # Make sure we always stop the simulator
            self.stop_simulator()

def main():
    """Main function to parse arguments and run the tests."""
    parser = argparse.ArgumentParser(description='AS2805 Transaction Batch Test Runner')
    parser.add_argument('--host', default='localhost', help='Host to connect to (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to connect to (default: 8000)')
    parser.add_argument('--count', type=int, default=5, help='Number of test transactions to generate (default: 5)')
    parser.add_argument('--report', help='Output file for the test report (default: test_report_TIMESTAMP.md)')
    
    args = parser.parse_args()
    
    # Create the test runner
    runner = TestRunner(host=args.host, port=args.port)
    
    try:
        # Run the complete test
        success, report_file = runner.run_complete_test(count=args.count)
        
        # Print the results
        if success:
            print(f"\n✅ All tests passed! Report generated: {report_file}")
        else:
            print(f"\n❌ Some tests failed. Report generated: {report_file}")
        
        # If a specific report file was requested, copy the report there
        if args.report and args.report != report_file:
            import shutil
            shutil.copy(report_file, args.report)
            print(f"Report copied to: {args.report}")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()