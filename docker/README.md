# Container Images

Platform-specific Dockerfiles live here. Use `scripts/build_images.sh`
to build OCI images for Linux, macOS, and Windows. Set `OFFLINE=1` to
install from local wheels or sdists and `FORMAT=oci` to output archives
in `dist/`.

See `docs/container_usage.md` for running and updating containers.
