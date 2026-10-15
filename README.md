# 🛡️ codex-prep

[![CI Status](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-success.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**`codex-prep`** is a fast, zero-dependency CLI utility that prepares, audits, and optimizes any codebase before handing it over to **OpenAI Codex**, cloud coding agents, or LLM workflows.

In under a second, it scans your repository to:
1. 📝 **Auto-generate `AGENTS.md`**: Creates a standardized architectural manifest so OpenAI Codex and autonomous agents understand your directory tree, build commands, and test suites immediately.
2. 🧮 **Estimate Token Budgets & Costs**: Calculates how many tokens your repository consumes (`o200k_base` heuristic) and highlights the heaviest files bloating your context window across `codex-mini-latest`, `o4-mini`, `o3`, and `gpt-4.1`.
3. 🔒 **Catch Leaked Secrets Pre-Flight**: Scans for accidentally hardcoded API keys (OpenAI, AWS, GitHub, Slack, RSA keys, `.env` files) before they leave your local machine or get committed by an agent.

---

## ⚡ Quick Preview

```text
$ python3 codex_prep.py --init
================================================================
🛡️  codex-prep v1.2.0 — AI Agent & OpenAI Codex Readiness Report
================================================================
📂 Target Workspace : /Users/dev/my-api-service
📄 Scanned Files    : 42 (6,840 lines)
🧮 Estimated Tokens : ~64,210 tokens (o200k_base approx)
----------------------------------------------------------------
💰 Estimated Full-Repo Context Cost (Single Pass):
   • codex-mini-latest    : $0.0963 USD ($1.50 / 1M tokens)
   • o4-mini              : $0.0706 USD ($1.10 / 1M tokens)
   • o3                   : $0.6421 USD ($10.00 / 1M tokens)
   • gpt-4.1              : $0.1284 USD ($2.00 / 1M tokens)
----------------------------------------------------------------
📊 Top Context Consumers:
   • src/schema/openapi_spec.json         18,400 tokens (28.7%)
   • src/services/billing_engine.py        6,120 tokens ( 9.5%)
   • tests/fixtures/mock_payloads.py       4,890 tokens ( 7.6%)
----------------------------------------------------------------
✅ Security Check   : Clean! No exposed API keys or secrets found.
================================================================
✨ Generated standardized 'AGENTS.md' for OpenAI Codex!
```

---

## 🚀 Installation & Usage

Because `codex-prep` relies strictly on the Python standard library (**zero external dependencies**), you can run it immediately in any environment without polluting your virtualenv.

### Option 1: Direct Run / Clone
```bash
git clone [https://github.com/juanjoseossalyon/codex-prep.git](https://github.com/juanjoseossalyon/codex-prep.git)
cd codex-prep
python3 codex_prep.py /path/to/your/repo --init
```

### Option 2: Install via `pip`
```bash
pip install -e .
codex-prep --init
```

---

## 🛠️ CLI Options

| Flag | Description |
| :--- | :--- |
| `path` | Target repository directory (defaults to `.`) |
| `--init` | Automatically generates or updates `AGENTS.md` with project structure and test commands |
| `--strict` | Returns exit code `1` if exposed API keys or sensitive files are detected (ideal for CI / `pre-commit` hooks) |
| `--json` | Outputs the full readiness audit as structured JSON for automated pipelines |
| `--self-test` | Runs the built-in diagnostic test suite |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](../../issues) if you want to contribute rules for additional frameworks or secret patterns.

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full details.
