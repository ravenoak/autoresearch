

# **The Agentic SDLC: An Architectural Framework for Systemic Workflow Automation in Cursor IDE**

## **Part I: A Systems-Thinking Framework for AI-Augmented Software Development**

The advent of AI-powered code editors marks a significant inflection point in the practice of software engineering. The prevailing metaphor for these tools is that of a "copilot" or an advanced "pair programmer"—an assistant that augments the individual developer's capabilities through sophisticated code completion and chat-based assistance.1 While this perspective accurately describes the tactical benefits, it fails to capture the profound strategic transformation that is now possible. To fully harness the potential of tools like Cursor IDE, a paradigm shift is required: from viewing AI as a mere assistant to understanding the developer, the AI, the codebase, and the IDE as components of a single, integrated, and programmable cybernetic system.

This report presents an architectural framework for achieving this systemic automation. It moves beyond tactical enhancements to outline a strategy for re-engineering the entire Software Development Life Cycle (SDLC) into an intelligent, self-correcting, and highly automated process. By applying principles of systems thinking, dialectical reasoning, and holistic analysis, this document provides not just a guide to features, but a catalogue of architectural patterns for building a truly agentic SDLC.

### **Beyond the "AI Copilot": Towards a Systemic View of Development**

The traditional view of the SDLC is a linear sequence of human-centric phases: planning, implementation, testing, deployment, and maintenance. AI assistants are typically slotted into these phases to accelerate specific tasks. A systems-thinking approach, however, reframes this model. It sees the development process as a complex, dynamic system characterized by interconnectedness, feedback loops, and emergent properties. The objective is not merely to make a single developer type code faster, but to optimize the health, velocity, predictability, and quality of the entire development system.

Cursor IDE, with its deep integration of AI that understands the entire codebase, can execute multi-file edits, and interact with the developer's environment, provides the necessary substrate for this systemic view.3 Its capabilities extend far beyond simple autocompletion, enabling it to function as an active agent within the development ecosystem.5 In this model, the codebase is not a static artifact being manipulated, but a dynamic state space. The AI agent, guided by the developer-architect, navigates this space, making changes that are continuously validated by feedback loops (e.g., automated tests, linting rules). The emergent property of this system is a development process that is more resilient, consistent, and capable of handling complexity at a scale beyond that of unassisted human cognition.

### **The Dialectical Engine of Automation: Thesis, Antithesis, Synthesis**

To construct a robust framework for automating this system, it is useful to employ a dialectical model of reasoning. This approach deconstructs the automation capabilities of Cursor IDE into two opposing but complementary forces, the resolution of which produces a higher-order synthesis: the intelligent workflow.

* Thesis (The Static Order): Rules  
  The Rules within Cursor IDE represent the thesis of the development system. They are the declarative, static, and persistent set of constraints, principles, and knowledge that define the project's "laws of physics." These rules codify the project's architecture, its coding standards, domain-specific logic, and security protocols.7 They are the system's constitution, establishing the boundaries of acceptable behavior and the definition of "correctness" for any code that exists within the project. They are the passive, foundational order against which all change is measured.  
* Antithesis (The Dynamic Action): Commands and Modes  
  The Commands and Modes represent the antithesis. They are the imperative, dynamic, and transient actions that introduce change and execute procedures within the system. They are the "verbs" of the development process. A Command is a predefined, reusable instruction to perform a specific task, such as writing a test or reviewing code.9 A Mode is a configured state or "persona" for the AI agent, equipping it with specific tools and behaviors to tackle a class of problems, such as debugging or refactoring.10 These primitives are the active, change-inducing forces that challenge the static order.  
* Synthesis (The Intelligent Workflow)  
  True, systemic automation—the synthesis—emerges from the dynamic interplay of these two forces. An action taken in isolation is incomplete. A Socratic inquiry illuminates this: Is a command to /write-tests truly useful if the AI does not know what constitutes a "good test" within the context of this specific project? The answer is no. The command is only effective when it executes within the constraints and guidance provided by the project's testing Rules. The synthesis is therefore an intelligent workflow: a dynamic action (Command or Mode) that is guided and constrained by the static order (Rules) to produce an outcome that is not only functionally correct but also architecturally compliant, stylistically consistent, and aligned with the project's established best practices.

### **The Developer as System Architect, Not Just Operator**

This systemic, dialectical framework precipitates a fundamental evolution in the role of the software developer. The developer is no longer merely an operator who uses an AI tool to write code. Instead, they become the architect of the human-AI development system itself. Their primary responsibility shifts from the direct, line-by-line production of code to the strategic encoding of their own expertise and the project's collective knowledge into the system's primitives: its Rules, Commands, and Modes.

This shift gives rise to a powerful, project-level, in-context training loop. Experienced users of Cursor IDE do not treat the AI as a static, infallible oracle. Instead, they engage in a continuous process of refinement.12 When the AI produces a suboptimal or incorrect output—for instance, by using a deprecated pattern or ignoring a project-specific convention—the novice user might simply correct the code manually. The system architect, however, asks a more profound question: "Why did the AI fail?" The root cause is almost invariably a lack of specific, project-level context.

The architect's response is not just to fix the immediate error, but to prevent its recurrence by codifying the missing knowledge. This correction is captured as a new or refined Rule. For example, if the AI consistently generates code with placeholder comments, a rule is added: "Never replace code with placeholders like // rest of the processing.... Always include complete code".14 A repetitive, multi-step correction process can be encapsulated into a Command.15 This act transforms a one-time, manual correction into a persistent, automated instruction. The developer is, in effect, performing a continuous, in-context fine-tuning of the AI's behavior at the project level. This creates a virtuous feedback loop where the system becomes progressively more intelligent, more aligned with the project's unique requirements, and more capable of autonomous operation.

## **Part II: Deconstructing Cursor's Automation Primitives: A Comparative Analysis**

A successful system architect must possess a deep understanding of their building materials. In Cursor IDE, the primary materials for constructing automated workflows are Rules, Commands, and Modes. While they all serve to guide the AI, they are fundamentally different primitives with distinct strategic purposes, structures, and limitations. A critical comparative analysis is essential for selecting the appropriate tool for each automation task.

### **Rules: The Declarative Foundation (The System's Constitution)**

Rules are the bedrock of systemic automation in Cursor. Their function is to provide persistent, reusable, system-level instructions and context to the AI agent for both chat and inline editing.8 They are the project's declarative "source of truth," ensuring that all AI-generated contributions adhere to a consistent set of standards.

Types and Structure:  
Cursor supports a hierarchical and flexible rule system, allowing for granular control over context provision:

* **Project Rules:** Stored in .cursor/rules as version-controlled .mdc files, these are the most powerful and flexible rule type. They are scoped to the specific codebase and can be organized in subdirectories.8 An .mdc file consists of two parts: YAML frontmatter for metadata and a Markdown body for the instructions. The metadata controls how the rule is applied, using properties like description, globs for file-path matching, and alwaysApply.16  
* **User Rules:** These are global, plain-text rules defined in the user's settings that apply across all projects. They are ideal for personal preferences, such as communication style ("Reply in a concise style") or universal coding habits.8  
* **Team Rules:** Available on Team and Enterprise plans, these are centrally managed, plain-text rules that are automatically applied to all team members. They are a powerful tool for enforcing organizational standards, though they lack the sophisticated glob-based scoping of Project Rules.8  
* **AGENTS.md:** As a simpler alternative to .mdc files, Cursor also supports a markdown file named AGENTS.md in the project root or subdirectories for defining agent instructions.8

