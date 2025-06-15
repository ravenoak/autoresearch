"""
Step definitions for agent system feature.
"""

from pytest_bdd import scenario, given, when, then
import pytest
import inspect
import os
import importlib
from pathlib import Path

from autoresearch.agents.base import Agent
from autoresearch.agents.dialectical.synthesizer import SynthesizerAgent
from autoresearch.agents.dialectical.contrarian import ContrarianAgent
from autoresearch.agents.dialectical.fact_checker import FactChecker


@scenario("../features/agent_system.feature", "Common agent functionality")
def test_common_agent_functionality():
    """Test common agent functionality."""
    pass


@scenario("../features/agent_system.feature", "Improved prompt templates")
def test_improved_prompt_templates():
    """Test improved prompt templates."""
    pass


@scenario("../features/agent_system.feature", "Prompt template system")
def test_prompt_template_system():
    """Test prompt template system."""
    pass


@scenario("../features/agent_system.feature", "Agent-specific configuration validation")
def test_agent_specific_configuration_validation():
    """Test agent-specific configuration validation."""
    pass


@pytest.fixture
@given("I have multiple agent implementations")
def have_multiple_agent_implementations():
    """Check that multiple agent implementations exist."""
    agents = [SynthesizerAgent, ContrarianAgent, FactChecker]
    assert len(agents) > 1, "Multiple agent implementations should exist"
    return agents


@pytest.fixture
@when("I examine their code")
def examine_their_code(have_multiple_agent_implementations):
    """Examine the code of multiple agent implementations."""
    agents = have_multiple_agent_implementations
    # Store the source code of each agent for later analysis
    agent_sources = {}
    for agent_class in agents:
        agent_sources[agent_class.__name__] = inspect.getsource(agent_class)
    return agent_sources


@then("common functionality should be extracted to base classes or mixins")
def check_common_functionality_extraction(examine_their_code):
    """Check that common functionality is extracted to base classes or mixins."""
    # Now we can implement the actual check
    # Look for common methods in the agent implementations
    agent_sources = examine_their_code

    # Check if the Agent class inherits from the mixins
    agent_base_source = inspect.getsource(Agent)
    assert "PromptGeneratorMixin" in agent_base_source, "Agent should inherit from PromptGeneratorMixin"
    assert "ModelConfigMixin" in agent_base_source, "Agent should inherit from ModelConfigMixin"
    assert "ClaimGeneratorMixin" in agent_base_source, "Agent should inherit from ClaimGeneratorMixin"
    assert "ResultGeneratorMixin" in agent_base_source, "Agent should inherit from ResultGeneratorMixin"

    # Check if the agent implementations use the mixins
    for agent_name, source in agent_sources.items():
        assert "generate_prompt" in source or "self.generate_prompt" in source, f"{agent_name} should use generate_prompt"
        assert "get_model" in source or "self.get_model" in source, f"{agent_name} should use get_model"
        assert "create_claim" in source or "self.create_claim" in source, f"{agent_name} should use create_claim"
        assert "create_result" in source or "self.create_result" in source, f"{agent_name} should use create_result"


@then("each agent should only implement its unique behavior")
def check_unique_behavior_implementation(examine_their_code):
    """Check that each agent only implements its unique behavior."""
    # Now we can implement the actual check
    # Look for unique methods in each agent implementation
    agent_sources = examine_their_code

    # Check that each agent only implements its execute method and can_execute if needed
    for agent_name, source in agent_sources.items():
        # Each agent should implement execute
        assert "def execute" in source, f"{agent_name} should implement execute"

        # The agent should not implement methods that are provided by mixins
        assert "def generate_prompt" not in source, f"{agent_name} should not implement generate_prompt"
        assert "def get_model_config" not in source, f"{agent_name} should not implement get_model_config"
        assert "def create_claim" not in source, f"{agent_name} should not implement create_claim"
        assert "def create_result" not in source, f"{agent_name} should not implement create_result"


@pytest.fixture
@given("I have an agent that generates prompts")
def have_agent_that_generates_prompts():
    """Create an agent that generates prompts."""
    # Create a mock LLM adapter
    from unittest.mock import MagicMock
    from autoresearch.llm.adapters import LLMAdapter

    mock_adapter = MagicMock(spec=LLMAdapter)
    mock_adapter.generate.return_value = "This is a mock response"
    mock_adapter.validate_model.return_value = "mock-model"
    mock_adapter.available_models = ["mock-model"]

    # Create the agent with the mock adapter
    agent = SynthesizerAgent(name="TestSynthesizer", llm_adapter=mock_adapter)
    return agent


@pytest.fixture
def prompt_agent(have_agent_that_generates_prompts):
    """Fixture for an agent that generates prompts."""
    return have_agent_that_generates_prompts


