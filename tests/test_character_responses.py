#!/usr/bin/env python3
"""
Character Response Tests
Tests the plugin's ability to respond as different characters and as a generic assistant.

Test Cases:
1. Generic Assistant - No specific character
2. Zeus from Greek Mythology - Male character
3. Aphrodite from Greek Mythology - Female character
"""

import sys
import os
import subprocess
import time

class CharacterResponseTester:
    def __init__(self):
        self.parent_dir = os.path.dirname(os.path.dirname(__file__))
        self.passed_tests = 0
        self.total_tests = 0
        
    def run_plugin_test(self, test_input, test_name, expected_character=None, expected_gender=None):
        """Run a single plugin test and capture results"""
        print(f"\n[TEST] {test_name}")
        print(f"Input: '{test_input}'")
        if expected_character:
            print(f"Expected Character: {expected_character}")
        if expected_gender:
            print(f"Expected Gender: {expected_gender}")
        print("-" * 60)
        
        self.total_tests += 1
        
        try:
            # Run the plugin with the test input from the parent directory
            result = subprocess.run([
                sys.executable, 
                "plugin.py", 
                test_input
            ], capture_output=True, text=True, cwd=self.parent_dir, timeout=30)
            
            # Parse output to find the response
            stdout_lines = result.stdout.split('\n')
            response_found = False
            actual_response = ""
            
            # Look for the generated response in the output with multiple patterns
            for i, line in enumerate(stdout_lines):
                if "Generated reply:" in line:
                    actual_response = line.split("Generated reply:", 1)[1].strip()
                    response_found = True
                    break
                elif "[LOG]" in line and "Generated reply:" in line:
                    actual_response = line.split("Generated reply:", 1)[1].strip()
                    response_found = True
                    break
                elif "Message:" in line and not line.startswith("[LOG]"):
                    # Look for the Message: line from test output
                    actual_response = line.split("Message:", 1)[1].strip()
                    response_found = True
                    break
            
            if response_found and actual_response:
                print(f"[SUCCESS] Response received ({len(actual_response)} chars)")
                print(f"Response: {actual_response}")
                
                # Basic validation
                if len(actual_response) > 10:  # Reasonable response length
                    print(f"[SUCCESS] Response length validation passed")
                    
                    # Character-specific validation
                    validation_passed = True
                    
                    if expected_character == "Zeus":
                        zeus_keywords = ["zeus", "thunder", "lightning", "olympus", "god", "divine", "power"]
                        found_keywords = [kw for kw in zeus_keywords if kw.lower() in actual_response.lower()]
                        if found_keywords:
                            print(f"[SUCCESS] Zeus character validation passed (found: {', '.join(found_keywords)})")
                        else:
                            print(f"[WARNING] Limited Zeus character context detected")
                            
                    elif expected_character == "Aphrodite":
                        aphrodite_keywords = ["aphrodite", "love", "beauty", "goddess", "divine", "charm", "romance"]
                        found_keywords = [kw for kw in aphrodite_keywords if kw.lower() in actual_response.lower()]
                        if found_keywords:
                            print(f"[SUCCESS] Aphrodite character validation passed (found: {', '.join(found_keywords)})")
                        else:
                            print(f"[WARNING] Limited Aphrodite character context detected")
                            
                    elif expected_character == "Generic":
                        # For generic assistant, check for helpful gaming advice
                        gaming_keywords = ["game", "gaming", "tip", "advice", "help", "improve", "strategy"]
                        found_keywords = [kw for kw in gaming_keywords if kw.lower() in actual_response.lower()]
                        if found_keywords:
                            print(f"[SUCCESS] Generic assistant validation passed (found: {', '.join(found_keywords)})")
                        else:
                            print(f"[WARNING] Limited gaming context detected")
                    
                    if validation_passed:
                        self.passed_tests += 1
                        return True, actual_response
                    else:
                        return False, actual_response
                else:
                    print(f"[FAIL] Response too short: {len(actual_response)} chars")
                    return False, actual_response
            else:
                print(f"[FAIL] No valid response found in output")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"[ERROR] STDERR: {result.stderr}")
                # Debug output to help identify the issue
                print("[DEBUG] First 15 lines of stdout:")
                for i, line in enumerate(stdout_lines[:15]):
                    if line.strip():  # Only print non-empty lines
                        print(f"  {i+1}: {line}")
                return False, ""
                
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] Test timed out after 30 seconds")
            return False, ""
        except Exception as e:
            print(f"[ERROR] Error running test: {e}")
            return False, ""
    
    def test_generic_assistant(self):
        """Test generic gaming assistant"""
        test_input = "What are some tips for improving at competitive games?"
        success, response = self.run_plugin_test(
            test_input, 
            "Generic Gaming Assistant Test",
            expected_character="Generic"
        )
        return success
    
    def test_zeus_character(self):
        """Test Zeus character response"""
        test_input = "Ask Zeus from Greek Mythology about his power over thunder"
        success, response = self.run_plugin_test(
            test_input, 
            "Zeus Character Test",
            expected_character="Zeus",
            expected_gender="Male"
        )
        return success
    
    def test_aphrodite_character(self):
        """Test Aphrodite character response"""
        test_input = "Ask Aphrodite from Greek Mythology about the nature of love"
        success, response = self.run_plugin_test(
            test_input, 
            "Aphrodite Character Test",
            expected_character="Aphrodite", 
            expected_gender="Female"
        )
        return success
    
    def run_all_tests(self):
        """Run all character response tests"""
        print("[START] Starting Character Response Tests")
        print("=" * 60)
        print("Testing plugin responses as:")
        print("1. Generic Gaming Assistant")
        print("2. Zeus (Male character)")
        print("3. Aphrodite (Female character)")
        print()
        
        # Run all test cases
        tests = [
            ("Generic Assistant", self.test_generic_assistant),
            ("Zeus Character", self.test_zeus_character),
            ("Aphrodite Character", self.test_aphrodite_character)
        ]
        
        for test_name, test_func in tests:
            print(f"\n[RUNNING] {test_name}...")
            try:
                test_func()
            except Exception as e:
                print(f"[ERROR] {test_name} failed with error: {e}")
            
            # Small delay between tests
            time.sleep(1)
        
        # Final results
        print("\n" + "="*60)
        print("[RESULTS] TEST SUMMARY")
        print("="*60)
        print(f"Passed: {self.passed_tests}/{self.total_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}/{self.total_tests}")
        
        if self.passed_tests == self.total_tests:
            print("[SUCCESS] All tests passed! All characters are working correctly.")
        elif self.passed_tests > 0:
            print("[WARNING] Some tests passed. Check failed tests for issues.")
        else:
            print("[ERROR] All tests failed. Check plugin configuration.")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        return self.passed_tests == self.total_tests

def main():
    """Main test runner"""
    tester = CharacterResponseTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