Application Logic:  
The application of Project Rules is governed by their metadata, enabling precise context management:

* **Always:** Rules with alwaysApply: true are always included in the model's context for the project.16 These are best for foundational principles like architectural overviews or core technology stack definitions.  
* **Auto Attached:** These rules are only included when a file matching their globs pattern is part of the AI's active context. For example, a rule for React component structure can be made to apply only when a .tsx file is being discussed or edited.8  
* **Manual:** Rules without specific application metadata are only included when explicitly invoked by the user in chat with the @ruleName syntax.8 This is useful for on-demand context, like a boilerplate template.

Strategic Purpose:  
The strategic purpose of Rules is to encode the non-negotiable truths of a project. This includes architectural patterns (e.g., "Follow the repository pattern"), coding standards ("Use Conventional Commits"), security best practices ("Validate all inputs"), and domain-specific knowledge ("Always use our internal RPC pattern").7 By establishing this foundation, Rules ensure that AI-generated code is not merely functional but is also compliant, maintainable, and idiomatic to the project.  
Limitations:  
Rules are fundamentally passive. They provide context and constraints but cannot initiate actions or execute workflows. Their effectiveness is dependent on the AI's ability to interpret and follow them. Overly long, complex, or contradictory rules can confuse the AI and degrade performance.18

### **Commands: The Imperative Toolkit (Encapsulated Procedures)**

If Rules are the project's "nouns" (the established standards), Commands are its "verbs" (the standardized actions). Their function is to create reusable, prompt-based workflows that can be triggered with a simple / prefix in the chat input.9 They serve as standardized recipes for common, multi-step tasks.

Structure and Scope:  
Commands are elegantly simple in their construction. They are defined as plain Markdown files stored in a .cursor/commands/ directory. This simplicity belies their power, as they can be scoped at three distinct levels 9:

* **Project Commands:** Stored within a project's repository, they encapsulate workflows specific to that project.  
* **Global Commands:** Stored in the user's home directory (\~/.cursor/commands), they provide a personal toolkit of reusable prompts available in any project.  
* **Team Commands:** Created by administrators in the team dashboard, they are automatically distributed to all team members, ensuring organizational process standardization.

The invocation syntax, /command-name \[parameters\], allows for a powerful combination of static and dynamic context. The Markdown file provides the static, well-crafted prompt, while the user-provided parameters inject the dynamic, task-specific details at runtime.9

Strategic Purpose:  
The primary strategic value of Commands lies in standardization and efficiency. They capture procedural knowledge and best practices for repetitive tasks, ensuring that every team member performs them in a consistent, high-quality manner. Common use cases include generating standardized unit tests, performing a comprehensive code review against a checklist, creating a pull request with a templated description, or running a security audit based on predefined criteria.15  
Limitations:  
Commands are essentially sophisticated prompt wrappers. They are stateless and non-interactive beyond their initial invocation. Their power is entirely derived from the quality of the underlying prompt and the contextual awareness provided by any active Rules. A Command without supporting Rules may produce functionally correct but non-compliant code.

### **Modes: The Agentic Personas (Specialized Task Executors)**

Modes represent the most advanced and dynamic form of automation in Cursor. A Mode configures the AI Agent for a specific type of task by defining its capabilities, the tools it can use, and its core behavioral instructions.10 Activating a Mode is akin to assigning the AI a specialized "persona" or job title, such as "Debugger," "Refactor Engine," or "Planner."

Standard and Custom Modes:  
Cursor provides several built-in modes optimized for common scenarios:

* **Agent Mode:** The default, fully autonomous mode with all tools enabled, designed for complex, multi-file feature implementation and refactoring.10  
* **Ask Mode:** A read-only mode with only search tools enabled, perfect for codebase exploration and learning without the risk of unintended changes.10  
* **Plan Mode:** A strategic mode that first researches the codebase and generates a detailed implementation plan for user review before any code is written, ideal for complex or ambiguous tasks.10

The true power for systemic automation, however, lies in **Custom Modes**. Users can configure their own modes by specifying a name, a preferred AI model, a dedicated keybinding, a selection of allowed tools (e.g., ReadFile, Terminal, Web Search, Edit), and a set of custom instructions that define the mode's core behavior.10 A prime example is the creation of a dedicated "Edit" mode. By enabling only the Edit tool and providing the instruction "You are strictly an editing tool do not explain anything," users can create a highly efficient, non-conversational refactoring assistant that is superior to both the standard inline edit and the full chat for targeted modifications.11

Strategic Purpose:  
Modes are designed for complex, stateful, or interactive workflows that go beyond a single prompt-response cycle. They control the AI's fundamental behavior and capabilities, whereas Rules control its knowledge. Custom modes are the key to creating highly specialized AI agents for tasks like autonomous Test-Driven Development (TDD) loops, interactive debugging sessions, or large-scale, rule-driven code modernizations.  
Limitations:  
The Custom Modes feature is still in beta, and its effectiveness is heavily dependent on the underlying Large Language Model's ability to reliably use tools and follow complex instructions.10 Granting access to powerful tools like the Terminal without proper guardrails or in a poorly configured mode can lead to unintended and potentially destructive consequences.

### **Comparative Analysis of Cursor's Automation Primitives**

To effectively architect automated workflows, it is crucial to understand the distinct roles and characteristics of these three primitives. The following table provides a comparative summary to guide architectural decisions.

| Feature | Rules | Commands | Custom Modes |
| :---- | :---- | :---- | :---- |
| **Core Function** | Provide Context & Constraints | Encapsulate & Standardize Prompts | Configure Agent Behavior & Tools |
| **Nature** | Declarative (What is true) | Imperative (Do this now) | Behavioral (Act like this) |
| **Persistence** | Persistent (Always available) | Transient (Single invocation) | State-based (Active for a session) |
| **Invocation** | Automatic (Globs) or Manual (@) | User-initiated (/) | User-initiated (Mode selection, shortcut) |
| **Scope** | Project, User, Team | Project, Global, Team | User-defined (local to the IDE) |
| **Primary Use Case** | Enforce standards, encode knowledge | Standardize repetitive tasks | Specialize agent for complex workflows |
| **Key Configuration** | .mdc file with YAML metadata & globs | .md file with prompt content | UI with tool selection & instructions |

This comparative analysis clarifies the dialectical relationship: Rules establish the static, declarative foundation. Commands provide standardized, imperative entry points for action. Custom Modes define the dynamic, behavioral personas that execute complex, stateful tasks. The synthesis of these three primitives is the key to unlocking systemic, end-to-end automation of the SDLC.

## **Part III: The Dialectics of SDLC Automation: Synthesizing Intelligent Workflows**

Understanding the individual automation primitives is the necessary foundation. The transformative potential, however, is realized when these components are synthesized into intelligent workflows that span the entire Software Development Life Cycle. By applying the dialectical framework—combining the static **Thesis** of Rules with the dynamic **Antithesis** of Commands and Modes—we can construct powerful, emergent automations for each phase of development.

### **Phase: Requirements & Planning**

The initial phase of any project involves translating a high-level business goal into a concrete, actionable, and architecturally sound technical plan. A generic AI might produce a plausible but naive plan that violates a project's core architectural tenets. An intelligent workflow ensures the plan is compliant from its inception.

