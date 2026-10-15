#!/usr/bin/env python3
"""
codex-prep: Zero-dependency repository readiness scanner, secret detector,
token budget estimator, and AGENTS.md generator for OpenAI Codex & AI Coding Agents.
License: MIT
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

__version__ = "1.2.0"

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    "dist", "build", ".next", ".idea", ".vscode", "coverage", ".pytest_cache"
}

CODE_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript (React)",
    ".jsx": "JavaScript (React)", ".go": "Go", ".rs": "Rust", ".java": "Java",
    ".c": "C", ".cpp": "C++", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".kt": "Kotlin", ".sh": "Shell", ".md": "Markdown", ".json": "JSON",
    ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".sql": "SQL", ".html": "HTML", ".css": "CSS"
}

SECRET_PATTERNS = [
    ("OpenAI API Key", re.compile(r"sk-[a-zA-Z0-9]{20}T3BlbkFJ[a-zA-Z0-9]{20}|sk-proj-[a-zA-Z0-9_-]{32,}")),
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub Personal Token", re.compile(r"ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82}")),
    ("Slack Webhook / Token", re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}")),
    ("Private RSA/SSH Key", re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|PGP) PRIVATE KEY-----")),
    ("Generic Hardcoded Secret", re.compile(r"(?i)(?:api_key|secret_key|access_token|auth_token)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]")),
]

MODEL_PRICING_PER_1M_INPUT = {
    "codex-mini-latest": 1.50,
    "o4-mini": 1.10,
    "o3": 10.00,
    "gpt-4.1": 2.00,
}


def estimate_tokens(text: str) -> int:
    """Fast heuristic BPE token estimation (~4 chars per token for source code)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def scan_repository(root_path: Path) -> Dict:
    total_files = 0
    total_lines = 0
    total_tokens = 0
    lang_breakdown: Dict[str, int] = {}
    findings: List[Tuple[str, int, str]] = []
    largest_files: List[Tuple[str, int]] = []
    tree_entries: List[str] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in sorted(dirnames) if d not in IGNORE_DIRS]
        rel_dir = Path(dirpath).relative_to(root_path)
        if str(rel_dir) != "." and len(tree_entries) < 40:
            tree_entries.append(f"{rel_dir}/")

        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            rel_path = str(fpath.relative_to(root_path))
            ext = fpath.suffix.lower()

            if fname == ".env" or fname.endswith(".pem") or fname.endswith(".key"):
                findings.append((rel_path, 1, f"Sensitive file tracked in workspace ({fname})"))

            if ext not in CODE_EXTENSIONS and fname not in {"Dockerfile", "Makefile"}:
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            total_files += 1
            lines = content.splitlines()
            total_lines += len(lines)
            file_tokens = estimate_tokens(content)
            total_tokens += file_tokens
            largest_files.append((rel_path, file_tokens))

            lang = CODE_EXTENSIONS.get(ext, "Other")
            lang_breakdown[lang] = lang_breakdown.get(lang, 0) + file_tokens

            for line_num, line in enumerate(lines, start=1):
                for label, pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        findings.append((rel_path, line_num, label))

    largest_files.sort(key=lambda x: x[1], reverse=True)
    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "total_tokens": total_tokens,
        "languages": dict(sorted(lang_breakdown.items(), key=lambda x: x[1], reverse=True)),
        "findings": findings,
        "largest_files": largest_files[:10],
        "tree": tree_entries[:25],
    }


def detect_commands(root_path: Path) -> Dict[str, str]:
    cmds = {
        "install": "See README.md for environment setup",
        "test": "pytest",
        "lint": "ruff check .",
    }
    if (root_path / "package.json").exists():
        cmds["install"] = "npm install"
        cmds["test"] = "npm test"
        cmds["lint"] = "npm run lint"
    elif (root_path / "Cargo.toml").exists():
        cmds["install"] = "cargo build"
        cmds["test"] = "cargo test"
        cmds["lint"] = "cargo clippy"
    elif (root_path / "go.mod").exists():
        cmds["install"] = "go mod download"
        cmds["test"] = "go test ./..."
        cmds["lint"] = "golangci-lint run"
    elif (root_path / "pyproject.toml").exists() or (root_path / "requirements.txt").exists():
        cmds["install"] = "pip install -e ."
        cmds["test"] = "python3 codex_prep.py --self-test"
    return cmds