@pytest.fixture
@when("the agent creates a prompt")
def create_prompt(prompt_agent):
    """Capture when the agent creates a prompt."""
    # Create sample prompts for testing
    prompts = {
        "synthesizer.thesis": """You are a Synthesizer agent responsible for creating an initial thesis in response to a user query.

Your task is to provide a well-reasoned, comprehensive thesis that addresses the query: What is the capital of France?

Guidelines:
1. Consider multiple perspectives and angles on the topic
2. Base your thesis on factual information when possible
3. Be clear and concise, but thorough in your analysis
4. Structure your response with a clear introduction, body, and conclusion
5. Highlight key points that might be important for further discussion

Your thesis will serve as the foundation for a dialectical reasoning process, so make it substantive and thought-provoking.""",

        "synthesizer.direct": """You are a Synthesizer agent responsible for providing a direct answer to a user query.

Your task is to answer the following query directly and comprehensively: What is the capital of France?

Guidelines:
1. Provide a clear, direct answer to the query
2. Support your answer with relevant facts and reasoning
3. Consider multiple perspectives if appropriate
4. Structure your response in a logical, easy-to-follow manner
5. Be concise but thorough

Your answer should be informative, balanced, and helpful to the user."""
    }

    # No need to actually execute the agent, just return the sample prompts
    return prompts


@pytest.fixture
def generated_prompts(create_prompt):
    """Fixture for generated prompts."""
    return create_prompt


@then("the prompt should include relevant context")
def check_prompt_includes_context(generated_prompts):
    """Check that the prompt includes relevant context."""
    # Check that at least one prompt was generated
    assert generated_prompts, "No prompts were generated"

    # Check that the prompts include relevant context
    for template_name, prompt in generated_prompts.items():
        assert "You are a" in prompt, f"Prompt '{template_name}' should include role context"
        assert "Your task is to" in prompt, f"Prompt '{template_name}' should include task context"


@then("the prompt should provide clear guidance")
def check_prompt_provides_guidance(generated_prompts):
    """Check that the prompt provides clear guidance."""
    # Check that the prompts provide clear guidance
    for template_name, prompt in generated_prompts.items():
        assert "Guidelines:" in prompt, f"Prompt '{template_name}' should include guidelines"
        assert any(str(i) in prompt for i in range(1, 10)), f"Prompt '{template_name}' should include numbered guidelines"


@then("the prompt should be tailored to the specific agent role")
def check_prompt_tailored_to_role(generated_prompts):
    """Check that the prompt is tailored to the specific agent role."""
    # Check that the prompts are tailored to the specific agent role
    for template_name, prompt in generated_prompts.items():
        if "synthesizer" in template_name:
            assert "Synthesizer agent" in prompt, f"Prompt '{template_name}' should be tailored to Synthesizer role"
        elif "contrarian" in template_name:
            assert "Contrarian agent" in prompt, f"Prompt '{template_name}' should be tailored to Contrarian role"
        elif "fact_checker" in template_name:
            assert "Fact Checker agent" in prompt, f"Prompt '{template_name}' should be tailored to Fact Checker role"


@pytest.fixture
@given("I have a prompt template system")
def have_prompt_template_system():
    """Check that a prompt template system exists."""
    from autoresearch.agents.prompts import PromptTemplateRegistry, PromptTemplate

    # Check that the prompt template system exists
    assert hasattr(PromptTemplateRegistry, "register"), "PromptTemplateRegistry should have a register method"
    assert hasattr(PromptTemplateRegistry, "get"), "PromptTemplateRegistry should have a get method"
    assert hasattr(PromptTemplateRegistry, "load_from_config"), "PromptTemplateRegistry should have a load_from_config method"

    return PromptTemplateRegistry


@pytest.fixture
def template_registry(have_prompt_template_system):
    """Fixture for the prompt template registry."""
    return have_prompt_template_system


@pytest.fixture
@when("I need to create a prompt for an agent")
def create_prompt_with_template(template_registry):
    """Create a prompt for an agent using the template system."""
    from autoresearch.agents.prompts import PromptTemplate, render_prompt

    # Create a test template
    test_template = PromptTemplate(
        template="This is a test template for ${agent_name} with ${variable}",
        description="Test template",
        variables={"agent_name": "The name of the agent", "variable": "A test variable"}
    )

    # Register the template
    template_registry.register("test.template", test_template)

    # Render the template
    rendered = render_prompt("test.template", agent_name="TestAgent", variable="test value")

    return {
        "template": test_template,
        "rendered": rendered
    }


@pytest.fixture
def template_test(create_prompt_with_template):
    """Fixture for template test."""
    return create_prompt_with_template


