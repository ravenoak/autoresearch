"""Base Agent class and role definitions for the dialectical system."""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..config.models import ConfigModel
from autoresearch.orchestration.state import QueryState
from .feedback import FeedbackEvent
from ..llm.adapters import LLMAdapter
from ..logging_utils import get_logger
from .mixins import (
    PromptGeneratorMixin,
    ModelConfigMixin,
    ClaimGeneratorMixin,
    ResultGeneratorMixin,
)
from .messages import AgentMessage
from .messages import MessageProtocol

log = get_logger(__name__)


class AgentRole(str, Enum):
    """Enumeration of standard agent roles in the dialectical system."""

    SYNTHESIZER = "Synthesizer"
    CONTRARIAN = "Contrarian"
    FACT_CHECKER = "FactChecker"
    SPECIALIST = "Specialist"
    MODERATOR = "Moderator"
    USER = "User"


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    model: Optional[str] = None
    enabled: bool = True
    prompt_templates: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("prompt_templates")
    @classmethod
    def validate_prompt_templates(cls, v: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Validate prompt templates."""
        for name, template in v.items():
            if "template" not in template:
                raise ValueError(
                    f"Prompt template '{name}' must have a 'template' field"
                )
        return v


class Agent(
    BaseModel,
    PromptGeneratorMixin,
    ModelConfigMixin,
    ClaimGeneratorMixin,
    ResultGeneratorMixin,
):
    """Base agent interface for dialectical cycle."""

    name: str
    role: AgentRole = AgentRole.SPECIALIST
    enabled: bool = True
    llm_adapter: Optional[LLMAdapter] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Execute agent's task on the given state."""
        raise NotImplementedError("Agent subclasses must implement execute()")

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Determine if this agent should execute in the current state."""
        return self.enabled

    def get_adapter(self, config: ConfigModel) -> LLMAdapter:
        """Get the LLM adapter to use for this agent.

        If an adapter was injected, use that. Otherwise, create one based on the config.
        """
        if self.llm_adapter:
            return self.llm_adapter

        from ..llm import get_pooled_adapter

        return get_pooled_adapter(config.llm_backend)

    def get_model(self, config: ConfigModel) -> str:
        """Get the model to use for this agent.

        Args:
            config: The configuration model.

        Returns:
            The model name to use.
        """
        adapter = self.get_adapter(config)
        return self.get_model_config(config, self.role.value, adapter)

    def _validate_and_adjust_prompt(
        self,
        prompt: str,
        model: str,
        config: ConfigModel
    ) -> str:
        """Validate prompt fits context and adjust if needed."""
        from ..llm.context_management import get_context_manager
        from ..llm.chunking import chunk_prompt, synthesize_chunk_results

        context_mgr = get_context_manager()
        adapter = self.get_adapter(config)
        provider = config.llm_backend

        validation = context_mgr.validate_prompt_fit(prompt, model, provider)

        if validation.fits:
            return prompt

        log.warning(
            f"{self.name}: Prompt exceeds context ({validation.estimated_tokens} > "
            f"{validation.available_tokens} tokens). {validation.recommendation}"
        )

        # Get overflow strategy from config
        overflow_strategy = config.context.overflow_strategy.value

        if overflow_strategy == "chunk" or validation.should_chunk:
            # Use chunking strategy
            log.info(f"{self.name}: Chunking prompt for processing")
            return self._handle_chunked_generation(prompt, model, config)
        elif overflow_strategy == "truncate" or validation.should_truncate:
            # Use truncation
            log.info(f"{self.name}: Truncating prompt to fit context")
            return context_mgr.truncate_intelligently(prompt, model)
        else:
            # Raise error if strategy is "error"
            from ..errors import LLMError
            raise LLMError(
                f"Prompt exceeds context size: {validation.estimated_tokens} tokens "
                f"(max: {validation.available_tokens})",
                model=model,
                suggestion=validation.recommendation
            )

    def _handle_chunked_generation(
        self,
        prompt: str,
        model: str,
        config: ConfigModel
    ) -> str:
        """Handle prompt that needs to be chunked."""
        from ..llm.context_management import get_context_manager
        from ..llm.chunking import chunk_prompt, synthesize_chunk_results

        context_mgr = get_context_manager()
        adapter = self.get_adapter(config)
        provider = config.llm_backend

        safe_budget = context_mgr.get_safe_budget(model, provider)
        chunks = chunk_prompt(prompt, safe_budget)

        log.info(f"{self.name}: Processing {len(chunks)} chunks")

        # Process each chunk
        chunk_results = []
        for i, (chunk_text, start, end) in enumerate(chunks):
            log.debug(f"{self.name}: Processing chunk {i+1}/{len(chunks)}")
            result = adapter.generate(chunk_text, model=model)
            chunk_results.append(result)

        # Synthesize results
        if len(chunk_results) == 1:
            return chunk_results[0]
        else:
            return synthesize_chunk_results(
                chunk_results,
                prompt[:200],  # Use beginning as query reference
                adapter,
                model
            )

    # ------------------------------------------------------------------
    # Message passing API
    # ------------------------------------------------------------------

    def send_message(
        self,
        state: QueryState,
        content: str,
        *,
        to: Optional[str] = None,
        coalition: Optional[str] = None,
        msg_type: str = "message",
        protocol: MessageProtocol = MessageProtocol.DIRECT,
    ) -> None:
        """Send a message to another agent or coalition."""

        msg = AgentMessage(
            **{"from": self.name},
            recipient=to,
            coalition=coalition,
            type=msg_type,
            protocol=protocol,
            content=content,
            cycle=state.cycle,
        )
        state.add_message(msg.to_dict())

    def broadcast(self, state: QueryState, content: str, coalition: str) -> None:
        """Broadcast a message to all members of a coalition."""

        if coalition not in state.coalitions:
            return
        for member in state.coalitions[coalition]:
            self.send_message(
                state,
                content,
                to=member,
                coalition=coalition,
                protocol=MessageProtocol.BROADCAST,
            )

    def get_messages(
        self,
        state: QueryState,
        *,
        from_agent: Optional[str] = None,
        coalition: Optional[str] = None,
        protocol: MessageProtocol | None = None,
    ) -> List[AgentMessage]:
        """Retrieve messages addressed to this agent."""

        raw = state.get_messages(
            recipient=self.name, coalition=coalition, protocol=protocol
        )
        if from_agent:
            raw = [m for m in raw if m.get("from") == from_agent]
        return [AgentMessage(**m) for m in raw]

    def send_feedback(self, state: QueryState, target: str, feedback: str) -> None:
        """Send a feedback message to another agent."""
        self.send_message(state, feedback, to=target, msg_type="feedback")
        state.add_feedback_event(
            FeedbackEvent(
                source=self.name,
                target=target,
                content=feedback,
                cycle=state.cycle,
            )
        )

    def get_feedback(self, state: QueryState) -> list[FeedbackEvent]:
        """Retrieve feedback events addressed to this agent."""
        return state.get_feedback_events(recipient=self.name)

    def format_feedback(self, state: QueryState) -> str:
        """Return feedback events as formatted text."""
        events = self.get_feedback(state)
        return "\n".join(f"{e.source}: {e.content}" for e in events)
