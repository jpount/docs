#!/usr/bin/env python3
"""
Test Runner for Framework Tests
Discovers and runs all tests in the framework/tests directory with detailed reporting.
"""

import sys
import os
import unittest
import time
from pathlib import Path
import argparse
from io import StringIO
import json

# Add framework directory to path
FRAMEWORK_DIR = Path(__file__).parent
sys.path.insert(0, str(FRAMEWORK_DIR))


class ColoredTestResult(unittest.TextTestResult):
    """Custom test result class with colored output"""

    # ANSI color codes
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_times = []

    def startTest(self, test):
        super().startTest(test)
        self._test_start_time = time.time()

    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = time.time() - self._test_start_time
        self.test_times.append((test, elapsed))
        if self.showAll:
            self.stream.writeln(f"{self.GREEN}✓{self.RESET} ({elapsed:.3f}s)")
        elif self.dots:
            self.stream.write(f"{self.GREEN}.{self.RESET}")
            self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        if self.showAll:
            self.stream.writeln(f"{self.RED}✗ ERROR{self.RESET}")
        elif self.dots:
            self.stream.write(f"{self.RED}E{self.RESET}")
            self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.showAll:
            self.stream.writeln(f"{self.RED}✗ FAILED{self.RESET}")
        elif self.dots:
            self.stream.write(f"{self.RED}F{self.RESET}")
            self.stream.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.showAll:
            self.stream.writeln(f"{self.YELLOW}⊝ SKIPPED{self.RESET}: {reason}")
        elif self.dots:
            self.stream.write(f"{self.YELLOW}s{self.RESET}")
            self.stream.flush()


class ColoredTestRunner(unittest.TextTestRunner):
    """Custom test runner with colored output"""

    resultclass = ColoredTestResult

    def run(self, test):
        """Run the test and print colored summary"""
        result = super().run(test)

        # Print summary
        self.stream.writeln("\n" + "=" * 70)
        self.stream.writeln(f"{ColoredTestResult.BOLD}TEST SUMMARY{ColoredTestResult.RESET}")
        self.stream.writeln("=" * 70)

        # Stats
        total = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        success = total - failures - errors - skipped

        # Success rate
        if total > 0:
            success_rate = (success / total) * 100
            color = ColoredTestResult.GREEN if success_rate == 100 else ColoredTestResult.YELLOW if success_rate >= 80 else ColoredTestResult.RED
            self.stream.writeln(f"Success Rate: {color}{success_rate:.1f}%{ColoredTestResult.RESET}")

        # Test counts
        self.stream.writeln(f"\nTests Run: {total}")
        if success > 0:
            self.stream.writeln(f"  {ColoredTestResult.GREEN}✓ Passed: {success}{ColoredTestResult.RESET}")
        if failures > 0:
            self.stream.writeln(f"  {ColoredTestResult.RED}✗ Failed: {failures}{ColoredTestResult.RESET}")
        if errors > 0:
            self.stream.writeln(f"  {ColoredTestResult.RED}✗ Errors: {errors}{ColoredTestResult.RESET}")
        if skipped > 0:
            self.stream.writeln(f"  {ColoredTestResult.YELLOW}⊝ Skipped: {skipped}{ColoredTestResult.RESET}")

        # Slowest tests
        if hasattr(result, 'test_times') and result.test_times:
            self.stream.writeln(f"\n{ColoredTestResult.BOLD}Slowest Tests:{ColoredTestResult.RESET}")
            sorted_times = sorted(result.test_times, key=lambda x: x[1], reverse=True)
            for test, elapsed in sorted_times[:5]:
                test_name = test.id().split('.')[-1]
                self.stream.writeln(f"  {test_name}: {elapsed:.3f}s")

        # Failed tests details
        if failures or errors:
            self.stream.writeln(f"\n{ColoredTestResult.RED}{ColoredTestResult.BOLD}FAILED TESTS:{ColoredTestResult.RESET}")
            for test, traceback in result.failures + result.errors:
                self.stream.writeln(f"\n{ColoredTestResult.RED}✗ {test.id()}{ColoredTestResult.RESET}")
                # Print just the assertion error, not full traceback
                lines = traceback.split('\n')
                for line in lines[-3:]:  # Last 3 lines usually contain the assertion
                    if line.strip():
                        self.stream.writeln(f"  {line}")

        self.stream.writeln("\n" + "=" * 70)

        return result


def discover_tests(test_dir: Path, pattern: str = "test_*.py", verbose: bool = False) -> unittest.TestSuite:
    """Discover all tests in the test directory"""
    if verbose:
        print(f"\n{ColoredTestResult.BLUE}Discovering tests in: {test_dir}{ColoredTestResult.RESET}")

    # Create test loader
    loader = unittest.TestLoader()

    # Discover tests
    suite = loader.discover(
        start_dir=str(test_dir),
        pattern=pattern,
        top_level_dir=str(FRAMEWORK_DIR.parent)
    )

    # Count tests
    test_count = suite.countTestCases()

    if verbose:
        # List all test files found
        test_files = list(test_dir.glob(pattern))
        if test_files:
            print(f"Found {len(test_files)} test file(s):")
            for test_file in sorted(test_files):
                print(f"  • {test_file.name}")

        print(f"Total tests discovered: {test_count}")

    return suite