def generate_agents_md(root_path: Path, report: Dict) -> str:
    cmds = detect_commands(root_path)
    primary_langs = ", ".join(list(report["languages"].keys())[:4]) or "Generic"
    tree_block = "\n".join(f"- `{item}`" for item in report["tree"]) or "- Root workspace files"
    heavy_files = "\n".join(
        f"- `{path}` (~{tok:,} tokens)" for path, tok in report["largest_files"][:5]
    )

    return f"""# AGENTS.md

> Auto-generated by [codex-prep](https://github.com/) v{__version__} for **OpenAI Codex** and autonomous coding agents.

## Project Overview
- **Primary Stack:** {primary_langs}
- **Indexed Source Files:** {report["total_files"]} files ({report["total_lines"]:,} lines)
- **Estimated Context Footprint:** ~{report["total_tokens"]:,} tokens

## Key Directories
{tree_block}

## High-Context Files (Read Selectively)
{heavy_files}

## Build, Test & Verification Commands
- **Install / Setup:** `{cmds["install"]}`
- **Run Tests:** `{cmds["test"]}`
- **Lint / Static Check:** `{cmds["lint"]}`

## Agent Guidelines & Safety Rules
1. Always run `{cmds["test"]}` after modifying core logic to verify regressions.
2. Never commit `.env` files, API credentials, or hardcoded tokens.
3. Keep pull requests atomic and update tests alongside new features.
"""


def print_report(report: Dict, root_path: Path) -> None:
    print("=" * 64)
    print(f"🛡️  codex-prep v{__version__} — AI Agent & OpenAI Codex Readiness Report")
    print("=" * 64)
    print(f"📂 Target Workspace : {root_path.resolve()}")
    print(f"📄 Scanned Files    : {report['total_files']} ({report['total_lines']:,} lines)")
    print(f"🧮 Estimated Tokens : ~{report['total_tokens']:,} tokens (o200k_base approx)")
    print("-" * 64)

    print("💰 Estimated Full-Repo Context Cost (Single Pass):")
    for model, price in MODEL_PRICING_PER_1M_INPUT.items():
        cost = (report["total_tokens"] / 1_000_000) * price
        print(f"   • {model:<20} : ${cost:.4f} USD (${price:.2f} / 1M tokens)")
    print("-" * 64)

    if report["largest_files"]:
        print("📊 Top Context Consumers:")
        for path, tok in report["largest_files"][:5]:
            pct = (tok / max(1, report["total_tokens"])) * 100
            print(f"   • {path:<36} {tok:>8,} tokens ({pct:4.1f}%)")
        print("-" * 64)

    if report["findings"]:
        print(f"⚠️  SECURITY ALERT: {len(report['findings'])} Potential Secret(s) Detected!")
        for fpath, line_no, label in report["findings"][:10]:
            print(f"   [!] {fpath}:{line_no} -> {label}")
        print("   👉 Fix or add these files to .gitignore before running cloud agents.")
    else:
        print("✅ Security Check   : Clean! No exposed API keys or secrets found.")
    print("=" * 64)


def run_self_test() -> int:
    """Built-in test suite for CI/CD verification."""
    print("Running codex-prep self-test suite...")
    assert estimate_tokens("print('hello world')") >= 1
    fake_secret = "sk-" + "a" * 20 + "T3BlbkFJ" + "b" * 20
    matched = any(p.search(fake_secret) for _, p in SECRET_PATTERNS)
    assert matched, "Secret scanner failed to detect test OpenAI pattern"
    report = scan_repository(Path("."))
    assert "total_tokens" in report and report["total_files"] >= 1
    md = generate_agents_md(Path("."), report)
    assert "# AGENTS.md" in md
    print("✅ All self-tests passed successfully!")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="codex-prep: Prepare and audit repositories for OpenAI Codex & AI coding agents."
    )
    parser.add_argument("path", nargs="?", default=".", help="Path to repository root (default: current directory)")
    parser.add_argument("--init", action="store_true", help="Generate or update AGENTS.md in the target repository")
    parser.add_argument("--json", action="store_true", help="Output scan report as machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if exposed secrets are found (for CI/pre-commit)")
    parser.add_argument("--self-test", action="store_true", help="Run internal diagnostic test suite")
    parser.add_argument("--version", action="version", version=f"codex-prep {__version__}")

    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    target = Path(args.path)
    if not target.exists() or not target.is_dir():
        print(f"Error: Target path '{target}' does not exist or is not a directory.", file=sys.stderr)
        return 1

    report = scan_repository(target)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report, target)

    if args.init:
        agents_file = target / "AGENTS.md"
        agents_content = generate_agents_md(target, report)
        agents_file.write_text(agents_content, encoding="utf-8")
        if not args.json:
            print(f"✨ Generated standardized '{agents_file}' for OpenAI Codex!")

    if args.strict and report["findings"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
