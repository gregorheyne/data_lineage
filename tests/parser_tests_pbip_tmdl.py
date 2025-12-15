import json
import os
from pathlib import Path
from data_lineage.lineage_parsers.pbip_tmdl_parser import get_pbip_sources

paths_to_pbips = [
    Path(os.getcwd()) / 'tests/pbip/pseudo_pbip.pbip'
]
# path_to_pbip_file = paths_to_pbips[0]
pbip_sources = get_pbip_sources(paths_to_pbips[0])

print(pbip_sources)