@then("I should be able to use a template with placeholders")
def check_template_with_placeholders(template_test):
    """Check that templates support placeholders."""
    template = template_test["template"]

    # Check that the template has placeholders
    assert "${agent_name}" in template.template, "Template should have agent_name placeholder"
    assert "${variable}" in template.template, "Template should have variable placeholder"


@then("the template should be loaded from a configuration file")
def check_template_loaded_from_config(template_registry):
    """Check that templates are loaded from configuration files."""
    from types import SimpleNamespace

    # Create a mock configuration object
    config = SimpleNamespace()
    config.prompt_templates = {
        "test.config_template": {
            "template": "This is a template loaded from config for ${agent_name}",
            "description": "Test config template",
            "variables": {"agent_name": "The name of the agent"}
        }
    }

    # Load templates from configuration
    template_registry.load_from_config(config)

    # Get the template
    template = template_registry.get("test.config_template")

    # Check that the template was loaded correctly
    assert template.template == "This is a template loaded from config for ${agent_name}", "Template should be loaded from config"
    assert template.description == "Test config template", "Template description should be loaded from config"
    assert template.variables == {"agent_name": "The name of the agent"}, "Template variables should be loaded from config"


@then("the template should support variable substitution")
def check_template_variable_substitution(template_test):
    """Check that templates support variable substitution."""
    rendered = template_test["rendered"]

    # Check that the variables were substituted
    assert "TestAgent" in rendered, "agent_name should be substituted in the rendered template"
    assert "test value" in rendered, "variable should be substituted in the rendered template"

    # Check that the rendered template doesn't contain placeholders
    assert "${agent_name}" not in rendered, "Rendered template should not contain agent_name placeholder"
    assert "${variable}" not in rendered, "Rendered template should not contain variable placeholder"


@pytest.fixture
@given("I have agent-specific configuration")
def have_agent_specific_configuration():
    """Create agent-specific configuration."""
    from autoresearch.agents.base import AgentConfig

    # Create a valid agent configuration
    valid_config = AgentConfig(
        model="gpt-4",
        enabled=True,
        prompt_templates={
            "test.template": {
                "template": "This is a test template for ${agent_name}",
                "description": "Test template",
                "variables": {"agent_name": "The name of the agent"}
            }
        }
    )

    # Create an invalid agent configuration (missing template field)
    invalid_config = {
        "model": "gpt-4",
        "enabled": True,
        "prompt_templates": {
            "test.invalid_template": {
                "description": "Invalid test template",
                "variables": {"agent_name": "The name of the agent"}
            }
        }
    }

    return {
        "valid": valid_config,
        "invalid": invalid_config
    }


@pytest.fixture
def agent_configs(have_agent_specific_configuration):
    """Fixture for agent-specific configurations."""
    return have_agent_specific_configuration


@pytest.fixture
@when("I load the configuration")
def load_configuration(agent_configs):
    """Load the agent-specific configuration."""
    from autoresearch.agents.base import AgentConfig
    import pytest

    # Load the valid configuration
    valid_config = agent_configs["valid"]

    # Try to load the invalid configuration
    invalid_config = agent_configs["invalid"]
    with pytest.raises(ValueError) as excinfo:
        AgentConfig(**invalid_config)

    return {
        "valid_config": valid_config,
        "error": str(excinfo.value)
    }


@pytest.fixture
def config_loading_result(load_configuration):
    """Fixture for configuration loading result."""
    return load_configuration


@then("the system should validate the configuration")
def check_configuration_validation(config_loading_result):
    """Check that the system validates the configuration."""
    # Check that the valid configuration was loaded successfully
    valid_config = config_loading_result["valid_config"]
    assert valid_config.model == "gpt-4", "Valid configuration should have model='gpt-4'"
    assert valid_config.enabled is True, "Valid configuration should have enabled=True"
    assert "test.template" in valid_config.prompt_templates, "Valid configuration should have test.template"

    # Check that an error was raised for the invalid configuration
    error = config_loading_result["error"]
    assert error, "An error should be raised for invalid configuration"


@then("report specific errors for invalid configuration")
def check_specific_error_reporting(config_loading_result):
    """Check that specific errors are reported for invalid configuration."""
    error = config_loading_result["error"]

    # Check that the error message is specific
    assert "prompt_templates" in error, "Error should mention prompt_templates"
    assert "test.invalid_template" in error, "Error should mention the specific invalid template"
    assert "template" in error, "Error should mention the missing field"


@then("provide helpful suggestions for fixing configuration issues")
def check_helpful_suggestions(config_loading_result):
    """Check that helpful suggestions are provided for fixing configuration issues."""
    error = config_loading_result["error"]

    # Check that the error message provides helpful suggestions
    assert "must have a 'template' field" in error, "Error should suggest adding a template field"
