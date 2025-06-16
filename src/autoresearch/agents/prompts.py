"""
Prompt template system for agent prompts.

This module provides a system for loading, managing, and rendering prompt templates
for agents. Templates can be loaded from configuration files and support variable
substitution.

The prompt template system consists of:
1. PromptTemplate: A Pydantic model for defining templates with variables
2. PromptTemplateRegistry: A registry for storing and retrieving templates
3. Helper functions for working with templates (get_prompt_template, render_prompt)

Templates support variable substitution using the string.Template syntax (${variable}).
Default templates for common agent types are provided, but custom templates can be
defined in configuration files or registered programmatically.
"""

import os
import string
from typing import Dict, Any, Optional
from pathlib import Path

from pydantic import BaseModel, Field, validator

from ..config import ConfigModel
from ..errors import ConfigError


class PromptTemplate(BaseModel):
    """A template for generating prompts with variable substitution.

    This class represents a prompt template that can be rendered with variables.
    It stores the template text, an optional description, and a dictionary of
    default variables with their descriptions.

    Templates use the string.Template syntax for variable substitution, where
    variables are referenced as ${variable_name} in the template text.

    When rendering a template, default variables are combined with any variables
    provided at render time, with the latter taking precedence if there are duplicates.
    """

    template: str
    description: Optional[str] = None
    variables: Dict[str, str] = Field(default_factory=dict)

    def render(self, **kwargs) -> str:
        """Render the template with the given variables.

        This method renders the template by substituting variables into the template text.
        It combines the default variables defined in the template with the variables
        provided as keyword arguments, with the latter taking precedence if there are
        duplicates.

        Variable substitution uses the string.Template syntax, where variables are
        referenced as ${variable_name} in the template text. All variables referenced
        in the template must be provided either as default variables or as keyword
        arguments, or a KeyError will be raised.

        Args:
            **kwargs: Variables to substitute in the template. These will override
                     any default variables with the same name.

        Returns:
            The rendered template as a string with all variables substituted.

        Raises:
            KeyError: If a variable referenced in the template is not provided
                     either as a default variable or as a keyword argument.
                     The error message includes the name of the missing variable
                     and a list of available variables.
        """
        # Combine default variables with provided kwargs
        variables = {**self.variables, **kwargs}

        # Use string.Template for variable substitution
        template = string.Template(self.template)
        try:
            return template.substitute(variables)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise KeyError(
                f"Missing required variable '{missing_var}' for prompt template. "
                f"Available variables: {', '.join(variables.keys())}"
            )


