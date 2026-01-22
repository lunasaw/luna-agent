# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Work Agent (luna-agent) is a production-ready AI Agent framework built with OpenAI Agents SDK. This is an engineering-grade scaffold following strict Python architectural principles: clean architecture, dependency injection, and comprehensive observability. The project serves as both a functional daily work assistant and a reference implementation for building robust AI agent applications.

**Architecture Pattern**: Clean Architecture / Hexagonal Architecture with strict layering and dependency inversion.

## Essential Commands

### Development Setup
```bash
# Install dependencies using uv (preferred)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Install API dependencies (optional)
uv pip install -e ".[api]"

# Configure environment
cp .env.example .env
# Edit .env to add OPENAI_API_KEY
```

### Running the Agent
```bash
# Single execution
python -m work_agent run "现在几点了?"

# Interactive REPL mode
python -m work_agent repl

# List available tools
python -m work_agent list-tools

# Start API server (requires [api] extras)
python -m work_agent serve --port 8000
```

### Testing
```bash
# Unit tests only (no external dependencies)
pytest tests/unit -v

# All tests including integration (requires API key)
RUN_INTEGRATION=1 pytest -v

# Coverage report
pytest --cov=work_agent --cov-report=html

# Run specific test
pytest tests/unit/test_tool_registry.py::test_load_tools_success -v

# Run tests matching pattern
pytest -k "registry" -v
```

### Code Quality
```bash
# Format code
ruff format .
black .

# Lint
ruff check .

# Type checking
mypy src/work_agent

# Run all checks
ruff check . && black --check . && mypy src/work_agent && pytest tests/unit
```

### Pre-commit Hooks
```bash
uv pip install pre-commit
pre-commit install
```

## Architecture

### Layer Structure and Dependency Rules

```
API/Tasks → Services → Domain
          ↘         ↗
            Adapters
```

