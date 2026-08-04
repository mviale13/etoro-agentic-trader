# MOVRvest

> Explainable Multi-Asset Investment Operating System

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Tests](https://img.shields.io/badge/tests-74%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-v0.4.0--alpha-orange)
![Architecture](https://img.shields.io/badge/architecture-clean-success)

MOVRvest combines portfolio data, market intelligence, investment policy, valuation, and specialist committee opinions to produce transparent investment recommendations.

It does not trade automatically.

It helps the investor make a better-informed decision.

## Philosophy

Before exploring the code, read the
**[Engineering Constitution](docs/ENGINEERING_CONSTITUTION.md)**. It holds the
principles that guide every architectural and investment decision;
[`docs/README.md`](docs/README.md) indexes the rest.

## Current status

**Version:** `v0.4.0-alpha`

MOVRvest is under active development and should not be treated as financial advice or a production trading system.

## Features

- Live eToro demo-account snapshot
- Portfolio allocation analysis
- Configurable investment policy
- Yahoo Finance market data
- Crypto Fear & Greed sentiment
- Market intelligence assessment
- Explainable investment committee
- Momentum, Risk, Cash, Diversification, and Value members
- Daily investment briefing
- Symbol-level explanations
- Watchlist analysis
- Rich terminal output
- Automated tests, linting, formatting, typing, and coverage checks

## Philosophy

MOVRvest is built around three principles:

### Explainable

Every recommendation should include the opinions and reasoning that produced it.

### Deterministic first

Transparent rules are preferred over opaque predictions. AI may later join the committee as one specialist, but it will not replace the decision process.

### Human controlled

MOVRvest recommends. The investor decides.

## Example

MOVRvest
Explain
══════════════════════════════

MSFT

Momentum          BUY     90%
Risk              HOLD    75%
Cash              BUY     90%
Diversification   HOLD    95%
Value             BUY     85%

──────────────────────────────

Recommendation
BUY

Confidence
87%


Commands
movrvest status
movrvest morning
movrvest market
movrvest policy
movrvest decision
movrvest intelligence
movrvest committee
movrvest daily
movrvest explain
movrvest watchlist


Architecture
Providers
    ↓
Domain snapshots
    ↓
Services
    ↓
Committee context
    ↓
Specialist committee members
    ↓
Committee chairman
    ↓
Recommendation
    ↓
Commands and renderers


INSTALLATION


MOVRvest requires Python 3.12 or later.

Clone the repository and enter the project directory:

git clone https://github.com/mviale13/etoro-agentic-trader.git
cd etoro-agentic-trader

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .

python -m pip install pytest pytest-cov ruff mypy pre-commit types-PyYAML

Configuration

Create the required environment configuration for your eToro connection.

Do not commit credentials, API keys, access tokens, or private account data.

The investment policy is stored in:
config/policy.yaml


License

A formal open-source license will be added before the repository is promoted as a public reusable project.