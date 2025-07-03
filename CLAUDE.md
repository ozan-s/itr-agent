# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ITR (Inspection, Test, and Review) Processing Agent built with the `smolagents` framework. It's a specialized AI agent that processes Excel-based ITR data through conversational interfaces. The architecture follows "Think like a model, not a developer" principles, consolidating 8 overlapping tools into 3 focused ones for better AI decision-making.

## Essential Commands

### Installation & Setup
```bash
uv sync                                    # Install dependencies
```

### Running the Application
```bash
uv run python agent.py                    # Start interactive ITR agent
uv run python tests/test_tools.py         # Run comprehensive tests
uv run python tests/create_test_data.py   # Generate test Excel data
```

### Environment Requirements
- `OPENAI_API_KEY` environment variable must be set
- Python >=3.12 required
- Main data file is `pcos.xlsx` (gitignored)
- Test data file is `test_pcos.xlsx`

## Architecture Overview

### Core Components

**agent.py** (110 lines): Main agent entry point
- Conversational memory management with OpenAI GPT-4.1
- Interactive commands: `/reset`, `/clear`, `/memory`, `quit`, `exit`
- Session management and error recovery

**tools.py** (700+ lines): Core business logic with 4 consolidated tools
- `ITRProcessor` class with intelligent caching system
- Global singleton pattern for performance optimization
- Smart cache invalidation based on file modification times
- Hierarchical data support: System → SubSystem → ITR

**Key Architecture Pattern**: Intent-driven tool design
- Each tool has a distinct, non-overlapping purpose
- Tools return comprehensive data that the LLM extracts from
- Designed specifically for how AI models make decisions

### The 4 Consolidated Tools

1. **`query_subsystem_itrs`**: THE comprehensive ITR data source
   - Returns complete breakdown: counts, types (ITR-A/B/C), completion rates
   - Handles all ITR status queries for any subsystem
   - Provides actionable next steps and guidance

2. **`search_subsystems`**: SubSystem-level pattern-based discovery
   - Searches by subsystem ID or description content
   - Supports partial matching and case-insensitive search
   - Returns matching subsystems with descriptions

3. **`search_systems`**: System-level pattern-based discovery  
   - Searches by system ID or description content
   - Returns system info with connected subsystem IDs
   - Provides hierarchical view: System → SubSystems
   - No ITR data (use query_subsystem_itrs for ITR details)

4. **`manage_cache`**: System management and performance
   - Cache status checking and forced reloads
   - Performance monitoring and diagnostics
   - Data freshness validation

### Performance Characteristics

- **17x faster** initial loading with optimized pandas parameters
- **394x faster** subsequent loads using pickle caching
- **7,000+ queries/second** when data is cached
- Automatic cache invalidation when Excel files change
- Memory-efficient column selection and data type optimization

## ITR Status Logic

Critical business rules that must be preserved:
- **Blank "End Cert."**: ITR not yet started
- **"N" in "End Cert."**: ITR started/ongoing but not complete  
- **"Y" in "End Cert."**: ITR completed
- **Open ITRs**: Not started + Ongoing (anything not "Y")

## Caching System

The caching system is performance-critical:
- Uses pickle for fast serialization
- Validates cache against Excel file modification times
- Located in `.cache/` directory (gitignored)
- Never bypass or disable caching in production code
- Cache invalidation is automatic and intelligent

## Testing Structure

**tests/test_tools.py**: Direct tool testing
- Unit tests for each of the 3 tools
- Edge case testing (invalid inputs, missing data)
- Performance verification tests

**tests/create_test_data.py**: Test data generation
- Creates realistic Excel structure for testing
- Generates various ITR types and statuses

## Development Guidelines

### When Modifying Tools
- Preserve the 4-tool architecture - maintain focused tool set
- Each tool must have distinct, non-overlapping purpose
- Return comprehensive data, let LLM extract specifics
- Maintain backwards compatibility with existing caching
- Respect System → SubSystem → ITR hierarchy

### When Working with Excel Data
- Always use the `ITRProcessor` class, never read Excel directly
- Respect the caching system - don't bypass it
- Use optimized pandas parameters for large file performance
- Handle missing files gracefully (fallback to test data)

### Performance Considerations
- The global `processor` instance should remain singleton
- Cache loading happens automatically on first use
- Never force cache reload unless explicitly requested
- Monitor memory usage when processing large datasets

## Data Files

- `pcos.xlsx`: Main production data (gitignored)
- `test_pcos.xlsx`: Test data file (committed)
- `.cache/`: Performance cache directory (gitignored)
- Both Excel files should have identical structure

