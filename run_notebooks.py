#!/usr/bin/env python3
"""
Script to run all numbered Jupyter notebooks in sequential order.
Fixes Windows event loop policy warning and provides clear execution feedback.
"""

import asyncio
import subprocess
import glob
import os
import sys


def setup_event_loop():
    """Fix Windows event loop policy to prevent ZMQ warnings."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_numbered_notebooks():
    """Get all notebooks that start with numbers, sorted numerically."""
    # Find all notebooks starting with digits
    notebooks = glob.glob("[0-9]*.ipynb")

    # Sort using natural/version sorting to handle multi-digit numbers correctly
    def natural_sort_key(filename):
        import re

        # Extract the leading number for proper sorting
        match = re.match(r"^(\d+)", filename)
        if match:
            return int(match.group(1))
        return 0

    return sorted(notebooks, key=natural_sort_key)


def run_notebook(notebook_path):
    """Execute a single notebook and return success status."""
    print(f"📓 Executing: {notebook_path}")

    try:
        result = subprocess.run(
            [
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace",
                notebook_path,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )  # 5 minute timeout

        if result.returncode == 0:
            print(f"✅ Successfully completed: {notebook_path}")
            return True
        else:
            print(f"❌ Error executing {notebook_path}")
            print(f"Error output: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout executing {notebook_path} (exceeded 5 minutes)")
        return False
    except Exception as e:
        print(f"💥 Exception executing {notebook_path}: {str(e)}")
        return False


def main():
    """Main execution function."""
    print("🚀 Starting numbered notebook execution...")

    # Fix Windows event loop policy
    setup_event_loop()

    # Get all numbered notebooks
    notebooks = get_numbered_notebooks()

    if not notebooks:
        print("📝 No numbered notebooks found (looking for files starting with digits)")
        return

    print(f"📋 Found {len(notebooks)} numbered notebooks:")
    for nb in notebooks:
        print(f"  - {nb}")
    print()

    # Execute notebooks in order
    successful = 0
    failed = 0

    for notebook in notebooks:
        if not os.path.exists(notebook):
            print(f"⚠️  Notebook not found: {notebook}")
            failed += 1
            continue

        success = run_notebook(notebook)
        if success:
            successful += 1
        else:
            failed += 1

        print()  # Add spacing between notebook executions

    # Summary
    print("=" * 50)
    print("📊 Execution Summary:")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📁 Total: {len(notebooks)}")

    if failed > 0:
        print(
            f"\n⚠️  {failed} notebook(s) failed to execute. Check the output above for details."
        )
        sys.exit(1)
    else:
        print("\n🎉 All notebooks executed successfully!")


if __name__ == "__main__":
    main()