* **Workflow:** From High-Level Goal to Architecturally-Aware Action Plan.  
* **Synthesis:**  
  * **Thesis (Rules):** The system is grounded by a foundational architecture.mdc rule. This is an Always rule, ensuring it is perpetually in context. It defines the project's non-negotiables: the technology stack (e.g., "Next.js with TypeScript, Tailwind CSS, and Supabase"), core architectural patterns ("Use the repository pattern for data access," "Keep business logic in service layers"), and guiding principles ("All API endpoints must be idempotent and stateless").7  
  * **Antithesis (Mode):** The developer engages the AI using the built-in Plan Mode. This mode is specifically designed for complex tasks that require forethought.10 The developer provides a high-level prompt, such as: "Design and plan the implementation for a user profile management feature, including endpoints for creating, updating, and retrieving user data."  
  * **Outcome (Synthesis):** The AI, operating in Plan Mode, does not generate a generic plan. Its reasoning process is constrained and informed by the architecture.mdc rule. It will research the existing codebase to understand current patterns, ask clarifying questions to resolve ambiguities, and then produce a detailed implementation plan that explicitly adheres to the specified repository pattern, service layer structure, and API principles. The output is an ephemeral virtual file that can be reviewed, edited, and saved to the workspace, serving as a compliant blueprint for development.10

### **Phase: Implementation & Development**

This phase is where the bulk of code is written. The "TDD Autopilot" is a cornerstone pattern that transforms this phase from a manual, error-prone cycle into a highly autonomous, self-correcting loop, drawing inspiration from best practices shared by experienced users.25

* **Workflow:** The "TDD Autopilot" Loop.  
* **Synthesis:**  
  * **Thesis (Rules):** An Auto Attached rule named testing-philosophy.mdc is created with globs: \["\*\*/\*.test.ts", "\*\*/\*.spec.ts"\]. This rule defines the project's specific testing conventions: "All tests must follow the Arrange-Act-Assert pattern," "Use Jest for unit tests and Playwright for end-to-end tests," "Mock all external service dependencies using our standard mocking library found in @/lib/mocks," and "Prefer integration tests for API controllers to validate the full request/response cycle".7  
  * **Antithesis (Command & Mode):** The workflow proceeds in two steps:  
    1. The developer initiates the process with a Command: /write-tests for user profile creation endpoint. The command's underlying prompt instructs the AI to generate a comprehensive suite of failing tests (unit, integration) for the specified feature, strictly adhering to the conventions outlined in the now-active testing-philosophy.mdc rule.  
    2. Once the failing tests are generated and accepted, the developer switches to a custom Mode named "ImplementAndFix". This mode is configured with the Edit and Terminal tools enabled. Its custom instructions are critical: "Your objective is to make all tests in the currently open test file pass. Read the test file and the related source files. Implement the necessary code to satisfy the tests. After implementing, run the test command npm test. Analyze the output. If tests fail, debug and fix the code. Repeat this cycle of editing and testing until all tests pass successfully." Crucially, this mode has the "YOLO" (auto-run) setting enabled, which allows the AI to execute terminal commands without requiring user confirmation for each step.26  
  * **Outcome (Synthesis):** The result is a highly autonomous development loop. The AI first generates standard-compliant tests and then enters a self-contained, iterative cycle of coding, testing, and debugging. It writes the implementation, runs the tests, observes the failures, and refines the code until the success criteria—passing tests—are met. The developer's role shifts from writing the code to defining the success criteria (the tests) and overseeing the autonomous agent that fulfills them.

### **Phase: Code Review & Quality Assurance**

Ensuring code quality, security, and consistency is a critical but often time-consuming process. An intelligent workflow can automate the majority of this review process, acting as a tireless guardian of project standards.

* **Workflow:** The "PR Guardian" for Automated Review and Compliance.  
* **Synthesis:**  
  * **Thesis (Rules):** A suite of Auto Attached project rules forms the quality gate. These include code-style.mdc (enforcing formatting and linting rules), security-checklist.mdc ("Check for SQL injection vulnerabilities," "Ensure proper input validation"), api-design.mdc ("Endpoints must use snake\_case," "Error responses must follow RFC 7807 format"), and commit-message.mdc ("All commit messages must follow the Conventional Commits specification").7  
  * **Antithesis (Command):** Before committing, the developer uses a series of Commands to prepare their changes for review.  
    1. With changes staged in git, they run /review-diff. The command prompt instructs the AI to analyze the output of git diff \--staged (referenced via @git) and check for any violations of the project's active Rules. The AI provides a list of suggested improvements.  
    2. After addressing the feedback, they run /commit-message. This command's prompt asks the AI to generate a compliant Conventional Commit message based on the staged changes.  
  * **Outcome (Synthesis):** This workflow shifts quality assurance "left," embedding it directly into the developer's pre-commit process. The AI acts as an objective, consistent, and comprehensive first-pass code reviewer that has perfect memory of all project rules. This reduces the burden on human reviewers, allowing them to focus on higher-level logic and architectural concerns rather than style nits or common errors. This process can be further integrated with external tools like Cursor's Bugbot for automated PR reviews in GitHub.22

### **Phase: Documentation & Maintenance**

Technical debt often accumulates in the form of outdated or non-existent documentation. An automated workflow can ensure that documentation is generated as a natural byproduct of development, keeping it synchronized with the code.

* **Workflow:** The "Self-Documenting Code" Pipeline.  
* **Synthesis:**  
  * **Thesis (Rules):** A docs-style.mdc rule defines the standards for all project documentation. For example: "All public API endpoints must be documented using the OpenAPI 3.0 specification format," and "All public functions and classes must have JSDoc comments explaining their purpose, parameters, and return values".20  
  * **Antithesis (Command):** Upon completing a new feature, such as a set of API endpoints in a controller file, the developer selects the relevant code block and invokes the Command /generate-docs. The prompt for this command is simple but powerful: "Generate documentation for the selected code, strictly following the formats and standards defined in the docs-style.mdc rule."  
  * **Outcome (Synthesis):** The AI generates high-quality, standardized documentation directly from the source code. Because this process is trivial to execute, developers are more likely to keep documentation up-to-date. This reduces the long-term cost of maintenance and onboarding, directly combating technical debt.5

## **Part IV: The Architectural Catalogue of Automated SDLC Patterns**

This section presents a detailed, implementable catalogue of composable automation patterns. Each pattern is a self-contained architectural solution to a common problem in the SDLC, synthesized from the primitives and principles established in the preceding sections. These patterns are designed to be both practical starting points and customizable templates for organization-specific needs.

The following table provides a summary index of the patterns detailed in this catalogue, allowing for quick identification of relevant solutions based on development phase and objective.

| Pattern Name | SDLC Phase(s) | Objective | Core Primitives |
| :---- | :---- | :---- | :---- |
| Architecturally-Aware Scaffolding | Planning, Implementation | Generate boilerplate code for new features that adheres to project architecture. | Rules, Command |
| TDD Autopilot | Implementation, Testing | Autonomously implement features based on a test-first approach. | Rules, Command, Custom Mode, YOLO |
| Autonomous Debugging Loop | Maintenance, Testing | Systematically diagnose and propose fixes for bugs in an interactive loop. | Rules, Custom Mode |
| PR Guardian | Code Review, Quality Assurance | Automate pre-commit code reviews and ensure compliance with project standards. | Rules, Command |
| Legacy Code Modernization | Maintenance, Refactoring | Systematically refactor legacy code to modern standards and patterns. | Rules, Custom Mode |
| Self-Healing Code Loop | Testing, Maintenance | Autonomously detect, diagnose, and fix runtime errors or failing tests. | Rules, Custom Mode, YOLO |
| The Meta-Automation System Builder | All Phases | Use the AI to create and maintain the automation rules and commands for the project. | Rules, Command |
| The Living Documentation Generator | Planning, Documentation | Capture the AI-assisted development process and decisions as version-controlled design documents. | Rules, Command |
| The Spec-Driven Implementation Engine | Planning, Implementation | Ensure AI-generated code strictly follows a detailed, version-controlled specification. | Rules, Command, Plan Mode |
| The Behavior-Driven Development (BDD) Automator | Testing, Implementation | Automate the BDD cycle from feature file generation to implementation. | Rules, Command, Custom Mode |