### Excel Structure
Required columns: `System`, `System Descr.`, `SubSystem`, `SubSystem Descr.`, `ITR`, `End Cert.`, `ITEM`, `Rule`, `Test`, `Form`

**Hierarchy**: System → SubSystem → ITR
- Example: System "7-1100-P-01" contains SubSystem "7-1100-P-01-05"
- Each SubSystem has multiple ITRs (ITR-A, ITR-B, ITR-C)
- Use `search_systems` for System-level queries, `search_subsystems` for SubSystem-level queries

**Deduplication**: Composite key from `ITEM`+`Rule`+`Test`+`Form` removes duplicates automatically at load time

## Error Handling Patterns

- Excel file not found → graceful fallback to test data
- Cache corruption → automatic rebuild from Excel
- Invalid subsystem queries → helpful error messages with suggestions
- OpenAI API issues → clear guidance for API key setup

## Data Processing Patterns

### Composite Key Deduplication Pattern  
- **Problem**: Remove duplicates based on multiple fields without losing data integrity
- **Solution**: Concatenate key fields with delimiter, deduplicate at load time
- **Implementation**: `field1|field2|field3|field4` format, handles empty/null values gracefully

### Load-Time Data Processing Pattern
- **Problem**: Choose between load-time vs query-time data transformation
- **Solution**: Heavy operations (deduplication) at load time, cache results
- **Benefit**: All subsequent operations work on clean data, no repeated processing

## Requirement Clarification Protocol

### STOP and Ask Before Implementing

When encountering ambiguous requirements, **ALWAYS** clarify these categories:

#### 1. **Data Behavior Ambiguity**
- **"Remove duplicates"** → Ask: "Delete duplicate rows OR count unique values?"
- **"Handle missing data"** → Ask: "Skip rows, use defaults, or error out?"
- **"Process Excel file"** → Ask: "Transform data in-place or preserve original?"

#### 2. **Architecture Scope Ambiguity**  
- **"Add new feature"** → Ask: "Minimal implementation or production-ready with all edge cases?"
- **"Support X"** → Ask: "Current files only or backward compatibility needed?"
- **"Improve performance"** → Ask: "Optimize for speed, memory, or maintainability?"

#### 3. **Implementation Strategy Ambiguity**
- **"Make it work"** → Ask: "Quick fix or proper solution following existing patterns?"
- **"Add validation"** → Ask: "Fail fast or graceful degradation?"
- **"Handle errors"** → Ask: "Log and continue or stop processing?"

### Clarification Question Templates

Use these exact phrases to avoid assumptions:

**For Data Operations:**
- "When you say [ambiguous term], do you mean [option A] or [option B]?"
- "Should this [preserve/modify/delete] the original data?"
- "How should we handle [specific edge case] - [option A], [option B], or something else?"

**For Architecture Decisions:**
- "Do you need this to work with existing [files/data/systems] or can we require [new format]?"
- "Should I implement the minimal version first, or the full solution with all edge cases?"
- "Are you optimizing for [speed/memory/maintainability/simplicity]?"

**For Scope Boundaries:**
- "This could be implemented as [simple approach] or [comprehensive approach]. Which do you prefer?"
- "Should I follow the existing pattern of [X] or create a new approach?"

### Anti-Pattern Prevention

**NEVER assume:**
- ❌ "Deduplication" means row deletion (could mean unique counting)
- ❌ "Support new format" means backward compatibility needed
- ❌ "Make it work" means add all possible edge case handling
- ❌ "Handle errors" means implement complex recovery logic

**ALWAYS clarify:**
- ✅ Exact data transformation behavior expected
- ✅ Compatibility requirements with existing systems
- ✅ Implementation scope (minimal vs comprehensive)
- ✅ Error handling strategy (fail fast vs graceful)

### When in Doubt, Ask Examples

**Template**: "Could you give me an example? If I have [specific input], what exactly should happen to produce [expected output]?"

This prevents architectural over-engineering and ensures the solution matches actual needs.

## Key Development Lessons

**Tool Parameter Exposure**: When creating tools for LLMs, ensure ALL useful parameters are exposed through the tool decorator. Internal method parameters that aren't exposed to the LLM create functional limitations where the AI cannot fully control the tool's behavior, leading to incomplete or suboptimal results.

**TDD for Data Processing**: Test-driven development is especially critical for data processing features where edge cases (missing values, duplicates, malformed data) are common and can cause silent failures in production.

**Clarification Over Assumptions**: When requirements have multiple valid interpretations, asking one clarifying question saves hours of implementing the wrong solution. Always clarify data behavior, architecture scope, and implementation strategy before coding.

This codebase represents a mature example of AI-first architecture design, optimized specifically for conversational AI agents rather than traditional software patterns.