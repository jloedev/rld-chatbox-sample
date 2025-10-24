"""
Data Setup Script

This script helps initialize the chatbot framework with sample data.
It creates sample user guide documents and optionally sets up a sample database.
"""

import os
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta


def create_sample_user_guides():
    """
    Create sample user guide documents for demonstration.
    """
    guides_dir = Path("./data/user_guides")
    guides_dir.mkdir(parents=True, exist_ok=True)

    print("Creating sample user guide documents...")

    # Sample guide 1: Getting Started
    getting_started = """
# Getting Started Guide

Welcome to our software platform. This guide will help you get started quickly.

## First Steps

1. Log in to your account using your credentials
2. Complete your profile setup
3. Explore the dashboard to familiarize yourself with the interface

## Dashboard Overview

The dashboard provides a central view of all your activities:
- Recent activities panel
- Quick action buttons
- System notifications
- Module shortcuts

## Navigation

Use the left sidebar to navigate between different modules:
- Inventory Management
- Reporting Suite
- User Management
- Settings

## Getting Help

If you need assistance:
- Click the Help icon in the top right corner
- Search our knowledge base
- Contact support via the chat widget
"""

    # Sample guide 2: Inventory Module
    inventory_guide = """
# Inventory Management Module

The Inventory Management module helps you track and manage your product inventory.

## Adding New Items

To add a new inventory item:
1. Navigate to Inventory > Add New Item
2. Fill in the item details (name, SKU, quantity, price)
3. Upload product images if available
4. Set reorder thresholds
5. Click Save

## Viewing Inventory

Access your inventory list:
- Go to Inventory > View All Items
- Use filters to narrow down results
- Sort by different columns (name, quantity, price)
- Export data to CSV or Excel

## Managing Stock Levels

Monitor and update stock levels:
- View current stock quantities
- Set low stock alerts
- Receive notifications when items need reordering
- Update quantities after receiving shipments

## Inventory Reports

Generate inventory reports:
1. Go to Inventory > Reports
2. Select report type (stock levels, movement, valuation)
3. Choose date range
4. Generate and download report
"""

    # Sample guide 3: Reporting Suite
    reporting_guide = """
# Reporting Suite

Create comprehensive reports to analyze your business data.

## Report Types

Available report types:
- Sales reports
- Inventory reports
- Customer activity reports
- Financial summaries
- Custom reports

## Creating Reports

To create a new report:
1. Navigate to Reports > Create New
2. Select report template or start from scratch
3. Choose data sources
4. Configure filters and parameters
5. Preview the report
6. Save or export

## Exporting Reports

Export reports in multiple formats:
- PDF for sharing and printing
- Excel for further analysis
- CSV for data import
- JSON for API integration

Steps to export:
1. Open the report you want to export
2. Click the Export button
3. Select format (PDF, Excel, CSV)
4. Choose export options
5. Download file

## Scheduling Reports

Set up automated report generation:
1. Open the report
2. Click Schedule button
3. Set frequency (daily, weekly, monthly)
4. Choose recipients
5. Configure delivery options (email, save to folder)
6. Activate schedule

## Report Customization

Customize reports to meet your needs:
- Add or remove columns
- Apply custom filters
- Create calculated fields
- Set up conditional formatting
- Add charts and visualizations
"""

    # Sample guide 4: User Management
    user_management = """
# User Management

Manage user accounts and permissions for your organization.

## Adding Users

To add a new user:
1. Go to Settings > User Management
2. Click Add New User
3. Enter user details (name, email, role)
4. Set permissions and module access
5. Send invitation email

## User Roles

Available user roles:
- Administrator: Full system access
- Manager: Access to all modules, limited admin functions
- User: Standard access to assigned modules
- Viewer: Read-only access

## Managing Permissions

Configure user permissions:
1. Select user from user list
2. Click Edit Permissions
3. Enable or disable module access
4. Set specific feature permissions
5. Save changes

## Deactivating Users

To deactivate a user account:
1. Go to User Management
2. Find the user
3. Click Deactivate
4. Confirm action
5. User will lose access immediately
"""

    guides = {
        "getting_started.md": getting_started,
        "inventory_module.md": inventory_guide,
        "reporting_suite.md": reporting_guide,
        "user_management.md": user_management
    }

    for filename, content in guides.items():
        file_path = guides_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  Created: {file_path}")

    print(f"\nCreated {len(guides)} sample user guide documents in {guides_dir}")