### **Pattern 1: The "Architecturally-Aware Scaffolding" Engine**

* **Problem:** Creating new features, such as API endpoints, UI components, or services, involves writing a significant amount of boilerplate code. This manual process is repetitive, error-prone, and can lead to inconsistencies if developers deviate from established architectural patterns.  
* **Implementation:**  
  * **Rules:** A set of Always and Auto Attached rules are established to define the project's architectural DNA.  
    * 00-architecture.mdc (alwaysApply: true): Defines the high-level structure. Example: "This is a NestJS application using TypeORM. All features must be structured into modules, with distinct files for controllers, services, providers, and entities. Use dependency injection for all services." 7  
    * api-patterns.mdc (globs: \["\*\*/\*.controller.ts"\]): Defines API-specific conventions. Example: "All controller methods must be decorated with @ApiOkResponse, @ApiNotFoundResponse, and @ApiBadRequestResponse. DTOs must be used for all request bodies and validated with class-validator." 16  
    * component-structure.mdc (globs: \["\*\*/\*.tsx"\]): Defines frontend component structure. Example: "React components must be functional components. Use named exports. Separate logic from presentation using custom hooks. Style with Tailwind CSS." 7  
  * **Command:** A command, /scaffold-feature \<type\> \<name\>, is created in .cursor/commands/scaffold-feature.md.  
    * **Prompt:** "You are a scaffolding agent. Based on the user's request to create a new feature of type {{type}} named {{name}}, and strictly following all active project architectural rules, generate the complete file and directory structure. This includes creating all necessary files (e.g., {{name}}.module.ts, {{name}}.controller.ts, {{name}}.service.ts, {{name}}.entity.ts) with the correct boilerplate code, imports, and class/function definitions. Do not omit any details."  
* **Workflow:**  
  1. A developer needs to add a new "products" API. They type /scaffold-feature api products into the chat.  
  2. The AI agent receives the prompt, with the parameters filled in.  
  3. Crucially, the agent's context is automatically populated with the 00-architecture.mdc rule because it is Always applied.  
  4. The agent begins generating the files. As it creates products.controller.ts, the api-patterns.mdc rule is automatically attached due to the glob match.  
  5. The agent generates a complete, multi-file feature skeleton that is fully compliant with the project's established architecture, including correct module definitions, controller decorators, and service stubs, ready for the developer to implement the business logic.3

### **Pattern 2: The "TDD Autopilot" Workflow**

* **Problem:** The manual cycle of writing a failing test, writing the implementation code, running the test, and repeating is fundamental to Test-Driven Development but can be slow and interrupt a developer's flow.  
* **Implementation:**  
  * **Rules:**  
    * testing-philosophy.mdc (globs: \["\*\*/\*.test.ts"\]): Defines testing standards as detailed in Section 3.2. Example: "Use Arrange-Act-Assert. Mock dependencies using Jest's jest.mock()." 7  
  * **Commands:**  
    * /write-tests.md: "Generate a comprehensive set of failing tests for the following feature: {{feature\_description}}. Adhere strictly to the testing-philosophy.mdc rule."  
  * **Custom Mode:**  
    * **Name:** ImplementAndFix  
    * **Keybinding:** Cmd+Shift+I  
    * **Tools:** Edit, Terminal  
    * **Auto-run ("YOLO"):** Enabled, with npm test in the allow list.26  
    * **Instructions:** "Your goal is to make all tests pass. Read the failing tests. Implement the feature code to satisfy them. Run npm test to verify. If tests fail, analyze the output, debug the code, and fix it. Repeat this edit-and-test cycle autonomously until npm test succeeds."  
* **Workflow:**  
  1. Developer runs /write-tests create a function sum(a, b) that returns the sum of two numbers. The AI generates a sum.test.ts file with failing tests for positive numbers, negative numbers, and zero.  
  2. Developer opens sum.ts and sum.test.ts, then activates the ImplementAndFix mode.  
  3. They prompt: "Implement the sum function to pass the tests."  
  4. The AI agent writes the initial implementation in sum.ts.  
  5. It then autonomously executes npm test in the terminal.  
  6. It observes the test results. If any fail, it re-reads the test, analyzes the failure message, modifies the implementation in sum.ts, and re-runs the tests.  
  7. This loop continues without further user interaction until all tests pass, at which point the agent reports success.25

### **Pattern 3: The "Autonomous Debugging" Loop**

* **Problem:** Debugging is often a non-linear, intuitive process that is difficult to automate. It involves forming hypotheses, gathering evidence, and iteratively narrowing down the problem.  
* **Implementation:**  
  * **Rules:**  
    * debugging-playbook.mdc (Always or Manual): Defines a structured debugging methodology. Example: "When presented with a bug, follow this process strictly: 1\. **OBSERVE:** Analyze the error message and stack trace. State your initial observations. 2\. **HYPOTHESIZE:** Form a clear, testable hypothesis about the root cause. 3\. **EXPERIMENT:** Do not suggest a fix yet. Instead, identify the key code sections and propose adding specific logging statements (console.log) to gather evidence that will confirm or deny your hypothesis. 4\. **ANALYZE:** After the user provides the log output, analyze it and state whether your hypothesis was correct. 5\. **SOLVE:** Only now, propose a specific code change to fix the issue." 14  
  * **Custom Mode:**  
    * **Name:** Debugger  
    * **Tools:** Edit, ReadFile, Grep  
    * **Instructions:** "You are a debugging assistant. Follow the debugging-playbook.mdc rule precisely to help the user diagnose and solve the issue."  
* **Workflow:**  
  1. A developer encounters a bug and copies the error message.  
  2. They activate the Debugger mode and paste the error, optionally @-mentioning the relevant files.  
  3. The AI, following the playbook, responds: "**OBSERVATION:** The error TypeError: cannot read properties of undefined occurs on line 42 of userService.ts. **HYPOTHESIS:** The user object is likely undefined at this point because the database query on line 35 returned no result. **EXPERIMENT:** Please add console.log('User object from DB:', user) on line 36 and run the process again. Provide me with the output."  
  4. The developer adds the log, runs the code, and pastes the output: "User object from DB: null".  
  5. The AI responds: "**ANALYSIS:** The log confirms the hypothesis. The user object is null. **SOLUTION:** We should add a null check after the database query to handle cases where a user is not found." It then provides the exact code change to implement.6

### **Pattern 4: The "PR Guardian" for Code Review and Compliance**

