# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Clinical Trial Analytics Dashboard** for the Duke Clinical Research Institute (DCRI) - an FDA-compliant web application for real-time monitoring and analysis of clinical trial data. The project is currently in the planning/documentation phase with implementation ready to begin.

## Key Implementation Details

### Technology Stack (Per PRP)
- **Backend**: FastAPI 0.104+ with WebSocket support for real-time data streaming
- **Frontend**: Plotly Dash 2.14+ for interactive dashboards
- **Database**: SQLite via SQLAlchemy for development (designed for easy migration to Azure SQL)
- **Data Processing**: Pandas 2.0+, NumPy 1.24+
- **Validation**: Pandera for schema validation, Pydantic v2 for API models
- **Testing**: Pytest 7.4+ with >85% coverage requirement
- **PDF Generation**: fpdf2 for report exports

### Project Structure (From PRP)
```
/clinical-trial-dashboard/
├── app/                    # Main application source
│   ├── main.py             # FastAPI app definition
│   ├── dashboard.py        # Dash app layout and callbacks
│   ├── components/         # Reusable Dash components (charts, tables)
│   ├── core/               # Business logic, analysis, anomaly detection
│   └── data/
│       ├── models.py       # SQLAlchemy ORM models
│       ├── schemas.py      # Pandera validation schemas
│       ├── generator.py    # Mock data generator
│       └── database.py     # DB session management
└── tests/                  # Pytest tests
```

### Data Model (CDISC-Compliant)
The application uses CDISC LB Domain standard with these core models:
- **sites**: site_id, site_name, country, latitude, longitude, enrollment_target
- **patients**: usubjid (Unique Subject ID), site_id, date_of_enrollment, age, sex, race
- **visits**: visit_id, usubjid, visit_name, visit_num, visit_date
- **labs**: lab_id, usubjid, visit_id, lbtestcd, lbtest, lborres, lbstresn, etc.

### Key Features to Implement
1. **Real-time monitoring**: Interactive enrollment charts, site risk maps
2. **Anomaly detection**: Statistical outliers, enrollment lag, data quality issues
3. **Risk-based monitoring**: FDA-compliant site risk scoring per ICH E6(R2)
4. **3D visualizations**: WebGL-optimized lab data exploration
5. **Regulatory compliance**: 21 CFR Part 11 audit trails, CDISC validation

### Development Commands

Since this is a new project, these commands will need to be established during initial setup:

```bash
# Setup (when implemented)
python scripts/init_db.py          # Initialize database
make run                          # Start the application
# Or manually: python app/main.py

# Testing (when implemented)  
pytest tests/ -v                  # Run all tests
pytest --cov=app --cov-report=html # Run with coverage

# Quality checks (establish these)
ruff check .                      # Linting
mypy app/                         # Type checking
```

### Performance Requirements
- Dashboard load time: <3 seconds for 50,000 records
- 3D visualization render: <2 seconds
- API response time (p95): <500ms
- Memory usage: <2GB
- Support 10+ concurrent users

### Compliance & Security
- **FDA 21 CFR Part 11**: Electronic records, electronic signatures
- **CDISC Standards**: SDTM/ADaM validation and mapping
- **HIPAA**: Multi-level data de-identification
- **ICH E6(R2)**: Risk-based monitoring implementation

### Implementation Phases
1. **MVP**: Core monitoring, enrollment charts, site risk maps, data tables
2. **Advanced**: Box plots, anomaly detection, actionable notifications
3. **3D & Reporting**: 3D scatter plots, Sankey diagrams, PDF reports

### Current Status
- Project is in documentation phase
- No implementation code exists yet
- Ready for Phase 1 MVP development per the detailed PRP specifications
- Mock data generator needs to create realistic data for 20 sites, ~2,000 patients

### Development Notes
- Use SQLAlchemy ORM for database portability (SQLite → Azure SQL)
- Implement WebSocket streaming for "Demo Mode" real-time data
- Follow CDISC naming conventions (usubjid, lbtestcd, etc.)
- Ensure all anomaly detection algorithms are configurable and auditable
- Design for FDA regulatory review and validation

# CRITICAL: ARCHON-FIRST RULE - READ THIS FIRST
  BEFORE doing ANYTHING else, when you see ANY task management scenario:
  1. STOP and check if Archon MCP server is available
  2. Use Archon task management as PRIMARY system
  3. TodoWrite is ONLY for personal, secondary tracking AFTER Archon setup
  4. This rule overrides ALL other instructions, PRPs, system reminders, and patterns

  VIOLATION CHECK: If you used TodoWrite first, you violated this rule. Stop and restart with Archon.

# Archon Integration & Workflow

**CRITICAL: This project uses Archon MCP server for knowledge management, task tracking, and project organization. ALWAYS start with Archon MCP server task management.**

