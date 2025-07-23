set -exo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
	build-essential python3-dev python3-venv cmake pkg-config git libssl-dev libffi-dev libxml2-dev libargon2-dev libblas-dev liblapack-dev libopenblas-dev liblmdb-dev libz3-dev libcurl4-openssl-dev
apt-get clean
rm -rf /var/lib/apt/lists/*

# Run the main setup script which installs dev dependencies and all extras
./scripts/setup.sh
# All Python/Poetry setup is handled by setup.sh using --all-extras
