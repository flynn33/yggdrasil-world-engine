#!/usr/bin/env python3
"""Prepare or verify a wiki projection from an exact repository commit.

This tool writes only explicitly mapped pages and the sidebar roadmap link. It
does not commit, push, remove pages, alter credentials, or accept milestones.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import quote, unquote, urlsplit

OWNER_REPOSITORY = "flynn33/yggdrasil-world-engine"
REVISION_RE = re.compile(r"[0-9a-f]{40}")
LINK_RE = re.compile(
    r"(?P<label>!?\[[^\]\n]*\])\((?P<target><[^>\n]+>|[^()\s\n]+)"
    r"(?P<title>\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\)"
)
REFERENCE_RE = re.compile(
    r"^(?P<prefix>[ \t]{0,3}\[[^\]\n]+\]:[ \t]+)"
    r"(?P<target><[^>\n]+>|\S+)(?P<rest>.*)$"
)


def git(root: Path, *args: str) -> bytes:
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False, env=environment
    )
    if result.returncode:
        raise ValueError(f"Git source operation failed: {' '.join(args[:2])}")
    return result.stdout


def repository_path(value: object, *, destination: bool = False) -> str:
    if (type(value) is not str or not value or "\\" in value or ":" in value
            or any(ord(character) < 32 for character in value)):
        raise ValueError("Mapping paths must be nonempty relative POSIX paths")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError(f"Unsafe mapping path: {value}")
    if destination and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*\.md", value):
        raise ValueError(f"Wiki destination must be an ordinary top-level Markdown page: {value}")
    return str(path)


def source_text(root: Path, revision: str, source: str) -> str:
    try:
        text = git(root, "show", f"{revision}:{source}").decode("utf-8")
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError(f"Source is missing or is not UTF-8 at {revision}: {source}") from error
    return text.replace("\r\n", "\n")


def pinned_url(repository: str, revision: str, path: str, *, tree: bool = False) -> str:
    kind = "tree" if tree else "blob"
    return f"https://github.com/{repository}/{kind}/{revision}/{quote(path, safe='/')}"


def rewrite_links(text: str, source: str, root: Path, revision: str, repository: str) -> str:
    """Rewrite Markdown destinations, leaving external/anchor links and code alone."""
    def target_url(raw: str) -> str:
        target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
        if re.match(r"^[A-Za-z]:[\\/]", target) or target.startswith("\\\\"):
            raise ValueError(f"Local-machine link must not be published: {source}")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return raw
        decoded = unquote(parsed.path)
        if "\\" in decoded:
            raise ValueError(f"Backslash link must not be published: {source}")
        parts = [] if decoded.startswith("/") else list(PurePosixPath(source).parent.parts)
        for part in decoded.split("/"):
            if not part or part == ".":
                continue
            if part == "..":
                if not parts:
                    raise ValueError(f"Link escapes repository: {source}: {target}")
                parts.pop()
            else:
                parts.append(part)
        path = "/".join(parts)
        if not path:
            url = f"https://github.com/{repository}/tree/{revision}"
        else:
            kind = git(root, "cat-file", "-t", f"{revision}:{path}").decode().strip()
            if kind not in ("blob", "tree"):
                raise ValueError(f"Unsupported repository link target: {source}: {target}")
            url = pinned_url(repository, revision, path, tree=kind == "tree")
        if parsed.query:
            url += "?" + parsed.query
        if parsed.fragment:
            url += "#" + parsed.fragment
        return url

    lines = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1]:
                fence = None
            lines.append(line)
            continue
        if fence is not None or line.startswith("    ") or line.startswith("\t"):
            lines.append(line)
            continue
        # An inline-code span is data, not a Markdown hyperlink.
        chunks = re.split(r"(`+[^`\n]*`+)", line)
        for index in range(0, len(chunks), 2):
            chunk = chunks[index]
            reference = REFERENCE_RE.match(chunk.rstrip("\n"))
            if reference:
                suffix = "\n" if chunk.endswith("\n") else ""
                chunks[index] = (reference["prefix"] + target_url(reference["target"])
                                 + reference["rest"] + suffix)
            else:
                chunks[index] = LINK_RE.sub(
                    lambda match: match["label"] + "(" + target_url(match["target"])
                    + (match["title"] or "") + ")", chunk
                )
        lines.append("".join(chunks))
    return "".join(lines)


def read_config(root: Path, revision: str, config_path: str) -> dict:
    config = json.loads(source_text(root, revision, repository_path(config_path)))
    if not isinstance(config, dict) or not isinstance(config.get("pages"), list) or not config["pages"]:
        raise ValueError("Wiki config requires a nonempty pages list")
    if config.get("repository", OWNER_REPOSITORY) != OWNER_REPOSITORY:
        raise ValueError("Wiki mapping belongs to a different owner repository")
    seen = set()
    for page in config["pages"]:
        if not isinstance(page, dict):
            raise ValueError("Each wiki mapping must be an object")
        destination = repository_path(page.get("destination"), destination=True)
        if destination.casefold() in seen:
            raise ValueError(f"Duplicate wiki destination: {destination}")
        seen.add(destination.casefold())
        repository_path(page.get("source"))
        kind = page.get("kind", "copy")
        if kind not in ("copy", "composite", "index", "reference"):
            raise ValueError(f"Unknown wiki page kind: {kind}")
        if kind == "composite":
            sources = page.get("sources")
            if not isinstance(sources, list) or not sources or page["source"] != sources[0]:
                raise ValueError("Composite sources must start with the declared primary source")
            for source in sources:
                repository_path(source)
        if kind == "index":
            entries = page.get("entries")
            if not isinstance(entries, list) or not entries:
                raise ValueError("Index requires source entries")
            for entry in entries:
                if not isinstance(entry, dict) or type(entry.get("label")) is not str or not entry["label"]:
                    raise ValueError("Index entries require a nonempty label")
                repository_path(entry.get("source"))
            for source in page.get("sections", []):
                repository_path(source)
    roadmap = repository_path(config.get("roadmap_destination", "Specification-Roadmap.md"), destination=True)
    if roadmap.casefold() not in seen:
        raise ValueError("Roadmap destination must be an explicitly generated page")
    return config


def projection(source_root: Path, wiki_root: Path, revision: str, config_path: str) -> dict[str, bytes]:
    source_root = source_root.resolve()
    wiki_root = wiki_root.resolve()
    if not source_root.is_dir() or not wiki_root.is_dir():
        raise ValueError("Source and wiki directories must already exist")
    repository_root = Path(git(source_root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if source_root != repository_root:
        raise ValueError("Source root must be the repository top-level directory")
    if wiki_root == source_root or source_root in wiki_root.parents:
        raise ValueError("Wiki checkout must stay outside the source repository")
    if not REVISION_RE.fullmatch(revision):
        raise ValueError("Source revision must be a complete lowercase Git commit SHA")
    resolved = git(source_root, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    if resolved != revision:
        raise ValueError("Source revision did not resolve to the supplied commit")
    config = read_config(source_root, revision, config_path)
    repository = config.get("repository", OWNER_REPOSITORY)
    result = {}
    for page in config["pages"]:
        destination = page["destination"]
        target = wiki_root / destination
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError(f"Unsafe wiki target: {destination}")
        kind = page.get("kind", "copy")
        source = page["source"]
        # Validate every mapped primary source, including reference/index owners.
        primary = source_text(source_root, revision, source)
        if kind == "copy":
            body = rewrite_links(primary, source, source_root, revision, repository)
        else:
            title = page.get("title")
            if type(title) is not str or not title or "\n" in title:
                raise ValueError(f"Page requires a one-line title: {destination}")
            body = f"# {title}\n\n" + page.get("introduction", "") + "\n\n"
            if kind == "composite":
                for section in page["sources"]:
                    text = source_text(source_root, revision, section)
                    body += "---\n\n" + rewrite_links(text, section, source_root, revision, repository).rstrip("\n") + "\n\n"
            elif kind == "index":
                body += "| Schema | Repository source |\n|---|---|\n"
                for entry in page["entries"]:
                    source_text(source_root, revision, entry["source"])
                    body += f"| {entry['label']} | [Source]({pinned_url(repository, revision, entry['source'])}) |\n"
                for section in page.get("sections", []):
                    body += "\n---\n\n" + rewrite_links(source_text(source_root, revision, section), section,
                        source_root, revision, repository).rstrip("\n") + "\n"
            else:
                body += f"[Read the canonical repository specification]({pinned_url(repository, revision, source)}).\n"
        provenance = f"<!-- Repository source: {pinned_url(repository, revision, source)} -->\n\n"
        result[destination] = (provenance + body.rstrip("\n") + "\n").encode("utf-8")
    sidebar = wiki_root / "_Sidebar.md"
    if sidebar.is_symlink() or not sidebar.is_file():
        raise ValueError("An existing regular _Sidebar.md must be preserved")
    original = sidebar.read_bytes()
    text = original.decode("utf-8")
    target = PurePosixPath(config.get("roadmap_destination", "Specification-Roadmap.md")).stem
    links = [name.split("|")[-1].split("#")[0].replace(" ", "-")
             for name in re.findall(r"\[\[([^]\n]+)\]\]", text)]
    links.extend(urlsplit(name).path.rsplit("/", 1)[-1].removesuffix(".md")
                 for name in re.findall(r"\[[^]\n]+\]\(([^)\s]+)\)", text))
    if target not in links:
        newline = b"\r\n" if b"\r\n" in original else b"\n"
        if original and not original.endswith((b"\n", b"\r")):
            original += newline
        original += newline + f"- [[{target.replace('-', ' ')}]]".encode() + newline
    result["_Sidebar.md"] = original
    return result


def prepare(source_root: Path, wiki_root: Path, revision: str, config_path: str, *, verify: bool = False) -> dict:
    # Compute and validate the complete graph before making the first write.
    expected = projection(source_root, wiki_root, revision, config_path)
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in wiki_root.glob("*.md") if path.is_file() and path.name not in expected}
    changed = [name for name, data in expected.items()
               if not (wiki_root / name).is_file() or (wiki_root / name).read_bytes() != data]
    if verify and changed:
        raise ValueError("Wiki projection differs from pinned sources: " + ", ".join(changed))
    if not verify:
        for name in changed:
            (wiki_root / name).write_bytes(expected[name])
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
             for path in wiki_root.glob("*.md") if path.is_file() and path.name not in expected}
    if before != after:
        raise ValueError("Unmapped wiki pages changed during preparation")
    return {"source_revision": revision, "mode": "verify" if verify else "prepare",
            "changed_paths": changed, "generated_sha256": {
                name: hashlib.sha256(data).hexdigest() for name, data in sorted(expected.items())},
            "preserved_unmapped_sha256": dict(sorted(after.items()))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "verify"))
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--wiki-root", required=True, type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--config", default=".github/wiki-sync.json")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if args.report:
            if args.report.exists() or args.report.is_symlink():
                raise ValueError("Preserve previous wiki reports; choose a new report path")
            if not args.report.parent.is_dir():
                raise ValueError("Wiki report parent directory must already exist")
            if args.wiki_root.resolve() == args.report.resolve().parent or args.wiki_root.resolve() in args.report.resolve().parents:
                raise ValueError("Write wiki readback reports outside the wiki checkout")
        report = prepare(args.source_root, args.wiki_root, args.source_revision,
                         args.config, verify=args.mode == "verify")
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wiki {args.mode} passed: {len(report['generated_sha256'])} generated surfaces; "
              f"{len(report['changed_paths'])} changed; {len(report['preserved_unmapped_sha256'])} preserved pages")
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Wiki {args.mode} refused: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
