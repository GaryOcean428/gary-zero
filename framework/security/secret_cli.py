#!/usr/bin/env python3
"""
Command Line Interface for Secret Store Management.

This module provides CLI commands for managing secrets in the Gary-Zero
internal secret store, including add, get, list, update, and delete operations.
"""

import argparse
import getpass
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .secret_store import (
    AccessLevel,
    SecretMetadata,
    SecretStoreConfig,
    SecretType,
    get_secret_store,
    initialize_from_environment,
)


class SecretCLI:
    """Command line interface for secret store operations."""

    def __init__(self):
        """Initialize the CLI."""
        self.store = get_secret_store()

    def add_secret(self, name: str, value: Optional[str] = None, 
                  secret_type: str = "other", access_level: str = "restricted",
                  description: Optional[str] = None, expires_days: Optional[int] = None,
                  rotation_days: Optional[int] = None, tags: Optional[str] = None,
                  overwrite: bool = False) -> bool:
        """
        Add a new secret to the store.
        
        Args:
            name: Name of the secret
            value: Secret value (will prompt if not provided)
            secret_type: Type of secret
            access_level: Access level for the secret
            description: Description of the secret
            expires_days: Days until expiration
            rotation_days: Days between rotations
            tags: Comma-separated tags
            overwrite: Whether to overwrite existing secret
            
        Returns:
            True if successful
        """
        try:
            # Get value if not provided
            if value is None:
                value = getpass.getpass(f"Enter value for secret '{name}': ")
                if not value:
                    print("Error: Secret value cannot be empty")
                    return False
            
            # Parse and validate inputs
            try:
                parsed_type = SecretType(secret_type.lower())
            except ValueError:
                print(f"Error: Invalid secret type '{secret_type}'. Valid types: {[t.value for t in SecretType]}")
                return False
                
            try:
                parsed_access = AccessLevel(access_level.lower())
            except ValueError:
                print(f"Error: Invalid access level '{access_level}'. Valid levels: {[l.value for l in AccessLevel]}")
                return False
            
            # Create metadata
            metadata = SecretMetadata(
                name=name,
                secret_type=parsed_type,
                access_level=parsed_access,
                description=description,
                expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
                rotation_interval_days=rotation_days,
                tags=tags.split(',') if tags else []
            )
            
            # Store the secret
            success = self.store.store_secret(name, value, metadata, overwrite=overwrite)
            
            if success:
                print(f"✓ Secret '{name}' added successfully")
                return True
            else:
                print(f"✗ Failed to add secret '{name}'")
                return False
                
        except Exception as e:
            print(f"✗ Error adding secret: {e}")
            return False

    def get_secret(self, name: str, show_metadata: bool = False) -> bool:
        """
        Retrieve and display a secret.
        
        Args:
            name: Name of the secret
            show_metadata: Whether to show metadata
            
        Returns:
            True if successful
        """
        try:
            value = self.store.get_secret(name)
            
            print(f"Secret '{name}': {value}")
            
            if show_metadata:
                secrets_list = self.store.list_secrets(include_metadata=True)
                metadata = next((s for s in secrets_list if s.name == name), None)
                if metadata:
                    print(f"Type: {metadata.secret_type.value}")
                    print(f"Access Level: {metadata.access_level.value}")
                    print(f"Created: {metadata.created_at}")
                    print(f"Updated: {metadata.updated_at}")
                    if metadata.description:
                        print(f"Description: {metadata.description}")
                    if metadata.expires_at:
                        print(f"Expires: {metadata.expires_at}")
                    if metadata.rotation_interval_days:
                        print(f"Rotation Interval: {metadata.rotation_interval_days} days")
                    if metadata.tags:
                        print(f"Tags: {', '.join(metadata.tags)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error retrieving secret: {e}")
            return False

    def list_secrets(self, show_values: bool = False, format_output: str = "table") -> bool:
        """
        List all secrets in the store.
        
        Args:
            show_values: Whether to show secret values (dangerous!)
            format_output: Output format (table, json)
            
        Returns:
            True if successful
        """
        try:
            secrets_list = self.store.list_secrets(include_metadata=True)
            
            if not secrets_list:
                print("No secrets found in store")
                return True
            
            if format_output == "json":
                output = []
                for metadata in secrets_list:
                    secret_data = metadata.dict()
                    if show_values:
                        secret_data["value"] = self.store.get_secret(metadata.name)
                    output.append(secret_data)
                print(json.dumps(output, indent=2, default=str))
                
            else:  # table format
                print(f"{'Name':<30} {'Type':<15} {'Access':<12} {'Created':<20} {'Description':<40}")
                print("-" * 117)
                
                for metadata in secrets_list:
                    created_str = metadata.created_at.strftime("%Y-%m-%d %H:%M")
                    desc = (metadata.description or "")[:37] + "..." if metadata.description and len(metadata.description) > 40 else (metadata.description or "")
                    
                    print(f"{metadata.name:<30} {metadata.secret_type.value:<15} {metadata.access_level.value:<12} {created_str:<20} {desc:<40}")
                    
                    if show_values:
                        try:
                            value = self.store.get_secret(metadata.name)
                            print(f"    Value: {value}")
                        except Exception as e:
                            print(f"    Value: [Error: {e}]")
                
                print(f"\nTotal: {len(secrets_list)} secrets")
            
            return True
            
        except Exception as e:
            print(f"✗ Error listing secrets: {e}")
            return False

    def update_secret(self, name: str, value: Optional[str] = None,
                     description: Optional[str] = None, expires_days: Optional[int] = None,
                     rotation_days: Optional[int] = None, tags: Optional[str] = None) -> bool:
        """
        Update an existing secret.
        
        Args:
            name: Name of the secret
            value: New secret value (will prompt if not provided)
            description: New description
            expires_days: New expiration in days
            rotation_days: New rotation interval in days
            tags: New comma-separated tags
            
        Returns:
            True if successful
        """
        try:
            # Check if secret exists
            current_value = self.store.get_secret(name)
            
            # Get current metadata
            secrets_list = self.store.list_secrets(include_metadata=True)
            current_metadata = next((s for s in secrets_list if s.name == name), None)
            
            if not current_metadata:
                print(f"✗ Secret '{name}' not found")
                return False
            
            # Get new value if requested
            new_value = current_value
            if value is not None:
                new_value = value
            elif input(f"Update value for '{name}'? (y/N): ").lower() == 'y':
                new_value = getpass.getpass(f"Enter new value for secret '{name}': ")
                if not new_value:
                    print("Keeping current value")
                    new_value = current_value
            
            # Update metadata
            updated_metadata = SecretMetadata(
                name=name,
                secret_type=current_metadata.secret_type,
                access_level=current_metadata.access_level,
                description=description if description is not None else current_metadata.description,
                expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days is not None else current_metadata.expires_at,
                rotation_interval_days=rotation_days if rotation_days is not None else current_metadata.rotation_interval_days,
                tags=tags.split(',') if tags is not None else current_metadata.tags,
                owner=current_metadata.owner
            )
            
            # Store updated secret
            success = self.store.store_secret(name, new_value, updated_metadata, overwrite=True)
            
            if success:
                print(f"✓ Secret '{name}' updated successfully")
                return True
            else:
                print(f"✗ Failed to update secret '{name}'")
                return False
                
        except Exception as e:
            print(f"✗ Error updating secret: {e}")
            return False

    def delete_secret(self, name: str, force: bool = False) -> bool:
        """
        Delete a secret from the store.
        
        Args:
            name: Name of the secret to delete
            force: Skip confirmation prompt
            
        Returns:
            True if successful
        """
        try:
            if not force:
                confirm = input(f"Are you sure you want to delete secret '{name}'? (y/N): ")
                if confirm.lower() != 'y':
                    print("Delete cancelled")
                    return False
            
            success = self.store.delete_secret(name)
            
            if success:
                print(f"✓ Secret '{name}' deleted successfully")
                return True
            else:
                print(f"✗ Failed to delete secret '{name}'")
                return False
                
        except Exception as e:
            print(f"✗ Error deleting secret: {e}")
            return False

    def import_from_env(self, prefix: str = "", overwrite: bool = False) -> bool:
        """
        Import secrets from environment variables.
        
        Args:
            prefix: Only import variables with this prefix
            overwrite: Overwrite existing secrets
            
        Returns:
            True if successful
        """
        try:
            loaded_count = initialize_from_environment(prefix=prefix, overwrite=overwrite)
            print(f"✓ Imported {loaded_count} secrets from environment variables")
            return True
            
        except Exception as e:
            print(f"✗ Error importing from environment: {e}")
            return False

    def export_metadata(self, output_file: Optional[str] = None) -> bool:
        """
        Export secret metadata (without values).
        
        Args:
            output_file: File to write export to (stdout if not provided)
            
        Returns:
            True if successful
        """
        try:
            metadata_export = self.store.export_metadata()
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(metadata_export, f, indent=2, default=str)
                print(f"✓ Metadata exported to {output_file}")
            else:
                print(json.dumps(metadata_export, indent=2, default=str))
            
            return True
            
        except Exception as e:
            print(f"✗ Error exporting metadata: {e}")
            return False

    def cleanup_expired(self) -> bool:
        """
        Clean up expired secrets.
        
        Returns:
            True if successful
        """
        try:
            cleaned_count = self.store.cleanup_expired_secrets()
            print(f"✓ Cleaned up {cleaned_count} expired secrets")
            return True
            
        except Exception as e:
            print(f"✗ Error cleaning up expired secrets: {e}")
            return False

    def check_rotation(self) -> bool:
        """
        Check for secrets needing rotation.
        
        Returns:
            True if successful
        """
        try:
            needing_rotation = self.store.get_secrets_needing_rotation()
            
            if needing_rotation:
                print(f"⚠ {len(needing_rotation)} secrets need rotation:")
                for name in needing_rotation:
                    print(f"  - {name}")
            else:
                print("✓ No secrets need rotation")
            
            return True
            
        except Exception as e:
            print(f"✗ Error checking rotation: {e}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Gary-Zero Secret Store CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add secret command
    add_parser = subparsers.add_parser("add", help="Add a new secret")
    add_parser.add_argument("name", help="Secret name")
    add_parser.add_argument("--value", help="Secret value (will prompt if not provided)")
    add_parser.add_argument("--type", default="other", help="Secret type")
    add_parser.add_argument("--access", default="restricted", help="Access level")
    add_parser.add_argument("--description", help="Description")
    add_parser.add_argument("--expires", type=int, help="Expiration in days")
    add_parser.add_argument("--rotation", type=int, help="Rotation interval in days")
    add_parser.add_argument("--tags", help="Comma-separated tags")
    add_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing secret")

    # Get secret command
    get_parser = subparsers.add_parser("get", help="Get a secret value")
    get_parser.add_argument("name", help="Secret name")
    get_parser.add_argument("--metadata", action="store_true", help="Show metadata")

    # List secrets command
    list_parser = subparsers.add_parser("list", help="List all secrets")
    list_parser.add_argument("--values", action="store_true", help="Show secret values (dangerous!)")
    list_parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    # Update secret command
    update_parser = subparsers.add_parser("update", help="Update an existing secret")
    update_parser.add_argument("name", help="Secret name")
    update_parser.add_argument("--value", help="New secret value")
    update_parser.add_argument("--description", help="New description")
    update_parser.add_argument("--expires", type=int, help="New expiration in days")
    update_parser.add_argument("--rotation", type=int, help="New rotation interval in days")
    update_parser.add_argument("--tags", help="New comma-separated tags")

    # Delete secret command
    delete_parser = subparsers.add_parser("delete", help="Delete a secret")
    delete_parser.add_argument("name", help="Secret name")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")

    # Import from environment command
    import_parser = subparsers.add_parser("import-env", help="Import secrets from environment")
    import_parser.add_argument("--prefix", default="", help="Environment variable prefix")
    import_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing secrets")

    # Export metadata command
    export_parser = subparsers.add_parser("export", help="Export metadata")
    export_parser.add_argument("--output", help="Output file (stdout if not provided)")

    # Cleanup expired command
    subparsers.add_parser("cleanup", help="Clean up expired secrets")

    # Check rotation command
    subparsers.add_parser("rotation", help="Check secrets needing rotation")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = SecretCLI()

    try:
        if args.command == "add":
            success = cli.add_secret(
                args.name, args.value, args.type, args.access,
                args.description, args.expires, args.rotation,
                args.tags, args.overwrite
            )
        elif args.command == "get":
            success = cli.get_secret(args.name, args.metadata)
        elif args.command == "list":
            success = cli.list_secrets(args.values, args.format)
        elif args.command == "update":
            success = cli.update_secret(
                args.name, args.value, args.description,
                args.expires, args.rotation, args.tags
            )
        elif args.command == "delete":
            success = cli.delete_secret(args.name, args.force)
        elif args.command == "import-env":
            success = cli.import_from_env(args.prefix, args.overwrite)
        elif args.command == "export":
            success = cli.export_metadata(args.output)
        elif args.command == "cleanup":
            success = cli.cleanup_expired()
        elif args.command == "rotation":
            success = cli.check_rotation()
        else:
            parser.print_help()
            return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n✗ Operation cancelled")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())