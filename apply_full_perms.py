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
import re
import uuid
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
            'GroupOwned': 'False'
        }
		#,
        #    'CreatorUUID': 'ospa:n=YourName Resident'
        
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

def sanitize_lsl_scripts(folder_path, dry_run=False, verbose=False):
    """
    Scan for and disable LSL scripts that auto-delete items based on permissions.
    Detects scripts that call llDie() when certain permissions are detected.
    """
    # Patterns that indicate auto-delete scripts
    suspicious_patterns = [
        r'llDie\s*\(',  # llDie() calls
        r'PERM_TRANSFER.*llDie',  # Transfer check -> die
        r'PERM_COPY.*llDie',  # Copy check -> die
        r'PERM_MODIFY.*llDie',  # Modify check -> die
        r'MASK_NEXT.*llDie',  # Next owner perms -> die
        r'MASK_EVERYONE.*llDie',  # Everyone perms -> die
    ]
    
    # Find all .lsl files in assets directory
    assets_dir = Path(folder_path) / 'assets'
    if not assets_dir.exists():
        if verbose:
            print(f"Assets directory not found: {assets_dir}")
        return 0
    
    lsl_files = list(assets_dir.glob('*.lsl'))
    # Also check for text files that might be scripts (some IARs don't use .lsl extension)
    # But be conservative - only process if they contain LSL keywords
    text_files = []
    for ext in ['', '.txt']:
        for f in assets_dir.glob(f'*{ext}'):
            if f.is_file() and f not in lsl_files:
                try:
                    with open(f, 'r', encoding='utf-8', errors='ignore') as test_file:
                        content = test_file.read(500)  # Read first 500 chars
                        if 'll' in content.lower() and ('function' in content.lower() or 'default' in content.lower()):
                            text_files.append(f)
                except:
                    pass
    
    all_script_files = lsl_files + text_files
    disabled_count = 0
    
    for script_file in all_script_files:
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(script_file, 'r', encoding=encoding) as f:
                        content = f.read()
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                if verbose:
                    print(f"Could not read {script_file.name} with any encoding")
                continue
            
            # Remove null bytes that can cause script reset issues
            original_content = content
            content = content.replace('\x00', '')
            had_null_bytes = (original_content != content)
            
            # Check if this script contains suspicious patterns
            is_suspicious = False
            matched_patterns = []
            
            # Check for llDie() calls (most direct indicator)
            llDie_matches = list(re.finditer(r'llDie\s*\(', content, re.IGNORECASE))
            if llDie_matches:
                is_suspicious = True
                matched_patterns.append(f'llDie() calls found: {len(llDie_matches)}')
            
            # Check for permission checks followed by llDie
            for pattern in suspicious_patterns[1:]:  # Skip the first one (llDie) as we already checked
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    is_suspicious = True
                    matched_patterns.append(pattern)
            
            # Additional check: look for the specific pattern from the example
            # Check for permission mask checks followed by llDie
            if re.search(r'(PERM_TRANSFER|PERM_COPY|PERM_MODIFY).*?llDie', content, re.IGNORECASE | re.DOTALL):
                is_suspicious = True
                if 'permission_check_then_die' not in matched_patterns:
                    matched_patterns.append('permission_check_then_die')
            
            if is_suspicious:
                if verbose:
                    print(f"⚠️  Suspicious script detected: {script_file.name}")
                    print(f"   Matched patterns: {', '.join(matched_patterns)}")
                    if had_null_bytes:
                        print(f"   Removed null bytes from script")
                
                if not dry_run:
                    # Simple approach: comment out problematic lines
                    # Split into lines to make replacements easier
                    lines = content.split('\n')
                    changes_made = []
                    lines_to_comment = set()
                    
                    # Find and comment out llDie() calls and their containing if statements
                    for match in llDie_matches:
                        start_pos = match.start()
                        line_num = content[:start_pos].count('\n')
                        if line_num < len(lines):
                            line = lines[line_num]
                            if not line.strip().startswith('//') and 'llDie' in line:
                                # Comment out the llDie line
                                lines_to_comment.add(line_num)
                                changes_made.append(f"llDie() call")
                                
                                # Look backwards for the if statement
                                for prev_line_num in range(line_num - 1, max(-1, line_num - 5), -1):
                                    if prev_line_num < 0:
                                        break
                                    prev_line = lines[prev_line_num].strip()
                                    if not prev_line or prev_line.startswith('//'):
                                        continue
                                    if (prev_line.startswith('if') and 
                                        ('PERM_' in prev_line or 'MASK_' in prev_line) and
                                        not prev_line.startswith('//')):
                                        lines_to_comment.add(prev_line_num)
                                        changes_made.append(f"if statement with permission check")
                                        break
                                    if prev_line.startswith('}') or 'function' in prev_line.lower():
                                        break
                    
                    # Find and comment out CheckPerms() calls (not function definitions)
                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        if 'CheckPerms' in stripped and '(' in stripped and not stripped.startswith('//'):
                            # It's a call if it's not a function definition (no opening brace on same/next line)
                            is_definition = False
                            if '{' in line:
                                is_definition = True
                            else:
                                # Check next few lines for opening brace
                                for j in range(i + 1, min(i + 3, len(lines))):
                                    if '{' in lines[j] and not lines[j].strip().startswith('//'):
                                        is_definition = True
                                        break
                                    if lines[j].strip() and not lines[j].strip().startswith('//'):
                                        break
                            
                            if not is_definition:
                                lines_to_comment.add(i)
                                changes_made.append(f"CheckPerms() call")
                    
                    # Note: We intentionally do NOT comment out llResetScript() calls
                    # because they help reset the script state and force reload of sanitized code
                    
                    # Comment out all identified lines
                    for line_num in sorted(lines_to_comment, reverse=True):
                        line = lines[line_num]
                        indentation = len(line) - len(line.lstrip())
                        commented_line = ' ' * indentation + '// DISABLED BY IAR FIXER: ' + line.lstrip()
                        lines[line_num] = commented_line
                    
                    # Reconstruct the content
                    sanitized_content = '\n'.join(lines)
                    
                    # Add header comment if we made changes
                    if changes_made:
                        unique_changes = list(set(changes_made))  # Remove duplicates
                        header = "/* DISABLED BY IAR FIXER - Auto-delete script detected\n"
                        header += f"   Disabled: {', '.join(unique_changes)}\n"
                        if had_null_bytes:
                            header += "   Removed null bytes\n"
                        header += "*/\n\n"
                        sanitized_content = header + sanitized_content
                    
                    # Write back with the same encoding we used to read, but always as UTF-8 to avoid null bytes
                    with open(script_file, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(sanitized_content)
                    
                    if verbose:
                        print(f"   ✓ Disabled {len(llDie_matches)} llDie() call(s)")
                        if had_null_bytes:
                            print(f"   ✓ Removed null bytes")
                
                disabled_count += 1
            elif had_null_bytes:
                # Even if not suspicious, remove null bytes
                if not dry_run:
                    with open(script_file, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(content)
                    if verbose:
                        print(f"✓ Cleaned null bytes from {script_file.name}")
            elif verbose:
                print(f"✓ Safe script: {script_file.name}")
                
        except Exception as e:
            if verbose:
                print(f"Error processing {script_file.name}: {e}")
            continue
    
    return disabled_count

def clear_saved_script_states(folder_path, sanitized_script_uuids, dry_run=False, verbose=False):
    """
    Clear SavedScriptState from object XML files that reference sanitized scripts.
    This forces the server to reload scripts from the IAR instead of using cached state.
    """
    assets_dir = Path(folder_path) / 'assets'
    if not assets_dir.exists():
        return 0
    
    # Find all object XML files
    object_files = list(assets_dir.glob('*_object.xml'))
    cleared_count = 0
    
    for object_file in object_files:
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(object_file, 'r', encoding=encoding) as f:
                        content = f.read()
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                continue
            
            # Parse XML (handle namespaces)
            try:
                # Register namespaces to avoid issues
                ET.register_namespace('', '')
                root = ET.fromstring(content)
            except ET.ParseError:
                continue
            
            # Find SavedScriptState elements (search without namespace)
            script_states_cleared = False
            
            # Search for SavedScriptState - handle both with and without namespaces
            # Use a recursive approach to track parent elements
            def find_and_remove_script_states(elem, parent=None):
                nonlocal script_states_cleared
                if 'SavedScriptState' in elem.tag:
                    # Check if this references a sanitized script
                    for child in elem.iter():
                        if 'Asset' in child.tag and child.text:
                            asset_uuid = child.text.strip()
                            if asset_uuid in sanitized_script_uuids:
                                # Remove this SavedScriptState
                                if parent is not None:
                                    parent.remove(elem)
                                    script_states_cleared = True
                                    if verbose:
                                        print(f"  Cleared SavedScriptState for script {asset_uuid} in {object_file.name}")
                                return
                # Recursively process children
                for child in list(elem):
                    find_and_remove_script_states(child, elem)
            
            find_and_remove_script_states(root)
            
            # Also check TaskInventory items that reference sanitized scripts
            for elem in root.iter():
                if 'TaskInventoryItem' in elem.tag:
                    # Find AssetID element, then UUID within it
                    for asset_id in elem.iter():
                        if 'AssetID' in asset_id.tag:
                            for uuid_elem in asset_id:
                                if 'UUID' in uuid_elem.tag and uuid_elem.text:
                                    asset_uuid = uuid_elem.text.strip()
                                    if asset_uuid in sanitized_script_uuids:
                                        if verbose:
                                            print(f"  Found TaskInventoryItem referencing sanitized script {asset_uuid} in {object_file.name}")
                                    break
                            break
            
            if script_states_cleared and not dry_run:
                # Reconstruct XML
                xml_content = '<?xml version="1.0" encoding="utf-16"?>\n'
                xml_content += ET.tostring(root, encoding='unicode')
                
                with open(object_file, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                
                cleared_count += 1
                
        except Exception as e:
            if verbose:
                print(f"Error processing {object_file.name}: {e}")
            continue
    
    return cleared_count

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
    
    # NEW: Sanitize LSL scripts if processing an extracted IAR
    # Check if we're in an extracted IAR directory (has assets/ folder)
    assets_dir = Path(args.folder) / 'assets'
    if assets_dir.exists():
        # Print the step message here so it appears before the script sanitization output
        print("[4/6] Scanning for auto-delete scripts...")
        import sys
        sys.stdout.flush()  # Ensure message is displayed before script processing
        disabled_scripts = sanitize_lsl_scripts(args.folder, args.dry_run, args.verbose)
        
        # Collect UUIDs of sanitized scripts
        sanitized_uuids = set()
        if disabled_scripts > 0:
            # Find script files that were sanitized
            for script_file in assets_dir.glob('*.lsl'):
                try:
                    with open(script_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(200)  # Read first 200 chars
                        if 'DISABLED BY IAR FIXER' in content:
                            # Extract UUID from filename (format: UUID_script.lsl)
                            uuid_part = script_file.stem.replace('_script', '')
                            if len(uuid_part) == 36:  # UUID length
                                sanitized_uuids.add(uuid_part)
                except:
                    pass
            
            # Clear SavedScriptState from object XML files
            if sanitized_uuids:
                print(f"Clearing SavedScriptState for {len(sanitized_uuids)} sanitized script(s)...")
                cleared_states = clear_saved_script_states(args.folder, sanitized_uuids, args.dry_run, args.verbose)
                if cleared_states > 0:
                    if args.dry_run:
                        print(f"DRY RUN: Would clear SavedScriptState from {cleared_states} object(s)")
                    else:
                        print(f"✓ Cleared SavedScriptState from {cleared_states} object(s)")
        
        if disabled_scripts > 0:
            if args.dry_run:
                print(f"DRY RUN: Would disable {disabled_scripts} suspicious script(s)")
            else:
                print(f"✓ Disabled {disabled_scripts} suspicious script(s)")
                print(f"\n⚠️  NOTE: If objects still auto-delete after import, the server may be")
                print(f"   loading scripts from asset cache by UUID. Try:")
                print(f"   1. Import to a different inventory folder (forces new asset UUIDs)")
                print(f"   2. Wait for server cache to expire (may take hours/days)")
                print(f"   3. Delete objects from inventory before re-importing")
        else:
            if args.verbose:
                print("No suspicious scripts found")

if __name__ == "__main__":
    main() 
