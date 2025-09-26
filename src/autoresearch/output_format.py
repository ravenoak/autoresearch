"""Adaptive output formatting for CLI and automation contexts.

This module provides functionality to format query responses in different formats
based on the context in which they are being displayed. It supports multiple output
formats including:

- JSON: Structured format suitable for programmatic consumption
- Plain text: Simple text format for basic terminal output
- Markdown: Rich text format with headings and lists for documentation
- Custom templates: User-defined templates for specialized output formats

The formatting system validates that the input conforms to the expected QueryResponse
structure before formatting, ensuring consistent output regardless of the source of
the data. It also supports *depth flags* that enable callers to reveal concise
summaries, key findings, claim tables, and full execution traces.

Typical usage:
    ```python
    from autoresearch.output_format import OutputFormatter

    # Format a query response as Markdown
    OutputFormatter.format(query_result, "markdown")

    # Format a query response as JSON with TL;DR depth
    OutputFormatter.format(query_result, "json", depth=["tldr"])

    # Format a query response as plain text
    OutputFormatter.format(query_result, "plain")

    # Format a query response using a custom template
    OutputFormatter.format(query_result, "template:my_template")
    ```
"""

import json
import re
import string
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, TypedDict, Union

from pydantic import BaseModel, ValidationError

from .config import ConfigLoader
from .errors import ValidationError as AutoresearchValidationError
from .logging_utils import get_logger
from .models import QueryResponse

log = get_logger(__name__)


class DepthLevel(str, Enum):
    """Enumeration of depth controls available in formatted output."""

    TLDR = "tldr"
    KEY_FINDINGS = "findings"
    CLAIMS = "claims"
    TRACE = "trace"
    FULL = "full"


EXPLICIT_DEPTH_LEVELS: Tuple[DepthLevel, ...] = (
    DepthLevel.TLDR,
    DepthLevel.KEY_FINDINGS,
    DepthLevel.CLAIMS,
    DepthLevel.TRACE,
)


class DepthSections(TypedDict, total=False):
    """Typed representation of optional depth sections."""

    tldr: str
    key_findings: List[str]
    claims: List[Dict[str, Any]]
    trace: List[str]


def _normalize_depth(depth: Optional[Iterable[Union[DepthLevel, str]]]) -> Set[DepthLevel]:
    """Convert raw depth inputs into a canonical set of ``DepthLevel`` values."""

    if not depth:
        return set()

    levels: Set[DepthLevel] = set()
    for raw in depth:
        if isinstance(raw, DepthLevel):
            level = raw
        else:
            try:
                level = DepthLevel(str(raw).lower())
            except ValueError:
                log.warning("Ignoring unknown depth flag: %s", raw)
                continue
        if level is DepthLevel.FULL:
            return set(EXPLICIT_DEPTH_LEVELS)
        levels.add(level)
    return levels


def _coerce_sequence(value: Any) -> List[Any]:
    """Return a shallow list representation for arbitrary sequences."""

    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, Mapping):
        return [f"{k}: {v}" for k, v in value.items()]
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def _truncate(text: str, limit: int = 280) -> str:
    """Truncate ``text`` to ``limit`` characters without breaking readability."""

    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _extract_tldr(response: QueryResponse) -> Optional[str]:
    """Derive a TL;DR string from common response fields."""

    metrics = response.metrics if isinstance(response.metrics, Mapping) else {}
    candidates: List[Any] = [
        getattr(response, "tldr", None),
        metrics.get("tldr"),
        metrics.get("summary"),
        metrics.get("tl_dr"),
    ]

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    answer = getattr(response, "answer", "") or ""
    if not answer.strip():
        return None

    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    if sentences:
        return _truncate(sentences[0])
    return _truncate(answer.strip())


def _extract_key_findings(response: QueryResponse) -> List[str]:
    """Extract key findings, falling back to reasoning claims when needed."""

    metrics = response.metrics if isinstance(response.metrics, Mapping) else {}
    direct: List[Any] = _coerce_sequence(getattr(response, "key_findings", None))
    if not direct:
        direct = _coerce_sequence(metrics.get("key_findings"))
    if not direct:
        direct = _coerce_sequence(metrics.get("findings"))

    findings: List[str] = [str(item).strip() for item in direct if str(item).strip()]
    if findings:
        return findings

    derived: List[str] = []
    for claim in _coerce_sequence(response.reasoning):
        if isinstance(claim, Mapping):
            content = str(claim.get("content", "")).strip()
        else:
            content = str(claim).strip()
        if content:
            derived.append(content)
        if len(derived) >= 5:
            break
    return derived