* **Problem:** Manual code reviews are essential for quality but are a significant bottleneck. They are often inconsistent, and reviewers spend too much time on stylistic issues instead of architectural or logical flaws.  
* **Implementation:**  
  * **Rules:** A comprehensive suite of project rules.  
    * security.mdc (globs: \["\*\*/\*"\]): "Check for hardcoded secrets, potential XSS vectors in frontend code, and SQL injection risks in backend queries." 7  
    * performance.mdc (globs: \["\*\*/\*"\]): "Identify inefficient loops (N+1 queries), and suggest optimizations." 7  
    * commit-message.mdc (Always): "Commit messages must use Conventional Commits (feat:, fix:, chore:)." 7  
  * **Commands:**  
    * /review-diff.md: "You are a senior staff engineer performing a code review. Analyze the staged git changes (@git). Check for any violations of our project's security.mdc, performance.mdc, and any other relevant coding standards. Provide a concise, actionable list of required changes, referencing the specific file and line number for each point."  
    * /generate-pr-description.md: "Based on the staged changes, write a pull request description. Include a 'Summary' section explaining the purpose of the change and a 'Changes' section with a bulleted list of the key modifications." 20  
* **Workflow:**  
  1. A developer finishes their work and stages their changes using git add.  
  2. Before committing, they run /review-diff.  
  3. The AI provides a detailed review, e.g., "In userController.ts:56, there is a potential N+1 query. Consider using Promise.all or refactoring the data fetching logic. In Profile.tsx:23, user input is rendered directly, creating a potential XSS vulnerability. Please sanitize this input."  
  4. The developer addresses the feedback and stages the new changes.  
  5. They then run /generate-pr-description and /commit-message to create the final artifacts.  
  6. The resulting pull request is submitted with high confidence that it meets all project standards, allowing human reviewers to focus on the core logic.

### **Pattern 5: The "Legacy Code Modernization" Assistant**

* **Problem:** Large-scale refactoring of legacy code—such as migrating from JavaScript to TypeScript, converting class-based React components to functional hooks-based components, or updating to a new API version—is a tedious, high-effort, and error-prone undertaking.  
* **Implementation:**  
  * **Rules:**  
    * modernization-target.mdc (globs: \["\*\*/\*.js", "\*\*/\*.jsx"\]): This rule defines the precise target state for the refactored code. Example: "The goal of this modernization is to convert legacy JavaScript React code to modern TypeScript. All files must be converted to .tsx. All props must have explicit interface definitions. All class components must be refactored into functional components using React Hooks (useState, useEffect). All fetch calls must be replaced with our custom useApi hook from @/hooks/useApi." 7  
  * **Custom Mode:**  
    * **Name:** Modernize  
    * **Tools:** Edit, ReadFile  
    * **Instructions:** "You are a code modernization specialist. Your sole task is to refactor the provided code to meet the exact specifications outlined in the modernization-target.mdc rule. Apply the necessary changes directly and comprehensively across the entire file. Do not provide explanations or conversational filler. Focus on a complete and accurate transformation."  
* **Workflow:**  
  1. A developer identifies a legacy JavaScript file, e.g., UserProfile.js, that needs to be modernized.  
  2. They open the file and activate the Modernize mode.  
  3. Because the file has a .js extension, the modernization-target.mdc rule is automatically attached to the AI's context.  
  4. The developer gives a simple prompt: "Modernize this component."  
  5. The AI agent reads the entire file and the modernization rule. It then performs a large-scale, multi-part edit, simultaneously converting the file to TypeScript, rewriting the class component as a functional component, adding prop types, and replacing old data-fetching logic with the specified custom hook.  
  6. The developer receives a fully refactored file in a single operation, ready for review and testing, dramatically accelerating the modernization process.

### **Pattern 6: The "Self-Healing Code" Loop**

* **Problem:** Code that passes initial tests may still fail at runtime or during integration due to environmental differences, unexpected data, or subtle integration bugs. The manual cycle of running, observing a failure, and debugging is a major time sink.  
* **Implementation:**  
  * **Rules:**  
    * self-heal-protocol.mdc (Always): Defines the agent's core logic for this task. Example: "Your primary directive is to ensure the command npm run test:e2e exits with code 0\. If it fails, you must enter a self-healing loop. **Loop Protocol:** 1\. **Execute:** Run the command. 2\. **Observe:** Capture the complete terminal output, including any error messages and stack traces. 3\. **Diagnose:** Analyze the output to form a hypothesis for the root cause. 4\. **Act:** Propose and apply a specific code change to fix the issue. 5\. **Repeat:** Go back to step 1\. Do not exit the loop until the command succeeds." 27  
  * **Custom Mode:**  
    * **Name:** SelfHeal  
    * **Tools:** Terminal, Edit, ReadFile  
    * **Auto-run ("YOLO"):** Enabled, with the target test or build command (e.g., npm run test:e2e) in the allow list.26  
    * **Instructions:** "You are a self-healing agent. Your only goal is to make the user-specified command succeed. Follow the self-heal-protocol.mdc rule without deviation."  
* **Workflow:**  
  1. A developer has a suite of end-to-end tests that are failing in the CI/CD pipeline.  
  2. They activate the SelfHeal mode and provide the initial prompt: "Fix the test suite by running npm run test:e2e until it passes."  
  3. The AI agent autonomously executes npm run test:e2e in the terminal.28  
  4. It observes the failure output, reads the relevant source files, and based on the self-heal-protocol, implements a code change to fix the first error.  
  5. It automatically re-runs the test command. This loop continues—executing, observing, and fixing—until the entire test suite passes, at which point the agent reports success. This pattern creates a feedback loop where the AI uses the application's own output to correct itself.29

### **Pattern 7: The "Meta-Automation" System Builder**

* **Problem:** Creating and maintaining a high-quality, comprehensive set of project Rules and Commands requires significant effort and expertise. This upfront cost can be a barrier to adopting a fully agentic workflow.  
* **Implementation:**  
  * **Rules:**  
    * meta-rule-creation.mdc (globs: \["\*\*/\*.mdc"\], alwaysApply: true): A "rule for writing rules." This meta-rule defines the required structure and best practices for all other .mdc files in the project. Example: "All rule files must contain YAML frontmatter with a description and appropriate globs. The rule content must be organized with Markdown headings, provide clear explanations, and include concrete code examples. Rules should be focused and under 500 lines." 18  
  * **Command:**  
    * /create-rule.md: "You are a project architect responsible for creating automation rules. Your task is to generate a new .mdc rule file based on the user's request: {{request}}. You must strictly follow the structure and guidelines defined in the meta-rule-creation.mdc rule. Ask clarifying questions to gather all necessary details before generating the final file."  
* **Workflow:**  
  1. A developer decides the project needs a standardized way to handle API error responses.  
  2. They run the command: /create-rule for API error handling using RFC 7807 format.  
  3. The AI, guided by the /create-rule prompt, engages in a dialogue: "Understood. To create this rule, I need a few details. Which file paths should this rule apply to (for the globs)? Can you provide a small code example of the desired error format?"  
  4. After gathering the information, the AI generates a new, perfectly formatted file named api-error-handling.mdc in the .cursor/rules/ directory, complete with the correct YAML metadata and content. This pattern uses the AI to bootstrap and expand its own operational knowledge base.13

### **Pattern 8: The "Living Documentation" Generator**