def create_sample_database():
    """
    Create a sample SQLite database with contract information.
    """
    db_path = Path("./data/contracts.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print("\nCreating sample database...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create contracts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            contract_id INTEGER PRIMARY KEY,
            customer_name VARCHAR(255),
            expiration_date DATE,
            pricing DECIMAL(10, 2),
            status VARCHAR(50)
        )
    """)

    # Create modules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            module_id INTEGER PRIMARY KEY,
            module_name VARCHAR(255),
            description TEXT
        )
    """)

    # Create contract_modules junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contract_modules (
            contract_id INTEGER,
            module_id INTEGER,
            purchased_date DATE,
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id),
            FOREIGN KEY (module_id) REFERENCES modules(module_id)
        )
    """)

    # Insert sample contracts
    contracts = [
        (1, "ACME Corp", "2024-12-31", 25000.00, "Active"),
        (2, "TechStart Inc", "2024-06-30", 15000.00, "Active"),
        (3, "Global Industries", "2025-03-15", 50000.00, "Active"),
        (4, "Small Business LLC", "2024-01-31", 8000.00, "Expiring Soon"),
        (5, "Enterprise Solutions", "2025-12-31", 100000.00, "Active")
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO contracts
        (contract_id, customer_name, expiration_date, pricing, status)
        VALUES (?, ?, ?, ?, ?)
    """, contracts)

    # Insert sample modules
    modules = [
        (1, "Inventory Management", "Comprehensive inventory tracking and management system"),
        (2, "Reporting Suite", "Advanced reporting and analytics tools"),
        (3, "User Management", "User access control and permission management"),
        (4, "API Access", "RESTful API for third-party integrations"),
        (5, "Mobile App", "Native mobile applications for iOS and Android"),
        (6, "Advanced Analytics", "Machine learning powered analytics and predictions"),
        (7, "Customer Portal", "Self-service portal for customers")
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO modules
        (module_id, module_name, description)
        VALUES (?, ?, ?)
    """, modules)

    # Insert sample contract-module relationships
    contract_modules = [
        (1, 1, "2023-01-15"),  # ACME Corp - Inventory Management
        (1, 2, "2023-01-15"),  # ACME Corp - Reporting Suite
        (2, 1, "2023-06-01"),  # TechStart - Inventory Management
        (2, 3, "2023-06-01"),  # TechStart - User Management
        (3, 1, "2023-03-10"),  # Global Industries - Inventory Management
        (3, 2, "2023-03-10"),  # Global Industries - Reporting Suite
        (3, 4, "2023-03-10"),  # Global Industries - API Access
        (3, 6, "2023-09-01"),  # Global Industries - Advanced Analytics
        (4, 1, "2023-02-01"),  # Small Business - Inventory Management
        (5, 1, "2024-01-01"),  # Enterprise - Inventory Management
        (5, 2, "2024-01-01"),  # Enterprise - Reporting Suite
        (5, 3, "2024-01-01"),  # Enterprise - User Management
        (5, 4, "2024-01-01"),  # Enterprise - API Access
        (5, 5, "2024-01-01"),  # Enterprise - Mobile App
        (5, 6, "2024-01-01"),  # Enterprise - Advanced Analytics
        (5, 7, "2024-01-01"),  # Enterprise - Customer Portal
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO contract_modules
        (contract_id, module_id, purchased_date)
        VALUES (?, ?, ?)
    """, contract_modules)

    conn.commit()
    conn.close()

    print(f"  Created database: {db_path}")
    print(f"  Inserted {len(contracts)} contracts")
    print(f"  Inserted {len(modules)} modules")
    print(f"  Inserted {len(contract_modules)} contract-module relationships")


def update_config_for_sqlite():
    """
    Update config.yaml to use SQLite database if it exists.
    """
    config_path = Path("config.yaml")

    if not config_path.exists():
        print("\nWarning: config.yaml not found. Skipping database configuration update.")
        return

    print("\nTo use the sample SQLite database, update your config.yaml:")
    print("\nsql_database:")
    print("  type: 'sqlite'")
    print("  database: './data/contracts.db'")
    print("\nOr you can keep using your existing database configuration.")


def main():
    """
    Main setup function.
    """
    print("Customer Service Chatbot - Data Setup")
    print("=" * 80)
    print()

    create_sample_user_guides()
    create_sample_database()
    update_config_for_sqlite()

    print("\n" + "=" * 80)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Review and update config.yaml if needed")
    print("2. Set up your .env file with API keys")
    print("3. Run 'python main.py check' to verify configuration")
    print("4. Run 'python main.py' to start chatting")


if __name__ == "__main__":
    main()
