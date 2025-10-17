#!/usr/bin/env python3
"""
Test batching script to run tests in isolated batches to prevent state pollution.

This script runs tests in separate processes with cleanup to ensure deterministic
results and prevent flaky failures due to shared state.

Usage:
    uv run python scripts/run_tests_in_batches.py [--parallel] [--verbose]

Options:
    --parallel: Run batches in parallel (default: sequential)
    --verbose: Enable verbose output
"""

import argparse
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


# Define test batches with their pytest markers/selectors
BATCHES = {
    "batch_1_core": {
        "description": "Unit tests for core modules",
        "selectors": [
            "tests/unit/",
            "not (storage or search or orchestration)",
        ],
        "timeout": 300,  # 5 minutes
    },
    "batch_2_storage": {
        "description": "Storage tests in isolated environment",
        "selectors": [
            "tests/unit/",
            "storage",
        ],
        "timeout": 600,  # 10 minutes
    },
    "batch_3_search": {
        "description": "Search tests with clean state",
        "selectors": [
            "tests/unit/",
            "search",
        ],
        "timeout": 600,  # 10 minutes
    },
    "batch_4_orchestration": {
        "description": "Orchestration tests",
        "selectors": [
            "tests/unit/",
            "orchestration",
        ],
        "timeout": 900,  # 15 minutes
    },
    "batch_5_integration": {
        "description": "Integration tests",
        "selectors": [
            "tests/integration/",
        ],
        "timeout": 1200,  # 20 minutes
    },
    "batch_6_behavior": {
        "description": "Behavior tests",
        "selectors": [
            "tests/behavior/",
        ],
        "timeout": 1800,  # 30 minutes
    },
}


def run_batch(batch_name: str, batch_config: Dict, verbose: bool = False) -> Tuple[int, str]:
    """
    Run a single test batch in an isolated environment.

    Returns:
        Tuple of (return_code, output)
    """
    print(f"Running {batch_name}: {batch_config['description']}")

    # Create temporary directory for this batch
    with tempfile.TemporaryDirectory(prefix=f"test_batch_{batch_name}_") as temp_dir:
        temp_path = Path(temp_dir)

        # Set environment variables for isolation
        env = dict(os.environ)
        env.update({
            "TEMP": str(temp_path),
            "TMPDIR": str(temp_path),
            "PYTEST_CURRENT_TEST": batch_name,  # Trigger per-test cache isolation
            "UV_CACHE_DIR": str(temp_path / "uv_cache"),
        })

        # Build pytest command
        cmd = [
            "uv", "run", "--extra", "test",
            "pytest", "--tb=short", "--durations=10"
        ]

        if verbose:
            cmd.append("-v")

        # Add selectors for this batch
        for selector in batch_config["selectors"]:
            if selector.startswith("tests/"):
                # Add as test path
                cmd.append(selector)
            else:
                # Add as keyword expression
                cmd.extend(["-k", selector])

        # Add timeout
        cmd.extend(["--timeout", str(batch_config["timeout"])])

        print(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                env=env,
                timeout=batch_config["timeout"] + 60,  # Add buffer
            )

            output = result.stdout + result.stderr
            return_code = result.returncode

        except subprocess.TimeoutExpired:
            output = "Test batch timed out"
            return_code = 124  # Timeout exit code

        except Exception as e:
            output = f"Error running batch: {e}"
            return_code = 1

    return return_code, output


def main():
    parser = argparse.ArgumentParser(description="Run tests in isolated batches")
    parser.add_argument("--parallel", action="store_true", help="Run batches in parallel")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--batch", help="Run only specific batch (e.g., batch_1_core)")

    args = parser.parse_args()

    if args.batch:
        if args.batch not in BATCHES:
            print(f"Unknown batch: {args.batch}")
            print(f"Available batches: {', '.join(BATCHES.keys())}")
            sys.exit(1)
        batches_to_run = {args.batch: BATCHES[args.batch]}
    else:
        batches_to_run = BATCHES

    results = {}

    if args.parallel and len(batches_to_run) > 1:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(batches_to_run), 4)) as executor:
            future_to_batch = {
                executor.submit(run_batch, name, config, args.verbose): name
                for name, config in batches_to_run.items()
            }

            for future in concurrent.futures.as_completed(future_to_batch):
                batch_name = future_to_batch[future]
                try:
                    return_code, output = future.result()
                    results[batch_name] = (return_code, output)
                except Exception as e:
                    results[batch_name] = (1, f"Exception: {e}")
    else:
        # Run sequentially
        for batch_name, batch_config in batches_to_run.items():
            return_code, output = run_batch(batch_name, batch_config, args.verbose)
            results[batch_name] = (return_code, output)

    # Report results
    print("\n" + "="*60)
    print("BATCH TEST RESULTS")
    print("="*60)

    all_passed = True
    total_return_code = 0

    for batch_name, (return_code, output) in results.items():
        status = "PASSED" if return_code == 0 else "FAILED"
        print(f"{batch_name}: {status}")

        if return_code != 0:
            all_passed = False
            total_return_code = return_code
            if args.verbose:
                print(f"Output for {batch_name}:\n{output}\n")
        else:
            if args.verbose:
                print(f"Output for {batch_name}:\n{output}\n")

    print("="*60)
    if all_passed:
        print("All batches passed! ✅")
        sys.exit(0)
    else:
        print("Some batches failed! ❌")
        sys.exit(total_return_code)


if __name__ == "__main__":
    main()