* **Problem:** The critical context and decision-making process behind architectural choices or complex features are often lost over time. Chat histories are ephemeral, and manual documentation quickly becomes outdated.  
* **Implementation:**  
  * **Rules:**  
    * design-doc-template.mdc (Manual): A rule that defines the structure for a project's design documents. Example: "All design documents must include the following sections: \#\# 1\. Goal, \#\# 2\. Background, \#\# 3\. Alternatives Considered, \#\# 4\. Final Decision & Rationale, \#\# 5\. Implementation Plan."  
  * **Command:**  
    * /save-discussion.md: "Summarize the key decisions, trade-offs, and final plan from the current chat history. Structure this summary as a formal design document, strictly following the template provided in the @design-doc-template rule. Save the output to a new file in the docs/design/ directory with a descriptive name."  
* **Workflow:**  
  1. A developer and the AI have a long, iterative conversation to design a new caching layer for the application, discussing options like Redis vs. in-memory caches and different eviction policies.  
  2. Once a final plan is agreed upon, the developer runs the command: /save-discussion caching-layer-design.  
  3. The AI processes its own chat history, extracts the salient points, and generates a structured Markdown document (e.g., docs/design/caching-layer-design.md) that captures the entire thought process.  
  4. This document is then committed to the repository, creating a permanent, version-controlled record of the architectural decision. This "living documentation" can be referenced in future AI prompts (@docs/design/caching-layer-design.md) to provide deep context for subsequent tasks.25

### **Pattern 9: The "Spec-Driven Implementation" Engine**

* **Problem:** Unstructured, "vibe-based" AI development often leads to inconsistent results, context window overload, and implementations that drift from the original requirements. A more rigorous approach is needed to ensure the AI builds exactly what was intended.34  
* **Implementation:**  
  * **Rules:**  
    * spec-guidelines.mdc (Manual): A rule defining the structure of a high-quality specification document. Example: "All specs must be Markdown files containing: 1\. A high-level goal. 2\. A set of user stories with clear acceptance criteria. 3\. A technical design section outlining proposed architecture, data models, and API contracts. 4\. A list of non-goals and out-of-scope items.".37  
  * **Commands:** A suite of commands to manage the Spec-Driven Development (SDD) lifecycle.  
    * /specify \<feature\_idea\>: "You are a product manager. Based on the user's idea {{feature\_idea}}, generate a comprehensive specification document. Follow the @spec-guidelines rule to structure the output into a new file named specs/{{feature\_idea}}.md.".38  
    * /plan-from-spec: "You are a technical architect. Read the provided specification file (@specs/...). Generate a detailed, step-by-step implementation plan in a new plans/{{feature\_name}}.md file. The plan should list all files to be created or modified and the specific changes required for each.".39  
  * **Plan Mode:** Cursor's built-in Plan Mode is a natural fit for the planning phase of this workflow, as it is designed to generate a plan before executing code changes.39  
* **Workflow:**  
  1. A developer initiates the process with an idea: /specify user-authentication.  
  2. The AI generates a detailed specs/user-authentication.md file. The developer reviews and refines this document, treating it as the single source of truth.40  
  3. Next, the developer runs /plan-from-spec and provides the spec file as context: @specs/user-authentication.md.  
  4. The AI generates a detailed technical plan. The developer reviews this plan for architectural soundness.  
  5. Finally, the developer uses the approved plan to guide the AI in Agent Mode: "Implement the feature described in @plans/user-authentication.md." The AI now has a clear, unambiguous blueprint to follow, dramatically improving the quality and consistency of the final code.34

### **Pattern 10: The "Behavior-Driven Development (BDD)" Automator**

* **Problem:** Behavior-Driven Development (BDD) is excellent for aligning technical implementation with business requirements, but the manual process of writing Gherkin feature files, creating corresponding step definitions, and then implementing the feature can be slow.42  
* **Implementation:**  
  * **Rules:**  
    * gherkin-style.mdc (globs: \["\*\*/\*.feature"\]): Defines best practices for writing BDD scenarios. Example: "All scenarios must follow the Given-When-Then structure. Use a declarative style; describe *what* the user does, not *how* they do it (e.g., 'Given the user is on the login page,' not 'Given the user navigates to /login'). Each scenario should test a single behavior.".42  
  * **Commands:**  
    * /generate-feature-file \<description\>: "Based on the feature description {{description}}, generate a BDD feature file using Gherkin syntax. Adhere to the standards in @gherkin-style." This command is particularly effective when given API documentation as context.45  
    * /generate-step-definitions: "Read the open \*.feature file and generate the boilerplate for all step definitions in the corresponding test file. Leave the function bodies empty.".45  
  * **Custom Mode:**  
    * **Name:** BDDImplementer (can be the same as the ImplementAndFix mode).  
    * **Tools:** Edit, Terminal, ReadFile.  
    * **Auto-run ("YOLO"):** Enabled, with the BDD test command (e.g., npm run test:cucumber) in the allow list.  
    * **Instructions:** "Your goal is to make all scenarios in the open .feature file pass. Read the feature file and the step definitions. Implement the necessary application code to satisfy the scenarios. Run npm run test:cucumber to verify. If tests fail, analyze the output, debug the code, and fix it. Repeat this cycle until all tests pass.".47  
* **Workflow:**  
  1. A developer runs /generate-feature-file "user login with valid credentials". The AI creates login.feature.  
  2. With the feature file open, the developer runs /generate-step-definitions. The AI creates the necessary function stubs in login.steps.ts.  
  3. The developer activates the BDDImplementer mode and prompts: "Implement the login feature to pass these scenarios."  
  4. The AI enters an autonomous loop: it writes the implementation code, runs the Cucumber tests, observes the failures, and refines the code until all scenarios pass, ensuring the final code perfectly matches the specified behavior.47

## **Part V: Strategic Implementation and Organizational Adoption**

The architectural patterns detailed in this report provide a blueprint for a highly automated SDLC. However, technology alone is insufficient. Successful adoption requires a deliberate strategy that addresses organizational structure, governance, and culture. The transition from using AI as a tactical tool to leveraging it as a systemic automation engine is a journey that must be managed.

### **The Maturity Model: From Individual Enhancement to Systemic Automation**

A phased approach to adoption is recommended to manage the learning curve and build institutional competency. This maturity model provides a roadmap for organizations to follow.

* **Level 1: Individual Productivity.** At this initial stage, developers use Cursor's base features like Chat (Cmd/Ctrl \+ L), Inline Edit (Cmd/Ctrl \+ K), and advanced autocompletion. The focus is on augmenting individual developer tasks. Success is measured in terms of individual time savings and reduced friction in coding.  
* **Level 2: Procedural Standardization.** Teams begin to identify and encapsulate common, repetitive workflows. They adopt shared Commands for tasks like generating tests or reviewing code. The focus shifts from individual efficiency to team-level consistency. Success is measured by the reduction in process variance and the adoption of standardized best practices.  
* **Level 3: Declarative Governance.** The organization makes a strategic investment in codifying its knowledge. Teams collaboratively develop and maintain a comprehensive set of project Rules that define architectural patterns, coding standards, and security requirements. The focus moves to proactive quality and compliance. Success is measured by a reduction in PR rework, fewer bugs related to non-compliance, and faster onboarding of new developers who are guided by the rules.  
* **Level 4: Systemic Automation.** The organization reaches the highest level of maturity by synthesizing all primitives. It combines Rules, Commands, and Custom Modes to build the end-to-end automated workflows described in the architectural catalogue. The focus is on optimizing the entire development system's velocity and reliability. Success is measured by metrics like cycle time, deployment frequency, and change failure rate.

### **Governance and Best Practices**

As the organization matures, formal governance becomes essential to manage the complexity and ensure the integrity of the automated system.