def _stringify_evidence(claim: Mapping[str, Any]) -> Optional[str]:
    """Return a compact evidence string for a claim mapping."""

    for key in ("evidence", "sources", "support"):
        if key not in claim:
            continue
        value = claim[key]
        values = _coerce_sequence(value)
        if not values:
            continue
        return ", ".join(str(v) for v in values)
    return None


def _extract_claim_rows(response: QueryResponse) -> List[Dict[str, Any]]:
    """Convert reasoning entries into a normalized table structure."""

    rows: List[Dict[str, Any]] = []
    for index, claim in enumerate(_coerce_sequence(response.reasoning), start=1):
        if isinstance(claim, Mapping):
            content = str(claim.get("content", "")).strip()
            claim_type = str(claim.get("type", "claim")).strip() or "claim"
            confidence = claim.get("confidence")
            if isinstance(confidence, (int, float)):
                confidence_text = f"{confidence:.2f}"
            elif confidence is None:
                confidence_text = ""
            else:
                confidence_text = str(confidence)
            evidence = _stringify_evidence(claim)
        else:
            content = str(claim).strip()
            claim_type = "statement"
            confidence_text = ""
            evidence = None

        if not content:
            continue

        rows.append(
            {
                "index": index,
                "content": content,
                "type": claim_type,
                "confidence": confidence_text,
                "evidence": evidence or "",
            }
        )
    return rows


def _stringify_trace_entry(entry: Any) -> Optional[str]:
    """Represent a trace entry as a readable string."""

    if entry is None:
        return None
    if isinstance(entry, str):
        return entry.strip() or None
    if isinstance(entry, Mapping):
        agent = entry.get("agent") or entry.get("role")
        action = entry.get("action") or entry.get("step")
        detail = entry.get("detail") or entry.get("content")
        parts = [str(part) for part in (agent, action, detail) if part]
        if parts:
            return " – ".join(parts)
        return json.dumps(entry, default=str)
    if isinstance(entry, Sequence) and not isinstance(entry, (bytes, str)):
        parts = [str(item) for item in entry if item]
        if parts:
            return " | ".join(parts)
        return None
    return str(entry)


def _extract_trace(response: QueryResponse) -> List[str]:
    """Gather detailed trace information from response metadata."""

    metrics = response.metrics if isinstance(response.metrics, Mapping) else {}
    candidates: List[Any] = [
        getattr(response, "trace", None),
        metrics.get("trace"),
        metrics.get("agent_trace"),
    ]

    audit = metrics.get("audit") or metrics.get("audit_log")
    if isinstance(audit, Mapping):
        candidates.append(audit.get("trace"))
        candidates.append(audit.get("steps"))
    elif audit is not None:
        candidates.append(audit)

    traces: List[str] = []
    for candidate in candidates:
        for entry in _coerce_sequence(candidate):
            formatted = _stringify_trace_entry(entry)
            if formatted:
                traces.append(formatted)
    return traces


def _extract_depth_sections(
    response: QueryResponse, depth_levels: Set[DepthLevel]
) -> DepthSections:
    """Collect depth-aware sections for the supplied response."""

    sections: DepthSections = {}
    if not depth_levels:
        return sections

    if DepthLevel.TLDR in depth_levels:
        tldr = _extract_tldr(response)
        if tldr:
            sections["tldr"] = tldr

    if DepthLevel.KEY_FINDINGS in depth_levels:
        findings = _extract_key_findings(response)
        if findings:
            sections["key_findings"] = findings

    if DepthLevel.CLAIMS in depth_levels:
        claims = _extract_claim_rows(response)
        if claims:
            sections["claims"] = claims

    if DepthLevel.TRACE in depth_levels:
        trace_entries = _extract_trace(response)
        if trace_entries:
            sections["trace"] = trace_entries

    return sections


