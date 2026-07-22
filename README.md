# Guizhi Tang Drug Repurposing via Multi-Layer Heterogeneous Graph Neural Networks

## Overview

This project implements a computational drug repurposing framework for **Guizhi Tang** (Cinnamon Twig Decoction), a classical Traditional Chinese Medicine formula, using multi-layer heterogeneous knowledge graphs and Graph Neural Networks (GNNs).

## Architecture

The system constructs a **5-layer heterogeneous network** with the following schema:

```
Herb (5) ──contains──> Compound (~60) ──acts_on──> Target (~34)
                              │                         │
                         may_treat               associated_with
                              │                         │
                              v                         v
                       Disease (~20) <────treats─── Drug (~20)
                                                          │
                                                   targets_protein
                                                          │
                                                          v
                                                    Target (shared)
```

**Node types**: Herb, Compound, Target, Disease, Drug
**Edge types**: contains, acts_on, associated_with, may_treat, treats, targets_protein, interacts_with (PPI)

**GNN models**: R-GCN (Relational GCN), HetGNN (Heterogeneous GNN with attention)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the complete pipeline (R-GCN model)
python run_pipeline.py --model rgcn --epochs 200

# Run with HetGNN model
python run_pipeline.py --model hetgnn --epochs 200

# Optional: collect fresh data from databases
python collect_data.py --all
```

## Project Structure

```
guizhi_tang_gnn_repurposing/
├── README.md
├── requirements.txt
├── collect_data.py              # Data collection from public databases
├── run_pipeline.py              # Main entry point
├── src/
│   ├── __init__.py
│   ├── config.py               # Configuration and hyperparameters
│   ├── graph_builder.py        # Heterogeneous graph construction
│   ├── model.py                # R-GCN and HetGNN models
│   ├── train.py                # Training pipeline with early stopping
│   ├── predict.py              # Drug repurposing predictions
│   └── visualize.py            # Publication-quality figures
├── data/
│   ├── guizhi_tang_compounds.json     # TCMSP compound data
│   ├── compound_target_interactions.json  # Compound-target pairs
│   └── target_disease_associations.json   # Target-disease from DisGeNET/OMIM
└── results/
    ├── best_model.pt
    ├── test_metrics.json
    ├── top_predictions.json
    ├── path_analysis.json
    ├── training_history.json
    └── *.png (figures)
```

## Data Sources

| Database | URL | Data Used |
|----------|-----|-----------|
| TCMSP | https://old.tcmsp-e.com/tcmsp.php | Herb compounds & targets |
| DrugBank | https://go.drugbank.com/ | Drug-target interactions |
| DisGeNET | https://www.disgenet.org/ | Gene-disease associations |
| OMIM | https://omim.org/ | Genetic disease data |
| STRING | https://string-db.org/ | Protein-protein interactions |
| BATMAN-TCM | http://bionet.ncpsb.org.cn/batman-tcm/ | TCM target prediction |

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| OB threshold | >= 30% | Oral bioavailability screening |
| DL threshold | >= 0.18 | Drug-likeness screening |
| Hidden dim | 128 | GNN hidden layer dimension |
| GNN layers | 3 | Number of message passing layers |
| Epochs | 200 | Maximum training epochs |
| Patience | 20 | Early stopping patience |
| Neg sample ratio | 5:1 | Negative to positive sample ratio |

## Citation

If you use this code, please cite:
- TCMSP Database: Ru et al. (2014). TCMSP: A database of systems pharmacology for drug discovery from herbal medicines. *Journal of Cheminformatics*, 6:13.
- R-GCN: Schlichtkrull et al. (2018). Modeling relational data with graph convolutional networks. *ESWC 2018*.

## License

MIT License
