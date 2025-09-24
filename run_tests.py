# ABOUTME: Comprehensive test runner for SA News Podcast
# ABOUTME: Runs all test types (unit, integration, e2e) with proper reporting

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    print()
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all tests with comprehensive reporting."""
    print("🎙️  SA News Podcast - Comprehensive Test Suite")
    print("=" * 60)
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Test results tracking
    results = {}
    
    # 1. Unit Tests
    print("\n📋 Running Unit Tests...")
    unit_tests = [
        ("python3 -m pytest tests/test_text_sanitization.py -v", "Text Sanitization Unit Tests"),
        ("python3 -m pytest tests/test_apostrophe_fix.py -v", "Apostrophe Fix Unit Tests"),
        ("python3 -m pytest tests/test_ai_news_fetcher.py -v", "AI News Fetcher Unit Tests"),
        ("python3 -m pytest tests/test_transcript_generator.py -v", "Transcript Generator Unit Tests"),
    ]
    
    for command, description in unit_tests:
        results[description] = run_command(command, description)
    
    # 2. Integration Tests
    print("\n🔗 Running Integration Tests...")
    integration_tests = [
        ("python3 -m pytest tests/test_workflow_integration.py -v", "Workflow Integration Tests"),
    ]
    
    for command, description in integration_tests:
        results[description] = run_command(command, description)
    
    # 3. End-to-End Tests
    print("\n🎯 Running End-to-End Tests...")
    e2e_tests = [
        ("python3 -m pytest tests/test_end_to_end.py -v", "End-to-End Tests"),
    ]
    
    for command, description in e2e_tests:
        results[description] = run_command(command, description)
    
    # 4. Run All Tests Together
    print("\n🚀 Running All Tests Together...")
    all_tests_passed = run_command("python3 -m pytest tests/ -v --tb=short", "Complete Test Suite")
    
    # 5. Test Coverage (if coverage is available)
    print("\n📊 Running Test Coverage...")
    coverage_available = run_command("python3 -c 'import coverage'", "Check Coverage Availability")
    
    if coverage_available:
        run_command("python3 -m pytest tests/ --cov=. --cov-report=term-missing", "Test Coverage Report")
    else:
        print("ℹ️  Coverage not available. Install with: pip install pytest-cov")
    
    # 6. Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Test Suites: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    
    if failed_tests > 0:
        print(f"\n❌ Failed Tests:")
        for test_name, passed in results.items():
            if not passed:
                print(f"  - {test_name}")
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
    
    # 7. Recommendations
    print(f"\n💡 Recommendations:")
    if all_tests_passed:
        print("  - All tests are passing! The codebase is in good shape.")
        print("  - Consider adding more edge case tests as the system grows.")
    else:
        print("  - Fix failing tests before committing code.")
        print("  - Review test output above for specific failure details.")
        print("  - Ensure all dependencies are installed: pip install -r requirements.txt")
    
    print(f"\n🔧 Test Commands Reference:")
    print("  - Run all tests: python3 -m pytest tests/ -v")
    print("  - Run specific test: python3 -m pytest tests/test_ai_news_fetcher.py -v")
    print("  - Run with coverage: python3 -m pytest tests/ --cov=. --cov-report=term-missing")
    print("  - Run only unit tests: python3 -m pytest tests/ -k 'not integration and not e2e' -v")
    print("  - Run only integration tests: python3 -m pytest tests/ -k 'integration' -v")
    print("  - Run only e2e tests: python3 -m pytest tests/ -k 'e2e' -v")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
