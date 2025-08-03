#!/usr/bin/env python3
"""
OpenSim IAR Full Permissions Script
===================================

This script applies full permissions to all XML files in a folder (and subfolders).
It's designed to work with OpenSim IAR (Inventory Archive) files.

Usage:
    python apply_full_perms.py [folder_path] [options]

Options:
    --max-perms    Use maximum possible permissions (2147483647)
    --standard     Use standard full perms (581639) - default
    --everyone     Set EveryonePermissions (default: 32768 - Copy only)
    --next         Set NextPermissions (default: 2147483647 - Full permissions)
    --recursive    Process subdirectories recursively
    --backup       Create backup files before modifying
    --dry-run      Show what would be changed without making changes
    --help         Show this help message

Examples:
    python apply_full_perms.py inventory/
    python apply_full_perms.py inventory/ --max-perms --recursive
    python apply_full_perms.py inventory/ --standard --backup --dry-run
"""

import os
import sys
import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

# Permission constants
PERMISSIONS = {
    'max': {
        'base': 2147483647,
        'current': 2147483647,
        'everyone': 32768,  # Copy only
        'next': 2147483647
    },
    'standard': {
        'base': 581639,      # Standard full permissions
        'current': 581639,   # Standard full permissions
        'everyone': 32768,   # Copy only
        'next': 581632       # Standard full permissions (slightly reduced)
    }
}

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Apply full permissions to OpenSim IAR XML files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('folder', nargs='?', default='.',
                       help='Folder containing XML files to process (default: current directory)')
    
    parser.add_argument('--max-perms', action='store_true',
                       help='Use maximum possible permissions (2147483647)')
    parser.add_argument('--standard', action='store_true',
                       help='Use standard full perms (581639) - default')
    parser.add_argument('--everyone', type=int, default=32768,
                       help='Set EveryonePermissions (default: 32768 - Copy only)')
    parser.add_argument('--next', type=int, default=581632,
                       help='Set NextPermissions (default: 581632 - Standard full permissions)')
    parser.add_argument('--recursive', '-r', action='store_true', default=True,
                       help='Process subdirectories recursively (default: True)')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Disable recursive processing')
    parser.add_argument('--backup', '-b', action='store_true',
                       help='Create backup files before modifying')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be changed without making changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    parser.add_argument('--no-confirm', action='store_true',
                       help='Skip confirmation prompt')
    
    return parser.parse_args()

def get_permission_values(args):
    """Get the permission values to apply based on arguments."""
    if args.max_perms:
        perms = PERMISSIONS['max'].copy()
    else:
        perms = PERMISSIONS['standard'].copy()
    
    # Override with command line values if specified
    perms['everyone'] = args.everyone
    perms['next'] = args.next
    
    return perms

def get_recursive_setting(args):
    """Get the recursive setting based on arguments."""
    if args.no_recursive:
        return False
    return True  # Default to True

def find_xml_files(folder_path, recursive=False):
    """Find all XML files in the given folder."""
    xml_files = []
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist.")
        return []
    
    if recursive:
        pattern = "**/*.xml"
    else:
        pattern = "*.xml"
    
    for xml_file in folder.glob(pattern):
        if xml_file.is_file():
            xml_files.append(xml_file)
    
    return sorted(xml_files)

def backup_file(file_path):
    """Create a backup of the file."""
    backup_path = file_path.with_suffix('.xml.backup')
    shutil.copy2(file_path, backup_path)
    return backup_path

def is_inventory_item_xml(file_path):
    """Check if the XML file is an OpenSim inventory item."""
    try:
        # Try different encodings since IAR files can have encoding issues
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # Remove the encoding declaration to avoid conflicts
                    if content.startswith('<?xml'):
                        lines = content.split('\n', 1)
                        if len(lines) > 1:
                            content = lines[1]
                    root = ET.fromstring(content)
                    return root.tag == 'InventoryItem'
            except (UnicodeDecodeError, ET.ParseError):
                continue
        
        return False
    except Exception:
        return False

