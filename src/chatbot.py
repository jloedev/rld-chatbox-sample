"""
Chatbot Orchestrator Module

This module coordinates all components of the customer service chatbot,
including intent classification, query routing, and response generation.
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory

from src.config_loader import ConfigLoader
from src.rag_system import RAGSystem
from src.sql_query_system import SQLQuerySystem


class IntentType(Enum):
    """
    Enumeration of possible user intent types.
    """
    USER_GUIDE = "user_guide"
    CONTRACT_INFO = "contract_info"
    GENERAL = "general"


class CustomerServiceChatbot:
    """
    Main chatbot orchestrator for customer service inquiries.

    This class coordinates intent classification, query routing between
    RAG and SQL systems, and response generation using LLMs.

    Attributes:
        config (ConfigLoader): Configuration loader
        llm: Language model instance
        rag_system (RAGSystem): Document retrieval system
        sql_system (SQLQuerySystem): SQL query system
        memory: Conversation memory
        intent_keywords (Dict): Keywords for intent classification
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the chatbot.

        Args:
            config_path (str): Path to configuration file
        """
        self.config = ConfigLoader(config_path)
        self.llm = None
        self.rag_system = None
        self.sql_system = None
        self.memory = None
        self.intent_keywords = self.config.get_intent_keywords()

        self._initialize_components()

    def _initialize_components(self) -> None:
        """
        Initialize all chatbot components.
        """
        self._initialize_llm()
        self._initialize_rag_system()
        self._initialize_sql_system()
        self._initialize_memory()

    def _initialize_llm(self) -> None:
        """
        Initialize the language model based on configuration.
        """
        ai_config = self.config.get_ai_provider_config()
        provider = ai_config.get('provider', 'openai')

        if provider == 'openai':
            self.llm = ChatOpenAI(
                api_key=ai_config.get('api_key'),
                model=ai_config.get('model', 'gpt-4-turbo-preview'),
                temperature=ai_config.get('temperature', 0.7),
                max_tokens=ai_config.get('max_tokens', 2000)
            )
        elif provider == 'anthropic':
            self.llm = ChatAnthropic(
                model=ai_config.get('model', 'claude-3-opus-20240229'),
                temperature=ai_config.get('temperature', 0.7),
                max_tokens=ai_config.get('max_tokens', 2000)
            )
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

    def _initialize_rag_system(self) -> None:
        """
        Initialize the RAG system for document retrieval.
        """
        vector_config = self.config.get_vector_store_config()
        documents_config = self.config.get('documents', default={})

        self.rag_system = RAGSystem(vector_config, documents_config)

        status = self.rag_system.initialize_or_load()
        print(f"RAG System: {status}")

    def _initialize_sql_system(self) -> None:
        """
        Initialize the SQL query system.
        """
        sql_config = self.config.get_sql_config()
        self.sql_system = SQLQuerySystem(sql_config)

    def _initialize_memory(self) -> None:
        """
        Initialize conversation memory.
        """
        chatbot_config = self.config.get_chatbot_config()

        if chatbot_config.get('enable_conversation_memory', True):
            max_history = chatbot_config.get('max_history_length', 10)
            self.memory = ConversationBufferWindowMemory(
                k=max_history,
                return_messages=True
            )

    def classify_intent(self, query: str) -> IntentType:
        """
        Classify user query intent using keyword matching.

        Args:
            query (str): User query

        Returns:
            IntentType: Classified intent type
        """
        query_lower = query.lower()

        user_guide_score = sum(
            1 for keyword in self.intent_keywords['user_guide']
            if keyword.lower() in query_lower
        )

        contract_score = sum(
            1 for keyword in self.intent_keywords['contract']
            if keyword.lower() in query_lower
        )

        if contract_score > user_guide_score:
            return IntentType.CONTRACT_INFO
        elif user_guide_score > 0:
            return IntentType.USER_GUIDE
        else:
            return IntentType.GENERAL

    def classify_intent_with_llm(self, query: str) -> IntentType:
        """
        Classify user query intent using LLM for more accurate classification.

        Args:
            query (str): User query

        Returns:
            IntentType: Classified intent type
        """
        classification_prompt = f"""
