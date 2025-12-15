"""tmdl_source_parser.py

Parser for extracting "source" sections from .tmdl (Tabular Model Definition Language) files
and pulling out file paths, database connections, and schema/item (table/view) names.


Functions:
    parse_tmdl(text) -> list of source entries
    extract_details_from_source(source_text) -> dict with file_paths, databases, schema_items

This parser is indentation-aware and handles "source =\n    let\n        ... in ..." style blocks,
plus some common TOM expressions like Csv.Document(File.Contents("...")),
Sql.Database("host", "database"), and Source{[Schema="...", Item="..."]}[Data].

Limitations and notes:
 - Heuristics-based; may fail for extremely unusual M or TOM constructs.
 - It does not execute M code — it only parses text with regular expressions.
 - It attempts to support escaped quotes and single/double quoting, but extremely complex
   string concatenations in the M expression are not fully evaluated.

"""

import re
import json
import sys
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

INDENT_RE = re.compile(r"^(?P<indent>[ \t]*)")

# Patterns to capture common source details
FILE_CONTENTS_RE = re.compile(r'File\.Contents\(\s*(["\'])(?P<path>.+?)\1\s*\)', re.IGNORECASE)
CSV_DOC_RE = re.compile(r'Csv\.Document\(\s*File\.Contents\(\s*(["\'])(?P<path>.+?)\1\s*\)', re.IGNORECASE)
SQL_DB_RE = re.compile(r'Sql\.Database\(\s*(["\'])(?P<server>.+?)\1\s*,\s*(["\'])(?P<database>.+?)\3\s*\)', re.IGNORECASE)
SCHEMA_ITEM_RE = re.compile(r'\{\s*\[\s*Schema\s*=\s*(["\'])(?P<schema>.+?)\1\s*,\s*Item\s*=\s*(["\'])(?P<item>.+?)\3\s*\]\s*\}', re.IGNORECASE)
TABLE_SOURCE_INSTANCE_RE = re.compile(r'^\s*source\s*=\s*$', re.IGNORECASE)
SOURCE_LINE_INSTANCE_RE = re.compile(r'^\s*source\s*=\s*', re.IGNORECASE)
EXPRESSION_INSTANCE_RE = re.compile(r'^\s*expression\s+(?P<name>[^=]+?)\s*=\s*(?P<value>.*?)(?:\s+meta\s|\s*$)', re.IGNORECASE)

def _line_indent(line: str) -> int:
    m = INDENT_RE.match(line)
    return len(m.group('indent')) if m else 0

def _strip_quotes(text: str) -> str:
    """Remove enclosing quotes (single or double) if present."""
    if not text:
        return text
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return text

def _get_indentation_block(lines, i):

    n = len(lines)
    line = lines[i]

    # Determine base indent of this line
    base_indent = _line_indent(line)
    # collect subsequent lines that are more indented than base_indent
    j = i + 1
    collected = []
    while j < n:
        ln = lines[j]
        ln_indent = _line_indent(ln)
        # stop if we hit a blank line at the same or less indent or next top-level
        if ln.strip() == '':
            collected.append(ln)
            j += 1
            continue
        if ln_indent <= base_indent and ln.strip() != '':
            break
        collected.append(ln)
        j += 1

    content = '\n'.join(collected).rstrip()

    return content, j

def _get_source_block(text: str) -> List[Dict[str, Any]]:
    """Parse the .tmdl text and return a list of detected source sections.

    Each entry is a dict with keys: start_line (0-based), end_line, content.
    """
    lines = text.splitlines()
    results = []
    i = 0
    n = len(lines)

    while i < n:
        # i=71
        line = lines[i]
        m = TABLE_SOURCE_INSTANCE_RE.match(line)
        if m:
            content, j = _get_indentation_block(lines, i)
            results.append({
                'start_line': i,
                'end_line': j - 1,
                'content': content,
            })
            i = j
            continue
        i += 1

    assert len(results) <= 1, 'found more than one source block in expression passed to get_source_block()'
    if results:
        return results[0]
    else:
        return []

def _get_source_line(text: str) -> List[Dict[str, Any]]:

    lines = text.splitlines()
    results = []
    i = 0
    n = len(lines)

    while i < n:
        # i=71
        line = lines[i]
        m = SOURCE_LINE_INSTANCE_RE.match(line)
        if m:
            results.append({
                'start_line': i,
                'end_line': i,
                'content': line,
            })
        i += 1

    assert len(results) <= 1, 'found more than one source line in text passed to _get_source_line()'
    if results:
        return results[0]
    else:
        return dict()

