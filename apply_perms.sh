#!/bin/bash
# OpenSim IAR Full Permissions Shell Script
# =========================================
#
# This shell script provides easy commands for applying full permissions
# to OpenSim IAR XML files.
#
# Usage examples:
#   ./apply_perms.sh new
#   ./apply_perms.sh new --backup
#   ./apply_perms.sh test new
#   ./apply_perms.sh max new

show_usage() {
    echo
    echo "OpenSim IAR Full Permissions Tool"
    echo "================================="
    echo
    echo "Usage: $0 [folder] [options]"
    echo "       $0 test [folder] [options]"
    echo "       $0 max [folder] [options]"
    echo
    echo "Default behavior:"
    echo "  - Uses standard full permissions (581639)"
    echo "  - Processes subdirectories recursively"
    echo "  - Asks for confirmation before applying"
    echo
    echo "Examples:"
    echo "  $0 new"
    echo "  $0 new --backup"
    echo "  $0 test new"
    echo "  $0 max new --no-confirm"
    echo
    echo "Options: --backup --no-confirm --verbose"
    echo
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Check for help
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

FOLDER="$1"
shift

# Check if it's a special command
if [ "$FOLDER" = "test" ]; then
    FOLDER="$1"
    shift
    PERM_ARGS="--standard --dry-run --no-confirm"
elif [ "$FOLDER" = "max" ]; then
    FOLDER="$1"
    shift
    PERM_ARGS="--max-perms --no-confirm"
else
    # Default to standard permissions (with confirmation)
    PERM_ARGS="--standard"
fi

echo "Applying standard full permissions to IAR files in '$FOLDER'..."
python3 apply_full_perms.py $PERM_ARGS "$FOLDER" "$@" 
