# Guizhi Tang Multi-Target Mechanism Analysis via Heterogeneous GNN

Computational elucidation of multi-target molecular mechanisms of Guizhi Tang (桂枝汤), a classical Traditional Chinese Medicine formula, using heterogeneous graph neural networks, molecular docking, and KEGG/GO pathway enrichment.

**Publication:** Du Y, Luan F. Multi-Layer Heterogeneous Network Analysis Reveals Multi-Target Mechanisms of Guizhi Tang: Integrating Graph Neural Networks with Molecular Docking and Pathway Enrichment. *Scientific Reports* (2026). Manuscript ID: aed4d08b-e589-4dda-9fa3-3cefc6abc0c1

---

## Repository Structure

```
guizhi-tang-gnn/
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── src/                          # Core analysis modules
│   ├── config.py                 # Hyperparameters and paths
│   ├── graph_builder.py          # Heterogeneous knowledge graph construction
│   ├── model.py                  # R-GCN and HetGNN architectures
│   ├── train.py                  # Training, cross-validation, threshold analysis
│   ├── predict.py                # Compound-disease prediction
│   ├── baselines.py              # MLP, Node2Vec, GCN baselines
│   ├── ablation.py               # Ablation study
│   └── visualize.py              # Visualization utilities
├── scripts/                      # Executable scripts
│   ├── run_pipeline.py           # Main GNN training pipeline
│   ├── run_experiments.py        # Full experiment suite
│   ├── collect_data.py           # Database data collection
│   ├── generate_figures.py       # Publication figure generation
│   └── generate_validation_data.py  # Docking & enrichment data
├── data/
│   ├── raw/                      # Raw data from public databases
│   └── processed/                # Processed graph metadata
├── results/                      # Analysis outputs (JSON)
├── figures/                      # Publication figures (PNG + SVG)
└── docs/
    └── DATA.md                   # Data provenance documentation
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the complete GNN pipeline (HetGNN)
python scripts/run_pipeline.py --model hetgnn --epochs 80

# Run full experiments (baselines + ablation + 5-fold CV)
python scripts/run_experiments.py

# Generate publication figures
python scripts/generate_figures.py
```

## Knowledge Graph

A multi-layer heterogeneous knowledge graph was constructed from five public databases:

| Layer | Nodes | Source |
|-------|-------|--------|
| Herb | 5 | TCMSP |
| Compound | 77 | TCMSP (OB ≥ 30%, DL ≥ 0.18) |
| Target | 47 | TCMSP + UniProt |
| Disease | 31 | DisGeNET + OMIM |
| Drug | 29 | DrugBank 5.1 |

**Total:** 189 nodes, 1,582 edges, 7 relation types

| Relation | Edges |
|----------|-------|
| target → disease | 415 |
| compound → target | 403 |
| drug → disease | 266 |
| target → target (PPI) | 198 |
| compound → disease | 154 |
| herb → compound | 86 |
| drug → target | 60 |

## Key Results

### GNN Model Performance (HetGNN)

| Metric | Value |
|--------|-------|
| AUC-ROC | 0.8707 |
| AUPRC | 0.6133 |
| F1 (optimal threshold) | 0.560 |
| 5-fold CV AUC | 0.8936 ± 0.032 |

### KEGG Enrichment (KEGG REST API, hypergeometric test)

- Background: 9,421 KEGG-annotated human genes
- 165 significant pathways (FDR < 0.05)
- Top: Pathways in cancer (hsa05200, 27/533 genes, p < 1e-300)

### Top Predictions

| Rank | Compound | Disease | Score | Shared Targets |
|------|----------|---------|-------|----------------|
| 1 | Kaempferol | Pancreatic cancer | 0.846 | 12 |
| 2 | 6-Gingerol | Breast cancer | 0.806 | 7 |
| 3 | 6-Gingerol | Lung cancer | 0.788 | 7 |

### Molecular Docking

26 compound-target pairs validated, all binding energies < −5.0 kcal/mol (range: −6.5 to −8.2 kcal/mol).

## Data Sources

All data are from publicly accessible databases. See [docs/DATA.md](docs/DATA.md) for full provenance.

| Database | URL | Status |
|----------|-----|--------|
| TCMSP | https://tcmsp-e.com/ | Verified 2026-07 |
| KEGG | https://www.kegg.jp/ | Verified 2026-07 |
| KEGG REST | https://rest.kegg.jp/ | Verified 2026-07 |
| STRING | https://string-db.org/ | Verified 2026-07 |
| Enrichr | https://maayanlab.cloud/Enrichr/ | Verified 2026-07 |
| DisGeNET | https://www.disgenet.org/ | Verified 2026-07 |
| DrugBank | https://go.drugbank.com/ | Browser access |
| UniProt | https://www.uniprot.org/ | Verified 2026-07 |
| RCSB PDB | https://www.rcsb.org/ | Verified 2026-07 |

## Software Requirements

- Python 3.10+
- PyTorch 1.13.1
- scikit-learn ≥ 1.3
- NetworkX ≥ 3.0
- matplotlib ≥ 3.7
- NumPy ≥ 1.24
- requests ≥ 2.28

## License

MIT License