Classify the following customer query into one of these categories:
1. USER_GUIDE - Questions about how to use the software, features, tutorials, instructions
2. CONTRACT_INFO - Questions about contract details, expiration dates, pricing, purchased modules
3. GENERAL - General questions or greetings

Query: {query}

Respond with only the category name (USER_GUIDE, CONTRACT_INFO, or GENERAL).
"""

        try:
            response = self.llm.invoke([HumanMessage(content=classification_prompt)])
            classification = response.content.strip().upper()

            if "USER_GUIDE" in classification:
                return IntentType.USER_GUIDE
            elif "CONTRACT" in classification:
                return IntentType.CONTRACT_INFO
            else:
                return IntentType.GENERAL
        except Exception as e:
            print(f"LLM classification failed: {str(e)}. Falling back to keyword matching.")
            return self.classify_intent(query)

    def handle_user_guide_query(self, query: str) -> str:
        """
        Handle user guide related queries using RAG system.

        Args:
            query (str): User query

        Returns:
            str: Generated response
        """
        context = self.rag_system.get_context_for_query(query, k=3)

        system_prompt = self.config.get('chatbot', 'system_prompt', default='')

        prompt = f"""
{system_prompt}

Context from user guides:
{context}

User question: {query}

Please provide a helpful answer based on the context above. If the context does not contain
the information needed, let the customer know and offer to escalate to a human agent.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content

    def handle_contract_query(self, query: str) -> str:
        """
        Handle contract-related queries using SQL system.

        Args:
            query (str): User query

        Returns:
            str: Generated response
        """
        try:
            sql_query, results = self.sql_system.query_and_format(query, self.llm)

            system_prompt = self.config.get('chatbot', 'system_prompt', default='')

            prompt = f"""
{system_prompt}

User question: {query}

Database query results:
{results}

SQL query used: {sql_query}

Please provide a helpful, natural language answer based on the query results above.
If no results were found, let the customer know politely and offer alternatives.
"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            return f"I apologize, but I encountered an error while looking up your contract information. Please contact our support team for assistance. Error: {str(e)}"

    def handle_general_query(self, query: str) -> str:
        """
        Handle general queries that don't fit specific categories.

        Args:
            query (str): User query

        Returns:
            str: Generated response
        """
        system_prompt = self.config.get('chatbot', 'system_prompt', default='')

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        response = self.llm.invoke(messages)
        return response.content

    def process_query(self, query: str, use_llm_classification: bool = False) -> Dict[str, Any]:
        """
        Process a user query end-to-end.

        Args:
            query (str): User query
            use_llm_classification (bool): Use LLM for intent classification

        Returns:
            Dict: Response containing answer, intent, and metadata
        """
        if use_llm_classification:
            intent = self.classify_intent_with_llm(query)
        else:
            intent = self.classify_intent(query)

        if intent == IntentType.USER_GUIDE:
            answer = self.handle_user_guide_query(query)
        elif intent == IntentType.CONTRACT_INFO:
            answer = self.handle_contract_query(query)
        else:
            answer = self.handle_general_query(query)

        if self.memory:
            self.memory.save_context(
                {"input": query},
                {"output": answer}
            )

        return {
            "query": query,
            "intent": intent.value,
            "answer": answer
        }

    def chat(self, query: str) -> str:
        """
        Simple chat interface that returns just the answer.

        Args:
            query (str): User query

        Returns:
            str: Generated answer
        """
        result = self.process_query(query)
        return result["answer"]

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history from memory.

        Returns:
            List[Dict]: List of message dictionaries
        """
        if not self.memory:
            return []

        messages = self.memory.load_memory_variables({}).get('history', [])

        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})

        return history

    def clear_history(self) -> None:
        """
        Clear conversation history.
        """
        if self.memory:
            self.memory.clear()

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get status of all chatbot components.

        Returns:
            Dict: Status information for all components
        """
        return {
            "llm_initialized": self.llm is not None,
            "rag_system_initialized": self.rag_system is not None,
            "sql_system_initialized": self.sql_system is not None,
            "sql_connection_active": self.sql_system.test_connection() if self.sql_system else False,
            "memory_enabled": self.memory is not None,
            "ai_provider": self.config.get('ai_provider', 'provider')
        }
