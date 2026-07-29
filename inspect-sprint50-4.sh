#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "MOVRvest — Sprint 50.4 BrainPipeline inspection"
echo "============================================================"

FILES=(
  "app/application/brain/__init__.py"
  "app/application/brain/investment_brain.py"
  "tests/test_investment_brain_architecture.py"
)

for file in "${FILES[@]}"; do
  echo
  echo "============================================================"
  echo "FILE: $file"
  echo "============================================================"

  if [[ -f "$file" ]]; then
    sed -n '1,260p' "$file"
  else
    echo "[NOT FOUND]"
  fi
done

echo
echo "============================================================"
echo "Related classes and imports"
echo "============================================================"

grep -R \
  --line-number \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=node_modules \
  -E \
  "class (BrainContextBuilder|ExecutiveReasoningService|ExecutiveSummaryService|InvestmentBrain)|InvestmentBrain\\(" \
  app tests \
  || true
