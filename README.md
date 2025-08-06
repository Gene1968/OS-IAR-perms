# OpenSim IAR Inventory Permissions Fix Tool

A comprehensive toolset for applying full permissions to OpenSim IAR (Inventory Archive) XML files. This tool is designed to work with OpenSim grids and can process entire IAR archives to ensure all items have the proper full permissions.

## Features

- **Multiple Permission Levels**: Choose between standard full perms (581639) or maximum perms (2147483647)
- **Recursive Processing**: Process entire directory trees with subdirectories
- **Safety Features**: Backup files before modifying, dry-run mode for testing
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Flexible**: Customize EveryonePermissions and NextPermissions values
- **Smart Detection**: Only processes valid OpenSim InventoryItem XML files

## Files Included

- `fix_iar.bat` - Windows front-end which adds TAR decompress, then runs the Python to apply the perms, then does a TAR recompress "xxx-FIXED.iar", then cleans up.  May be all you need to run
- `apply_full_perms.py` - Main Python script with full functionality
- `apply_perms.bat` - Windows batch file for easy command-line usage
- `apply_perms.sh` - Unix/Linux shell script for easy command-line usage
- `README.md` - This documentation file

## External Dependencies:

- Python
- tar - GNU tar 1.35 was already on my path (along with 1.12, 1.29, etc. and any of them works.  Try `tar --version`)

## Quick Start

### Recommended/easiest workflow (Windows):

