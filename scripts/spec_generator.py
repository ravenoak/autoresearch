#!/usr/bin/env python3
"""
Specification generator for spec-driven development in autoresearch project.

This script helps create comprehensive specifications for new features following
the project's specification-driven development methodology.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class SpecificationSection:
    """Represents a section of a specification document."""
    title: str
    content: str
    subsections: List['SpecificationSection'] = field(default_factory=list)

    def to_markdown(self, level: int = 2) -> str:
        """Convert section to markdown format."""
        header = "#" * level
        result = f"{header} {self.title}\n\n{self.content}\n\n"

        for subsection in self.subsections:
            result += subsection.to_markdown(level + 1)

        return result


@dataclass
class Specification:
    """Complete specification document."""
    title: str
    feature_name: str
    sections: List[SpecificationSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Convert specification to markdown format."""
        result = [f"# {self.title}\n"]

        if self.metadata:
            result.append("## Metadata\n")
            for key, value in self.metadata.items():
                result.append(f"- **{key}**: {value}")
            result.append("")

        for section in self.sections:
            result.append(section.to_markdown())

        return "\n".join(result)


class SpecGenerator:
    """Generates comprehensive specifications for autoresearch features."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.specs_dir = self.project_root / "docs" / "specs"

        # Ensure specs directory exists
        self.specs_dir.mkdir(parents=True, exist_ok=True)

    def generate_agent_spec(self, agent_name: str, agent_type: str, description: str) -> Specification:
        """Generate specification for a new AI agent."""
        spec = Specification(
            title=f"Agent Specification: {agent_name}",
            feature_name=agent_name,
            metadata={
                "Type": "Agent",
                "Created": datetime.now().isoformat(),
                "Status": "Draft"
            }
        )

        # Executive Summary
        spec.sections.append(SpecificationSection(
            title="Executive Summary",
            content=f"""**Agent Overview**: {agent_name} is a new {agent_type} agent designed to enhance the autoresearch platform's capabilities.

**Purpose**: {description}

**Business Value**:
- Improves the platform's ability to handle {agent_type.lower()} tasks
- Enhances user experience through more intelligent {agent_type.lower()} capabilities
- Increases platform reliability and performance in {agent_type.lower()} scenarios

**Success Metrics**:
- Agent accuracy rate > 90%
- Response time < 100ms for typical queries
- Error rate < 1%
- User satisfaction score > 4.5/5

**Scope**:
- Includes: Core agent logic, message handling, error recovery
- Excludes: UI components, external integrations (unless specified)
"""
        ))

        # Technical Design
        spec.sections.append(SpecificationSection(
            title="Technical Design",
            content="""**Architecture Impact**:
- Integrates with existing agent framework in `src/autoresearch/agents/`
- Follows established agent patterns and interfaces
- Maintains compatibility with current orchestration system

**Component Design**:
- Inherits from base agent class for consistent behavior
- Implements domain-specific reasoning algorithms
- Includes comprehensive error handling and recovery
- Provides clear, documented public APIs

**API Design**:
```python
class {agent_name}(BaseAgent):
    \"\"\"{agent_name} agent for {agent_type.lower()} tasks.\"\"\"

    async def process_message(self, message: AgentMessage) -> AgentResponse:
        \"\"\"Process incoming message and return response.\"\"\"
        pass

    async def validate_input(self, input_data: Dict) -> bool:
        \"\"\"Validate input data for processing.\"\"\"
        pass
```

**Integration Points**:
- Message broker for inter-agent communication
- Orchestration system for task coordination
- Storage layer for persistent state management
""",
            subsections=[
                SpecificationSection(
                    title="Agent Architecture",
                    content=f"""**Core Components**:
- `{agent_name}`: Main agent class implementing {agent_type.lower()} logic
- `{agent_name}Config`: Configuration management for agent settings
- `{agent_name}Tests`: Comprehensive test suite

**Reasoning Engine**:
- Implements dialectical reasoning patterns appropriate for {agent_type.lower()}
- Uses evidence-based decision making
- Supports context-aware processing
- Includes fallback mechanisms for edge cases
"""
                ),
                SpecificationSection(
                    title="Message Handling",
                    content="""**Message Types**:
