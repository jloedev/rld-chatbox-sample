"""
SQL Query System Module

This module handles natural language to SQL conversion and query execution
for contract-related questions.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase


class SQLQuerySystem:
    """
    Manages natural language to SQL conversion and execution for contract data.

    This system translates user questions about contracts into SQL queries,
    executes them safely, and formats the results.

    Attributes:
        config (Dict): SQL database configuration
        engine (Engine): SQLAlchemy database engine
        db (SQLDatabase): LangChain SQL database wrapper
        schema_description (str): Human-readable schema description
    """

    def __init__(self, sql_config: Dict[str, Any]):
        """
        Initialize the SQL query system.

        Args:
            sql_config (Dict): SQL database configuration
        """
        self.config = sql_config
        self.engine = None
        self.db = None
        self.schema_description = sql_config.get('schema_description', '')

        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """
        Initialize database connection.

        Creates SQLAlchemy engine and LangChain SQLDatabase wrapper.

        Raises:
            ValueError: If database type is not supported
        """
        db_type = self.config.get('type', 'postgresql').lower()

        if db_type == 'postgresql':
            connection_string = self._build_postgres_connection_string()
        elif db_type == 'mysql':
            connection_string = self._build_mysql_connection_string()
        elif db_type == 'sqlite':
            connection_string = self._build_sqlite_connection_string()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        try:
            self.engine = create_engine(connection_string)
            self.db = SQLDatabase(self.engine)
        except Exception as e:
            print(f"Warning: Database connection failed: {str(e)}")
            print("SQL query system will operate in mock mode.")
            self.engine = None
            self.db = None

    def _build_postgres_connection_string(self) -> str:
        """
        Build PostgreSQL connection string.

        Returns:
            str: PostgreSQL connection string
        """
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 5432)
        database = self.config.get('database', '')
        username = self.config.get('username', '')
        password = self.config.get('password', '')

        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    def _build_mysql_connection_string(self) -> str:
        """
        Build MySQL connection string.

        Returns:
            str: MySQL connection string
        """
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 3306)
        database = self.config.get('database', '')
        username = self.config.get('username', '')
        password = self.config.get('password', '')

        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

    def _build_sqlite_connection_string(self) -> str:
        """
        Build SQLite connection string.

        Returns:
            str: SQLite connection string
        """
        database = self.config.get('database', 'contracts.db')
        return f"sqlite:///{database}"

    def get_table_info(self) -> str:
        """
        Get information about database tables and schema.

        Returns:
            str: Formatted table information
        """
        if self.db is None:
            return self.schema_description

        try:
            return self.db.get_table_info()
        except Exception as e:
            return f"Unable to retrieve table info: {str(e)}\n\n{self.schema_description}"

    def natural_language_to_sql(self, question: str, llm) -> str:
        """
        Convert natural language question to SQL query.

        Args:
            question (str): Natural language question
            llm: Language model for query generation

        Returns:
            str: Generated SQL query
        """
        if self.db is None:
            return self._generate_mock_sql(question)

        try:
            chain = create_sql_query_chain(llm, self.db)
            sql_query = chain.invoke({"question": question})

            # Clean up the SQL query by removing common prefixes and explanations
            if isinstance(sql_query, str):
                sql_query = sql_query.strip()

                # If there's a "SQLQuery:" marker, extract everything after it
                if 'SQLQuery:' in sql_query:
                    sql_query = sql_query.split('SQLQuery:', 1)[1].strip()

                # Remove code block markers
                if sql_query.startswith('```sql'):
                    sql_query = sql_query[6:].strip()
                elif sql_query.startswith('```'):
                    sql_query = sql_query[3:].strip()

                if sql_query.endswith('```'):
                    sql_query = sql_query[:-3].strip()

                # Remove other common prefixes if they're still at the start
                prefixes_to_remove = ['SQL:', 'Query:', 'sql:', 'query:']
                for prefix in prefixes_to_remove:
                    if sql_query.startswith(prefix):
                        sql_query = sql_query[len(prefix):].strip()
                        break

                # Extract only the SQL statement (starts with SELECT, INSERT, UPDATE, DELETE, WITH)
                # This removes any explanation text before the query
                import re
                sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'CREATE', 'DROP', 'ALTER']
                for keyword in sql_keywords:
                    pattern = f'({keyword}\\s+.*)'
                    match = re.search(pattern, sql_query, re.IGNORECASE | re.DOTALL)
                    if match:
                        sql_query = match.group(1).strip()
                        break

            return sql_query
        except Exception as e:
            print(f"Error generating SQL: {str(e)}")
            return ""

    def _generate_mock_sql(self, question: str) -> str:
        """
        Generate mock SQL query for demonstration purposes.

        Args:
            question (str): Natural language question

        Returns:
            str: Mock SQL query
        """
        question_lower = question.lower()

        if 'expiration' in question_lower or 'expires' in question_lower:
            return "SELECT contract_id, customer_name, expiration_date FROM contracts WHERE customer_name = 'Customer Name';"
        elif 'modules' in question_lower or 'purchased' in question_lower:
            return """
