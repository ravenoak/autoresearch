# Examples

## Overview
The examples package bundles runnable workflows demonstrating library
features.

## Algorithm
Each example registers a CLI entry that constructs agents and executes a
predefined scenario.

## Proof sketch
Examples rely on tested modules; running them composes proven components,
so scenarios succeed when dependencies pass.

## Simulation
`tests/unit/test_examples_package.py` imports every example to confirm
entrypoints resolve.

## References
- [code](../../src/autoresearch/examples/)
- [spec](../specs/examples.md)
- [tests](../../tests/unit/test_examples_package.py)

## Related Issues
- [Prepare first alpha release][issue]

[issue]: ../../issues/prepare-first-alpha-release.md