def _get_source_text_details(source_text: str) -> Dict[str, Any]:
    """From the source block text extract file paths, sql server/db pairs, and schema/item pairs.

    Returns dict: {file_paths: [...], databases: [{'server','database'}], schema_items: [{'schema','item'}]}
    """
    file_paths = []
    databases = []
    schema_items = []

    # Search for Csv.Document(File.Contents("...")) first (most common for files)
    for m in CSV_DOC_RE.finditer(source_text):
        path = m.group('path').strip()
        file_paths.append(path)

    # Also look for standalone File.Contents(...) usages
    for m in FILE_CONTENTS_RE.finditer(source_text):
        path = m.group('path').strip()
        if path not in file_paths:
            file_paths.append(path)

    # Sql.Database("server", "database") occurrences
    for m in SQL_DB_RE.finditer(source_text):
        server = m.group('server').strip()
        database = m.group('database').strip()
        pair = {'server': server, 'database': database}
        if pair not in databases:
            databases.append(pair)

    # Schema and Item lookups in Source{[Schema="...", Item="..."]}
    for m in SCHEMA_ITEM_RE.finditer(source_text):
        schema = m.group('schema').strip()
        item = m.group('item').strip()
        pair = {'schema': schema, 'item': item}
        if pair not in schema_items:
            schema_items.append(pair)

    # Another pattern: access like Source{[Schema="s",Item="t"]}[Data]
    # We'll attempt a more permissive capture if the strict pattern failed
    if not schema_items:
        permissive = re.compile(r'Source\s*\{[^\}]*Schema\s*=\s*(["\'])(?P<schema>.+?)\1[^\}]*Item\s*=\s*(["\'])(?P<item>.+?)\3', re.IGNORECASE)
        for m in permissive.finditer(source_text):
            schema = m.group('schema').strip()
            item = m.group('item').strip()
            pair = {'schema': schema, 'item': item}
            if pair not in schema_items:
                schema_items.append(pair)

    return {
        'file_paths': file_paths,
        'databases': databases,
        'schema_items': schema_items,
    }

def get_source_from_table_tmdl(fp_table_tmdl) -> List[Dict[str, Any]]:
    """
    Top-level helper that finds the source block in a pbi table tmdl 
    and extracts structured details from it.
    """
    with open(fp_table_tmdl, 'r', encoding='utf-8') as f:
        text = f.read()
    source_block = _get_source_block(text)
    details = _get_source_text_details(source_block['content'])
    source = {
        'start_line': source_block['start_line'],
        'end_line': source_block['end_line'],
        'details': details,
        'raw': source_block['content']
    }
    return source

def _get_expression_blocks(text: str):
    
    lines = text.splitlines()
    results = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        m = EXPRESSION_INSTANCE_RE.match(line)
        if m:
            name_raw = m.group('name')
            name = _strip_quotes(name_raw) if name_raw else None
            value_raw = m.group('value')
            value = _strip_quotes(value_raw) if value_raw else None
            content, j = _get_indentation_block(lines, i)
            results.append({
                'name': name,
                'value': value,
                'type': 'expression',
                'start_line': i,
                'end_line': j - 1,
                'content': content,
            })
            i = j
            continue
        i += 1

    return results

def get_expressions(fp_expressions_tmdl):
    """Top-level helper that finds all expression in expressions.tmdl and extracts structure details from it."""
    with open(fp_expressions_tmdl, 'r', encoding='utf-8') as f:
        text = f.read()
    expressions = _get_expression_blocks(text)
    for i, expression in enumerate(expressions):
        # expression = expressions[-2]
        # print(expression['content'])
        source_line = _get_source_line(expression['content'])
        if source_line:
            source_details = _get_source_text_details(source_line['content'])
            expressions[i] = expression | source_details
    
    return expressions

def get_pbip_sources(path_to_pbip_file):
    """
    Extracts Sources from Tables
    Requires saving the pbi report in pbip format with tmdl option activated
    """

    dir_pbib_definition = Path(str(path_to_pbip_file).replace('.pbip', '') + '.SemanticModel/definition')

    dir_tables = dir_pbib_definition / 'tables'
    fps_table_tmdls = [dir_tables / fn for fn in os.listdir(dir_tables)]

    fp_expressions_tmdl = dir_pbib_definition / 'expressions.tmdl'

    # extract sources from tables
    tmdl_table_sources = []
    for fp_table_tmdl in fps_table_tmdls:
        source = {
            'name': fp_table_tmdl.name.upper(),
            'type': 'table_tmdl'
            }
        source = source | get_source_from_table_tmdl(fp_table_tmdl)
        tmdl_table_sources.append(source)
    
    # extract sources from expressions
    expressions = get_expressions(fp_expressions_tmdl)
    
    # collect all oringial sources from tmdl_table_sources and expressions
    pbi_sources = []
    for tmdl_table_source in tmdl_table_sources:
        # tmdl_table_source = tmdl_table_sources[2]
        if 'details' in tmdl_table_source:
            if 'file_paths' in tmdl_table_source['details']:
                for file_path in tmdl_table_source['details']['file_paths']:
                    # file_path = tmdl_table_source['details']['file_paths'][0]
                    pbi_source = {'type': 'file', 'name': file_path}
                    if pbi_source not in pbi_sources:
                        pbi_sources.append(pbi_source)
            if 'schema_items' in tmdl_table_source['details']:
                for schema_pair in tmdl_table_source['details']['schema_items']:
                    # schema_pair = tmdl_table_source['details']['schema_items'][0]
                    pbi_source = {'type': 'db_object', 'name': schema_pair['schema'] + '.' + schema_pair['item']}
                    if pbi_source not in pbi_sources:
                        pbi_sources.append(pbi_source)
    for expression in expressions:
        # expression = expressions[-2]
        if 'file_paths' in expression.keys():
            for filepath in expression['file_paths']:
                pbi_source = {'type': 'file', 'name': filepath}
                if pbi_source not in pbi_sources:
                    pbi_sources.append(pbi_source)
        if 'schema_items' in expression.keys():
            for schema_pair in expression['schema_items']:
                # schema_pair = tmdl_table_source['details']['schema_items'][0]
                pbi_source = {'type': 'db_object', 'name': schema_pair['schema'] + '.' + schema_pair['item']}
                if pbi_source not in pbi_sources:
                    pbi_sources.append(pbi_source)

    return pbi_sources