def apply_permissions_to_xml(file_path, permissions, dry_run=False, verbose=False):
    """Apply permissions to a single XML file."""
    try:
        # Try different encodings since IAR files can have encoding issues
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    used_encoding = encoding
                    break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return False, "Could not read file with any encoding"
        
        # Remove the encoding declaration to avoid conflicts
        original_declaration = None
        if content.startswith('<?xml'):
            lines = content.split('\n', 1)
            if len(lines) > 1:
                original_declaration = lines[0]
                content = lines[1]
        
        root = ET.fromstring(content)
        
        if root.tag != 'InventoryItem':
            if verbose:
                print(f"Skipping {file_path.name} - not an InventoryItem XML")
            return False, "Not an InventoryItem XML"
        
        changes_made = []
        
        # Apply permissions to each permission field
        permission_fields = {
            'BasePermissions': permissions['base'],
            'CurrentPermissions': permissions['current'],
            'EveryOnePermissions': permissions['everyone'],
            'NextPermissions': permissions['next']
        }
        
        # Apply additional fields to ensure proper configuration
        additional_fields = {
            'SaleType': '0',
            'SalePrice': '0',
            'GroupID': '00000000-0000-0000-0000-000000000000',
            'GroupOwned': 'False',
            'CreatorUUID': 'ospa:n=Gene Freenote'
        }
        
        # Apply permission changes
        for field_name, new_value in permission_fields.items():
            field = root.find(field_name)
            if field is not None:
                old_value = field.text
                if old_value != str(new_value):
                    if not dry_run:
                        field.text = str(new_value)
                    changes_made.append(f"{field_name}: {old_value} -> {new_value}")
        
        # Apply additional field changes
        for field_name, new_value in additional_fields.items():
            field = root.find(field_name)
            if field is not None:
                old_value = field.text
                if old_value != str(new_value):
                    if not dry_run:
                        field.text = str(new_value)
                    changes_made.append(f"{field_name}: {old_value} -> {new_value}")
        
        # Apply Flags bitwise operations to remove unwanted flags
        flags_field = root.find('Flags')
        if flags_field is not None:
            try:
                old_flags = int(flags_field.text)
                
                # Define bits to clear (remove these flags)
                # Bit 12 (4096): No-modify  
                # Bit 13 (8192): No-transfer
                # Bit 21 (2097152): For sale
                # Bit 22 (4194304): For sale (additional)
                # Bit 23 (8388608): For sale (additional)
                # Bit 24 (16777216): For sale (additional)
                # Keep bit 8 (256): Container flag - DO NOT CLEAR (working examples have this)
                # Keep bit 20 (1048576): Container flag - DO NOT CLEAR
                # 0x1E00000 = bits 21-24 (2097152 + 4194304 + 8388608 + 16777216)
                # 0x3000 = bits 12-13 (4096 + 8192)
                bits_to_clear = 0x1E3300  # 2097152 + 4194304 + 8388608 + 16777216 + 4096 + 8192 = 31469568
                
                new_flags = old_flags & ~bits_to_clear
                
                if old_flags != new_flags:
                    if not dry_run:
                        flags_field.text = str(new_flags)
                    changes_made.append(f"Flags: {old_flags} -> {new_flags} (cleared bits 12-13, 21-24, preserved bit 8)")
                    
            except ValueError:
                # If flags field is not a valid integer, skip it
                if verbose:
                    print(f"Warning: Invalid Flags value '{flags_field.text}' in {file_path.name}")
                pass
        
        if changes_made:
            if not dry_run:
                # Reconstruct the XML with proper formatting
                tree = ET.ElementTree(root)
                
                # Create the XML content with original declaration but save as UTF-8
                # This preserves the "utf-16" declaration in the XML while actually saving as UTF-8
                xml_content = '<?xml version="1.0" encoding="utf-16"?>\n'
                xml_content += ET.tostring(root, encoding='unicode')
                
                # Write the file as UTF-8 (without BOM) but keep the utf-16 declaration
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
            
            if verbose:
                print(f"Modified {file_path.name}:")
                for change in changes_made:
                    print(f"  {change}")
            
            return True, changes_made
        else:
            if verbose:
                print(f"No changes needed for {file_path.name}")
            return False, "No changes needed"
            
    except ET.ParseError as e:
        return False, f"XML parse error: {e}"
    except Exception as e:
        return False, f"Error processing file: {e}"

def main():
    """Main function."""
    args = parse_arguments()
    
    # Get permission values and settings
    permissions = get_permission_values(args)
    recursive = get_recursive_setting(args)
    
    # Find XML files
    xml_files = find_xml_files(args.folder, recursive)
    
    if not xml_files:
        print(f"No XML files found in '{args.folder}'")
        return
    
    print(f"Found {len(xml_files)} XML files to process")
    print(f"Using permissions: {permissions}")
    print(f"Recursive processing: {recursive}")
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
    
    # Show what will be done and ask for confirmation (unless --no-confirm or --dry-run)
    if not args.dry_run and not args.no_confirm:
        print(f"\nAbout to modify {len(xml_files)} files with standard full permissions.")
        print("This will set:")
        print(f"  BasePermissions: {permissions['base']}")
        print(f"  CurrentPermissions: {permissions['current']}")
        print(f"  EveryOnePermissions: {permissions['everyone']}")
        print(f"  NextPermissions: {permissions['next']}")
        print("  SaleType: 0 (not for sale)")
        print("  SalePrice: 0")
        print("  GroupID: 00000000-0000-0000-0000-000000000000 (no group)")
        print("  GroupOwned: False")
        print("  Flags: Will clear bits 8 (no-copy), 12 (no-modify), and 19-24 (for-sale, no-transfer, etc.)")
        
        if args.backup:
            print("Backup files will be created.")
        
        response = input("\nContinue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return
    
    # Process each XML file
    processed_count = 0
    modified_count = 0
    skipped_count = 0
    
    for xml_file in xml_files:
        processed_count += 1
        
        # Check if it's an inventory item XML
        if not is_inventory_item_xml(xml_file):
            if args.verbose:
                print(f"Skipping {xml_file.name} - not an InventoryItem XML")
            skipped_count += 1
            continue
        
        # Create backup if requested
        if args.backup and not args.dry_run:
            backup_path = backup_file(xml_file)
            if args.verbose:
                print(f"Created backup: {backup_path.name}")
        
        # Apply permissions
        success, result = apply_permissions_to_xml(
            xml_file, permissions, args.dry_run, args.verbose
        )
        
        if success:
            modified_count += 1
        else:
            skipped_count += 1
            if args.verbose:
                print(f"Skipped {xml_file.name}: {result}")
    
    # Summary
    print(f"\nSummary:")
    print(f"  Files processed: {processed_count}")
    print(f"  Files modified: {modified_count}")
    print(f"  Files skipped: {skipped_count}")
    
    if args.dry_run and modified_count > 0:
        print(f"\nDRY RUN: {modified_count} files would have been modified")
    elif modified_count > 0:
        print(f"\nSuccessfully modified {modified_count} files")

if __name__ == "__main__":
    main() 
