"""
Graph Builder: Constructs multi-layer heterogeneous graph
from TCMSP, DrugBank, OMIM, DisGeNET data.

Node types: herb, compound, target, disease, drug
Edge types:
  1. herb -> contains -> compound
  2. compound -> acts_on -> target
  3. target -> associated_with -> disease
  4. drug -> targets_protein -> target
  5. drug -> treats -> disease
  6. target -> interacts_with -> target (PPI, from STRING)
  7. compound -> may_treat -> disease (prediction target)
"""
import json
import os
import numpy as np
import torch
from collections import defaultdict

try:
    from torch_geometric.data import HeteroData
    from torch_geometric.transforms import ToUndirected
    HAS_PYG = True
except ImportError:
    HAS_PYG = False
    print("[WARNING] torch_geometric not installed. Using fallback graph representation.")


class HeterogeneousGraphBuilder:
    """Builds the multi-layer heterogeneous knowledge graph for Guizhi Tang."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.node_maps = {}       # node_type -> {name: idx}
        self.node_features = {}   # node_type -> feature_dim
        self.edges = defaultdict(list)  # (src_type, rel, dst_type) -> [(src_idx, dst_idx)]
        self.metadata = {}

    def load_data(self):
        """Load all data files."""
        with open(os.path.join(self.data_dir, "guizhi_tang_compounds.json"), "r", encoding="utf-8") as f:
            self.compounds_data = json.load(f)
        with open(os.path.join(self.data_dir, "compound_target_interactions.json"), "r", encoding="utf-8") as f:
            self.cti_data = json.load(f)
        with open(os.path.join(self.data_dir, "target_disease_associations.json"), "r", encoding="utf-8") as f:
            self.tda_data = json.load(f)

    def _register_node(self, node_type, name):
        """Register a node and return its index."""
        if node_type not in self.node_maps:
            self.node_maps[node_type] = {}
        if name not in self.node_maps[node_type]:
            self.node_maps[node_type][name] = len(self.node_maps[node_type])
        return self.node_maps[node_type][name]

    def _add_edge(self, src_type, rel, dst_type, src_name, dst_name):
        """Add an edge between two nodes."""
        src_idx = self._register_node(src_type, src_name)
        dst_idx = self._register_node(dst_type, dst_name)
        edge_key = (src_type, rel, dst_type)
        self.edges[edge_key].append((src_idx, dst_idx))

    def build_graph(self):
        """Build the complete heterogeneous graph."""
        self.load_data()

        # 1. Herb -> contains -> Compound
        for herb_name, herb_info in self.compounds_data["herbs"].items():
            for comp in herb_info["compounds"]:
                self._add_edge("herb", "contains", "compound",
                               herb_name, comp["name"])

        # 2. Compound -> acts_on -> Target
        for comp in self.cti_data["compounds"]:
            for target in comp["targets"]:
                self._add_edge("compound", "acts_on", "target",
                               comp["name"], target)

        # 3. Target -> associated_with -> Disease
        for disease in self.tda_data["diseases"]:
            for target in disease["associated_targets"]:
                self._add_edge("target", "associated_with", "disease",
                               target, disease["name"])

        # 4. Drug -> targets_protein -> Target
        for drug in self.tda_data["drugbank_drugs_sharing_targets"]:
            for target in drug["targets"]:
                if target in self.node_maps.get("target", {}):
                    self._add_edge("drug", "targets_protein", "target",
                                   drug["name"], target)

        # 5. Drug -> treats -> Disease
        # We create synthetic drug-disease links based on shared targets
        drug_targets = {}
        for drug in self.tda_data["drugbank_drugs_sharing_targets"]:
            drug_targets[drug["name"]] = set(drug["targets"])

        for drug_name, targets in drug_targets.items():
            for disease in self.tda_data["diseases"]:
                disease_targets = set(disease["associated_targets"])
                if len(targets & disease_targets) >= 2:
                    self._add_edge("drug", "treats", "disease",
                                   drug_name, disease["name"])

        # 6. Target -> interacts_with -> Target (PPI from known interactions)
        ppi_pairs = self._get_ppi_pairs()
        for t1, t2 in ppi_pairs:
            if t1 in self.node_maps.get("target", {}) and t2 in self.node_maps.get("target", {}):
                self._add_edge("target", "interacts_with", "target", t1, t2)

        # 7. Compound -> may_treat -> Disease (known links for training/validation)
        self._build_compound_disease_links()

        # Build node features
        self._build_features()

        return self._to_pyg_data() if HAS_PYG else self._to_dict_data()

    def _get_ppi_pairs(self):
        """Generate PPI pairs based on known pathway memberships from STRING."""
        ppi_known = [
            # PI3K-Akt pathway
            ("AKT1", "TP53"), ("AKT1", "MAPK1"), ("AKT1", "BCL2"),
            ("AKT1", "NFKB1"), ("AKT1", "STAT3"), ("AKT1", "MTOR"),
            ("AKT1", "VEGFA"), ("AKT1", "SRC"), ("AKT1", "HRAS"),
            ("AKT1", "CDK2"), ("AKT1", "CDK4"), ("AKT1", "EGFR"),
            ("AKT1", "BAX"), ("AKT1", "CASP3"), ("AKT1", "CASP9"),
            ("AKT1", "NOS3"), ("AKT1", "NOS2"),
            # p53 pathway
            ("TP53", "BCL2"), ("TP53", "BAX"), ("TP53", "CASP3"), ("TP53", "MYC"),
            ("TP53", "CASP9"), ("TP53", "CDK2"), ("TP53", "CDK4"),
            ("TP53", "STAT3"), ("TP53", "NFKB1"), ("TP53", "SRC"),
            ("TP53", "MTOR"), ("TP53", "HRAS"),
            # Apoptosis
            ("BCL2", "BAX"), ("BCL2", "CASP9"), ("BCL2", "CASP3"),
            ("BCL2", "MYC"), ("BCL2", "STAT3"), ("BCL2", "NFKB1"),
            ("BAX", "CASP9"), ("BAX", "CASP3"), ("BAX", "TP53"),
            ("CASP3", "CASP9"), ("CASP3", "BAX"), ("CASP3", "STAT3"),
            ("CASP3", "NFKB1"),
            # Inflammation/TNF
            ("TNF", "NFKB1"), ("TNF", "RELA"), ("TNF", "IL6"), ("TNF", "CASP3"),
            ("TNF", "IL1B"), ("TNF", "CXCL8"), ("TNF", "CCL2"),
            ("TNF", "STAT3"), ("TNF", "MAPK8"), ("TNF", "MMP9"),
            ("TNF", "NOS2"), ("TNF", "BCL2"), ("TNF", "BAX"),
            ("IL6", "STAT3"), ("IL6", "NFKB1"), ("IL6", "JUN"),
            ("IL6", "VEGFA"), ("IL6", "MMP9"), ("IL6", "CCL2"),
            ("IL6", "CXCL8"), ("IL6", "MAPK1"), ("IL6", "AKT1"),
            ("IL1B", "NFKB1"), ("IL1B", "RELA"), ("IL1B", "PTGS2"),
            ("IL1B", "NOS2"), ("IL1B", "CXCL8"), ("IL1B", "CCL2"),
            ("IL1B", "MMP9"), ("IL1B", "STAT3"),
            # NF-kB pathway
            ("NFKB1", "RELA"), ("NFKB1", "STAT3"), ("NFKB1", "NOS2"),
            ("NFKB1", "CASP3"), ("NFKB1", "BCL2"), ("NFKB1", "VEGFA"),
            ("NFKB1", "MMP9"), ("NFKB1", "CXCL8"), ("NFKB1", "CCL2"),
            ("NFKB1", "ICAM1"), ("NFKB1", "MYC"),
            ("RELA", "STAT3"), ("RELA", "NOS2"), ("RELA", "BCL2"),
            ("RELA", "CXCL8"), ("RELA", "MMP9"),
            # MAPK pathway
            ("MAPK1", "MAPK8"), ("MAPK1", "JUN"), ("MAPK1", "FOS"),
            ("MAPK1", "MYC"), ("MAPK1", "STAT3"), ("MAPK1", "EGFR"),
            ("MAPK1", "SRC"), ("MAPK1", "HRAS"), ("MAPK1", "MTOR"),
            ("MAPK1", "CDK2"), ("MAPK1", "VEGFA"),
            ("MAPK8", "JUN"), ("MAPK8", "FOS"), ("MAPK8", "TP53"),
            ("MAPK8", "STAT3"), ("MAPK8", "CASP3"), ("MAPK8", "BCL2"),
            # COX/NOS
            ("PTGS1", "PTGS2"), ("PTGS1", "NOS2"), ("PTGS2", "NOS2"),
            ("PTGS2", "NOS3"), ("PTGS1", "NOS3"), ("PTGS2", "MMP9"),
            ("PTGS2", "STAT3"), ("PTGS2", "NFKB1"),
            ("NOS2", "HMOX1"), ("NOS2", "NFE2L2"), ("NOS2", "STAT3"),
            ("NOS3", "VEGFA"), ("NOS3", "AKT1"), ("NOS3", "SRC"),
            # Nrf2/antioxidant
            ("NFE2L2", "HMOX1"), ("NFE2L2", "NOS2"), ("NFE2L2", "NFKB1"),
            ("NFE2L2", "STAT3"), ("NFE2L2", "TP53"),
            ("HMOX1", "STAT3"), ("HMOX1", "NFKB1"), ("HMOX1", "BCL2"),
            # VEGF/angiogenesis
            ("VEGFA", "AKT1"), ("VEGFA", "STAT3"), ("VEGFA", "SRC"),
            ("VEGFA", "MMP9"), ("VEGFA", "MMP2"), ("VEGFA", "NOS3"),
            ("VEGFA", "EGFR"), ("VEGFA", "HRAS"),
            # Cell cycle
            ("CDK2", "CDK4"), ("CDK2", "TP53"), ("CDK2", "MYC"),
            ("CDK4", "TP53"), ("CDK4", "MYC"), ("CDK4", "SRC"),
            ("MYC", "JUN"), ("MYC", "FOS"), ("MYC", "STAT3"),
            ("MYC", "SRC"), ("MYC", "HRAS"), ("MYC", "MTOR"),
            # Kinase signaling
            ("SRC", "HRAS"), ("SRC", "STAT3"), ("SRC", "EGFR"),
            ("SRC", "MTOR"), ("SRC", "VEGFA"), ("SRC", "NFKB1"),
            ("HRAS", "MAPK1"), ("HRAS", "EGFR"), ("HRAS", "MTOR"),
            ("HRAS", "STAT3"),
            ("EGFR", "STAT3"), ("EGFR", "AKT1"), ("EGFR", "SRC"),
            ("EGFR", "MTOR"), ("EGFR", "MAPK1"),
            ("MTOR", "AKT1"), ("MTOR", "STAT3"),
            # MMPs
            ("MMP9", "MMP2"), ("MMP9", "TNF"), ("MMP9", "STAT3"),
            ("MMP9", "VEGFA"), ("MMP9", "NFKB1"),
            ("MMP2", "STAT3"), ("MMP2", "VEGFA"),
            # Chemokines/adhesion
            ("CXCL8", "CCL2"), ("CXCL8", "NFKB1"), ("CXCL8", "STAT3"),
            ("CCL2", "NFKB1"), ("CCL2", "STAT3"), ("CCL2", "MMP9"),
            ("ICAM1", "SELE"), ("ICAM1", "NFKB1"), ("ICAM1", "TNF"),
            ("SELE", "NFKB1"), ("SELE", "TNF"),
            # Nuclear receptors
            ("ESR1", "AR"), ("ESR1", "STAT3"), ("ESR1", "SRC"),
            ("ESR1", "PPARG"), ("ESR1", "NR3C1"), ("ESR1", "CYP19A1"),
            ("AR", "STAT3"), ("AR", "SRC"), ("AR", "PPARG"),
            ("PPARG", "NFKB1"), ("PPARG", "STAT3"), ("PPARG", "NOS2"),
            ("NR3C1", "STAT3"), ("NR3C1", "NFKB1"),
            # Dopamine/neuro
            ("DRD2", "AKT1"), ("DRD2", "SRC"), ("DRD2", "MAPK1"),
            # Additional
            ("JUN", "FOS"), ("JUN", "STAT3"), ("JUN", "NFKB1"),
            ("FOS", "STAT3"), ("FOS", "NFKB1"),
            ("STAT3", "VEGFA"), ("STAT3", "BCL2"), ("STAT3", "MYC"),
            ("STAT3", "NFKB1"), ("STAT3", "SRC"), ("STAT3", "MTOR"),
            ("CYP19A1", "ESR1"), ("CYP19A1", "AR"),
            ("HSD11B1", "NR3C1"), ("HSD11B1", "PPARG"),
            ("ACE", "ADRB1"), ("ACE", "NOS3"), ("ACE", "AGT"),
            ("ADRB1", "ADRB2"), ("ADRB1", "SRC"),
        ]
        return ppi_known

    def _build_compound_disease_links(self):
        """Build known compound-disease links for training/validation."""
        # Load from data file if available
        known_links = self.tda_data.get("compound_disease_known_links", {})
        if known_links:
            for comp_name, diseases in known_links.items():
                for disease_name in diseases:
                    if (comp_name in self.node_maps.get("compound", {}) and
                            disease_name in self.node_maps.get("disease", {})):
                        self._add_edge("compound", "may_treat", "disease",
                                       comp_name, disease_name)
        else:
            # Fallback to minimal set
            compound_disease = {
                "Quercetin": ["Rheumatoid arthritis", "Hypertension"],
                "Kaempferol": ["Rheumatoid arthritis"],
            }
            for comp_name, diseases in compound_disease.items():
                for disease_name in diseases:
                    if (comp_name in self.node_maps.get("compound", {}) and
                            disease_name in self.node_maps.get("disease", {})):
                        self._add_edge("compound", "may_treat", "disease",
                                       comp_name, disease_name)

    def _build_features(self):
        """Build node feature vectors."""
        # Herb features: one-hot encoding (5 herbs)
        n_herbs = len(self.node_maps.get("herb", {}))
        self.node_features["herb"] = np.eye(n_herbs, dtype=np.float32)

        # Compound features: OB + DL + degree-based
        n_comps = len(self.node_maps.get("compound", {}))
        comp_features = np.zeros((n_comps, 4), dtype=np.float32)  # [OB, DL, degree, herb_count]
        comp_idx_to_info = {}
        for herb_info in self.compounds_data["herbs"].values():
            for comp in herb_info["compounds"]:
                comp_name = comp["name"]
                if comp_name in self.node_maps.get("compound", {}):
                    idx = self.node_maps["compound"][comp_name]
                    comp_features[idx, 0] = comp["ob"] / 100.0  # normalize OB
                    comp_features[idx, 1] = comp["dl"]
                    if idx not in comp_idx_to_info:
                        comp_idx_to_info[idx] = {"herb_count": 0}
                    comp_idx_to_info[idx]["herb_count"] += 1

        # Compound degrees from acts_on edges
        for src_idx, dst_idx in self.edges.get(("compound", "acts_on", "target"), []):
            if src_idx < n_comps:
                comp_features[src_idx, 2] += 1.0  # degree
        comp_features[:, 2] = comp_features[:, 2] / (comp_features[:, 2].max() + 1e-8)

        for idx, info in comp_idx_to_info.items():
            comp_features[idx, 3] = info["herb_count"] / 5.0  # normalize

        self.node_features["compound"] = comp_features

        # Target features: degree-based + type encoding
        n_targets = len(self.node_maps.get("target", {}))
        target_features = np.zeros((n_targets, 3), dtype=np.float32)
        for src_idx, dst_idx in self.edges.get(("compound", "acts_on", "target"), []):
            if dst_idx < n_targets:
                target_features[dst_idx, 0] += 1.0
        for src_idx, dst_idx in self.edges.get(("target", "associated_with", "disease"), []):
            if src_idx < n_targets:
                target_features[src_idx, 1] += 1.0
        # PPI degree
        for src_idx, dst_idx in self.edges.get(("target", "interacts_with", "target"), []):
            if src_idx < n_targets:
                target_features[src_idx, 2] += 1.0
        # Normalize
        for col in range(3):
            mx = target_features[:, col].max()
            if mx > 0:
                target_features[:, col] /= mx
        self.node_features["target"] = target_features

        # Disease features: number of associated targets
        n_diseases = len(self.node_maps.get("disease", {}))
        disease_features = np.zeros((n_diseases, 2), dtype=np.float32)
        for src_idx, dst_idx in self.edges.get(("target", "associated_with", "disease"), []):
            if dst_idx < n_diseases:
                disease_features[dst_idx, 0] += 1.0
        for src_idx, dst_idx in self.edges.get(("drug", "treats", "disease"), []):
            if dst_idx < n_diseases:
                disease_features[dst_idx, 1] += 1.0
        for col in range(2):
            mx = disease_features[:, col].max()
            if mx > 0:
                disease_features[:, col] /= mx
        self.node_features["disease"] = disease_features

        # Drug features: one-hot of target proteins (compressed)
        n_drugs = len(self.node_maps.get("drug", {}))
        self.node_features["drug"] = np.eye(max(n_drugs, 1), dtype=np.float32)

    def _to_pyg_data(self):
        """Convert to PyTorch Geometric HeteroData object."""
        data = HeteroData()

        # Set node features
        for node_type, features in self.node_features.items():
            data[node_type].x = torch.tensor(features, dtype=torch.float32)
            data[node_type].num_nodes = features.shape[0]

        # Set edges
        for (src_type, rel, dst_type), edge_list in self.edges.items():
            if not edge_list:
                continue
            src_indices = [e[0] for e in edge_list]
            dst_indices = [e[1] for e in edge_list]
            edge_index = torch.tensor([src_indices, dst_indices], dtype=torch.long)
            data[(src_type, rel, dst_type)].edge_index = edge_index

        # Store metadata
        self.metadata["node_maps"] = self.node_maps
        self.metadata["reverse_node_maps"] = {
            nt: {v: k for k, v in nm.items()}
            for nt, nm in self.node_maps.items()
        }

        # Print statistics
        print("=" * 60)
        print("Heterogeneous Graph Statistics")
        print("=" * 60)
        for node_type in self.node_maps:
            print(f"  {node_type} nodes: {len(self.node_maps[node_type])}")
        for edge_key, edge_list in self.edges.items():
            print(f"  {edge_key[0]} ->{edge_key[1]}-> {edge_key[2]}: {len(edge_list)} edges")
        total_edges = sum(len(v) for v in self.edges.values())
        print(f"  Total edges: {total_edges}")
        print("=" * 60)

        return data

    def _to_dict_data(self):
        """Fallback: return graph as plain dictionary when PyG is unavailable."""
        graph = {
            "node_maps": self.node_maps,
            "node_features": self.node_features,
            "edges": dict(self.edges),
            "metadata": self.metadata,
        }
        print("=" * 60)
        print("Heterogeneous Graph Statistics (dict mode)")
        print("=" * 60)
        for node_type in self.node_maps:
            print(f"  {node_type} nodes: {len(self.node_maps[node_type])}")
        for edge_key, edge_list in self.edges.items():
            print(f"  {edge_key[0]} ->{edge_key[1]}-> {edge_key[2]}: {len(edge_list)} edges")
        total_edges = sum(len(v) for v in self.edges.values())
        print(f"  Total edges: {total_edges}")
        print("=" * 60)
        return graph

    def save(self, output_dir):
        """Save graph data and metadata."""
        os.makedirs(output_dir, exist_ok=True)
        meta = {
            "node_maps": {k: v for k, v in self.node_maps.items()},
            "edge_counts": {f"{k[0]}->{k[1]}->{k[2]}": len(v)
                            for k, v in self.edges.items()},
        }
        with open(os.path.join(output_dir, "graph_metadata.json"), "w") as f:
            json.dump(meta, f, indent=2)

        # Save node feature dimensions
        dims = {k: v.shape for k, v in self.node_features.items()}
        with open(os.path.join(output_dir, "feature_dims.json"), "w") as f:
            json.dump({k: list(v) for k, v in dims.items()}, f, indent=2)

        print(f"Graph metadata saved to {output_dir}")

    def get_statistics(self):
        """Return graph statistics for the paper."""
        stats = {
            "nodes": {},
            "edges": {},
            "total_nodes": 0,
            "total_edges": 0,
        }
        for node_type in self.node_maps:
            n = len(self.node_maps[node_type])
            stats["nodes"][node_type] = n
            stats["total_nodes"] += n
        for edge_key, edge_list in self.edges.items():
            key_str = f"{edge_key[0]}-{edge_key[1]}-{edge_key[2]}"
            stats["edges"][key_str] = len(edge_list)
            stats["total_edges"] += len(edge_list)
        return stats
