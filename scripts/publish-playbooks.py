#!/usr/bin/env python3
"""
Publish Playbooks to GitHub Releases

This script automates the process of publishing playbooks to GitHub Releases:
1. Scans playbooks/ directory for all YAML files
2. Calculates checksums and collects metadata
3. Generates playbooks-index.json manifest
4. Creates GitHub release (optional)
5. Uploads playbook files and manifest (optional)

Usage:
    # Generate index only (dry-run)
    python scripts/publish-playbooks.py

    # Generate and publish to GitHub
    python scripts/publish-playbooks.py --publish --github-token YOUR_TOKEN

    # Specify version and exclude certain directories
    python scripts/publish-playbooks.py --version 1.0.0 --exclude tests examples
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Add parent directory to path to import from ignition_toolkit
sys.path.insert(0, str(Path(__file__).parent.parent))

from ignition_toolkit.playbook.loader import PlaybookLoader


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes"""
    return file_path.stat().st_size


def extract_playbook_metadata(yaml_file: Path, repo_url: str, release_tag: str) -> dict[str, Any]:
    """
    Extract metadata from a playbook YAML file

    Args:
        yaml_file: Path to playbook YAML file
        repo_url: GitHub repository URL
        release_tag: GitHub release tag (e.g., "playbooks-v1.0.0")

    Returns:
        Dictionary with playbook metadata
    """
    # Load playbook
    loader = PlaybookLoader()
    playbook = loader.load_from_file(yaml_file)

    # Parse YAML to get additional fields not in Playbook model
    with open(yaml_file, "r") as f:
        yaml_data = yaml.safe_load(f)

    # Extract metadata
    domain = yaml_data.get("domain", "unknown")
    group = yaml_data.get("group", "")
    verified = yaml_data.get("verified", False)

    # Get author from metadata section
    metadata_section = yaml_data.get("metadata", {})
    author = metadata_section.get("author", "Ignition Automation Toolkit")
    tags = metadata_section.get("tags", [])
    release_notes = metadata_section.get("release_notes", "")

    # Build playbook path (e.g., "gateway/module_upgrade")
    relative_path = yaml_file.relative_to(Path("playbooks"))
    playbook_path = str(relative_path.with_suffix("")).replace(os.sep, "/")

    # Build download URL
    filename = f"{playbook_path.replace('/', '-')}-{playbook.version}.yaml"
    download_url = f"{repo_url}/releases/download/{release_tag}/{filename}"

    # Calculate checksum and size
    checksum = calculate_sha256(yaml_file)
    size_bytes = get_file_size(yaml_file)

    # Build metadata dictionary
    metadata = {
        "version": playbook.version,
        "domain": domain,
        "verified": verified,
        "description": playbook.description,
        "download_url": download_url,
        "checksum": checksum,
        "size_bytes": size_bytes,
        "dependencies": [],  # TODO: Extract from playbook if we add dependency support
        "author": author,
        "tags": tags if isinstance(tags, list) else [],
        "group": group,
    }

    # Add optional fields
    if verified:
        metadata["verified_by"] = "Nigel G"
        metadata["verified_at"] = datetime.now(timezone.utc).isoformat()

    if release_notes:
        metadata["release_notes"] = release_notes

    return playbook_path, metadata


def scan_playbooks(
    playbooks_dir: Path,
    exclude_dirs: list[str],
    repo_url: str,
    release_tag: str
) -> dict[str, dict[str, Any]]:
    """
    Scan playbooks directory and collect metadata

    Args:
        playbooks_dir: Root playbooks directory
        exclude_dirs: List of directory names to exclude (e.g., ["tests", "examples"])
        repo_url: GitHub repository URL
        release_tag: GitHub release tag

    Returns:
        Dictionary mapping playbook paths to metadata
    """
    playbooks = {}

    # Find all YAML files
    for yaml_file in playbooks_dir.rglob("*.yaml"):
        # Skip backup files
        if ".backup." in yaml_file.name:
            continue

        # Skip excluded directories
        relative_path = yaml_file.relative_to(playbooks_dir)
        if any(excluded in relative_path.parts for excluded in exclude_dirs):
            continue

        try:
            playbook_path, metadata = extract_playbook_metadata(yaml_file, repo_url, release_tag)
            playbooks[playbook_path] = metadata
            print(f"✓ Processed: {playbook_path} (v{metadata['version']})")
        except Exception as e:
            print(f"✗ Failed to process {yaml_file}: {e}")
            continue

    return playbooks


