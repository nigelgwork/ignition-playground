#!/bin/bash
#
# Backup and Restore User-Duplicated Playbooks
#
# This script helps you backup and restore your duplicated playbooks
# to prevent data loss from git operations or system restarts.
#

set -e

PLAYBOOKS_DIR="/git/ignition-playground/playbooks"
BACKUP_DIR="$HOME/.ignition-toolkit/user_playbooks"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

show_usage() {
    cat << EOF
Usage: $0 {backup|restore|list|sync}

Commands:
  backup   - Copy all *_copy*.yaml and *.backup.*.yaml files to ~/.ignition-toolkit/user_playbooks/
  restore  - Copy all files from ~/.ignition-toolkit/user_playbooks/ back to playbooks/
  list     - Show all duplicated playbooks in the git repo
  sync     - Two-way sync (backup + restore, keeps newer version)

Examples:
  $0 backup     # Backup your custom playbooks
  $0 restore    # Restore from backup after a git reset
  $0 list       # See what playbooks would be backed up
EOF
}

list_user_playbooks() {
    echo "=== Duplicated Playbooks in Git Repo ==="
    find "$PLAYBOOKS_DIR" -type f \( -name "*_copy*.yaml" -o -name "*.backup.*.yaml" \) | sort
    echo ""
    echo "=== Backed Up Playbooks ==="
    find "$BACKUP_DIR" -type f -name "*.yaml" 2>/dev/null | sort
}

backup_playbooks() {
    echo "Backing up user playbooks to $BACKUP_DIR..."

    # Create backup directory structure
    mkdir -p "$BACKUP_DIR"/{gateway,perspective,designer}

    # Find and copy all duplicated playbooks
    COUNT=0
    while IFS= read -r -d '' file; do
        # Get relative path from playbooks dir
        REL_PATH=$(realpath --relative-to="$PLAYBOOKS_DIR" "$file")
        DEST="$BACKUP_DIR/$REL_PATH"

        # Create parent directory
        mkdir -p "$(dirname "$DEST")"

        # Copy file
        cp -v "$file" "$DEST"
        ((COUNT++))
    done < <(find "$PLAYBOOKS_DIR" -type f \( -name "*_copy*.yaml" -o -name "*.backup.*.yaml" \) -print0)

    echo ""
    echo "✅ Backed up $COUNT playbook(s) to $BACKUP_DIR"
}

restore_playbooks() {
    echo "Restoring playbooks from $BACKUP_DIR to $PLAYBOOKS_DIR..."

    if [ ! -d "$BACKUP_DIR" ]; then
        echo "❌ Backup directory not found: $BACKUP_DIR"
        exit 1
    fi

    COUNT=0
    while IFS= read -r -d '' file; do
        # Get relative path from backup dir
        REL_PATH=$(realpath --relative-to="$BACKUP_DIR" "$file")
        DEST="$PLAYBOOKS_DIR/$REL_PATH"

        # Create parent directory
        mkdir -p "$(dirname "$DEST")"

        # Copy file
        cp -v "$file" "$DEST"
        ((COUNT++))
    done < <(find "$BACKUP_DIR" -type f -name "*.yaml" -print0)

    echo ""
    echo "✅ Restored $COUNT playbook(s) to $PLAYBOOKS_DIR"
}

sync_playbooks() {
    echo "Syncing playbooks (two-way, keeps newer files)..."

    # Backup first
    backup_playbooks
    echo ""

    # Then restore (rsync will only copy if source is newer)
    echo "Checking for updates from backup..."
    rsync -av --update "$BACKUP_DIR/" "$PLAYBOOKS_DIR/"

    echo ""
    echo "✅ Sync complete"
}

# Main command handler
case "${1:-}" in
    backup)
        backup_playbooks
        ;;
    restore)
        restore_playbooks
        ;;
    list)
        list_user_playbooks
        ;;
    sync)
        sync_playbooks
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
