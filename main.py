"""
Customer Service Chatbot - Main Entry Point

This script demonstrates how to use the customer service chatbot framework.
It provides examples of both simple chat interface and detailed query processing.
"""

import sys
from pathlib import Path

from src.chatbot import CustomerServiceChatbot


def print_separator():
    """Print a visual separator line."""
    print("\n" + "=" * 80 + "\n")


def simple_chat_example():
    """
    Demonstrate simple chat interface.
    """
    print("Simple Chat Interface Example")
    print_separator()

    chatbot = CustomerServiceChatbot("config.yaml")

    queries = [
        "How do I export a report?",
        "When does my contract expire?",
        "What modules have I purchased?",
        "Hello, can you help me?"
    ]

    for query in queries:
        print(f"User: {query}")
        answer = chatbot.chat(query)
        print(f"Assistant: {answer}")
        print_separator()


def detailed_query_example():
    """
    Demonstrate detailed query processing with intent classification.
    """
    print("Detailed Query Processing Example")
    print_separator()

    chatbot = CustomerServiceChatbot("config.yaml")

    queries = [
        "How do I configure the inventory module?",
        "What is the pricing for my current contract?",
        "Can you show me the modules I purchased last year?"
    ]

    for query in queries:
        print(f"User Query: {query}")

        result = chatbot.process_query(query, use_llm_classification=True)

        print(f"Classified Intent: {result['intent']}")
        print(f"Response: {result['answer']}")
        print_separator()


def interactive_chat():
    """
    Run interactive chat session.
    """
    print("Interactive Customer Service Chatbot")
    print("Type 'exit' or 'quit' to end the conversation")
    print("Type 'history' to see conversation history")
    print("Type 'status' to see system status")
    print_separator()

    chatbot = CustomerServiceChatbot("config.yaml")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Thank you for using our customer service chatbot. Goodbye!")
                break

            if user_input.lower() == 'history':
                history = chatbot.get_conversation_history()
                if history:
                    print("\nConversation History:")
                    for msg in history:
                        role = msg['role'].capitalize()
                        content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                        print(f"{role}: {content}")
                else:
                    print("No conversation history yet.")
                print()
                continue

            if user_input.lower() == 'status':
                status = chatbot.get_system_status()
                print("\nSystem Status:")
                for key, value in status.items():
                    print(f"  {key}: {value}")
                print()
                continue

            result = chatbot.process_query(user_input)
            print(f"\nAssistant: {result['answer']}")
            print(f"(Intent: {result['intent']})\n")

        except KeyboardInterrupt:
            print("\n\nExiting chatbot...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


def system_check():
    """
    Perform system check and display configuration.
    """
    print("System Configuration Check")
    print_separator()

    try:
        chatbot = CustomerServiceChatbot("config.yaml")

        status = chatbot.get_system_status()

        print("Component Status:")
        for component, is_active in status.items():
            status_symbol = "[OK]" if is_active else "[FAIL]"
            print(f"  {status_symbol} {component}: {is_active}")

        print_separator()

        if not all(status.values()):
            print("Warning: Some components are not fully initialized.")
            print("The chatbot will operate in mock/demo mode for those components.")
            print("Please check your configuration and database connection.")
        else:
            print("All systems operational.")

    except Exception as e:
        print(f"System check failed: {str(e)}")
        sys.exit(1)


def main():
    """
    Main entry point with command-line interface.
    """
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "check":
            system_check()
        elif command == "simple":
            simple_chat_example()
        elif command == "detailed":
            detailed_query_example()
        elif command == "interactive":
            interactive_chat()
        elif command == "help":
            print("Customer Service Chatbot - Usage")
            print("\nCommands:")
            print("  python main.py check        - Run system configuration check")
            print("  python main.py simple       - Run simple chat examples")
            print("  python main.py detailed     - Run detailed query processing examples")
            print("  python main.py interactive  - Start interactive chat session")
            print("  python main.py help         - Show this help message")
            print("\nDefault: Runs interactive chat session")
        else:
            print(f"Unknown command: {command}")
            print("Run 'python main.py help' for usage information")
    else:
        interactive_chat()


if __name__ == "__main__":
    main()
