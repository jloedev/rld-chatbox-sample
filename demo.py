"""
Demo script to showcase the chatbot functionality
"""

from src.chatbot import CustomerServiceChatbot

def print_separator():
    print("\n" + "=" * 80 + "\n")

def main():
    print("Customer Service Chatbot Demo")
    print_separator()

    print("Initializing chatbot...")
    chatbot = CustomerServiceChatbot("config.yaml")
    print("Chatbot initialized successfully!")
    print_separator()

    # Demo queries
    queries = [
        {
            "query": "How do I export a report?",
            "expected_intent": "USER_GUIDE"
        },
        {
            "query": "When does my contract expire for ACME Corp?",
            "expected_intent": "CONTRACT_INFO"
        },
        {
            "query": "What modules have I purchased?",
            "expected_intent": "CONTRACT_INFO"
        },
        {
            "query": "How do I add a new inventory item?",
            "expected_intent": "USER_GUIDE"
        }
    ]

    for i, item in enumerate(queries, 1):
        query = item["query"]
        print(f"Query {i}: {query}")
        print(f"Expected Intent: {item['expected_intent']}")
        print("-" * 80)

        result = chatbot.process_query(query)

        print(f"Detected Intent: {result['intent'].upper()}")
        print(f"\nResponse:\n{result['answer']}")
        print_separator()

    print("Demo completed successfully!")

if __name__ == "__main__":
    main()