def generate_index(
    version: str,
    repo_url: str,
    playbooks: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """
    Generate playbooks-index.json manifest

    Args:
        version: Index version (semver)
        repo_url: GitHub repository URL
        playbooks: Dictionary of playbook metadata

    Returns:
        Complete index dictionary
    """
    return {
        "version": version,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "repository": repo_url,
        "playbooks": playbooks,
    }


def save_index(index: dict[str, Any], output_path: Path) -> None:
    """Save index to JSON file"""
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2)
    print(f"\n✓ Index saved to: {output_path}")


def publish_to_github(
    release_tag: str,
    index_path: Path,
    playbooks_dir: Path,
    github_token: str,
    repo_owner: str,
    repo_name: str
) -> None:
    """
    Publish playbooks to GitHub Releases

    Args:
        release_tag: GitHub release tag (e.g., "playbooks-v1.0.0")
        index_path: Path to playbooks-index.json
        playbooks_dir: Root playbooks directory
        github_token: GitHub personal access token
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
    """
    try:
        import requests
    except ImportError:
        print("✗ Error: 'requests' library required for GitHub publishing")
        print("  Install with: pip install requests")
        sys.exit(1)

    # TODO: Implement GitHub API integration
    # 1. Create release using GitHub API
    # 2. Upload playbooks-index.json
    # 3. Upload all playbook YAML files

    print("\n⚠ GitHub publishing not yet implemented")
    print("  You can manually:")
    print(f"  1. Create release: {release_tag}")
    print(f"  2. Upload: {index_path}")
    print(f"  3. Upload all YAML files from: {playbooks_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Publish playbooks to GitHub Releases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Index version (semver, default: 1.0.0)"
    )

    parser.add_argument(
        "--exclude",
        nargs="*",
        default=["tests", "examples"],
        help="Directories to exclude (default: tests examples)"
    )

    parser.add_argument(
        "--repo-url",
        default="https://github.com/nigelgwork/ignition-playground",
        help="GitHub repository URL"
    )

    parser.add_argument(
        "--repo-owner",
        default="nigelgwork",
        help="GitHub repository owner"
    )

    parser.add_argument(
        "--repo-name",
        default="ignition-playground",
        help="GitHub repository name"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("playbooks-index.json"),
        help="Output path for index file (default: playbooks-index.json)"
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish to GitHub Releases (requires --github-token)"
    )

    parser.add_argument(
        "--github-token",
        help="GitHub personal access token (for publishing)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.publish and not args.github_token:
        parser.error("--publish requires --github-token")

    # Build paths
    playbooks_dir = Path("playbooks")
    if not playbooks_dir.exists():
        print(f"✗ Error: Playbooks directory not found: {playbooks_dir}")
        sys.exit(1)

    # Build release tag
    release_tag = f"playbooks-v{args.version}"

    print(f"Playbook Publisher v{args.version}")
    print(f"{'=' * 60}")
    print(f"Playbooks directory: {playbooks_dir}")
    print(f"Excluding: {', '.join(args.exclude)}")
    print(f"Repository: {args.repo_url}")
    print(f"Release tag: {release_tag}")
    print(f"{'=' * 60}\n")

    # Scan playbooks
    print("Scanning playbooks...")
    playbooks = scan_playbooks(
        playbooks_dir=playbooks_dir,
        exclude_dirs=args.exclude,
        repo_url=args.repo_url,
        release_tag=release_tag
    )

    print(f"\n✓ Found {len(playbooks)} playbooks")

    # Generate index
    print("\nGenerating index...")
    index = generate_index(
        version=args.version,
        repo_url=args.repo_url,
        playbooks=playbooks
    )

    # Save index
    save_index(index, args.output)

    # Publish to GitHub (if requested)
    if args.publish:
        print("\nPublishing to GitHub...")
        publish_to_github(
            release_tag=release_tag,
            index_path=args.output,
            playbooks_dir=playbooks_dir,
            github_token=args.github_token,
            repo_owner=args.repo_owner,
            repo_name=args.repo_name
        )
    else:
        print("\n⚠ Dry-run mode (use --publish to upload to GitHub)")

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