* **Treating "AI Code" as Code:** The artifacts that configure the AI—Rules (.mdc files) and Commands (.md files)—are critical project assets. They must be treated with the same rigor as application source code. This means they should be stored in version control, subject to code review through pull requests, and have clear ownership and maintenance processes.20 Changes to a core architectural rule should be debated and approved with the same seriousness as a change to the database schema.  
* **The "Rule Gardener" Role:** To prevent rule sets from becoming bloated, contradictory, or outdated, it is advisable to appoint senior engineers or architects to the role of "Rule Gardener." Their responsibility is to curate, refactor, and maintain the project's rule set, ensuring it remains a coherent and effective guide for the AI.  
* **Cost and Model Management:** The choice of AI model has significant implications for both capability and cost. More powerful models like GPT-5 or Claude Opus are more expensive per token but may be more effective at complex reasoning and tool use, making them suitable for Custom Modes like the "TDD Autopilot".31 Less expensive models like Claude Sonnet or Groq may be sufficient for simpler Commands. Organizations should leverage Cursor's "Auto" mode, which dynamically selects the best model for a given task, to balance performance and cost, and should monitor usage through the editor's built-in dashboards.12

### **The Human in the Loop: Fostering a Culture of Critical Collaboration**

This framework does not seek to replace the developer but to elevate their role and amplify their expertise. The most critical skills in an agentic SDLC are not the ability to write boilerplate code but the ability to think strategically, decompose complex problems, and critically guide an AI partner.

* **Training and Mindset Shift:** Organizations must invest in training developers to transition from being code operators to system architects. This involves teaching them how to:  
  * **Decompose Problems:** Break down large, ambiguous features into small, well-defined tasks that are suitable for AI execution, a skill identified as critical by experienced users.25  
  * **Author Effective Rules and Commands:** Write clear, specific, and unambiguous instructions for the AI, providing concrete examples and context.  
  * **Critically Review AI Output:** Maintain a healthy skepticism and rigorously review all AI-generated code, especially in security-sensitive areas like authentication and payment processing.14 The developer's role as the final arbiter of quality and correctness becomes more important than ever.

In conclusion, the Agentic SDLC represents a new frontier in software engineering. It moves beyond the simple augmentation of individual tasks to the systemic automation of the entire development process. By architecting a collaborative system where human expertise is encoded into Rules, standardized procedures are encapsulated in Commands, and specialized AI agents are configured with Modes, organizations can achieve a step-change in productivity, quality, and velocity. The future of developer productivity will be measured not by the lines of code an individual writes, but by the intelligence, efficiency, and resilience of the development system they architect.

#### **Works cited**