- Query messages for information requests
- Command messages for action requests
- Status messages for system updates

**Processing Pipeline**:
1. Message validation and parsing
2. Context retrieval and analysis
3. Reasoning and decision making
4. Response generation and formatting
5. Error handling and recovery
"""
                )
            ]
        ))

        # Implementation Plan
        spec.sections.append(SpecificationSection(
            title="Implementation Plan",
            content=f"""**Development Tasks**:

1. **Agent Foundation** (Week 1)
   - Create base agent class structure
   - Implement core message handling
   - Add basic configuration management

2. **Reasoning Engine** (Week 2)
   - Implement {agent_type.lower()}-specific reasoning algorithms
   - Add evidence evaluation capabilities
   - Integrate with existing knowledge base

3. **Integration & Testing** (Week 3)
   - Connect with orchestration system
   - Implement comprehensive test suite
   - Add performance monitoring

4. **Documentation & Deployment** (Week 4)
   - Complete API documentation
   - Create usage examples
   - Deploy to staging environment

**Dependencies**:
- Base agent framework must be stable
- Message broker integration ready
- Test infrastructure available
- Documentation system configured

**Risk Assessment**:
- **Technical Risk**: Medium - New agent patterns may require framework changes
- **Integration Risk**: Low - Uses established interfaces
- **Performance Risk**: Medium - May impact response times under load
- **Testing Risk**: Low - Standard testing patterns apply

**Testing Strategy**:
- Unit tests for core agent functionality
- Integration tests for message handling
- Performance tests for response times
- End-to-end tests for complete workflows
"""
        ))

        # Rollout & Migration
        spec.sections.append(SpecificationSection(
            title="Rollout & Migration",
            content="""**Deployment Plan**:
- Deploy to staging environment for validation
- Gradual rollout to production with monitoring
- Feature flags for controlled activation
- Rollback plan ready for immediate execution

**Migration Strategy**:
- No data migration required for new agent
- Existing agents unaffected by new implementation
- Backward compatibility maintained

**Rollback Plan**:
- Immediate rollback capability via feature flags
- Database backups ensure data safety
- Monitoring alerts trigger automatic rollback if needed

**Documentation Updates**:
- Update agent registry documentation
- Add usage examples to developer guide
- Update API reference with new agent capabilities
"""
        ))

        return spec

    def generate_orchestration_spec(self, feature_name: str, description: str) -> Specification:
        """Generate specification for orchestration features."""
        spec = Specification(
            title=f"Orchestration Feature Specification: {feature_name}",
            feature_name=feature_name,
            metadata={
                "Type": "Orchestration",
                "Created": datetime.now().isoformat(),
                "Status": "Draft"
            }
        )

        # Executive Summary
        spec.sections.append(SpecificationSection(
            title="Executive Summary",
            content=f"""**Feature Overview**: {feature_name} enhances the orchestration capabilities of the autoresearch platform.

**Purpose**: {description}

**Business Value**:
- Improves task coordination and execution efficiency
- Enhances system reliability and error recovery
- Provides better visibility into system operations
- Enables more complex workflow automation

**Success Metrics**:
- Task completion rate > 95%
- Error recovery success rate > 90%
- System throughput increase > 20%
- Mean time to resolution < 5 minutes

**Scope**:
- Includes: Task scheduling, execution coordination, error recovery
- Excludes: Agent-specific logic, user interface components
"""
        ))

        # Technical Design
        spec.sections.append(SpecificationSection(
            title="Technical Design",
            content="""**Architecture Impact**:
- Extends existing orchestration framework in `src/autoresearch/orchestration/`
- Integrates with current task graph and state management systems
- Maintains compatibility with existing agent interfaces

**Component Design**:
- New orchestration components follow established patterns
- Implements proper error handling and recovery mechanisms
- Provides comprehensive monitoring and logging
- Supports both synchronous and asynchronous operations

