"""ContrarianAgent challenges the thesis with alternative viewpoints."""

from typing import Dict, Any, List, Mapping, Sequence

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...orchestration.workspace_context import get_active_workspace_hints
from ...search import Search
from ...storage import ensure_source_id

log = get_logger(__name__)


class ContrarianAgent(Agent):
    """Challenges thesis with alternative viewpoints."""

    role: AgentRole = AgentRole.CONTRARIAN

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Generate counterpoints to existing claims."""
        log.info(f"ContrarianAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Find the thesis to challenge
        thesis = next(
            (c for c in state.claims if c.get("type") == "thesis"),
            None,
        )
        thesis_text = thesis.get("content") if thesis else state.query

        # Generate an antithesis using the prompt template
        prompt = self.generate_prompt("contrarian.antithesis", thesis=thesis_text)
        try:
            antithesis = adapter.generate(prompt, model=model)
            lm_error: dict[str, Any] | None = None
        except Exception as exc:
            from ...errors import LLMError

            err = exc if isinstance(exc, LLMError) else LLMError(str(exc), cause=exc)
            log.warning("Contrarian antithesis generation failed: %s", err)
            antithesis = "Antithesis unavailable due to LM error."
            lm_error = {
                "message": str(err),
                "metadata": getattr(err, "metadata", None),
            }
        else:
            lm_error = None

        workspace_sources: List[Dict[str, Any]] = []
        workspace_evidence: Dict[str, List[str]] = {}
        hints = get_active_workspace_hints()
        if isinstance(hints, Mapping):
            repo_section = hints.get("search", {}).get("repositories", {})
            resource_ids: set[str] = set()
            if isinstance(repo_section, Mapping):
                for payload in repo_section.values():
                    specs = payload.get("resource_specs") if isinstance(payload, Mapping) else None
                    if isinstance(specs, Sequence):
                        for spec in specs:
                            if isinstance(spec, Mapping):
                                rid = spec.get("resource_id")
                                if rid:
                                    resource_ids.add(str(rid))
            for resource_id in sorted(resource_ids):
                try:
                    lookup = Search.external_lookup(
                        state.query,
                        max_results=1,
                        workspace_hints=hints,
                        workspace_filters={"resource_ids": [resource_id]},
                    )
                except Exception as exc:  # pragma: no cover - defensive logging
                    log.debug(
                        "Contrarian workspace lookup failed",  # pragma: no cover - debug only
                        extra={"resource_id": resource_id, "error": str(exc)},
                    )
                    continue
                docs = list(getattr(lookup, "results", lookup)) if lookup is not None else []
                if not docs:
                    continue
                doc = dict(docs[0])
                doc.setdefault("workspace_resource_id", resource_id)
                doc.setdefault("retrieval_query", state.query)
                doc.setdefault("agent", self.name)
                ensured = ensure_source_id(doc)
                workspace_sources.append(ensured)
                source_id = str(ensured.get("source_id") or "")
                if source_id:
                    workspace_evidence.setdefault(resource_id, []).append(source_id)

        # Create and return the result
        claim = self.create_claim(antithesis, "antithesis")
        metadata: Dict[str, Any] = {"phase": DialoguePhase.ANTITHESIS}
        if lm_error:
            metadata["lm_error"] = lm_error
        if workspace_evidence:
            metadata.setdefault("workspace_evidence", {}).update({"resources": workspace_evidence})
        return self.create_result(
            claims=[claim],
            metadata=metadata,
            results={"antithesis": antithesis},
            sources=workspace_sources if workspace_sources else None,
        )

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute in dialectical mode when there's a thesis."""
        if config.reasoning_mode != ReasoningMode.DIALECTICAL:
            return False
        has_thesis = any(claim.get("type") == "thesis" for claim in state.claims)
        return super().can_execute(state, config) and has_thesis
