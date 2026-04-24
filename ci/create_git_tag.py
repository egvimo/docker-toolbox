#!/usr/bin/env python3

import argparse
import re
import subprocess
from pathlib import Path

FROM_RE: re.Pattern[str] = re.compile(r"^FROM\s([^:\s]+):([^\s]+)")
TAG_VERSION_RE: re.Pattern[str] = re.compile(r"#\stag-version:\s([a-zA-Z0-9-]+)")
APK_VERSION_RE: re.Pattern[str] = re.compile(r"([a-zA-Z0-9-]+)=([^\s]+)")


def run(cmd: list[str], capture_output: bool = True, check: bool = True) -> str:
    """Run a subprocess command and return its stdout."""
    try:
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=capture_output,
            check=check,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{exc.stderr}") from exc

    return result.stdout.strip() if capture_output else ""


def git_tags() -> set[str]:
    """Fetch all existing git tags."""
    out: str = run(["git", "tag"])
    return set(out.splitlines()) if out else set()


def create_tag(tag: str, dry_run: bool) -> None:
    """Create and push a git tag, or simulate if dry_run is True."""
    if dry_run:
        print(f"🧪 Would create tag: {tag}")
        return

    print(f"✅ Creating tag: {tag}")
    run(["git", "tag", "-a", tag, "-m", tag], capture_output=False)
    run(["git", "push", "origin", tag], capture_output=False)


def package_version_to_semver(pkg_version: str) -> str:
    """
    Convert Alpine package version to SemVer-style version.
    Supports:
    - MAJOR.MINOR-rX       -> MAJOR.MINOR.X
    - MAJOR.MINOR.PATCH-rX -> MAJOR.MINOR.PATCH
    """
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)-r(\d+)", pkg_version)
    if match:
        major, minor, patch, _ = match.groups()
        return f"{major}.{minor}.{patch}"

    match = re.fullmatch(r"(\d+)\.(\d+)-r(\d+)", pkg_version)
    if match:
        major, minor, revision = match.groups()
        return f"{major}.{minor}.{revision}"

    raise ValueError(f"Invalid Alpine version: {pkg_version}")


def extract_last_from(lines: list[str]) -> tuple[str, str] | None:
    """Extract image name and version from the last FROM statement."""
    for line in reversed(lines):
        if match := FROM_RE.match(line):
            image = match.group(1).split("/")[-1]
            version = match.group(2)
            return image, version
    return None


def extract_tagged_package(lines: list[str]) -> tuple[str, str] | None:
    """
    Extract package name and version from tag-version comment.

    Looks for a comment like: # tag-version: postgresql18-client
    Then finds the version of that package in subsequent lines.
    """
    target_package: str | None = None
    in_apk_block = False
    pattern: re.Pattern[str] | None = None

    for line in lines:
        if tag_match := TAG_VERSION_RE.search(line):
            target_package = tag_match.group(1)
            pattern = re.compile(rf"{re.escape(target_package)}=([^\s]+)")
            continue

        if not target_package:
            continue

        if "apk add" in line:
            in_apk_block = True

        if in_apk_block and pattern:
            if version_match := pattern.search(line):
                version = package_version_to_semver(version_match.group(1))
                return target_package, version

        if in_apk_block and not line.rstrip().endswith("\\"):
            in_apk_block = False

    return None


def process_dockerfile(
    dockerfile: Path, existing_tags: set[str], dry_run: bool
) -> None:
    """Process a single Dockerfile and create tags if necessary."""
    dockerfile_name: str = dockerfile.name.removesuffix(".Dockerfile")
    lines: list[str] = dockerfile.read_text().splitlines()

    # Priority 1: Explicitly tagged package line
    if package_version := extract_tagged_package(lines):
        _, version = package_version
        tag = f"{dockerfile_name}-{version}"
    # Priority 2: Last FROM statement
    elif from_version := extract_last_from(lines):
        _, version = from_version
        tag = f"{dockerfile_name}-{version}"
    else:
        return

    if tag in existing_tags:
        print(f"⏭️ Tag exists: {tag}")
        return

    create_tag(tag, dry_run=dry_run)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create git tags based on Dockerfile versions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print tags that would be created without creating them",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_args()

    run(["git", "fetch", "--tags"], capture_output=False)
    existing_tags: set[str] = git_tags()

    for dockerfile in Path("docker").glob("*.Dockerfile"):
        process_dockerfile(dockerfile, existing_tags, args.dry_run)


if __name__ == "__main__":
    main()