def _render_claims_markdown(claims: Sequence[Mapping[str, Any]]) -> str:
    """Return a Markdown table for claim rows."""

    if not claims:
        return ""

    lines = [
        "| # | Claim | Type | Confidence | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in claims:
        lines.append(
            "| {index} | {content} | {type} | {confidence} | {evidence} |".format(
                index=row.get("index", ""),
                content=row.get("content", "").replace("|", "\\|"),
                type=row.get("type", ""),
                confidence=row.get("confidence", ""),
                evidence=row.get("evidence", ""),
            )
        )
    return "\n".join(lines)


def _render_depth_sections_markdown(sections: DepthSections) -> str:
    """Render depth sections to Markdown."""

    lines: List[str] = []

    if "tldr" in sections:
        lines.extend(["## TL;DR", "", sections["tldr"], ""])

    if "key_findings" in sections:
        lines.extend(["## Key Findings", ""])
        for finding in sections["key_findings"]:
            lines.append(f"- {finding}")
        lines.append("")

    if "claims" in sections:
        table = _render_claims_markdown(sections["claims"])
        if table:
            lines.extend(["## Claim Table", "", table, ""])

    if "trace" in sections:
        lines.extend(["## Trace", ""])
        for entry in sections["trace"]:
            lines.append(f"- {entry}")

    return "\n".join(lines).strip()


def _render_depth_sections_plain(sections: DepthSections) -> str:
    """Render depth sections to a plain-text block."""

    parts: List[str] = []

    if "tldr" in sections:
        parts.append(f"TL;DR:\n{sections['tldr']}")

    if "key_findings" in sections:
        findings = "\n".join(f"- {finding}" for finding in sections["key_findings"])
        parts.append(f"Key Findings:\n{findings}")

    if "claims" in sections:
        rows: List[str] = []
        for row in sections["claims"]:
            label = f"{row.get('index', '')}. [{row.get('type', '')}] {row.get('content', '')}"
            confidence = row.get("confidence")
            evidence = row.get("evidence")
            extras: List[str] = []
            if confidence:
                extras.append(f"confidence={confidence}")
            if evidence:
                extras.append(f"evidence={evidence}")
            if extras:
                label += f" ({'; '.join(extras)})"
            rows.append(f"- {label}")
        parts.append("Claim Table:\n" + "\n".join(rows))

    if "trace" in sections:
        trace_lines = "\n".join(f"- {entry}" for entry in sections["trace"])
        parts.append(f"Trace:\n{trace_lines}")

    return "\n\n".join(parts)


class FormatTemplate(BaseModel):
    """A template for formatting query responses.

    This class represents a format template that can be used to format QueryResponse
    objects. It uses the string.Template syntax for variable substitution, where
    variables are referenced as ${variable_name} in the template text.

    Attributes:
        name: The name of the template.
        description: An optional description of the template.
        template: The template text with variable placeholders.
    """

    name: str
    description: Optional[str] = None
    template: str

    def render(self, response: QueryResponse) -> str:
        """Render the template with the given QueryResponse.

        Args:
            response: The QueryResponse object to format.

        Returns:
            The rendered template as a string.

        Raises:
            KeyError: If a variable referenced in the template is not available in the response.
        """
        # Create a dictionary of variables from the response
        variables = {
            "answer": response.answer,
            "citations": "\n".join([f"- {c}" for c in response.citations]),
            "reasoning": "\n".join([f"- {r}" for r in response.reasoning]),
            "metrics": "\n".join([f"- {k}: {v}" for k, v in response.metrics.items()]),
        }

        depth_sections = _extract_depth_sections(response, set(EXPLICIT_DEPTH_LEVELS))
        variables.update(
            {
                "tldr": depth_sections.get("tldr", ""),
                "key_findings": "\n".join(
                    f"- {finding}" for finding in depth_sections.get("key_findings", [])
                ),
                "claims_table": _render_claims_markdown(depth_sections.get("claims", [])),
                "trace": "\n".join(depth_sections.get("trace", [])),
            }
        )

        # Add individual metrics as variables
        for k, v in response.metrics.items():
            variables[f"metric_{k}"] = str(v)

        # Use string.Template for variable substitution
        template = string.Template(self.template)
        try:
            return template.substitute(variables)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise KeyError(
                f"Missing required variable '{missing_var}' for format template '{self.name}'. "
                f"Available variables: {', '.join(variables.keys())}"
            )


class TemplateRegistry:
    """Registry for format templates.

    This class provides a centralized registry for storing and retrieving format templates.
    It maintains a dictionary of templates indexed by name and provides methods for
    registering, retrieving, and loading templates from configuration and files.
    """

    _templates: Dict[str, FormatTemplate] = {}
    _default_templates: Dict[str, Dict[str, Any]] = {
        "markdown": {
            "name": "markdown",
            "description": "Markdown format with headings and lists",
            "template": """# Answer
${answer}

## Citations
${citations}

## Reasoning
${reasoning}

## Metrics
${metrics}
""",
        },
        "plain": {
            "name": "plain",
            "description": "Simple text format for basic terminal output",
            "template": """Answer:
${answer}

Citations:
${citations}

Reasoning:
${reasoning}

Metrics:
${metrics}
""",
        },
    }

    @classmethod
    def register(cls, template: FormatTemplate) -> None:
        """Register a format template in the registry.

        Args:
            template: The template to register.
        """
        cls._templates[template.name] = template
        log.debug(f"Registered format template: {template.name}")

    @classmethod
    def get(cls, name: str) -> FormatTemplate:
        """Get a format template by name.

        Args:
            name: The name of the template.

        Returns:
            The format template.

        Raises:
            KeyError: If the template is not found.
        """
        if name not in cls._templates:
            # If the template is not registered, try to load it from the default templates
            if name in cls._default_templates:
                cls.register(FormatTemplate(**cls._default_templates[name]))
            else:
                # Try to load from template directory
                cls._load_template_from_file(name)

            if name not in cls._templates:
                raise KeyError(f"Format template '{name}' not found")

        return cls._templates[name]

    @classmethod
    def _load_template_from_file(cls, name: str) -> None:
        """Load a template from a file.

        Args:
            name: The name of the template.
        """
        config = ConfigLoader().config
        template_dir = getattr(config, "template_dir", None)

        if not template_dir:
            # Check common locations
            locations = [
                Path.cwd() / "templates",
                Path.home() / ".config" / "autoresearch" / "templates",
                Path("/etc/autoresearch/templates"),
            ]

            for loc in locations:
                if loc.exists() and loc.is_dir():
                    template_dir = str(loc)
                    break

        if not template_dir:
            return

        template_path = Path(template_dir) / f"{name}.tpl"

        if not template_path.exists():
            return

        try:
            with open(template_path, "r") as f:
                template_text = f.read()

            # First line can be a description
            lines = template_text.split("\n")
            description = None
            if lines and lines[0].startswith("#"):
                description = lines[0][1:].strip()
                template_text = "\n".join(lines[1:])

            template = FormatTemplate(
                name=name, description=description, template=template_text
            )
            cls.register(template)
        except Exception as e:
            log.warning(f"Failed to load template from {template_path}: {e}")

    @classmethod
    def load_from_config(cls) -> None:
        """Load templates from configuration."""
        config = ConfigLoader().config
        templates = getattr(config, "output_templates", {})

        for name, template_data in templates.items():
            if isinstance(template_data, dict) and "template" in template_data:
                try:
                    template = FormatTemplate(name=name, **template_data)
                    cls.register(template)
                except Exception as e:
                    log.warning(f"Failed to load template '{name}' from config: {e}")


class OutputFormatter:
    """Utility class for formatting query responses in various output formats.

    This class provides static methods to format QueryResponse objects into
    different output formats suitable for various contexts, such as CLI output,
    API responses, or documentation.

    The class validates that the input conforms to the QueryResponse structure
    before formatting, ensuring consistent output regardless of the source of
    the data.

    Supported formats:
        - json: Structured JSON format for programmatic consumption
        - plain/text: Simple text format for basic terminal output
        - markdown (default): Rich text format with headings and lists
        - template:<name>: Custom template format (e.g., "template:html")
    """

    @classmethod
    def _initialize(cls) -> None:
        """Initialize the formatter by loading templates from configuration."""
        try:
            TemplateRegistry.load_from_config()
        except Exception as e:
            log.warning(f"Failed to load templates from config: {e}")

    @classmethod
    def collect_depth_sections(
        cls,
        response: QueryResponse,
        depth: Optional[Iterable[Union[DepthLevel, str]]],
    ) -> DepthSections:
        """Collect depth-aware sections for reuse."""

        return _extract_depth_sections(response, _normalize_depth(depth))

    @staticmethod
    def render_claim_table_markdown(claims: Sequence[Mapping[str, Any]]) -> str:
        """Expose Markdown claim-table rendering for UI components."""

        return _render_claims_markdown(claims)

    @staticmethod
    def render_depth_sections(sections: DepthSections, fmt: str = "markdown") -> str:
        """Render depth sections to either Markdown or plain text."""

        if fmt in {"plain", "text"}:
            return _render_depth_sections_plain(sections)
        return _render_depth_sections_markdown(sections)

    @classmethod
    def format(
        cls,
        result: Any,
        format_type: str = "markdown",
        depth: Optional[Iterable[Union[DepthLevel, str]]] = None,
    ) -> None:
        """Validate and format a query result to the specified output format."""

        cls._initialize()

        try:
            response = (
                result
                if isinstance(result, QueryResponse)
                else QueryResponse.model_validate(result)
            )
        except ValidationError as exc:  # pragma: no cover - handled by caller
            raise AutoresearchValidationError(
                "Invalid response format", cause=exc
            ) from exc

        fmt = format_type.lower()
        sections = cls.collect_depth_sections(response, depth)

        if fmt == "json":
            payload = response.model_dump(mode="json")
            if sections:
                payload["depth_sections"] = sections
            sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        elif fmt == "graph":
            from rich.tree import Tree
            from rich.console import Console

            tree = Tree("Knowledge Graph")
            ans_node = tree.add("Answer")
            ans_node.add(response.answer)

            citations_node = ans_node.add("Citations")
            for c in response.citations:
                citations_node.add(str(c))

            reasoning_node = tree.add("Reasoning")
            for r in response.reasoning:
                reasoning_node.add(str(r))

            metrics_node = tree.add("Metrics")
            for k, v in response.metrics.items():
                metrics_node.add(f"{k}: {v}")

            Console(file=sys.stdout, force_terminal=False, color_system=None).print(tree)
        elif fmt.startswith("template:"):
            # Custom template format
            template_name = fmt.split(":", 1)[1]
            try:
                template = TemplateRegistry.get(template_name)
                output = template.render(response)
                if sections:
                    extra = cls.render_depth_sections(
                        sections, "plain" if template_name == "plain" else "markdown"
                    )
                    if extra:
                        output = output.rstrip() + "\n\n" + extra
                sys.stdout.write(output + "\n")
            except KeyError as e:
                log.error(f"Template error: {e}")
                # Fall back to markdown if template not found
                log.warning(
                    f"Template '{template_name}' not found, falling back to markdown"
                )
                cls.format(result, "markdown", depth=depth)
        elif fmt in {"plain", "text"}:
            try:
                template = TemplateRegistry.get("plain")
                output = template.render(response)
                if sections:
                    extra = cls.render_depth_sections(sections, "plain")
                    if extra:
                        output = output.rstrip() + "\n\n" + extra
                sys.stdout.write(output + "\n")
            except KeyError:
                # Fall back to hardcoded plain format if template not found
                sys.stdout.write("Answer:\n")
                sys.stdout.write(response.answer + "\n\n")
                sys.stdout.write("Citations:\n")
                for c in response.citations:
                    sys.stdout.write(f"{c}\n")
                sys.stdout.write("\nReasoning:\n")
                for r in response.reasoning:
                    sys.stdout.write(f"{r}\n")
                sys.stdout.write("\nMetrics:\n")
                for k, v in response.metrics.items():
                    sys.stdout.write(f"{k}: {v}\n")
        else:
            try:
                template = TemplateRegistry.get("markdown")
                output = template.render(response)
                if sections:
                    extra = cls.render_depth_sections(sections, "markdown")
                    if extra:
                        output = output.rstrip() + "\n\n" + extra
                sys.stdout.write(output + "\n")
            except KeyError:
                sys.stdout.write("# Answer\n")
                sys.stdout.write(response.answer + "\n\n")
                sys.stdout.write("## Citations\n")
                for c in response.citations:
                    sys.stdout.write(f"- {c}\n")
                sys.stdout.write("\n## Reasoning\n")
                for r in response.reasoning:
                    sys.stdout.write(f"- {r}\n")
                sys.stdout.write("\n## Metrics\n")
                for k, v in response.metrics.items():
                    sys.stdout.write(f"- **{k}**: {v}\n")
                if sections:
                    extra = cls.render_depth_sections(sections, "markdown")
                    if extra:
                        sys.stdout.write("\n" + extra + "\n")
