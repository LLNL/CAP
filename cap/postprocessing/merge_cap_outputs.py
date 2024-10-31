"""
Used to merge the CAP outputs together
"""

import os
import pickle
import numpy as np
import argparse
import pyarrow as pa
import pyarrow.parquet as pq
from bincfg import progressbar


def merge_outputs(output_path, num_chunks, token_path):
    """Combines output parquet files. Assumes all parquet files in output path are used"""
    files = [os.path.join(output_path, f) for f in os.listdir(output_path) if f.endswith(('.parquet', '.pq'))]
    chunks = np.array_split(np.array(files, dtype=object), num_chunks)

    try:
        import duckdb
        _merge_duckdb(output_path, chunks, token_path)
    except ImportError:
        import pandas
        print("WARNING: could not find package: `duckdb`. Using `pandas` instead. This will be much slower and use a lot more memory!")
        _merge_pandas(output_path, chunks, token_path)
    

def _merge_duckdb(output_path, chunks, token_path):
    import duckdb
    print("merging with duckdb")

    with open(token_path, 'rb') as f:
        tokens = pickle.load(f)
    
    for i in range(len(chunks)):
        outfile = _get_filepath(output_path, i)
        duckdb.sql("COPY (SELECT * FROM read_parquet(%s)) TO '%s' (FORMAT 'parquet')" % (repr(list(chunks[i])), outfile))
        _write_tokens_and_INDEX(outfile, tokens)


def _merge_pandas(output_path, chunks, token_path):
    import pandas as pd
    print("merging with pandas")

    with open(token_path, 'rb') as f:
        tokens = pickle.load(f)

    for i in range(len(chunks)):
        outfile = _get_filepath(output_path, i)
        pd.concat([pd.read_parquet(f) for f in chunks[i]], axis=0).to_parquet(outfile, index=False)
        _write_tokens_and_INDEX(outfile, tokens)


def _write_tokens_and_INDEX(outfile, tokens):
    """Loads in file again with pyarrow, inserts tokens and INDEX column, writes back to file"""
    tempfile = outfile + '-temp_.parquet'
    table = pq.read_table(outfile)
    table = table.append_column('INDEX', pa.array(np.arange(len(table)))).replace_schema_metadata({b'tokens': pickle.dumps(tokens)})
    if '__index_level_0__' in table.schema.names:
        table = table.drop(['__index_level_0__'])
    pq.write_table(table, tempfile)
    os.rename(tempfile, outfile)


def _get_filepath(output_path, idx):
    return os.path.join(output_path, 'merged-%d.parquet' % idx)


def merge_logs(cap_path, log_name, delete):
    """
    Merges all the logs together. Assumes all logs in the directory that start with a number are the correct logs to merge.
    Merges only the debug files.
    """
    log_path = os.path.join(cap_path, 'logs')
    debug_files = [os.path.join(log_path, f) for f in os.listdir(log_path) if f.endswith('_debug.log')]

    if log_name[0] in "0123456789":
        raise ValueError("Log name cannot start with a number")
    if not log_name.endswith('.log'):
        log_name = log_name + '.log'
    
    full_lines = []
    for f in progressbar(debug_files):
        with open(f, 'r') as _f:
            full_lines += _f.readlines()
    
    with open(os.path.join(log_path, log_name), 'w') as f:
        f.writelines(full_lines)
    
    if delete:
        for f in [os.path.join(log_path, f) for f in os.listdir(log_path) if f.endswith('_debug.log') or f.endswith('_error.log')]:
            os.remove(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine cap outputs')
    parser.add_argument('path', action='store', help='The path to the cap output. Assumes all parquet files in this directory are used.')
    parser.add_argument('num_chunks', action='store', type=float, help='The total number of chunks (output files) to merge into')
    parser.add_argument('--token_path', action='store', default=None, help='The path to atomic token dictionary. Only used for \'output\' task.')
    parser.add_argument('--task', action='store', default='output', help='The merging task to do. Can be \'logs\' or \'output\'. Defaults to \'output\'')    

    args = parser.parse_args()

    num_chunks = args.num_chunks if args.num_chunks > 0 else 1

    if args.task.lower() in ['logs', 'log']:
        print("Running task:", args.task.lower())
        merge_logs(args.path, 'logs-merged.log')
    elif args.task.lower() in ['outputs', 'output']:
        print("Running task:", args.task.lower())
        merge_outputs(args.path, num_chunks, args.token_path)
    else:
        raise ValueError("Unknown merging task: %s" % repr(args.task))