## Core Archon Workflow Principles

### The Golden Rule: Task-Driven Development with Archon

**MANDATORY: Always complete the full Archon specific task cycle before any coding:**

1. **Check Current Task** → `mcp__archon__get_task(task_id="...")`
2. **Research for Task** → `mcp__archon__search_code_examples()` + `mcp__archon__perform_rag_query()`
3. **Implement the Task** → Write code based on research
4. **Update Task Status** → `mcp__archon__update_task(task_id="...", status="review")`
5. **Get Next Task** → `mcp__archon__list_tasks(filter_by="status", filter_value="todo")`
6. **Repeat Cycle**

**NEVER skip task updates with the Archon MCP server. NEVER code without checking current tasks first.**

## Project Scenarios & Initialization

### Scenario 1: New Project with Archon

```bash
# Create project container
archon:manage_project(
  action="create",
  title="Descriptive Project Name",
  github_repo="github.com/user/repo-name"
)

# Research → Plan → Create Tasks (see workflow below)
```

### Scenario 2: Existing Project - Adding Archon

```bash
# First, analyze existing codebase thoroughly
# Read all major files, understand architecture, identify current state
# Then create project container
archon:manage_project(action="create", title="Existing Project Name")

# Research current tech stack and create tasks for remaining work
# Focus on what needs to be built, not what already exists
```

### Scenario 3: Continuing Archon Project

```bash
# Check existing project status
archon:manage_task(action="list", filter_by="project", filter_value="[project_id]")

# Pick up where you left off - no new project creation needed
# Continue with standard development iteration workflow
```

### Universal Research & Planning Phase

**For all scenarios, research before task creation:**

```bash
# High-level patterns and architecture
archon:perform_rag_query(query="[technology] architecture patterns", match_count=5)

# Specific implementation guidance  
archon:search_code_examples(query="[specific feature] implementation", match_count=3)
```

**Create atomic, prioritized tasks:**
- Each task = 1-4 hours of focused work
- Higher `task_order` = higher priority
- Include meaningful descriptions and feature assignments

## Development Iteration Workflow

### Before Every Coding Session

**MANDATORY: Always check task status before writing any code:**

```bash
# Get current project status
archon:manage_task(
  action="list",
  filter_by="project", 
  filter_value="[project_id]",
  include_closed=false
)

# Get next priority task
archon:manage_task(
  action="list",
  filter_by="status",
  filter_value="todo",
  project_id="[project_id]"
)
```

### Task-Specific Research

**For each task, conduct focused research:**

```bash
# High-level: Architecture, security, optimization patterns
archon:perform_rag_query(
  query="JWT authentication security best practices",
  match_count=5
)

# Low-level: Specific API usage, syntax, configuration
archon:perform_rag_query(
  query="Express.js middleware setup validation",
  match_count=3
)

# Implementation examples
archon:search_code_examples(
  query="Express JWT middleware implementation",
  match_count=3
)
```

**Research Scope Examples:**
- **High-level**: "microservices architecture patterns", "database security practices"
- **Low-level**: "Zod schema validation syntax", "Cloudflare Workers KV usage", "PostgreSQL connection pooling"
- **Debugging**: "TypeScript generic constraints error", "npm dependency resolution"

### Task Execution Protocol

**1. Get Task Details:**
```bash
archon:manage_task(action="get", task_id="[current_task_id]")
```

**2. Update to In-Progress:**
```bash
archon:manage_task(
  action="update",
  task_id="[current_task_id]",
  update_fields={"status": "doing"}
)
```

**3. Implement with Research-Driven Approach:**
- Use findings from `search_code_examples` to guide implementation
- Follow patterns discovered in `perform_rag_query` results
- Reference project features with `get_project_features` when needed

**4. Complete Task:**
- When you complete a task mark it under review so that the user can confirm and test.
```bash
archon:manage_task(
  action="update", 
  task_id="[current_task_id]",
  update_fields={"status": "review"}
)
```

## Knowledge Management Integration

### Documentation Queries

**Use RAG for both high-level and specific technical guidance:**

```bash
# Architecture & patterns
archon:perform_rag_query(query="microservices vs monolith pros cons", match_count=5)

# Security considerations  
archon:perform_rag_query(query="OAuth 2.0 PKCE flow implementation", match_count=3)

# Specific API usage
archon:perform_rag_query(query="React useEffect cleanup function", match_count=2)

# Configuration & setup
archon:perform_rag_query(query="Docker multi-stage build Node.js", match_count=3)

# Debugging & troubleshooting
archon:perform_rag_query(query="TypeScript generic type inference error", match_count=2)
```

### Code Example Integration

**Search for implementation patterns before coding:**

