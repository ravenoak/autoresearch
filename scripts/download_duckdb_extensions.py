#!/usr/bin/env python3
"""
Download DuckDB extensions for offline use.

This script downloads DuckDB extensions and saves them to a specified directory.
It's particularly useful for environments with limited network access, allowing
you to download extensions once and then use them offline.

Usage:
    python download_duckdb_extensions.py [--output-dir DIR] [--extensions EXT1,EXT2,...] [--platform PLATFORM]

Arguments:
    --output-dir DIR       Directory to save extensions to (default: ./extensions)
    --extensions EXT1,...  Comma-separated list of extensions to download (default: vector)
    --platform PLATFORM    Platform to download extensions for (default: auto-detect)
                           Options: linux, osx, windows, osx_arm64

Examples:
    # Download vector extension to default directory
    python download_duckdb_extensions.py

    # Download vector and json extensions to custom directory
    python download_duckdb_extensions.py --output-dir /path/to/extensions --extensions vector,json

    # Download vector extension for macOS ARM64
    python download_duckdb_extensions.py --platform osx_arm64
"""

import argparse
import os
import platform
import sys
import tempfile
import shutil
from pathlib import Path
import logging

try:
    import duckdb
except ImportError:
    print("Error: duckdb package is not installed. Please install it with 'pip install duckdb'.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def detect_platform():
    """Detect the current platform for DuckDB extension compatibility."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        return "linux"
    elif system == "darwin":
        if machine == "arm64" or machine == "aarch64":
            return "osx_arm64"
        else:
            return "osx"
    elif system == "windows":
        return "windows"
    else:
        logger.warning(f"Unknown platform: {system} {machine}. Defaulting to linux.")
        return "linux"

def download_extension(extension_name, output_dir, platform_name=None):
    """
    Download a DuckDB extension to the specified directory.

    Args:
        extension_name: Name of the extension to download
        output_dir: Directory to save the extension to
        platform_name: Platform to download the extension for (auto-detect if None)

    Returns:
        Path to the downloaded extension
    """
    if platform_name is None:
        platform_name = detect_platform()

    # Create a temporary database to download the extension
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "temp.duckdb")
        conn = duckdb.connect(temp_db_path)

        try:
            # Install the extension to the temporary database
            logger.info(f"Downloading {extension_name} extension for {platform_name}...")
            conn.execute(f"INSTALL {extension_name}")

            # Get the extension directory
            extension_dir = os.path.join(temp_dir, ".duckdb", "extensions", platform_name)

            # Check if the extension was downloaded
            if not os.path.exists(extension_dir):
                logger.error(f"Failed to download {extension_name} extension. Extension directory not found.")
                return None

            # Find the extension files
            extension_files = []
            for root, _, files in os.walk(extension_dir):
                for file in files:
                    if extension_name in file and file.endswith(".duckdb_extension"):
                        extension_files.append(os.path.join(root, file))

            if not extension_files:
                logger.error(f"No {extension_name} extension files found in {extension_dir}")
                return None

            # Create the output directory structure
            output_extension_dir = os.path.join(output_dir, "extensions", extension_name)
            os.makedirs(output_extension_dir, exist_ok=True)

            # Copy the extension files
            for file_path in extension_files:
                file_name = os.path.basename(file_path)
                output_file_path = os.path.join(output_extension_dir, file_name)
                shutil.copy2(file_path, output_file_path)
                logger.info(f"Copied {file_name} to {output_extension_dir}")

            return output_extension_dir

        except Exception as e:
            logger.error(f"Error downloading {extension_name} extension: {e}")
            return None
        finally:
            conn.close()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Download DuckDB extensions for offline use.")
    parser.add_argument("--output-dir", default="./extensions", help="Directory to save extensions to")
    parser.add_argument("--extensions", default="vss", help="Comma-separated list of extensions to download")
    parser.add_argument("--platform", default=None, help="Platform to download extensions for (auto-detect if not specified)")

    args = parser.parse_args()

    # Create the output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Parse the extensions list
    extensions = [ext.strip() for ext in args.extensions.split(",")]

    # Detect platform if not specified
    platform_name = args.platform or detect_platform()
    logger.info(f"Using platform: {platform_name}")

    # Download each extension
    success = True
    for extension in extensions:
        result = download_extension(extension, output_dir, platform_name)
        if result is None:
            success = False

    # Print configuration instructions
    if success:
        logger.info("\nExtensions downloaded successfully!")
        logger.info("\nTo use the downloaded extensions, add the following to your autoresearch.toml file:")
        logger.info("\n[storage.duckdb]")
        logger.info(f"vector_extension_path = \"{os.path.join(output_dir, 'extensions', 'vss')}\"")
    else:
        logger.error("\nFailed to download some extensions. See errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
