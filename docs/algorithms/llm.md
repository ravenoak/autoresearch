# LLM

## Overview
The llm package adapts model providers and normalizes responses.

## Algorithm
Adapters map provider APIs to a common interface and enforce token limits
through the token budget helper.

## Proof sketch
Each adapter validates content length before dispatch, so returned
messages respect configured budgets.

## Simulation
`tests/unit/test_llm_adapter.py` exercises adapter logic and token
accounting.

## References
- [code](../../src/autoresearch/llm/)
- [spec](../specs/llm.md)
- [tests](../../tests/unit/test_llm_adapter.py)

## Related Issues
- [Resolve LLM extra installation failure][issue]

[issue]: ../../issues/archive/resolve-llm-extra-installation-failure.md
