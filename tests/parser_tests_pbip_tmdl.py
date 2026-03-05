import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # project root for data_lineage
import json
import os
from pathlib import Path
from data_lineage.lineage_parsers.pbip_tmdl_parser import get_pbip_sources

paths_to_pbips = [
    Path(os.getcwd()) / 'pbip/pseudo_pbip.pbip'
]
# path_to_pbip_file = paths_to_pbips[0]
pbip_sources = get_pbip_sources(paths_to_pbips[0])

for pbi_source in pbip_sources:
    print(pbi_source)