class PromptTemplateRegistry:
    """Registry for prompt templates.

    This class provides a centralized registry for storing and retrieving prompt templates.
    It maintains a dictionary of templates indexed by name and provides methods for
    registering, retrieving, and loading templates from configuration.

    The registry includes a set of default templates for common agent types, which are
    loaded on demand when requested. Custom templates can be registered programmatically
    or loaded from configuration files.

    All methods are class methods, as the registry is a singleton that maintains state
    across the application.
    """

    _templates: Dict[str, PromptTemplate] = {}
    _default_templates: Dict[str, Dict[str, Any]] = {
        "planner.research_plan": {
            "template": """You are a Planner agent responsible for structuring complex research tasks.

Your task is to create a comprehensive research plan for the following query: ${query}

Guidelines:
1. Break down the query into key components and sub-questions
2. Identify the main research areas that need to be explored
3. Outline a logical sequence of research steps
4. Specify what information needs to be gathered at each step
5. Identify potential methodologies or approaches for different aspects of the research
6. Anticipate potential challenges or limitations and how to address them
7. Suggest criteria for evaluating the quality and relevance of information
8. Create a structured outline with clear sections and subsections

Your research plan should be comprehensive, well-organized, and provide a clear roadmap for conducting thorough research on the topic.
""",
            "description": "Create a structured research plan for a complex query",
            "variables": {
                "query": "The research query"
            },
        },
        "summarizer.concise": {
            "template": """You are a Summarizer agent responsible for generating concise, clear summaries of complex information.

Your task is to create a concise summary of the following content related to the query: ${query}

Content:
${content}

Guidelines:
1. Distill the essential information while maintaining accuracy
2. Focus on the most important points, findings, and conclusions
3. Organize the summary in a logical, easy-to-follow structure
4. Use clear, precise language that is accessible to the target audience
5. Maintain objectivity and balance in representing different perspectives
6. Aim for brevity without sacrificing critical details or nuance
7. Ensure the summary stands on its own as a complete, coherent piece
8. Highlight key takeaways or actionable insights when relevant

Your summary should be significantly shorter than the original content while preserving its core meaning and value.
""",
            "description": "Generate a concise summary of complex information",
            "variables": {
                "query": "The original query",
                "content": "The content to summarize"
            },
        },
        "critic.evaluation": {
            "template": """You are a Critic agent responsible for evaluating the quality of research and providing constructive feedback.

Your task is to critically evaluate the following claims related to the query: ${query}

Claims:
${claims}

Guidelines:
1. Assess the logical structure and coherence of the claims
2. Identify strengths and weaknesses in the research and reasoning
3. Evaluate the quality and sufficiency of evidence provided
4. Check for potential biases, assumptions, or logical fallacies
5. Assess the comprehensiveness of the analysis
6. Identify any missing perspectives or counterarguments
7. Evaluate the clarity and precision of language used
8. Provide specific, actionable recommendations for improvement

Your critique should be balanced, highlighting both strengths and areas for improvement, and should aim to enhance the overall quality of the research.
""",
            "description": "Evaluate research quality and provide constructive feedback",
            "variables": {
                "query": "The research query",
                "claims": "The claims to evaluate"
            },
        },
        "researcher.findings": {
            "template": """You are a Researcher agent responsible for conducting in-depth research on a topic.

Your task is to analyze the following sources and provide comprehensive research findings on the query: ${query}

Sources:
${sources}

Guidelines:
1. Extract key information, facts, and insights from the sources
2. Identify patterns, trends, and connections across multiple sources
3. Highlight areas of consensus and disagreement among sources
4. Evaluate the credibility and relevance of each source
5. Organize your findings in a clear, structured format
6. Prioritize depth and comprehensiveness over brevity
7. Include specific details, statistics, and examples when available
8. Note any gaps in the available information that would benefit from further research

Your research findings should be thorough, well-organized, and provide a solid foundation for further analysis.
""",
            "description": "Generate comprehensive research findings from multiple sources",
            "variables": {
                "query": "The research query",
                "sources": "The sources to analyze"
            },
        },
        "synthesizer.thesis": {
            "template": """You are a Synthesizer agent responsible for creating an initial thesis in response to a user query.

Your task is to provide a well-reasoned, comprehensive thesis that addresses the query: ${query}

Guidelines:
1. Consider multiple perspectives and angles on the topic
2. Base your thesis on factual information when possible
3. Be clear and concise, but thorough in your analysis
4. Structure your response with a clear introduction, body, and conclusion
5. Highlight key points that might be important for further discussion

Your thesis will serve as the foundation for a dialectical reasoning process, so make it substantive and thought-provoking.
""",
            "description": "Generate an initial thesis for the given query",
            "variables": {"query": "The user's query"},
        },
        "synthesizer.direct": {
            "template": """You are a Synthesizer agent responsible for providing a direct answer to a user query.

Your task is to answer the following query directly and comprehensively: ${query}

Guidelines:
1. Provide a clear, direct answer to the query
2. Support your answer with relevant facts and reasoning
3. Consider multiple perspectives if appropriate
4. Structure your response in a logical, easy-to-follow manner
5. Be concise but thorough

Your answer should be informative, balanced, and helpful to the user.
""",
            "description": "Generate a direct answer for the given query",
            "variables": {"query": "The user's query"},
        },
        "synthesizer.synthesis": {
            "template": """You are a Synthesizer agent responsible for creating a final synthesis from multiple claims.

Your task is to synthesize the following claims into a coherent, comprehensive answer:

${claims}

Guidelines:
1. Identify common themes and points of agreement across the claims
2. Reconcile contradictions and opposing viewpoints when possible
3. Evaluate the strength of evidence supporting different positions
4. Create a balanced synthesis that incorporates the strongest elements from each claim
5. Structure your synthesis with a clear introduction, integrated body, and conclusion
6. Highlight any remaining uncertainties or areas for further exploration

Your synthesis should represent a higher-level understanding that emerges from considering all perspectives.
""",
            "description": "Generate a synthesis from the given claims",
            "variables": {"claims": "The claims to synthesize"},
        },
        "contrarian.antithesis": {
            "template": """You are a Contrarian agent responsible for challenging an existing thesis with alternative viewpoints.

Your task is to provide a well-reasoned antithesis to the following thesis:

${thesis}

Guidelines:
1. Identify the key assumptions and claims in the thesis
2. Challenge these assumptions with alternative perspectives
3. Provide counterarguments and counterexamples
4. Present alternative interpretations of the evidence
5. Highlight limitations, exceptions, or weaknesses in the thesis
6. Structure your antithesis clearly, with specific points of contention
7. Be respectful but thorough in your critique

Your antithesis should be substantive and thought-provoking, not merely contradictory. The goal is to enrich the dialectical process by ensuring all perspectives are considered.
""",
            "description": "Generate an antithesis for the given thesis",
            "variables": {"thesis": "The thesis to challenge"},
        },
        "fact_checker.verification": {
            "template": """You are a Fact Checker agent responsible for verifying the factual accuracy of claims.

Your task is to verify the following claims:

${claims}

Guidelines:
1. Evaluate each claim for factual accuracy
2. Identify any factual errors, misrepresentations, or unsupported assertions
3. Distinguish between facts, opinions, and interpretations
4. Note where claims may be technically correct but misleading
5. Provide corrections for inaccurate information
6. Indicate where claims would benefit from additional context
7. Rate the overall reliability of each claim (e.g., accurate, partially accurate, inaccurate)

Your verification should be objective, balanced, and focused on factual accuracy rather than agreement or disagreement with the claims.
""",
            "description": "Verify the factual accuracy of the given claims",
            "variables": {"claims": "The claims to verify"},
        },
    }

    @classmethod
    def register(cls, name: str, template: PromptTemplate) -> None:
        """Register a prompt template in the registry.

        This method adds a prompt template to the registry with the given name.
        If a template with the same name already exists, it will be overwritten.

        Template names typically follow a convention of "agent_type.template_type",
        for example "synthesizer.thesis" or "contrarian.antithesis".

        Args:
            name: The name of the template. Used as a key in the registry.
            template: The template to register. Must be a PromptTemplate instance.

        Note:
            This method modifies the global registry state. Changes will affect
            all parts of the application that use the registry.
        """
        cls._templates[name] = template

    @classmethod
    def get(cls, name: str) -> PromptTemplate:
        """Get a prompt template by name.

        Args:
            name: The name of the template.

        Returns:
            The prompt template.

        Raises:
            KeyError: If the template is not found.
        """
        if name not in cls._templates:
            # If the template is not registered, try to load it from the default templates
            if name in cls._default_templates:
                cls.register(name, PromptTemplate(**cls._default_templates[name]))
            else:
                raise KeyError(f"Prompt template '{name}' not found")
        return cls._templates[name]

    @classmethod
    def load_from_config(cls, config: ConfigModel) -> None:
        """Load prompt templates from configuration.

        Args:
            config: The configuration model.

        Raises:
            ConfigError: If the prompt templates configuration is invalid.
        """
        prompt_config = config.prompt_templates if hasattr(config, "prompt_templates") else {}

        for name, template_config in prompt_config.items():
            try:
                template = PromptTemplate(**template_config)
                cls.register(name, template)
            except Exception as e:
                raise ConfigError(
                    f"Invalid prompt template configuration for '{name}': {str(e)}"
                )

    @classmethod
    def reset(cls) -> None:
        """Reset the registry, clearing all registered templates."""
        cls._templates.clear()


def get_prompt_template(name: str) -> PromptTemplate:
    """Get a prompt template by name.

    Args:
        name: The name of the template.

    Returns:
        The prompt template.

    Raises:
        KeyError: If the template is not found.
    """
    return PromptTemplateRegistry.get(name)


def render_prompt(name: str, **kwargs) -> str:
    """Render a prompt template with the given variables.

    Args:
        name: The name of the template.
        **kwargs: Variables to substitute in the template.

    Returns:
        The rendered prompt as a string.

    Raises:
        KeyError: If the template is not found or a required variable is missing.
    """
    template = get_prompt_template(name)
    return template.render(**kwargs)