**Critical Rules (from RULE.md)**:
- **domain/**: Pure business logic. ZERO external dependencies. No I/O, no env vars, no framework coupling.
- **services/**: Use case orchestration. Depends on domain abstractions. Receives adapters via DI.
- **adapters/**: External system integration (LLM, tools, observability). Implements domain interfaces.
- **api/**: Web layer (FastAPI). Only calls services, never adapters directly.
- **tasks/**: Background task entry points. Calls services.
- **app.py/container.py**: ONLY place where dependencies are assembled. All DI happens here.

**Forbidden Dependencies**:
- domain MUST NOT import services/adapters/api/tasks
- services MUST NOT import api
- adapters MUST NOT import api or services
- Business code MUST NOT read environment variables (only config.py does this)

### Key Architectural Patterns

**1. No Side Effects on Import**
- `__init__.py` files are empty or only contain exports
- NO I/O, env reads, logging config, or resource initialization on import
- All initialization happens in `app.py` or `container.py`

**2. Dependency Injection**
- `container.py` is the sole dependency assembler
- Services receive dependencies via constructor injection
- No global singletons or module-level clients
- Container manages resource lifecycle (startup/shutdown)

**3. Configuration Management**
- `config.py` is the ONLY place that reads environment variables
- Uses Pydantic BaseSettings for type-safe validation
- Configuration is immutable after load
- All modules receive config via injection

**4. Tool Plugin System**
- Tools in `adapters/tools/` are auto-discovered
- Each tool file must expose a `get_tool()` function
- Tools decorated with `@function_tool` from OpenAI Agents SDK
- Registry pattern with conflict detection

**5. Observability**
- Structured logging with trace_id correlation
- Thread-safe trace propagation via contextvars
- Custom log formatter in `logging.py`
- Hooks for OpenTelemetry/Langfuse (currently local mode)

## Common Development Tasks

### Adding a New Tool

Create a file in `src/work_agent/adapters/tools/`:

```python
"""Tool description"""
from typing import Any
from agents import function_tool

@function_tool
def your_tool_name(param: str) -> str:
    """
    Detailed description for the LLM.

    Args:
        param: Parameter description

    Returns:
        Return value description
    """
    # Implementation
    return result

def get_tool() -> Any:
    """Required for auto-discovery"""
    return your_tool_name
```

**Requirements**:
- Type annotations on all parameters
- Comprehensive docstring (used by LLM)
- Must expose `get_tool()` function
- No side effects on import
- File name: snake_case
- Do not start filename with `_` (except `_registry.py`)

**Verification**:
```bash
python -m work_agent list-tools  # Should show your new tool
```

### Adding a New Service

1. Create service in `src/work_agent/services/`:
```python
from work_agent.domain.models import SomeModel

class NewService:
    def __init__(self, dependency: SomeDependency) -> None:
        self.dependency = dependency

    def execute(self, input_data: str) -> SomeModel:
        # Use case orchestration logic
        pass
```

2. Register in `container.py`:
```python
def build_container(config: Config) -> Container:
    # ...
    new_service = NewService(dependency=some_adapter)
    return Container(..., new_service=new_service)
```

### Adding a New Adapter

Create in `src/work_agent/adapters/external/`:
```python
class NewAdapter:
    def __init__(self, config: Config) -> None:
        self.config = config
        # Initialize client

    def fetch_data(self) -> dict:
        # External system interaction
        pass

    def close(self) -> None:
        # Cleanup resources
        pass
```

Register in `container.py` and ensure cleanup in shutdown hooks.

## Critical Engineering Rules (RULE.md)

This project follows a 467-line engineering specification. Key points:

**Initialization & Globals**:
- `__init__.py` MUST have no side effects (no I/O, no env reads)
- NO module-level global state or external resource objects
- All resources created in `container.py`, cleaned up in shutdown hooks

**Configuration**:
- `config.py` is the single source for environment variable reads
- All other modules receive config via injection
- Never scatter `os.getenv()` across codebase

**Logging**:
- `logging.py` configures logging once at startup
- All logs must include: timestamp, level, module, trace_id, message
- NO `print()` statements in production code
- NO sensitive data in logs (passwords, tokens, keys)

**Error Handling**:
- Domain layer throws domain exceptions (business rule violations)
- Adapters catch external library exceptions and convert to domain exceptions
- API layer maps exceptions to HTTP responses
- NEVER swallow exceptions with bare `except: pass`

**Testing**:
- `tests/unit/`: No external dependencies, fast, always runnable
- `tests/integration/`: Real external systems, gated by `RUN_INTEGRATION` env var
- Domain and services MUST have unit test coverage
- Tests must be repeatable and order-independent

**Resource Management**:
- All external resources (DB, Redis, HTTP clients, etc.) MUST be closeable
- Resources created in container, destroyed in shutdown hooks
- NO reliance on interpreter exit for cleanup
- Thread/async safety must be documented

**Type Safety**:
- Services and domain functions MUST have type annotations
- Mypy strict mode enabled for core business logic
- Use Pydantic for data validation at boundaries

## File Structure Reference

```
src/work_agent/
├── domain/              # Pure business models & exceptions
│   ├── models.py        # AgentRequest, AgentResponse
│   └── errors.py        # Domain exceptions
├── services/            # Use case orchestration
│   └── agent_service.py # Core agent service (run_once, repl)
├── adapters/
│   ├── llm/            # LLM provider integration
│   │   ├── agent_factory.py   # Creates Agent instances
│   │   ├── runner_factory.py  # Creates Runner instances
│   │   └── models.py          # LLM model configs
│   ├── tools/          # Auto-discovered tool plugins
│   │   ├── _registry.py       # Tool discovery & registration
│   │   ├── time_now.py        # Example tool
│   │   └── shell_echo.py      # Example tool
│   ├── observability/  # Logging & tracing
│   │   ├── context.py         # Trace ID management (contextvars)
│   │   └── tracing.py         # Tracing hooks
│   └── external/       # Future external adapters
├── api/                # FastAPI web layer (optional)
│   ├── app.py          # FastAPI factory
│   ├── routes.py       # Route definitions
│   └── dto.py          # Request/Response DTOs
├── tasks/              # Background task entry points
│   └── example_task.py
├── utils/              # Minimal utilities (strict admission)
│   └── typing.py       # Type definitions
├── app.py              # Application assembly & CLI entry
├── container.py        # Dependency injection container
├── config.py           # Configuration (ONLY place reading env vars)
└── logging.py          # Logging setup
```

## Environment Variables

See `.env.example` for all options. Key variables:

```bash
OPENAI_API_KEY=sk-...        # Required
AGENT_MODEL=gpt-4o           # Default model
LOG_LEVEL=INFO               # DEBUG|INFO|WARNING|ERROR
ENABLE_TRACING=false         # Enable observability tracing
SESSION_BACKEND=memory       # memory|sqlite
API_HOST=0.0.0.0            # API server host
API_PORT=8000               # API server port
```

## API Endpoints (when running in API mode)

- `GET /health` - Health check
- `GET /tools` - List all available tools
- `POST /run` - Execute agent task
  ```json
  {
    "user_input": "现在几点了?",
    "trace_id": "optional-trace-id"
  }
  ```
- `PUT /config/instructions` - Update instructions (placeholder)

API docs available at: `http://localhost:8000/docs`

## Troubleshooting

**`OPENAI_API_KEY not found`**:
- Ensure `.env` file exists in project root
- Check format: `OPENAI_API_KEY=sk-...` (no quotes)
- Or export directly: `export OPENAI_API_KEY=sk-...`

**Tool not discovered**:
- Confirm file is in `src/work_agent/adapters/tools/`
- Filename must not start with `_` (except `_registry.py`)
- Must expose `get_tool()` function
- Check `python -m work_agent list-tools` for error logs

**Test failures**:
- Unit test failures: Check mock configuration
- Integration test failures: Set `RUN_INTEGRATION=1` and verify API key
- Verbose logs: `pytest -vv --log-cli-level=DEBUG`

## Important Patterns to Follow

When modifying this codebase:

1. **Never add I/O or env reads to `__init__.py`** - This will break the clean initialization pattern
2. **Never create module-level clients** - All resources via DI in container
3. **Never import adapters from domain** - Maintain dependency direction
4. **Never skip writing tests** - Domain and services require unit tests
5. **Never log sensitive data** - API keys, passwords, tokens must be redacted
6. **Always use type hints** - Especially in services and domain
7. **Always clean up resources** - Register shutdown hooks in container
8. **Always validate at boundaries** - Use Pydantic for API inputs

## Model Configuration

Current: OpenAI via OpenAI Agents SDK

To change model: Edit `AGENT_MODEL` in `.env`
To add new provider: Modify `adapters/llm/agent_factory.py` and `models.py`

Future support planned for:
- Azure OpenAI
- Anthropic Claude
- Custom API endpoints
