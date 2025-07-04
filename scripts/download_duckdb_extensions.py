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
    --extensions EXT1,...  Comma-separated list of extensions to download (default: vss)
    --platform PLATFORM    Platform to download extensions for (default: auto-detect)
                           Options: linux_amd64, linux_arm64, osx_amd64, osx_arm64, windows_amd64

Examples:
    # Download vss extension to default directory
    python download_duckdb_extensions.py

    # Download vss and json extensions to custom directory
    python download_duckdb_extensions.py --output-dir /path/to/extensions --extensions vss,json

    # Download vss extension for macOS ARM64
    python download_duckdb_extensions.py --platform osx_arm64

Note:
    The script uses DuckDB's native extension installation mechanism and will download
    the appropriate extension for your platform. The vss extension is also available
    as a Python package (duckdb-extension-vss) which can be installed via pip or poetry.
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
        if machine in ["x86_64", "amd64"]:
            return "linux_amd64"
        elif machine in ["arm64", "aarch64"]:
            return "linux_arm64"
        else:
            logger.warning(f"Unknown Linux architecture: {machine}. Defaulting to linux_amd64.")
            return "linux_amd64"
    elif system == "darwin":
        if machine in ["arm64", "aarch64"]:
            return "osx_arm64"
        else:
            return "osx_amd64"
    elif system == "windows":
        if machine in ["x86_64", "amd64"]:
            return "windows_amd64"
        else:
            logger.warning(f"Unknown Windows architecture: {machine}. Defaulting to windows_amd64.")
            return "windows_amd64"
    else:
        logger.warning(f"Unknown platform: {system} {machine}. Defaulting to linux_amd64.")
        return "linux_amd64"

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

    # Create the output directory structure
    output_extension_dir = os.path.join(output_dir, "extensions", extension_name)
    os.makedirs(output_extension_dir, exist_ok=True)

    # Create a temporary database to download the extension
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "temp.duckdb")
        conn = duckdb.connect(temp_db_path)

        try:
            # Set the extension directory to our output directory
            extension_dir_path = os.path.join(output_dir, "extensions")
            logger.info(f"Setting extension directory to: {extension_dir_path}")
            conn.execute(f"SET extension_directory='{extension_dir_path}'")

            # Install the extension using the Python API
            logger.info(f"Downloading {extension_name} extension for {platform_name}...")
            conn.install_extension(extension_name)

            # Verify the extension was installed
            result = conn.execute("SELECT * FROM duckdb_extensions() WHERE extension_name = ?", [extension_name]).fetchall()
            if not result:
                logger.error(f"Failed to install {extension_name} extension.")
                return None

            # Find the extension files
            extension_files = []
            for root, _, files in os.walk(output_extension_dir):
                for file in files:
                    if file.endswith(".duckdb_extension"):
                        extension_files.append(os.path.join(root, file))

            if not extension_files:
                # If no files found in output directory, check the default DuckDB extension directory
                default_ext_dir = os.path.join(temp_dir, ".duckdb", "extensions", platform_name)
                if os.path.exists(default_ext_dir):
                    for root, _, files in os.walk(default_ext_dir):
                        for file in files:
                            if extension_name in file and file.endswith(".duckdb_extension"):
                                src_path = os.path.join(root, file)
                                dst_path = os.path.join(output_extension_dir, file)
                                shutil.copy2(src_path, dst_path)
                                extension_files.append(dst_path)
                                logger.info(f"Copied {file} to {output_extension_dir}")

            if not extension_files:
                logger.error(f"No {extension_name} extension files found")
                return None

            logger.info(f"Successfully downloaded {extension_name} extension to {output_extension_dir}")
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

        # Find the actual vss extension file to provide the correct path
        vss_extension_file = None
        vss_dir = os.path.join(output_dir, 'extensions', 'vss')
        if os.path.exists(vss_dir):
            for file in os.listdir(vss_dir):
                if file.endswith('.duckdb_extension'):
                    vss_extension_file = os.path.join(vss_dir, file)
                    break

        if vss_extension_file:
            logger.info(f"vector_extension_path = \"{vss_extension_file}\"")
            logger.info("\nNote: The vector_extension_path must point to the .duckdb_extension file, not just the directory.")
        else:
            logger.info(f"vector_extension_path = \"{os.path.join(output_dir, 'extensions', 'vss', 'vss.duckdb_extension')}\"")
            logger.info("\nNote: The vector_extension_path must point to the .duckdb_extension file. Please verify the exact filename.")
    else:
        logger.error("\nFailed to download some extensions. See errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
