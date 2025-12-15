- microsoft fabric community post on exporting the meta data of a model:
  - https://community.fabric.microsoft.com/t5/DAX-Commands-and-Tips/Power-BI-Documentation/m-p/4795208
  - all of those options only export the full m-query and not the original clean input sources (paths etc)
  - so, the best options seems to be saving in tmdl pbip and then run the python on it, pointing explicitely to the tables and expressions tmdl file
  - also chatgtp "confirmed" that all available export solutions dont extract original source info but rather the full source query, on which you have to apply some sort of regex or similar to extract from the TOM statements e.g. the file path
  - also opening pbix automatically via python / tabular editor and exporting the semantic model does not work
  - optionally one can extend the tmdl parsing to capture all the expressions in order to infer dynamically composed sources, e.g. the = "full_path" = "start_path" & variable & "end_path". we dont do that for the moment, since in the actual use cases we mostly use simple direct file links and load of complete tables from the db

- example_files/tables sourced from
  - https://github.com/mthierba/tmdl-history/tree/main
  - also some more here:
    - https://github.com/pbi-tools/adventureworksdw2020-pbix/tree/main

- Microsoft resources about TMDL and TOM
  - https://learn.microsoft.com/en-gb/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025
  - https://learn.microsoft.com/en-gb/analysis-services/tom/introduction-to-the-tabular-object-model-tom-in-analysis-services-amo?view=sql-analysis-services-2025

- some stuff about pbli-cli:
  - https://pbi.tools/tmdl/

- some discussion on the tabluar editor github, which has a seld build solution for parsing a tmdl file:
  - https://github.com/TabularEditor/TabularEditor/issues/1212
  