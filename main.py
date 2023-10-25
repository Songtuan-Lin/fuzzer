from fuzzer import *
from transformer import *
from tqdm import tqdm

import os
import logging
import argparse
import subprocess
import multiprocessing

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M",
    filename="log",
    filemode="w")

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
    "--harden", type=float,
    help="percentage of actions to be restricted")
parser.add_argument(
    "--downward", type=str,
    help="path to the fast-downward executable")
parser.add_argument(
    "--time_limit", type=str, default="120",
    help="time limit for running fast-downward")
parser.add_argument(
    "--num_cpus", type=int,
    help="number of cpus used")
args = parser.parse_args()


def exec_cmd(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        if cmd[0] == "cp":
            logging.error(str(proc.stderr))
        elif cmd[0] == args.downward:
            if proc.returncode == 23:
                msg = "Reaching time limit: {task_file}".format(
                    task_file=cmd[-1])
                logging.info(msg)
            elif proc.returncode == 12:
                msg = "No solutions found: {task_file}".format(
                    task_file=cmd[-1])
                logging.warning(msg)
            else:
                msg = "Error for solving the task: {task_file} -- {err_msg}".format(
                    task_file=cmd[-1],
                    err_msg=str(proc.stderr))
                logging.error(msg)
        else:
            logging.error(str(proc.stderr))


def solve(outdir):
    domain_file = os.path.join(outdir, "domain.pddl")
    task_file = os.path.join(outdir, "task.pddl")
    plan_file = os.path.join(outdir, "plan")
    sas_file = os.path.join(outdir, "output.sas")
    cmd = [
        args.downward,
        "--overall-time-limit",
        args.time_limit,
        "--plan-file",
        plan_file,
        "--sas-file",
        sas_file,
        "--alias",
        "lama",
        domain_file,
        task_file]
    exec_cmd(cmd)


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
        cmd = ["cp", domain_file, domain_outfile]
        exec_cmd(cmd)
        modified_outfile = os.path.join(domain_outdir, "domain-modified.pddl")
        if args.relax is None and args.harden is None:
            if "domain-modified.pddl" not in os.listdir(domain_dir):
                continue
            modified_file = os.path.join(domain_dir, "domain-modified.pddl")
            cmd = ["cp", modified_file, modified_outfile]
            exec_cmd(cmd)
        else:
            relax_rate = args.relax if args.relax is not None else 0.0
            harden_rate = args.harden if args.harden is not None else 0.0
            fuzzer = Fuzzer(harden_rate, relax_rate, domain_file)
            fuzzer.output_domain(modified_outfile)
            ops_outfile = os.path.join(domain_outdir, "flaws")
            fuzzer.output_operations(ops_outfile)
        task_names = filter(lambda x: "domain" not in x, os.listdir(domain_dir))
        for task_name in task_names:
            task_file = os.path.join(domain_dir, task_name)
            task_outdir = os.path.join(domain_outdir, task_name.replace(".pddl", ""))
            if not os.path.exists(task_outdir):
                os.mkdir(task_outdir)
            task_outfile = os.path.join(task_outdir, task_name)
            cmd = ["cp", task_file, task_outfile]
            exec_cmd(cmd)
            pos_dir = os.path.join(task_outdir, "white-list")
            if not os.path.exists(pos_dir):
                os.mkdir(pos_dir)
            neg_dir = os.path.join(task_outdir, "black-list")
            if not os.path.exists(neg_dir):
                os.mkdir(neg_dir)
            if args.harden is None:
                # if we do not harden the problem
                # we then relax the definition of positive plans
                # such that a positive plan only need to be a
                # solution to the ground truth problem
                domain_tempfile = os.path.join(pos_dir, "domain.pddl")
                cmd = ["cp", domain_outfile, domain_tempfile]
                exec_cmd(cmd)
                task_tempfile = os.path.join(pos_dir, "task.pddl")
                cmd = ["cp", task_outfile, task_tempfile]
                exec_cmd(cmd)
            else:
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