**API Design**:
```python
class {feature_name}(OrchestratorComponent):
    \"\"\"{feature_name} orchestration component.\"\"\"

    async def execute_task(self, task: OrchestrationTask) -> TaskResult:
        \"\"\"Execute orchestration task with proper coordination.\"\"\"
        pass

    async def handle_error(self, error: Exception, task: OrchestrationTask) -> ErrorResult:
        \"\"\"Handle errors with appropriate recovery strategies.\"\"\"
        pass
```

**Integration Points**:
- Task graph for dependency management
- State management for distributed coordination
- Circuit breaker for failure prevention
- Monitoring system for observability
""",
            subsections=[
                SpecificationSection(
                    title="Task Coordination",
                    content="""**Task Types**:
- Sequential tasks requiring ordered execution
- Parallel tasks for concurrent processing
- Conditional tasks with decision-based execution
- Retry tasks with error recovery logic

**Dependency Management**:
- Hard dependencies that block execution
- Soft dependencies that don't prevent progress
- Resource dependencies for capacity management
- Data dependencies for information flow
"""
                ),
                SpecificationSection(
                    title="Error Recovery",
                    content="""**Recovery Strategies**:
- Automatic retry with exponential backoff
- Circuit breaker pattern for repeated failures
- Alternative execution paths for critical tasks
- Manual intervention escalation when needed

**State Management**:
- Consistent state across distributed components
- Transaction-like behavior for complex operations
- Rollback capabilities for failed operations
- State validation and integrity checks
"""
                )
            ]
        ))

        # Implementation Plan
        spec.sections.append(SpecificationSection(
            title="Implementation Plan",
            content=f"""**Development Tasks**:

1. **Core Implementation** (Week 1)
   - Design and implement {feature_name} component
   - Integrate with existing orchestration framework
   - Add basic error handling and recovery

2. **Advanced Features** (Week 2)
   - Implement sophisticated coordination algorithms
   - Add comprehensive monitoring and metrics
   - Develop testing infrastructure

3. **Integration & Validation** (Week 3)
   - Connect with existing task management systems
   - Implement end-to-end testing scenarios
   - Performance optimization and tuning

4. **Documentation & Deployment** (Week 4)
   - Complete technical documentation
   - Create operational runbooks
   - Deploy to production environment

**Dependencies**:
- Orchestration framework must be stable
- Task graph implementation ready
- State management system operational
- Monitoring infrastructure available

**Risk Assessment**:
- **Technical Risk**: Medium - Complex coordination logic may require multiple iterations
- **Integration Risk**: Medium - Must integrate with multiple existing systems
- **Performance Risk**: High - May impact overall system performance
- **Scalability Risk**: Medium - Must handle varying load patterns

**Testing Strategy**:
- Unit tests for individual coordination algorithms
- Integration tests for component interactions
- Load tests for performance validation
- Failure scenario tests for error recovery
"""
        ))

        return spec

    def generate_search_spec(self, feature_name: str, description: str) -> Specification:
        """Generate specification for search enhancements."""
        spec = Specification(
            title=f"Search Feature Specification: {feature_name}",
            feature_name=feature_name,
            metadata={
                "Type": "Search",
                "Created": datetime.now().isoformat(),
                "Status": "Draft"
            }
        )

        # Executive Summary
        spec.sections.append(SpecificationSection(
            title="Executive Summary",
            content=f"""**Feature Overview**: {feature_name} enhances search capabilities in the autoresearch platform.

**Purpose**: {description}

**Business Value**:
- Improves information discovery and retrieval
- Enhances user experience with faster, more accurate results
- Increases platform utility and user satisfaction
- Enables more sophisticated research workflows

**Success Metrics**:
- Query response time < 200ms
- Result relevance score > 0.8
- Search accuracy > 95%
- User satisfaction > 4.5/5

**Scope**:
- Includes: Query processing, result ranking, caching strategies
- Excludes: UI components, external data source integration
"""
        ))

        return spec

    def generate_storage_spec(self, feature_name: str, description: str) -> Specification:
        """Generate specification for storage features."""
        spec = Specification(
            title=f"Storage Feature Specification: {feature_name}",
            feature_name=feature_name,
            metadata={
                "Type": "Storage",
                "Created": datetime.now().isoformat(),
                "Status": "Draft"
            }
        )

        # Executive Summary
        spec.sections.append(SpecificationSection(
            title="Executive Summary",
            content=f"""**Feature Overview**: {feature_name} enhances data storage capabilities in the autoresearch platform.

