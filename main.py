from fuzzer import *
from transformer import *
from tqdm import tqdm

import os
import argparse
import subprocess
import multiprocessing

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
        "--input", type=str,
        help="path to the input directory")
parser.add_argument(
        "--output", type=str,
        help="path to the output directory")
parser.add_argument(
        "--relax", type=float,
        help="percentage of actions to be relaxed")
parser.add_argument(
        "--restrict", type=float,
        help="percentage of actions to be restricted")
parser.add_argument(
        "--downward", type=str,
        help="path to the fast-downward executable")
parser.add_argument(
        "--num_cpus", type=int,
        help="number of cpus used")
args = parser.parse_args()


def solve(outdir):
    domain_file = os.path.join(outdir, "domain.pddl")
    task_file = os.path.join(outdir, "task.pddl")
    plan_file = os.path.join(outdir, "plan")
    sas_file = os.path.join(outdir, "output.sas")
    cmd = [
            args.downward,
            "--overall-time-limit",
            "100",
            "--plan-file",
            plan_file,
            "--sas-file",
            sas_file,
            "--alias",
            "lama",
            domain_file,
            task_file]
    _ = subprocess.run(cmd, capture_output=True)

if __name__ == '__main__':
    instances = []
    for domain in os.listdir(args.input):
        domain_dir = os.path.join(args.input, domain)
        if not os.path.isdir(domain_dir):
            continue
        if "domain.pddl" not in os.listdir(domain_dir):
            continue
        domain_file = os.path.join(domain_dir, "domain.pddl")
        domain_outdir = os.path.join(args.output, domain)
        if not os.path.exists(domain_outdir):
            os.mkdir(domain_outdir)
        domain_outfile = os.path.join(domain_outdir, "domain.pddl")
        _ = subprocess.run(["cp", domain_file, domain_outfile])
        modified_outfile = os.path.join(domain_outdir, "domain-modified.pddl")
        if args.relax is None and args.restrict is None:
            if "domain-modified.pddl" not in os.listdir(domain_dir):
                continue
            modified_file = os.path.join(domain_dir, "domain-modified.pddl")
            _ = subprocess.run(["cp", modified_file, modified_outfile])
        else:
            relax_rate = args.relax if args.relax is not None else 0.0
            restrict_rate = args.restrict if args.restrict is not None else 0.0
            fuzzer = Fuzzer(restrict_rate, relax_rate, domain_file)
            fuzzer.writeDomain(modified_outfile)
        task_names = filter(lambda x: "domain" not in x, os.listdir(domain_dir))
        for task_name in task_names:
            task_file = os.path.join(domain_dir, task_name)
            task_outdir = os.path.join(domain_outdir, task_name.replace(".pddl", ""))
            if not os.path.exists(task_outdir):
                os.mkdir(task_outdir)
            task_outfile = os.path.join(task_outdir, task_name)
            _ = subprocess.run(["cp", task_file, task_outfile])
            pos_dir = os.path.join(task_outdir, "positive-plans")
            if not os.path.exists(pos_dir):
                os.mkdir(pos_dir)
            neg_dir = os.path.join(task_outdir, "negative-plans")
            if not os.path.exists(neg_dir):
                os.mkdir(neg_dir)
            dx, dy = Domain(domain_outfile), Domain(modified_outfile)
            t = Transformer(dx, dy)
            t.output_domain(pos_dir)
            t.output_task(task_outfile, pos_dir)
            instances.append(pos_dir)
            dx, dy = Domain(modified_outfile), Domain(domain_outfile)
            t = Transformer(dx, dy)
            t.output_domain(neg_dir)
            t.output_task(task_outfile, neg_dir)
            instances.append(neg_dir)
    num_cpus = multiprocessing.cpu_count()
    if args.num_cpus is not None:
        num_cpus = args.num_cpus
    with multiprocessing.Pool(num_cpus) as p:
        _ = list(tqdm(p.imap_unordered(solve, instances), total=len(instances)))
