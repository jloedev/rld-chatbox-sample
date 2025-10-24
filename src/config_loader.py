"""
Configuration Loader Module

This module handles loading and parsing the configuration file,
including environment variable substitution.
"""

import os
import re
import yaml
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv


class ConfigLoader:
    """
    Loads and manages configuration from YAML file with environment variable support.

    Attributes:
        config_path (Path): Path to the configuration file
        config (Dict): Parsed configuration dictionary
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration loader.

        Args:
            config_path (str): Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = None
        self._load_env()
        self._load_config()

    def _load_env(self) -> None:
        """
        Load environment variables from .env file if it exists.
        """
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)

    def _load_config(self) -> None:
        """
        Load and parse the YAML configuration file.

        Raises:
            FileNotFoundError: If configuration file does not exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as file:
            raw_config = yaml.safe_load(file)

        self.config = self._substitute_env_vars(raw_config)

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in configuration values.

        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.

        Args:
            config (Any): Configuration value (can be dict, list, str, etc.)

        Returns:
            Any: Configuration with environment variables substituted
        """
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_string(config)
        else:
            return config

    def _substitute_string(self, value: str) -> str:
        """
        Substitute environment variables in a string.

        Args:
            value (str): String potentially containing ${VAR_NAME} patterns

        Returns:
            str: String with environment variables substituted
        """
        pattern = r'\$\{([^}:]+)(?::([^}]+))?\}'

        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""
            return os.getenv(var_name, default_value)

        return re.sub(pattern, replacer, value)

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            *keys: Configuration key path (e.g., 'ai_provider', 'openai', 'model')
            default: Default value if key not found

        Returns:
            Any: Configuration value or default
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_ai_provider_config(self) -> Dict[str, Any]:
        """
        Get the active AI provider configuration.

        Returns:
            Dict: Configuration for the selected AI provider
        """
        provider = self.get('ai_provider', 'provider')
        provider_config = self.get('ai_provider', provider, default={})
        return {
            'provider': provider,
            **provider_config
        }

    def get_vector_store_config(self) -> Dict[str, Any]:
        """
        Get vector store configuration.

        Returns:
            Dict: Vector store configuration
        """
        return self.get('vector_store', default={})

    def get_sql_config(self) -> Dict[str, Any]:
        """
        Get SQL database configuration.

        Returns:
            Dict: SQL database configuration
        """
        return self.get('sql_database', default={})

    def get_intent_keywords(self) -> Dict[str, list]:
        """
        Get intent classification keywords.

        Returns:
            Dict: Dictionary with user_guide_keywords and contract_keywords lists
        """
        return {
            'user_guide': self.get('intent_classification', 'user_guide_keywords', default=[]),
            'contract': self.get('intent_classification', 'contract_keywords', default=[])
        }

    def get_chatbot_config(self) -> Dict[str, Any]:
        """
        Get general chatbot configuration.

        Returns:
            Dict: Chatbot configuration
        """
        return self.get('chatbot', default={})

    def reload(self) -> None:
        """
        Reload the configuration from file.
        Useful for updating configuration without restarting the application.
        """
        self._load_env()
        self._load_config()