**Purpose**: {description}

**Business Value**:
- Improves data reliability and availability
- Enhances system performance and scalability
- Provides better data management and backup capabilities
- Enables more sophisticated data processing workflows

**Success Metrics**:
- Data consistency > 99.9%
- Backup success rate > 99%
- Query performance improvement > 30%
- Storage cost optimization > 20%

**Scope**:
- Includes: Data persistence, caching, backup strategies
- Excludes: External storage systems, UI components
"""
        ))

        return spec

    def save_specification(self, spec: Specification) -> Path:
        """Save specification to file."""
        # Create filename from feature name
        filename = f"{spec.feature_name.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}.md"
        filepath = self.specs_dir / filename

        # Write specification to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(spec.to_markdown())

        print(f"✅ Specification saved to: {filepath}")
        return filepath

    def interactive_spec_creation(self) -> Specification:
        """Create specification through interactive prompts."""
        print("🔧 Interactive Specification Generator")
        print("=" * 50)

        # Get basic information
        feature_name = input("Feature name: ").strip()
        if not feature_name:
            print("❌ Feature name is required")
            return None

        feature_type = input("Feature type (agent/orchestration/search/storage): ").strip().lower()
        if feature_type not in ['agent', 'orchestration', 'search', 'storage']:
            print("❌ Invalid feature type. Choose: agent, orchestration, search, or storage")
            return None

        description = input("Feature description: ").strip()
        if not description:
            print("❌ Feature description is required")
            return None

        # Generate specification based on type
        if feature_type == 'agent':
            agent_type = input("Agent type (specialized/dialectical): ").strip().lower()
            if agent_type not in ['specialized', 'dialectical']:
                print("❌ Invalid agent type. Choose: specialized or dialectical")
                return None
            spec = self.generate_agent_spec(feature_name, agent_type, description)
        elif feature_type == 'orchestration':
            spec = self.generate_orchestration_spec(feature_name, description)
        elif feature_type == 'search':
            spec = self.generate_search_spec(feature_name, description)
        elif feature_type == 'storage':
            spec = self.generate_storage_spec(feature_name, description)

        # Save specification
        filepath = self.save_specification(spec)

        # Show next steps
        print("
📋 Next Steps:"        print(f"1. Review and edit: {filepath}")
        print("2. Share with team for feedback"        print("3. Update specification based on review"        print("4. Use specification to guide implementation"
        return spec


def main():
    """Main entry point for specification generation."""
    parser = argparse.ArgumentParser(description="Generate specifications for autoresearch features")
    parser.add_argument(
        "--type",
        choices=["agent", "orchestration", "search", "storage"],
        help="Type of feature specification to generate"
    )
    parser.add_argument(
        "--name",
        help="Name of the feature"
    )
    parser.add_argument(
        "--description",
        help="Description of the feature"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use interactive mode for specification creation"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)"
    )

    args = parser.parse_args()

    generator = SpecGenerator(Path(args.project_root))

    if args.interactive:
        spec = generator.interactive_spec_creation()
    elif args.type and args.name and args.description:
        # Generate specification from arguments
        if args.type == 'agent':
            agent_type = input("Agent type (specialized/dialectical): ").strip().lower()
            if agent_type not in ['specialized', 'dialectical']:
                print("❌ Invalid agent type. Choose: specialized or dialectical")
                sys.exit(1)
            spec = generator.generate_agent_spec(args.name, agent_type, args.description)
        elif args.type == 'orchestration':
            spec = generator.generate_orchestration_spec(args.name, args.description)
        elif args.type == 'search':
            spec = generator.generate_search_spec(args.name, args.description)
        elif args.type == 'storage':
            spec = generator.generate_storage_spec(args.name, args.description)

        filepath = generator.save_specification(spec)
        print(f"✅ Specification generated: {filepath}")
    else:
        parser.print_help()
        print("\n❌ Missing required arguments. Use --interactive for guided creation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
