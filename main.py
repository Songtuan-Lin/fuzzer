from fuzzer import *
from transformer import *

import os
import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument(
#         "--benchmark_dir",  type=str,
#         help="path to the ipc benchmark set")
# parser.add_argument(
#         "--out_dir", type=str,
#         help="path to the output directory")
# parser.add_argument(
#         "--err_rate", type=float,
#         help="percentage of actions that have errors")
parser = argparse.ArgumentParser()
parser.add_argument(
        "--origin", type=str,
        help="path to the original domain file")
parser.add_argument(
        "--modified", type=str,
        help="path to the modified domain file")
parser.add_argument(
        "--task", type=str,
        help="path to the task file")
parser.add_argument(
        "--pos_dir", type=str,
        help="path to the directory for producing positive plans")
parser.add_argument(
        "--neg_dir", type=str,
        help="path to the directory for producing negative plans")

if __name__ == '__main__':
    # args = parser.parse_args()
    # root = args.out_dir
    # source = args.benchmark_dir
    # marked = set()
    # for domain in os.listdir(source):
    #     name = domain.split("-")[0]
    #     if name in marked:
    #         continue
    #     marked.add(name)
    #     domain_dir = os.path.join(source, domain)
    args = parser.parse_args()
    dx = Domain(args.origin)
    dy = Domain(args.modified)
    tp = Transformer(dx, dy)
    # tn = Transformer(dy, dx)
    tp.output_domain(args.pos_dir)
    tp.output_task(args.task, args.pos_dir)
    # tn.output_domain(args.neg_dir)
    # tn.output_task(args.task, args.neg_dir)
    dx = Domain(args.modified)
    dy = Domain(args.origin)
    tn = Transformer(dx, dy)
    tn.output_domain(args.neg_dir)
    tn.output_task(args.task, args.neg_dir)
