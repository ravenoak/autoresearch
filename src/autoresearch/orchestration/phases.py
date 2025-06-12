"""
Dialogue phases for dialectical reasoning.
"""

from enum import Enum


class DialoguePhase(str, Enum):
    """Phases of dialectical reasoning."""

    THESIS = "thesis"
    ANTITHESIS = "antithesis"
    VERIFICATION = "verification"
    SYNTHESIS = "synthesis"
    INTERVENTION = "intervention"