SELECT c.customer_name, m.module_name, cm.purchased_date
FROM contracts c
JOIN contract_modules cm ON c.contract_id = cm.contract_id
JOIN modules m ON cm.module_id = m.module_id
WHERE c.customer_name = 'Customer Name';
"""
        elif 'pricing' in question_lower or 'cost' in question_lower:
            return "SELECT customer_name, pricing FROM contracts WHERE customer_name = 'Customer Name';"
        else:
            return "SELECT * FROM contracts WHERE customer_name = 'Customer Name' LIMIT 5;"

    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.

        Args:
            sql_query (str): SQL query to execute

        Returns:
            List[Dict]: Query results as list of dictionaries

        Raises:
            ValueError: If query contains unsafe operations
        """
        if not self._is_safe_query(sql_query):
            raise ValueError("Query contains unsafe operations (INSERT, UPDATE, DELETE, DROP)")

        if self.engine is None:
            return self._generate_mock_results(sql_query)

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                columns = result.keys()
                rows = result.fetchall()

                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return []

    def _is_safe_query(self, sql_query: str) -> bool:
        """
        Check if SQL query is safe (read-only).

        Args:
            sql_query (str): SQL query to check

        Returns:
            bool: True if query is safe, False otherwise
        """
        unsafe_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = sql_query.upper()

        return not any(keyword in query_upper for keyword in unsafe_keywords)

    def _generate_mock_results(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Generate mock results for demonstration purposes.

        Args:
            sql_query (str): SQL query

        Returns:
            List[Dict]: Mock results
        """
        if 'modules' in sql_query.lower():
            return [
                {
                    'customer_name': 'ACME Corp',
                    'module_name': 'Inventory Management',
                    'purchased_date': '2023-01-15'
                },
                {
                    'customer_name': 'ACME Corp',
                    'module_name': 'Reporting Suite',
                    'purchased_date': '2023-03-22'
                }
            ]
        elif 'expiration' in sql_query.lower():
            return [
                {
                    'contract_id': 12345,
                    'customer_name': 'ACME Corp',
                    'expiration_date': '2024-12-31'
                }
            ]
        elif 'pricing' in sql_query.lower():
            return [
                {
                    'customer_name': 'ACME Corp',
                    'pricing': 25000.00
                }
            ]
        else:
            return [
                {
                    'contract_id': 12345,
                    'customer_name': 'ACME Corp',
                    'expiration_date': '2024-12-31',
                    'pricing': 25000.00,
                    'status': 'Active'
                }
            ]

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format query results as human-readable text.

        Args:
            results (List[Dict]): Query results

        Returns:
            str: Formatted results
        """
        if not results:
            return "No results found."

        if len(results) == 1:
            result = results[0]
            lines = [f"{key}: {value}" for key, value in result.items()]
            return "\n".join(lines)
        else:
            formatted = []
            for i, result in enumerate(results, 1):
                formatted.append(f"\nResult {i}:")
                for key, value in result.items():
                    formatted.append(f"  {key}: {value}")
            return "\n".join(formatted)

    def query_and_format(self, question: str, llm) -> tuple[str, str]:
        """
        Convert question to SQL, execute, and format results.

        Args:
            question (str): Natural language question
            llm: Language model for query generation

        Returns:
            tuple: (SQL query, formatted results)
        """
        sql_query = self.natural_language_to_sql(question, llm)
        results = self.execute_query(sql_query)
        formatted_results = self.format_results(results)

        return sql_query, formatted_results

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        if self.engine is None:
            return False

        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False
