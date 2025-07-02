#!/usr/bin/env python3
"""
ITR Processing Agent using smolagents framework.

AI agent that can query Excel ITR data with conversational memory.
"""

import os
from smolagents import CodeAgent, OpenAIServerModel
from tools import (
    query_subsystem_itrs,
    search_subsystems, 
    manage_cache
)


def create_agent():
    """
    Create ITR processing agent with OpenAI GPT-4.1.
    
    Returns:
        CodeAgent: Agent with 3 ITR tools and conversational memory
    """
    # Initialize the OpenAI model
    # The API key is read from the OPENAI_API_KEY environment variable
    model = OpenAIServerModel(
        model_id="gpt-4.1",
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    # Create agent with 3 ITR tools
    agent = CodeAgent(
        tools=[
            query_subsystem_itrs,
            search_subsystems,
            manage_cache
        ],
        model=model,
        verbosity_level=1,
        stream_outputs=False,
    )
    
    return agent


def main():
    """
    Main function to run the ITR processing agent with conversational memory.
    """
    print("🤖 ITR Processing Agent initialized!")
    print("I can help you query ITR status information from your Excel file.")
    print("Try asking: 'How many open ITRs are in subsystem 7-1100-P-01-05?'")
    print("Then follow up with: 'How many of them are ITR-A type?'")
    print("Or ask: 'Find subsystems starting with 7-1100'")
    print("\nCommands:")
    print("- Type 'quit' or 'exit' to end")
    print("- Type '/reset' or '/clear' to start fresh conversation")
    print("- Type '/memory' to see conversation status\n")
    
    # Create the agent
    agent = create_agent()
    conversation_turns = 0
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            # Check for conversation management commands
            if user_input.lower() in ['/reset', '/clear']:
                print("🔄 Starting fresh conversation...")
                agent = create_agent()  # Create new agent instance
                conversation_turns = 0
                print("✅ Conversation memory cleared.\n")
                continue
            
            if user_input.lower() == '/memory':
                print(f"💭 Conversation status: {conversation_turns} turns in current session")
                print("🧠 Agent maintains memory of previous questions and answers")
                if conversation_turns > 0:
                    print("🔗 You can ask follow-up questions using 'them', 'those', 'it', etc.\n")
                else:
                    print("💡 Start by asking about an ITR subsystem!\n")
                continue
            
            # Skip empty input
            if not user_input:
                continue
            
            # Run the agent with user input, maintaining conversation memory
            print("\n🤖 Agent:", end=" ")
            response = agent.run(user_input, reset=False)  # Key change: reset=False
            print(f"{response}\n")
            
            conversation_turns += 1
            
        except KeyboardInterrupt:
            print("\n👋 Conversation interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again, type '/reset' to clear memory, or 'quit' to exit.\n")


if __name__ == "__main__":
    main()