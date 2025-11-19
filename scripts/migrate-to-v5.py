#!/usr/bin/env python3
"""
Migration script for v5.0 - Plugin Architecture

Migrates existing playbooks from the old structure to the new plugin architecture:
- Base playbooks (6) stay in ignition_toolkit/playbooks/ (built-in)
- Other playbooks move to ~/.ignition-toolkit/playbooks/ (user-created)
- Registers all playbooks in the registry

Usage:
    python scripts/migrate-to-v5.py [--dry-run] [--clean]

Options:
    --dry-run    Show what would be migrated without actually doing it
    --clean      Remove old playbooks directory after migration
"""

import argparse
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ignition_toolkit.core.paths import (
    get_package_root,
    get_builtin_playbooks_dir,
    get_user_playbooks_dir,
)
from ignition_toolkit.playbook.registry import PlaybookRegistry
from ignition_toolkit.playbook.loader import PlaybookLoader

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Define the 6 base Gateway playbooks
BASE_PLAYBOOKS = {
    'gateway/gateway_login.yaml',
    'gateway/backup_gateway.yaml',
    'gateway/module_install.yaml',
    'gateway/module_uninstall.yaml',
    'gateway/module_upgrade.yaml',
    'gateway/gateway_restart.yaml',
}


def is_base_playbook(relative_path: str) -> bool:
    """Check if a playbook is one of the 6 base playbooks"""
    return relative_path in BASE_PLAYBOOKS


def migrate_playbooks(dry_run: bool = False) -> dict:
    """
    Migrate playbooks from old structure to new structure

    Args:
        dry_run: If True, only show what would be done

    Returns:
        dict: Migration statistics
    """
    old_playbooks_dir = get_package_root() / "playbooks"
    user_playbooks_dir = get_user_playbooks_dir()
    builtin_playbooks_dir = get_builtin_playbooks_dir()

    stats = {
        'base_playbooks_found': 0,
        'user_playbooks_migrated': 0,
        'backup_files_skipped': 0,
        'errors': 0,
    }

    # Check if old playbooks directory exists
    if not old_playbooks_dir.exists():
        logger.info("✓ No old playbooks directory found - nothing to migrate")
        return stats

    logger.info(f"Scanning old playbooks directory: {old_playbooks_dir}")

    # Initialize loader for reading playbook metadata
    loader = PlaybookLoader()

    # Initialize registry
    registry = PlaybookRegistry()
    registry.load()

    # Scan all YAML files in old directory
    yaml_files = list(old_playbooks_dir.rglob("*.yaml"))
    logger.info(f"Found {len(yaml_files)} YAML files")

    for yaml_file in yaml_files:
        # Skip backup files
        if '.backup.' in yaml_file.name:
            stats['backup_files_skipped'] += 1
            continue

        # Calculate relative path from old playbooks directory
        try:
            relative_path = str(yaml_file.relative_to(old_playbooks_dir))
        except ValueError:
            logger.warning(f"Skipping file outside playbooks directory: {yaml_file}")
            continue

        # Check if it's a base playbook
        if is_base_playbook(relative_path):
            stats['base_playbooks_found'] += 1
            logger.info(f"  ✓ Base playbook (already in built-in): {relative_path}")

            # Register base playbook in registry
            try:
                playbook = loader.load_from_file(yaml_file)
                builtin_path = builtin_playbooks_dir / relative_path

                if not dry_run:
                    registry.register_playbook(
                        playbook_path=relative_path.replace('.yaml', ''),
                        version=playbook.version,
                        location=str(builtin_path),
                        source="built-in",
                        verified=playbook.metadata.get('verified', False)
                    )
                    logger.debug(f"    Registered as built-in: {relative_path}")
            except Exception as e:
                logger.error(f"    Error registering base playbook: {e}")
                stats['errors'] += 1
            continue

        # It's a user playbook - migrate it
        try:
            # Load playbook to get metadata
            playbook = loader.load_from_file(yaml_file)

            # Determine target path in user playbooks directory
            target_path = user_playbooks_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)

            if target_path.exists():
                logger.warning(f"  ! Already exists in user directory: {relative_path}")
                continue

            # Copy to user playbooks directory
            if not dry_run:
                shutil.copy2(yaml_file, target_path)
                logger.info(f"  → Migrated to user directory: {relative_path}")

                # Register in registry as user-created
                registry.register_playbook(
                    playbook_path=relative_path.replace('.yaml', ''),
                    version=playbook.version,
                    location=str(target_path),
                    source="user-created",
                    verified=playbook.metadata.get('verified', False)
                )
                logger.debug(f"    Registered as user-created: {relative_path}")
            else:
                logger.info(f"  → Would migrate to user directory: {relative_path}")

            stats['user_playbooks_migrated'] += 1

        except Exception as e:
            logger.error(f"  ✗ Error migrating {relative_path}: {e}")
            stats['errors'] += 1

    # Save registry
    if not dry_run:
        registry.save()
        logger.info(f"✓ Registry updated: {registry.registry_path}")

    return stats


def clean_old_directory(dry_run: bool = False):
    """
    Clean up the old playbooks directory

    Args:
        dry_run: If True, only show what would be done
    """
    old_playbooks_dir = get_package_root() / "playbooks"

    if not old_playbooks_dir.exists():
        logger.info("✓ Old playbooks directory already removed")
        return

    if dry_run:
        logger.info(f"Would remove old playbooks directory: {old_playbooks_dir}")
    else:
        # Create backup before removing
        backup_path = get_package_root() / f"playbooks.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Creating backup: {backup_path}")
        shutil.copytree(old_playbooks_dir, backup_path)

        # Remove old directory
        shutil.rmtree(old_playbooks_dir)
        logger.info(f"✓ Removed old playbooks directory (backup saved to {backup_path})")


def main():
    """Main migration entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate playbooks to v5.0 plugin architecture',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without doing it')
    parser.add_argument('--clean', action='store_true', help='Remove old playbooks directory after migration')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Ignition Automation Toolkit - v5.0 Migration")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    # Run migration
    logger.info("")
    logger.info("Step 1: Migrating playbooks...")
    logger.info("-" * 60)
    stats = migrate_playbooks(dry_run=args.dry_run)

    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Migration Summary")
    logger.info("=" * 60)
    logger.info(f"Base playbooks found: {stats['base_playbooks_found']}")
    logger.info(f"User playbooks migrated: {stats['user_playbooks_migrated']}")
    logger.info(f"Backup files skipped: {stats['backup_files_skipped']}")
    logger.info(f"Errors: {stats['errors']}")

    if stats['errors'] > 0:
        logger.warning(f"⚠ Migration completed with {stats['errors']} errors")
        sys.exit(1)

    # Clean up if requested
    if args.clean:
        logger.info("")
        logger.info("Step 2: Cleaning up old directory...")
        logger.info("-" * 60)
        clean_old_directory(dry_run=args.dry_run)

    logger.info("")
    if args.dry_run:
        logger.info("✓ Dry run complete - run without --dry-run to perform migration")
    else:
        logger.info("✓ Migration complete!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Test that all playbooks load correctly")
        logger.info("2. Browse the playbook library to install additional playbooks")
        logger.info("3. Run with --clean to remove old playbooks directory")

    logger.info("=" * 60)


if __name__ == '__main__':
    main()