1. Cursor Features Every Developer Should Know About \- Sidetool, accessed October 21, 2025, [https://www.sidetool.co/post/cursor-features-every-developer-should-know-about/](https://www.sidetool.co/post/cursor-features-every-developer-should-know-about/)  
2. Cursor AI: The AI-powered code editor changing the game \- Daily.dev, accessed October 21, 2025, [https://daily.dev/blog/cursor-ai-everything-you-should-know-about-the-new-ai-code-editor-in-one-place](https://daily.dev/blog/cursor-ai-everything-you-should-know-about-the-new-ai-code-editor-in-one-place)  
3. Guide to Cursor | Software.com, accessed October 21, 2025, [https://www.software.com/ai-index/tools/cursor](https://www.software.com/ai-index/tools/cursor)  
4. Cursor: Geniusee analysis of the tool \- pros & cons, accessed October 21, 2025, [https://geniusee.com/single-blog/cursor-ai](https://geniusee.com/single-blog/cursor-ai)  
5. Software Development with AI Tools: A Practical Look at Cursor IDE \- ELEKS, accessed October 21, 2025, [https://eleks.com/research/cursor-ide/](https://eleks.com/research/cursor-ide/)  
6. Cursor AI: An In Depth Review in 2025 \- Engine Labs Blog, accessed October 21, 2025, [https://blog.enginelabs.ai/cursor-ai-an-in-depth-review](https://blog.enginelabs.ai/cursor-ai-an-in-depth-review)  
7. Top Cursor Rules for Coding Agents \- PromptHub, accessed October 21, 2025, [https://www.prompthub.us/blog/top-cursor-rules-for-coding-agents](https://www.prompthub.us/blog/top-cursor-rules-for-coding-agents)  
8. Rules | Cursor Docs, accessed October 21, 2025, [https://cursor.com/docs/context/rules](https://cursor.com/docs/context/rules)  
9. Commands | Cursor Docs, accessed October 21, 2025, [https://cursor.com/docs/agent/chat/commands](https://cursor.com/docs/agent/chat/commands)  
10. Modes | Cursor Docs, accessed October 21, 2025, [https://cursor.com/docs/agent/modes](https://cursor.com/docs/agent/modes)  
11. Build a Better Edit Tool in Cursor with Custom Agent Modes ..., accessed October 21, 2025, [https://egghead.io/build-a-better-edit-tool-in-cursor-with-custom-agent-modes\~21rr0](https://egghead.io/build-a-better-edit-tool-in-cursor-with-custom-agent-modes~21rr0)  
12. 10 Tips for Writing Playwright Tests with Cursor \- Filip Hric, accessed October 21, 2025, [https://filiphric.com/cursor-playwright-tips](https://filiphric.com/cursor-playwright-tips)  
13. My Cursor AI Workflow That Actually Works \- Reddit, accessed October 21, 2025, [https://www.reddit.com/r/cursor/comments/1jd4s83/my\_cursor\_ai\_workflow\_that\_actually\_works/](https://www.reddit.com/r/cursor/comments/1jd4s83/my_cursor_ai_workflow_that_actually_works/)  
14. My Cursor AI Workflow That Actually Works in Production | N's Blog, accessed October 21, 2025, [https://nmn.gl/blog/cursor-guide](https://nmn.gl/blog/cursor-guide)  
15. Cursor commands are here \- Reddit, accessed October 21, 2025, [https://www.reddit.com/r/cursor/comments/1n89ms1/cursor\_commands\_are\_here/](https://www.reddit.com/r/cursor/comments/1n89ms1/cursor_commands_are_here/)  
16. Awesome Cursor Rules You Can Setup for Your Cursor AI IDE Now \- Apidog, accessed October 21, 2025, [https://apidog.com/blog/awesome-cursor-rules/](https://apidog.com/blog/awesome-cursor-rules/)  
17. digitalchild/cursor-best-practices: Best practices when ... \- GitHub, accessed October 21, 2025, [https://github.com/digitalchild/cursor-best-practices](https://github.com/digitalchild/cursor-best-practices)  
18. Setting Up Cursor Rules: The Complete Guide to AI-Enhanced Development \- DEV Community, accessed October 21, 2025, [https://dev.to/stamigos/setting-up-cursor-rules-the-complete-guide-to-ai-enhanced-development-24cg](https://dev.to/stamigos/setting-up-cursor-rules-the-complete-guide-to-ai-enhanced-development-24cg)  
19. 16 Cursor IDE AI Tips and Tricks \+ Commands cheat sheet \+ YOLO mode \- Medium, accessed October 21, 2025, [https://medium.com/ai-dev-tips/16-cursor-ide-ai-tips-and-tricks-commands-cheat-sheet-yolo-mode-e8fbd8c4deb4](https://medium.com/ai-dev-tips/16-cursor-ide-ai-tips-and-tricks-commands-cheat-sheet-yolo-mode-e8fbd8c4deb4)  
20. hamzafer/cursor-commands: Cursor Custom Slash ... \- GitHub, accessed October 21, 2025, [https://github.com/hamzafer/cursor-commands](https://github.com/hamzafer/cursor-commands)  
21. Coding with Cursor: a Beginner's Guide \- Sid Bharath, accessed October 21, 2025, [https://www.siddharthbharath.com/coding-with-cursor-beginners-guide/](https://www.siddharthbharath.com/coding-with-cursor-beginners-guide/)  
22. Blog · Cursor, accessed October 21, 2025, [https://cursor.com/blog](https://cursor.com/blog)  
23. Tools | Cursor Docs, accessed October 21, 2025, [https://cursor.com/docs/agent/tools](https://cursor.com/docs/agent/tools)  
24. PatrickJS/awesome-cursorrules: Configuration files that ... \- GitHub, accessed October 21, 2025, [https://github.com/PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)  
25. Cursor IDE: Setup and Workflow in Larger Projects : r/cursor \- Reddit, accessed October 21, 2025, [https://www.reddit.com/r/cursor/comments/1ikq9m6/cursor\_ide\_setup\_and\_workflow\_in\_larger\_projects/](https://www.reddit.com/r/cursor/comments/1ikq9m6/cursor_ide_setup_and_workflow_in_larger_projects/)  
26. How I use Cursor (+ my best tips) \- Builder.io, accessed October 21, 2025, [https://www.builder.io/blog/cursor-tips](https://www.builder.io/blog/cursor-tips)  
27. My Cursor AI Workflow That Actually Works : r/ChatGPTCoding \- Reddit, accessed October 21, 2025, [https://www.reddit.com/r/ChatGPTCoding/comments/1jiyzro/my\_cursor\_ai\_workflow\_that\_actually\_works/](https://www.reddit.com/r/ChatGPTCoding/comments/1jiyzro/my_cursor_ai_workflow_that_actually_works/)  
28. Ai Self Healing / From Within\! \- Discussions \- Cursor \- Community Forum, accessed October 21, 2025, [https://forum.cursor.com/t/ai-self-healing-from-within/117012](https://forum.cursor.com/t/ai-self-healing-from-within/117012)  
29. I Made Cursor \+ AI Write Perfect SQL. Here's the Exact Setup \- MotherDuck Blog, accessed October 21, 2025, [https://motherduck.com/blog/vibe-coding-sql-cursor/](https://motherduck.com/blog/vibe-coding-sql-cursor/)  
30. Writing Cursor Rules with a Cursor Rule \- Adithyan, accessed October 21, 2025, [https://www.adithyan.io/blog/writing-cursor-rules-with-a-cursor-rule](https://www.adithyan.io/blog/writing-cursor-rules-with-a-cursor-rule)  
31. Models | Cursor Docs, accessed October 21, 2025, [https://cursor.com/docs/models](https://cursor.com/docs/models)  
32. Cursor Deep Dive: Custom Agents, Planning Mode, and Live Debugging \- YouTube, accessed October 21, 2025, [https://www.youtube.com/watch?v=1sZkTeXxADs](https://www.youtube.com/watch?v=1sZkTeXxADs)  
33. Cursor \- Community Forum \- The official forum to discuss Cursor., accessed October 21, 2025, [https://forum.cursor.com/](https://forum.cursor.com/)  
34. Spec-Driven Development: The Next Step in AI-Assisted Engineering \- BEON.tech, accessed October 21, 2025, [https://beon.tech/blog/spec-driven-development-the-next-step-in-ai-assisted-engineering](https://beon.tech/blog/spec-driven-development-the-next-step-in-ai-assisted-engineering)  
35. Free-form AI coding vs spec-driven AI workflows : r/ExperiencedDevs \- Reddit, accessed October 21, 2025, [https://www.reddit.com/r/ExperiencedDevs/comments/1mugowu/freeform\_ai\_coding\_vs\_specdriven\_ai\_workflows/](https://www.reddit.com/r/ExperiencedDevs/comments/1mugowu/freeform_ai_coding_vs_specdriven_ai_workflows/)  
36. Spec-driven development is underhyped\! Here's how you build better with Cursor\! \- Reddit, accessed October 21, 2025, [https://www.reddit.com/r/cursor/comments/1nomd8t/specdriven\_development\_is\_underhyped\_heres\_how/](https://www.reddit.com/r/cursor/comments/1nomd8t/specdriven_development_is_underhyped_heres_how/)  
37. Mastering Spec-Driven Development with Prompted AI Workflows: A Step-by-Step Implementation Guide \- Augment Code, accessed October 21, 2025, [https://www.augmentcode.com/guides/mastering-spec-driven-development-with-prompted-ai-workflows-a-step-by-step-implementation-guide](https://www.augmentcode.com/guides/mastering-spec-driven-development-with-prompted-ai-workflows-a-step-by-step-implementation-guide)  
38. madebyaris/spec-kit-command-cursor: SDD toolkit for Cursor IDE \- GitHub, accessed October 21, 2025, [https://github.com/madebyaris/spec-kit-command-cursor](https://github.com/madebyaris/spec-kit-command-cursor)  
39. Spec-Driven Development: Designing Before You Code (Again) | by Dave Patten \- Medium, accessed October 21, 2025, [https://medium.com/@dave-patten/spec-driven-development-designing-before-you-code-again-21023ac91180](https://medium.com/@dave-patten/spec-driven-development-designing-before-you-code-again-21023ac91180)  
40. Spec-Driven Development & AI Agents Explained \- Augment Code, accessed October 21, 2025, [https://www.augmentcode.com/guides/spec-driven-development-ai-agents-explained](https://www.augmentcode.com/guides/spec-driven-development-ai-agents-explained)  
41. Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl \- Martin Fowler, accessed October 21, 2025, [https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)  
42. Behavior-Driven Development (BDD): Ultimate Guide & Benefits \- Testomat.io, accessed October 21, 2025, [https://testomat.io/blog/mastering-a-robust-bdd-development-workflow/](https://testomat.io/blog/mastering-a-robust-bdd-development-workflow/)  
43. Behaviour-Driven Development \- Cucumber, accessed October 21, 2025, [https://cucumber.io/docs/bdd/](https://cucumber.io/docs/bdd/)  
44. BDD \- Automation Panda, accessed October 21, 2025, [https://automationpanda.com/bdd/](https://automationpanda.com/bdd/)  
45. How We Used Cursor to Generate BDD Tests and Cut QA Time by 70% (Open Source), accessed October 21, 2025, [https://forum.cursor.com/t/how-we-used-cursor-to-generate-bdd-tests-and-cut-qa-time-by-70-open-source/66775](https://forum.cursor.com/t/how-we-used-cursor-to-generate-bdd-tests-and-cut-qa-time-by-70-open-source/66775)  
46. Behavior-Driven Development (BDD) With TestComplete \- SmartBear Support, accessed October 21, 2025, [https://support.smartbear.com/testcomplete/docs/bdd/index.html](https://support.smartbear.com/testcomplete/docs/bdd/index.html)  
47. Automated Testing Pipeline with Cursor and Cucumber Integration \- Discussions, accessed October 21, 2025, [https://forum.cursor.com/t/automated-testing-pipeline-with-cursor-and-cucumber-integration/48098](https://forum.cursor.com/t/automated-testing-pipeline-with-cursor-and-cucumber-integration/48098)