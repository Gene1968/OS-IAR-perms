# OpenSim/Second Life Inventory Flags Reference

## Overview
OpenSim and Second Life use integer bitmasks to represent various object properties and states. Each bit position represents a specific flag or property.

## Common Flag Values and Meanings

### Basic Flags
- **0** = No special flags (normal object)
- **256** = No-copy (unique item, cannot be copied)

### Container/Object Inventory Flags
- **1048576** = Object has inventory (container) - Bit 20
- **2097152** = Object has inventory + For sale - Bits 20 + 21
- **1572864** = Object has inventory + No-copy - Bits 20 + 8
- **2097408** = Object has inventory + For sale + No-copy - Bits 20 + 21 + 8

### Other Common Values
- **1052672** = Object has inventory + No-copy + other flags
- **32768** = Copy permission only (when used in permissions context)

## Bit Position Analysis

### Key Bit Positions
- **Bit 8** (256): No-copy flag
- **Bit 20** (1048576): Object has inventory/container
- **Bit 21** (2097152): For sale flag

### Flag Combinations
When multiple flags are set, their values are added together:
- Container + For sale = 1048576 + 1048576 = 2097152
- Container + No-copy = 1048576 + 256 = 1572864
- Container + For sale + No-copy = 1048576 + 1048576 + 256 = 2097408

## Script Implementation

The `apply_full_perms.py` script uses bitwise operations to clear specific unwanted flags:

```python
# Define bits to clear (remove these flags)
# Bit 8 (256): No-copy
# Bit 12 (4096): No-modify
# Bits 19-24: Various flags including for-sale, no-modify, no-transfer, and other restrictions
bits_to_clear = 0x1F80100  # 33048576 in decimal (bits 8, 12, 19-24)

# Clear the unwanted bits while preserving all others
new_flags = old_flags & ~bits_to_clear
```

This approach:
- Removes bit 8 (no-copy flag)
- Removes bit 12 (no-modify flag)
- Removes bits 19-24 (for-sale, no-transfer, and other restrictions)
- Preserves all other flags (container, touch, etc.)
- Works with any flag combination, not just predefined values

## Purpose of These Replacements

The script is designed to:
1. **Preserve all desired functionality** - Keep container, touch, and other useful flags
2. **Remove unwanted restrictions** - Clear no-copy, for-sale, no-modify, no-transfer flags
3. **Use bitwise operations** - Precisely target specific bits without affecting others

This results in objects that:
- Can still function as containers (hold other objects)
- Can be touched and interacted with
- Are not for sale
- Can be copied, modified, and transferred freely
- Maintain their basic functionality while removing commercial and usage restrictions

## Verification

To verify flag meanings, you can:
1. Use the script's `--dry-run --verbose` mode to see what changes would be made
2. Check the original IAR files to see what flags are present
3. Test the modified objects in-world to confirm they behave as expected

## Notes

- **1048576 is NOT for sale** - it's just the container flag
- **For sale** is typically bit 21 (2097152 when combined with container)
- **No-copy** is bit 8 (256)
- **Container** is bit 20 (1048576)

The script correctly preserves container functionality while removing commercial and copy restrictions. 