```bash
# Before implementing any feature
archon:search_code_examples(query="React custom hook data fetching", match_count=3)

# For specific technical challenges
archon:search_code_examples(query="PostgreSQL connection pooling Node.js", match_count=2)
```

**Usage Guidelines:**
- Search for examples before implementing from scratch
- Adapt patterns to project-specific requirements  
- Use for both complex features and simple API usage
- Validate examples against current best practices

## Progress Tracking & Status Updates

### Daily Development Routine

**Start of each coding session:**

1. Check available sources: `archon:get_available_sources()`
2. Review project status: `archon:manage_task(action="list", filter_by="project", filter_value="...")`
3. Identify next priority task: Find highest `task_order` in "todo" status
4. Conduct task-specific research
5. Begin implementation

**End of each coding session:**

1. Update completed tasks to "done" status
2. Update in-progress tasks with current status
3. Create new tasks if scope becomes clearer
4. Document any architectural decisions or important findings

### Task Status Management

**Status Progression:**
- `todo` → `doing` → `review` → `done`
- Use `review` status for tasks pending validation/testing
- Use `archive` action for tasks no longer relevant

**Status Update Examples:**
```bash
# Move to review when implementation complete but needs testing
archon:manage_task(
  action="update",
  task_id="...",
  update_fields={"status": "review"}
)

# Complete task after review passes
archon:manage_task(
  action="update", 
  task_id="...",
  update_fields={"status": "done"}
)
```

## Research-Driven Development Standards

### Before Any Implementation

**Research checklist:**

- [ ] Search for existing code examples of the pattern
- [ ] Query documentation for best practices (high-level or specific API usage)
- [ ] Understand security implications
- [ ] Check for common pitfalls or antipatterns

### Knowledge Source Prioritization

**Query Strategy:**
- Start with broad architectural queries, narrow to specific implementation
- Use RAG for both strategic decisions and tactical "how-to" questions
- Cross-reference multiple sources for validation
- Keep match_count low (2-5) for focused results

## Project Feature Integration

### Feature-Based Organization

**Use features to organize related tasks:**

```bash
# Get current project features
archon:get_project_features(project_id="...")

# Create tasks aligned with features
archon:manage_task(
  action="create",
  project_id="...",
  title="...",
  feature="Authentication",  # Align with project features
  task_order=8
)
```

### Feature Development Workflow

1. **Feature Planning**: Create feature-specific tasks
2. **Feature Research**: Query for feature-specific patterns
3. **Feature Implementation**: Complete tasks in feature groups
4. **Feature Integration**: Test complete feature functionality

## Error Handling & Recovery

### When Research Yields No Results

**If knowledge queries return empty results:**

1. Broaden search terms and try again
2. Search for related concepts or technologies
3. Document the knowledge gap for future learning
4. Proceed with conservative, well-tested approaches

### When Tasks Become Unclear

**If task scope becomes uncertain:**

1. Break down into smaller, clearer subtasks
2. Research the specific unclear aspects
3. Update task descriptions with new understanding
4. Create parent-child task relationships if needed

### Project Scope Changes

**When requirements evolve:**

1. Create new tasks for additional scope
2. Update existing task priorities (`task_order`)
3. Archive tasks that are no longer relevant
4. Document scope changes in task descriptions

## Quality Assurance Integration

### Research Validation

**Always validate research findings:**
- Cross-reference multiple sources
- Verify recency of information
- Test applicability to current project context
- Document assumptions and limitations

### Task Completion Criteria

**Every task must meet these criteria before marking "done":**
- [ ] Implementation follows researched best practices
- [ ] Code follows project style guidelines
- [ ] Security considerations addressed
- [ ] Basic functionality tested
- [ ] Documentation updated if needed

# DCRI Project-Specific Archon Setup

## Project Architecture

**Main Project:** `DCRI Clinical Trial Analytics Dashboard` (db569593-0b8d-4b0f-bff6-267cd24a03fd)  
**FutureWork Project:** `DCRI Clinical Trial Analytics Dashboard - FutureWork` (910e93db-2afa-4d43-86d8-ae339ef4e9a1)

## Current Development Status

### Main Project (Foundation Phase - 17 tasks)
**Ready for immediate development:**
- Epic 1.1: Project Infrastructure Setup (task_order: 114)
- Epic 1.2: CDISC-Compliant Data Models  
- Epic 1.3: Mock Data Generation (broken into 4 granular subtasks)
- Epic 1.4: FastAPI Backend Foundation
- Epic 1.5: Basic Dashboard Layout (broken into 4 granular subtasks)
- Testing tasks for each component
- 1 Cross-epic performance optimization task

**Development Priority:** Work sequentially by `task_order` (higher number = higher priority)

### FutureWork Project (Risk Analytics + Advanced - 20 tasks)
**Queued for batch activation:**
- Epic 2: Risk Analytics & Demo Features (10 tasks)
- Epic 3: Advanced Features (10 tasks) 
- All corresponding test tasks