1. Make sure you have a subfolder of your Opensim/OSG bin folder where you'd like to work with IAR files. It really helps avoid confusion now, and also to ignore at sim update time.  eg: bin/_myIARediting but it can be anything
2. CD there in your Terminal.  eg:
`cd C:\[path to your OSgrid bin]\_myIARediting`. I like to use a second tab next to my OS console
3. Put these scripts either on your command path (to be available globally in the future), or just directly in that IAR folder if you prefer. Update - I moved mine to my commands path folder, and found I still need a copy of the PY file here in my editing folder for now.  Should try to improve the reference later.
4. In-world make an inventory folder to hold some number of NM, NC and/or NT items you want to convert.  eg. /temp-convert directly under Inventory.  I started small, but have done hundreds at once and had no unexpected problems (missing server assets on OSGrid are not made worse by this process; they're either missing or not)
5. Make or choose another inventory folder to restore the fixes to.  Could be /_Restored or /_Import but either way it's helpful once you start doing a bunch of batches of these and you want to compare/test/sort them before deleting originals (or after)
6. Copy or move some NC, NM and/or NT items into your folder eg: /_temp-convert.  Did you know you can any combination of `(no copy) (no modify) (no transfer)` in your search bar to filter/locate them? Very helpful! :)
7. From the OS console, save your folder to an IAR, eg: `save iar [Firstname Lastname] /temp-convert [yourpassword] _myIARediting/temp-convert.iar` (or whatever folder and filename you like, but you'll need to remember it)
8. you can:  `fix_iar temp-convert` - or whatever you named your file.  The .IAR file extension is optional.  (If you're on Linux you can probably script the tar x, py and tar c commands the same way I did in the Windows bat. We should add that to the repo!)
9. If you like the output and it shows some modified files, you can now load the new IAR back to the grid, like:  `load iar [Firstname Lastname] _Restored [yourpassword] _myIARediting/temp-convert_fixed.iar`

And that's it, now you can try out your items.  Many will be proper full perm, but I've also found many difficult-to-convert items which __*show*__ as full perm in inventory, but then get much harder to work with once you rezz them.  I'm guessing this might be due to more perms being stored on the asset server side(?)  In these cases they're still improved since you can now rename them in inventory AND copy them, before they revert on rezz sadface.  I also noticed that wearing them from inv reverts some of them, so make a copy and then wear the copy.  I like to mark troubly ones as "FMP" for full/mixed/perms, reminding me they look full but probably have NextOwner issues or rezz issues at the very least.

The nice thing is you can rapidly repeat steps 6-9 all you want and get a rhythm going, since both IARs would just get overwritten if you simply use the up arrow in each console to reuse both filenames.  I find no point in keeping any of the IARs since I already back up my organized folders, but you might save them as a way to "copy No Copy" but basically that's any IAR.





### Windows Users
```batch
# Apply standard full permissions to 'new' folder (with confirmation)
apply_perms.bat new

# Apply with backup files
apply_perms.bat new --backup

# Test run (see what would be changed)
apply_perms.bat test new

# Apply maximum permissions
apply_perms.bat max new
```

### Unix/Linux/macOS Users
```bash
# Make the script executable
chmod +x apply_perms.sh

# Apply standard full permissions to 'new' folder (with confirmation)
./apply_perms.sh new

# Apply with backup files
./apply_perms.sh new --backup

# Test run (see what would be changed)
./apply_perms.sh test new

# Apply maximum permissions
./apply_perms.sh max new
```

### Direct Python Usage
```bash
# Apply standard permissions (with confirmation)
python apply_full_perms.py new

# Apply maximum permissions
python apply_full_perms.py new --max-perms

# Test run with verbose output
python apply_full_perms.py new --dry-run --verbose

# Skip confirmation
python apply_full_perms.py new --no-confirm
```

## Permission Types

### Standard Full Permissions (Default)
- **BasePermissions**: 581639
- **CurrentPermissions**: 581639
- **EveryOnePermissions**: 32768
- **NextPermissions**: 581632
- **SaleType**: 0 (not for sale)
- **SalePrice**: 0
- **GroupID**: 00000000-0000-0000-0000-000000000000 (no group)
- **GroupOwned**: False

This is the most commonly used "full perm" setting in OpenSim and is compatible with all grids.

### Maximum Permissions
- **BasePermissions**: 2147483647
- **CurrentPermissions**: 2147483647
- **EveryOnePermissions**: 581632
- **NextPermissions**: 581632
- **SaleType**: 0 (not for sale)
- **SalePrice**: 0
- **GroupID**: 00000000-0000-0000-0000-000000000000 (no group)
- **GroupOwned**: False

This gives the absolute maximum permissions possible (32-bit integer max). Use this if you want the most permissive settings.

## Default Behavior

The scripts now default to:
- **Standard full permissions** (581639) - the most commonly used "full perm" setting
- **Recursive processing** - automatically processes subdirectories
- **Confirmation prompt** - asks for confirmation before applying changes
- **No backups** - doesn't create backup files unless requested

## Command Line Options

### Basic Options
- `--max-perms` - Use maximum possible permissions (2147483647)
- `--standard` - Use standard full perms (581639) - default
- `--everyone VALUE` - Set EveryonePermissions (default: 581632)
- `--next VALUE` - Set NextPermissions (default: 581632)

### Safety Options
- `--backup` or `-b` - Create backup files before modifying
- `--dry-run` or `-n` - Show what would be changed without making changes
- `--no-recursive` - Disable recursive processing
- `--no-confirm` - Skip confirmation prompt
- `--verbose` or `-v` - Show detailed output

## Examples

### Basic Usage
```bash
# Apply standard permissions to current directory
python apply_full_perms.py

# Apply to specific folder
python apply_full_perms.py inventory/

# Apply maximum permissions
python apply_full_perms.py inventory/ --max-perms
```

### Advanced Usage
```bash
# Process recursively with backups
python apply_full_perms.py inventory/ --recursive --backup

# Test run to see what would be changed
python apply_full_perms.py inventory/ --dry-run --verbose

# Custom permissions
python apply_full_perms.py inventory/ --everyone 32768 --next 581632

# Process entire IAR archive
python apply_full_perms.py . --recursive --max-perms --backup
```

## Understanding OpenSim Permissions

### Permission Bitmasks
OpenSim uses bitmasks to represent permissions. The most common values are:

- **581639** = Standard "full perm" (Copy, Modify, Transfer, Export)
- **581632** = Full perm without Export (Copy, Modify, Transfer)
- **2147483647** = Maximum possible permissions (all bits set)
- **32768** = Copy permission only

### Permission Fields
- **BasePermissions**: The original permissions set by the creator
- **CurrentPermissions**: Current permissions for the owner
- **EveryOnePermissions**: Permissions for everyone (when set to "Everyone")
- **NextPermissions**: Permissions that will be granted to the next owner

### Additional Fields
- **SaleType**: 0 = not for sale, 1 = original price, 2 = copy price
- **SalePrice**: Price in Linden dollars (0 = free)
- **GroupID**: UUID of the group that owns the object (00000000-0000-0000-0000-000000000000 = no group)
- **GroupOwned**: Whether the object is owned by a group (False = owned by individual)
- **Flags**: Bitwise operations to clear specific flags:
  - Clears bit 8 (256): No-copy flag
  - Clears bit 12 (4096): No-modify flag
  - Clears bits 19-24: For-sale, no-transfer, and other restrictions
  - Preserves all other flags including container, touch, and other functionality
  - Uses bitwise AND with complement (~0x1F80100) to remove unwanted bits

## Safety Features

### Backup Files
When using `--backup`, the script creates `.xml.backup` files before making any changes. This allows you to restore the original files if needed.

### Dry Run Mode
Use `--dry-run` to see exactly what changes would be made without actually modifying any files. This is perfect for testing and verification.

### Smart File Detection
The script only processes XML files that contain valid OpenSim `<InventoryItem>` elements, skipping other XML files automatically.

## Troubleshooting

### Common Issues

**"No XML files found"**
- Make sure you're pointing to the correct directory
- Check that the directory contains XML files
- Use `--recursive` if files are in subdirectories

**"XML parse error"**
- The XML file might be corrupted or not a valid OpenSim inventory item
- Check the file manually to ensure it's properly formatted

**"Permission denied"**
- Make sure you have write permissions to the directory
- On Unix systems, you might need to use `sudo` for system directories

### Getting Help
```bash
# Show help for the Python script
python apply_full_perms.py --help

# Show help for the batch script (Windows)
apply_perms.bat help

# Show help for the shell script (Unix/Linux)
./apply_perms.sh help
```

## Requirements

- Python 3.6 or higher
- No additional Python packages required (uses only standard library)

## License

This tool is provided as-is for use with OpenSim IAR files. Feel free to modify and distribute as needed.

## Contributing

If you find bugs or have suggestions for improvements, please feel free to contribute by:
1. Reporting issues
2. Suggesting new features
3. Submitting pull requests

## Version History

- **v1.0** - Initial release with basic permission application functionality
- Added support for both standard and maximum permissions
- Included safety features (backup, dry-run)
- Added cross-platform batch and shell scripts 
