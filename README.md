# ITR Processing Agent

An AI agent using the smolagents framework with consolidated, intent-driven tools for Excel ITR (Inspection, Test, and Review) processing. Built following the principle "Think like a model, not a developer" with just 3 focused tools instead of 8 overlapping ones.

## Installation

1. Install dependencies:
```bash
uv sync
```

## Usage

### Interactive Mode
Run the ITR processing agent:
```bash
uv run python simple_agent.py
```

### Test the Tools
Test the functionality:
```bash
uv run python test_itr_tool.py
```

### Create Test Data
Generate sample Excel file:
```bash
uv run python create_test_data.py
```

## Features

- **🎯 Intent-Driven Design**: 3 focused tools instead of 8 overlapping ones
- **🧠 Conversational Memory**: Maintain context across multiple questions  
- **📊 Comprehensive Data**: Each tool returns rich data that LLM extracts from
- **⚡ Performance Optimized**: Smart caching system for large Excel files
- **🔍 Smart Search**: Pattern-based subsystem discovery and filtering
- **📈 Complete ITR Analysis**: All ITR types, statuses, and completion rates
- **🛠️ Easy Cache Management**: Simple status checking and data refresh
- **🤖 LLM-Friendly**: Designed for how AI models actually think and work

## Performance Benefits

- **17x faster** initial Excel loading with optimized pandas parameters
- **394x faster** subsequent loads using intelligent caching
- **7,000+ queries/second** once data is cached
- **Smart cache invalidation** - automatically detects Excel file changes
- **Memory efficient** - loads only required columns and data types

## Example Queries

The agent intelligently uses **3 consolidated tools** to answer any ITR question:

### 🎯 **query_subsystem_itrs** - The Comprehensive Tool
- "How many open ITRs are in subsystem 7-1100-P-01-05?" → *LLM extracts: 1439 open ITRs*
- "How many of them are ITR-A type?" → *LLM extracts: 1392 ITR-A*  
- "What's the completion rate?" → *LLM extracts: 2.4%*
- "Show me the complete breakdown" → *LLM shows full type analysis*

### 🔍 **search_subsystems** - Smart Discovery
- "Find subsystems starting with 7-1100" → *Returns 12 matching subsystems*
- "Show me all available subsystems" → *Lists all 1270 subsystems*
- "Search for subsystems containing P-01" → *Pattern-based filtering*

### 🛠️ **manage_cache** - System Control  
- "Check cache status" → *Shows age, validity, record count*
- "Reload data from Excel" → *Forces fresh data load*

### 🧠 **Conversational Magic**
Agent remembers context, so you can ask follow-up questions naturally:
1. *"How many open ITRs in 7-1100-P-01-05?"* → 1439 open ITRs
2. *"How many are ITR-A?"* → 1392 ITR-A *(remembers previous subsystem)*
3. *"What about completion rate?"* → 2.4% *(still in context)*

## Testing

### Test All Functionality
```bash
uv run python tests/test_tools.py
```

### Create Test Data
```bash
uv run python tests/create_test_data.py
```

## ITR Status Logic

- **Blank "End Cert."**: ITR not yet started
- **"N" in "End Cert."**: ITR started/ongoing but not complete
- **"Y" in "End Cert."**: ITR completed
- **Open ITRs**: Not started + Ongoing (anything not "Y")