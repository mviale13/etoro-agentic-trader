#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "MOVRvest — InvestorPerception inspection"
echo "============================================================"

for file in \
  app/services/signal_service.py \
  app/services/investor_observation_service.py \
  app/services/memory_service.py \
  app/services/pattern_engine.py \
  app/services/investor_dna_service.py \
  app/domain/brain_context.py
do
  echo
  echo "============================================================"
  echo "FILE: $file"
  echo "============================================================"

  if [ -f "$file" ]; then
    sed -n '1,260p' "$file"
  else
    echo "[NOT FOUND]"
  fi
done