def run_specific_test(test_path: str, verbose: int = 2) -> bool:
    """Run a specific test module or test case"""
    print(f"\n{ColoredTestResult.BLUE}Running specific test: {test_path}{ColoredTestResult.RESET}")

    loader = unittest.TestLoader()

    try:
        # Try to load the test
        if ':' in test_path:
            # Specific test method: module:TestClass.test_method
            module_name, test_name = test_path.split(':', 1)
            module = loader.loadTestsFromName(module_name)
            suite = unittest.TestSuite()

            for test_group in module:
                for test in test_group:
                    if test_name in str(test):
                        suite.addTest(test)
        elif '.' in test_path and not test_path.endswith('.py'):
            # Test class or method: module.TestClass or module.TestClass.test_method
            suite = loader.loadTestsFromName(test_path)
        else:
            # Full module
            module_name = test_path.replace('.py', '').replace('/', '.')
            suite = loader.loadTestsFromName(module_name)

        # Run the test
        runner = ColoredTestRunner(verbosity=verbose)
        result = runner.run(suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"{ColoredTestResult.RED}Error loading test: {e}{ColoredTestResult.RESET}")
        return False


def run_coverage(test_dir: Path) -> None:
    """Run tests with coverage reporting"""
    try:
        import coverage
    except ImportError:
        print(f"{ColoredTestResult.YELLOW}Coverage module not installed. Install with: pip install coverage{ColoredTestResult.RESET}")
        return

    print(f"\n{ColoredTestResult.BLUE}Running tests with coverage...{ColoredTestResult.RESET}")

    # Initialize coverage
    cov = coverage.Coverage(source=[str(FRAMEWORK_DIR / 'scripts')])
    cov.start()

    # Run tests
    suite = discover_tests(test_dir)
    runner = unittest.TextTestRunner(verbosity=0, stream=StringIO())
    result = runner.run(suite)

    # Stop coverage
    cov.stop()
    cov.save()

    # Print coverage report
    print(f"\n{ColoredTestResult.BOLD}Coverage Report:{ColoredTestResult.RESET}")
    print("-" * 60)
    cov.report()

    # Generate HTML report
    html_dir = FRAMEWORK_DIR / 'coverage_html'
    cov.html_report(directory=str(html_dir))
    print(f"\nDetailed HTML report generated at: {html_dir}/index.html")


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description='Run framework tests with colored output and detailed reporting'
    )
    parser.add_argument(
        'test',
        nargs='?',
        help='Specific test to run (e.g., test_citation_manager, test_citation_manager.TestCitationManager)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=1,
        help='Increase verbosity (use -vv for more detail)'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode - minimal output'
    )
    parser.add_argument(
        '-p', '--pattern',
        default='test_*.py',
        help='Pattern for test file discovery (default: test_*.py)'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage analysis'
    )
    parser.add_argument(
        '--json',
        help='Output results to JSON file'
    )
    parser.add_argument(
        '--failfast',
        action='store_true',
        help='Stop on first failure'
    )

    args = parser.parse_args()

    # Adjust verbosity
    if args.quiet:
        verbosity = 0
    else:
        verbosity = args.verbose

    # Print header
    if not args.quiet:
        print(f"\n{ColoredTestResult.BOLD}{'=' * 70}{ColoredTestResult.RESET}")
        print(f"{ColoredTestResult.BOLD}FRAMEWORK TEST RUNNER{ColoredTestResult.RESET}")
        print(f"{ColoredTestResult.BOLD}{'=' * 70}{ColoredTestResult.RESET}")

    # Determine test directory
    test_dir = FRAMEWORK_DIR / 'tests'

    if not test_dir.exists():
        print(f"{ColoredTestResult.RED}Error: Test directory not found: {test_dir}{ColoredTestResult.RESET}")
        return 1

    # Run coverage if requested
    if args.coverage and not args.test:
        run_coverage(test_dir)
        return 0

    # Run specific test if provided
    if args.test:
        success = run_specific_test(args.test, verbosity)
        return 0 if success else 1

    # Discover and run all tests
    suite = discover_tests(test_dir, args.pattern, verbose=(verbosity > 1))

    if suite.countTestCases() == 0:
        print(f"{ColoredTestResult.YELLOW}No tests found matching pattern: {args.pattern}{ColoredTestResult.RESET}")
        return 1

    # Create runner
    runner = ColoredTestRunner(
        verbosity=verbosity,
        failfast=args.failfast
    )

    # Run tests
    start_time = time.time()
    result = runner.run(suite)
    elapsed_time = time.time() - start_time

    # Print timing
    if not args.quiet:
        print(f"Total time: {elapsed_time:.2f}s")

    # Output JSON if requested
    if args.json:
        json_results = {
            'total_tests': result.testsRun,
            'successes': result.testsRun - len(result.failures) - len(result.errors),
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'elapsed_time': elapsed_time,
            'success': result.wasSuccessful()
        }

        with open(args.json, 'w') as f:
            json.dump(json_results, f, indent=2)

        if not args.quiet:
            print(f"\nResults written to: {args.json}")

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())