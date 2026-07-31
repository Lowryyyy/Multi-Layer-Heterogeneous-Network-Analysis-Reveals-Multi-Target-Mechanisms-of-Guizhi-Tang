"""
Data Collector: Automated data retrieval from public databases.

Supports:
- TCMSP: herb compounds and targets
- DrugBank: drug-target interactions (XML)
- DisGeNET: gene-disease associations (API/CSV)
- STRING: protein-protein interactions (API)

Usage:
    python collect_data.py [--herb Guizhi] [--all]
"""
import os
import sys
import json
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.config import *

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class TCMSPCollector:
    """Collect data from TCMSP database."""

    def __init__(self, base_url=TCMSP_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session() if HAS_REQUESTS else None

    def get_herb_compounds(self, herb_name):
        """
        Query TCMSP for all compounds of a given herb.
        Returns list of compounds with OB, DL values.

        Note: TCMSP web interface requires manual download.
        This function provides the URL pattern for batch download.
        """
        if not HAS_REQUESTS:
            print("[WARNING] requests library not available.")
            return []

        # TCMSP uses herb name search
        url = f"{self.base_url}"
        print(f"  TCMSP URL: {url}")
        print(f"  Search herb: {herb_name}")
        print(f"  Manual steps:")
        print(f"    1. Visit {url}")
        print(f"    2. Search '{herb_name}' in the herb search box")
        print(f"    3. Set OB >= 30% and DL >= 0.18")
        print(f"    4. Download compound-target list")

        return []

    def get_compound_targets(self, mol_id):
        """Get predicted targets for a compound from TCMSP."""
        if not HAS_REQUESTS:
            return []

        print(f"  Fetching targets for {mol_id} from TCMSP...")
        # TCMSP target prediction page
        url = f"https://old.tcmsp-e.com/tcmspsearch.php?qr={mol_id}&qrs=1"
        try:
            resp = self.session.get(url, timeout=30)
            # Parse response (HTML parsing would be needed)
            print(f"  Response status: {resp.status_code}")
        except Exception as e:
            print(f"  Error: {e}")

        return []


class DrugBankCollector:
    """Collect drug-target interactions from DrugBank."""

    def __init__(self):
        self.api_url = "https://go.drugbank.com/api/v1"

    def search_drug(self, query):
        """Search DrugBank for a drug by name."""
        if not HAS_REQUESTS:
            return None

        # DrugBank open API
        url = f"https://go.drugbank.com/unstructured_search/v2/search.json"
        params = {"query": query, "page": 1, "limit": 5}
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"  DrugBank API error: {e}")
        return None

    def download_xml(self, output_path):
        """
        Download DrugBank full XML database.
        Requires DrugBank account credentials.
        """
        if not DRUGBANK_USER or not DRUGBANK_PASS:
            print("  [INFO] DrugBank credentials not set.")
            print("  To download DrugBank XML:")
            print("    1. Register at https://go.drugbank.com/")
            print("    2. Download full_database.xml.zip")
            print(f"    3. Place in: {output_path}")
            return None

        url = DRUGBANK_XML_URL
        try:
            resp = requests.get(url, auth=(DRUGBANK_USER, DRUGBANK_PASS),
                                stream=True, timeout=120)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"  DrugBank XML downloaded to {output_path}")
                return output_path
        except Exception as e:
            print(f"  Download error: {e}")
        return None


class DisGeNETCollector:
    """Collect gene-disease associations from DisGeNET."""

    def __init__(self, api_url=DISGENET_API_URL):
        self.api_url = api_url

    def get_gene_diseases(self, gene_symbol, gda_threshold=0.1):
        """
        Get disease associations for a gene from DisGeNET.
        Returns list of (disease_name, disease_id, gda_score).
        """
        if not HAS_REQUESTS:
            return []

        url = f"{self.api_url}/gda/gene/{gene_symbol}"
        params = {"min_score": gda_threshold}
        headers = {"Accept": "application/json"}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {
                        "disease_name": d.get("diseaseName", ""),
                        "disease_id": d.get("diseaseId", ""),
                        "gda_score": d.get("score", 0),
                        "pmid_count": d.get("numberOfPmids", 0),
                    }
                    for d in data
                    if d.get("score", 0) >= gda_threshold
                ]
            else:
                print(f"  DisGeNET API returned {resp.status_code}")
        except Exception as e:
            print(f"  DisGeNET API error for {gene_symbol}: {e}")
        return []

    def bulk_download(self, output_path):
        """
        Download DisGeNET bulk data files.
        URL: https://www.disgenet.org/static/disgenet_ap1/files/downloads/
        """
        files = {
            "all_gene_disease": "all_gene_disease_associations.tsv.gz",
            "curated_gene_disease": "curated_gene_disease_associations.tsv.gz",
        }
        base_url = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/"
        for name, filename in files.items():
            url = f"{base_url}{filename}"
            print(f"  Download: {url}")
            print(f"  Save to: {os.path.join(output_path, filename)}")


