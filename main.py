from fuzzer import *
from transformer import *

import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
        "--benchmark_dir",  type=str,
        help="path to the ipc benchmark set")
parser.add_argument(
        "--out_dir", type=str,
        help="path to the output directory")
parser.add_argument(
        "--err_rate", type=float,
        help="percentage of actions that have errors")

if __name__ == '__main__':
    args = parser.parse_args()
    root = args.out_dir
    source = args.benchmark_dir
    marked = set()
    for domain in os.listdir(source):
        name = domain.split("-")[0]
        if name in marked:
            continue
        marked.add(name)
        domain_dir = os.path.join(source, domain)