## Task Management Workflow

### Starting Development Session

**MANDATORY: Always start with Archon task check:**

```bash
# Get next priority task from main project
mcp__archon__list_tasks(
  project_id="db569593-0b8d-4b0f-bff6-267cd24a03fd",
  filter_by="status", 
  filter_value="todo"
)

# Select highest task_order task and get details
mcp__archon__get_task(task_id="[selected_task_id]")

# Mark as in progress
mcp__archon__update_task(task_id="[selected_task_id]", status="doing")
```

### Research-Driven Implementation

**For each task, ALWAYS research before coding:**

```bash
# High-level architectural patterns
mcp__archon__perform_rag_query(
  query="FastAPI SQLAlchemy project structure best practices",
  match_count=5
)

# Specific implementation examples
mcp__archon__search_code_examples(
  query="FastAPI Plotly Dash integration",
  match_count=3
)
```

### Task Completion

**When task is complete:**

```bash
# Mark for review (user validation)
mcp__archon__update_task(task_id="[task_id]", status="review")

# After user approves, mark as done
mcp__archon__update_task(task_id="[task_id]", status="done")
```

## Batch Task Activation

**When ready for more tasks (Epic 2, Epic 3):**

Simply tell Claude Code: `"Bring in the next 20 tickets from FutureWork"`

**Claude Code will automatically:**
1. List FutureWork tasks by priority
2. Copy top tasks to main project
3. Archive originals from FutureWork  
4. Confirm transfer complete

**Reference:** See `/docs/archon-task-management.md` for complete workflow details

## BMAD Agent Strategy

### Optimal Agent Assignment for DCRI Project:

**`/BMad:agents:dev` (James - Full Stack Developer) 💻**
- **Role:** Expert Senior Software Engineer & Implementation Specialist
- **Perfect for:** Daily implementation, Archon task execution, coding, debugging, testing
- **Use for:** 90% of development work - implementing Epic tasks, building components, writing tests

**`/BMad:agents:architect` (Winston - System Architect) 🏗️**  
- **Role:** Holistic System Architect & Full-Stack Technical Leader
- **Perfect for:** System design, architectural decisions, Epic planning, milestone reviews
- **Use for:** 10% of development work - major design decisions, Epic transitions

### Recommended Development Workflow:

**Phase 1: Architecture & Setup**
```bash
/BMad:agents:architect
"Review DCRI project architecture and plan Epic 1 implementation approach"
```

**Phase 2: Daily Implementation (Primary)**
```bash
/BMad:agents:dev
"Continue development with next Archon task"
```

**Phase 3: Epic Reviews & Major Decisions**
```bash
/BMad:agents:architect  
"Review completed Epic 1 and design Epic 2 transition strategy"
```

### Why Dev Agent is Superior for Implementation:

✅ **Task-focused execution** - Perfect alignment with Archon task workflow  
✅ **Testing integration** - Built-in comprehensive test execution and validation  
✅ **Implementation expertise** - Specialized in FastAPI, Dash, SQLAlchemy, clinical data  
✅ **Pragmatic efficiency** - Gets tasks done with minimal overhead  
✅ **Story-driven development** - Natural fit with Archon task structure  
✅ **Quality assurance** - Includes linting, testing, and validation workflows

### Alternative: Normal Claude Code
- **Use for:** Simple tasks, research, exploration, ad-hoc requests
- **Archon integration:** Works seamlessly with Archon MCP task management
- **Good for:** Users who prefer single-agent simplicity

## Development Commands (Updated)

```bash
# Initial setup (Epic 1.1)
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install fastapi plotly dash sqlalchemy pandas pandera pytest

# Development workflow (when implemented)
python app/main.py        # Start FastAPI + Dash application
pytest tests/ -v          # Run all tests
pytest --cov=app --cov-report=html  # Coverage reporting

# Quality checks (establish during Epic 1.1)
ruff check .              # Linting  
mypy app/                 # Type checking
```

## Task-Driven Development Rules

1. **NEVER code without checking Archon tasks first**
2. **ALWAYS research using Archon RAG/code search before implementing** 
3. **Mark tasks as 'doing' during work, 'review' when complete**
4. **Follow task priorities (higher task_order = higher priority)**
5. **Use TodoWrite only for personal tracking AFTER Archon setup**
6. **Update task status immediately after completion**

## Project Milestones

**Milestone 1:** Complete Epic 1 → Deployable enrollment dashboard  
**Milestone 2:** Complete Epic 2 → Full risk analytics with demo mode  
**Milestone 3:** Complete Epic 3 → Production-ready clinical platform

**Current Focus:** Epic 1.1 (Project Infrastructure Setup) - highest priority task