class STRINGCollector:
    """Collect protein-protein interactions from STRING database."""

    def __init__(self, api_url=STRING_API_URL):
        self.api_url = api_url

    def get_interactions(self, genes, species=9606, min_score=400):
        """
        Get PPI network for a list of genes from STRING.

        Args:
            genes: list of gene symbols
            species: NCBI taxonomy ID (9606 = human)
            min_score: minimum combined score (400 = medium confidence)
        """
        if not HAS_REQUESTS or not genes:
            return []

        url = f"{self.api_url}/json/network"
        params = {
            "identifiers": "%0d".join(genes),
            "species": species,
            "required_score": min_score,
        }

        try:
            resp = requests.get(url, params=params, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                interactions = []
                for edge in data.get("network", {}).get("edges", []):
                    interactions.append({
                        "gene_a": edge.get("preferredName_A", ""),
                        "gene_b": edge.get("preferredName_B", ""),
                        "score": edge.get("score", 0),
                    })
                print(f"  Retrieved {len(interactions)} PPI interactions from STRING")
                return interactions
        except Exception as e:
            print(f"  STRING API error: {e}")
        return []


def collect_all_data(output_dir):
    """Run complete data collection pipeline."""
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("Data Collection Pipeline")
    print("=" * 60)

    # 1. TCMSP data
    print("\n[1/4] TCMSP Data Collection")
    tcmsp = TCMSPCollector()
    for herb_name in HERBS:
        print(f"\n  Herb: {herb_name} ({HERBS[herb_name]['latin']})")
        tcmsp.get_herb_compounds(herb_name)

    # 2. DrugBank data
    print("\n[2/4] DrugBank Data Collection")
    db = DrugBankCollector()
    db.download_xml(os.path.join(output_dir, "drugbank.xml.zip"))

    # 3. DisGeNET data
    print("\n[3/4] DisGeNET Data Collection")
    disgenet = DisGeNETCollector()
    # Collect for key targets
    key_targets = ["TNF", "IL6", "PTGS2", "AKT1", "TP53", "MAPK1", "STAT3", "VEGFA"]
    all_associations = {}
    for gene in key_targets:
        print(f"\n  Gene: {gene}")
        associations = disgenet.get_gene_diseases(gene, gda_threshold=0.1)
        all_associations[gene] = associations
        time.sleep(1)  # Rate limiting

    if all_associations:
        with open(os.path.join(output_dir, "disgenet_associations.json"), "w") as f:
            json.dump(all_associations, f, indent=2)

    # 4. STRING PPI data
    print("\n[4/4] STRING PPI Data Collection")
    string = STRINGCollector()
    all_targets = ["PTGS1", "PTGS2", "TNF", "IL6", "IL1B", "AKT1", "MAPK1",
                   "MAPK8", "TP53", "NFKB1", "RELA", "CASP3", "CASP9", "BCL2",
                   "BAX", "STAT3", "VEGFA", "NOS2", "NOS3", "NFE2L2", "HMOX1",
                   "ESR1", "AR", "NR3C1", "PPARG", "CXCL8", "CCL2", "MMP9",
                   "MMP2", "MYC", "JUN", "FOS"]
    ppi_data = string.get_interactions(all_targets, min_score=400)
    if ppi_data:
        with open(os.path.join(output_dir, "string_ppi.json"), "w") as f:
            json.dump(ppi_data, f, indent=2)

    print(f"\nData collection complete. Files saved to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect data from public databases")
    parser.add_argument("--output-dir", type=str, default=str(RAW_DATA_DIR))
    parser.add_argument("--herb", type=str, default=None, help="Collect for specific herb")
    parser.add_argument("--all", action="store_true", help="Collect all data")
    args = parser.parse_args()

    if args.all or args.herb is None:
        collect_all_data(args.output_dir)
    elif args.herb:
        tcmsp = TCMSPCollector()
        tcmsp.get_herb_compounds(args.herb)
