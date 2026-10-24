#!/usr/bin/env bash
# Gerader Draht 2D (Elmer mgdyn2D_steady_wire) — komplette Validierungskette.
# Abhangigkeiten: ElmerGrid, ElmerSolver (apt PPA elmer-csc-ubuntu), Python3.
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/3 ElmerGrid (1 2: ElmerGrid-.grd -> Elmer-Mesh) =="
rm -rf wire2d
ElmerGrid 1 2 wire2d.grd --log 3

echo "== 2/3 ElmerSolver (Az-Feld, B/H via MagnetoDynamicsCalcFields) =="
ElmerSolver case.sif 2>&1 | grep -iE "Converged|relative error|FINISHED|ERROR|MUMPS" || true

echo "== 3/3 Biot-Savart-Pruefung (f.dat vs. exakte 1/r-Loesung) =="
python3 biot_savart_pruefe.py
