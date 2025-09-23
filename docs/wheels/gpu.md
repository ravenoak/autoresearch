# GPU wheel cache

Certain optional extras rely on GPU-enabled wheels that are slower to build
from source. Hydrate the offline cache before running commands with
`EXTRAS="gpu"` so repeated installs reuse the local artifacts instead of
rebuilding them.

1. Download the platform-appropriate files for each dependency listed below.
2. Place the wheels in `wheels/gpu/` at the repository root.
3. Invoke pip with `--find-links` so installs prefer the cached binaries.

```bash
uv pip install --find-links wheels/gpu bertopic pynndescent scipy lmstudio
```

Reference wheels are available from PyPI:

- [bertopic 0.17.3](https://pypi.org/project/bertopic/0.17.3/#files)
- [pynndescent 0.5.13](https://pypi.org/project/pynndescent/0.5.13/#files)
- [scipy 1.16.0](https://pypi.org/project/scipy/1.16.0/#files)
- [lmstudio 1.4.1](https://pypi.org/project/lmstudio/1.4.1/#files)

The cache resides outside the documentation tree so MkDocs builds remain small,
but this page preserves the installation steps within the published guide.
