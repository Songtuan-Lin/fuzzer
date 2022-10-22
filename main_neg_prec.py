import os
import math
import sys
import argparse
import subprocess
import multiprocessing
import logging
import traceback
import shutil
from tqdm import tqdm
from fuzzer import Fuzzer
from fuzzer import FuzzerNegPrec
from fd.pddl.conditions import Conjunction
from fd.pddl.conditions import Atom, NegatedAtom
from fd.pddl.conditions import Truth
from fd.pddl.effects import Effect

arg_parser = argparse.ArgumentParser(description="CMD Arguments for Fuzzer")
arg_parser.add_argument("benchmark_dir", type=str, help="Directory of the benchmark")
arg_parser.add_argument("output_dir", type=str, help="Directory of the output")
arg_parser.add_argument("err_rate", type=float, help="Percentage of actions modified")
arg_parser.add_argument("--downward", default=None, type=str, help="Path to fast-downward")
arg_parser.add_argument("--num_workers", default=None, type=int, help="Number of working processes")

logging.basicConfig(filename="err.log", level=logging.DEBUG, 
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger=logging.getLogger(__name__)

def run_downward(dir_info):
    df_path, tf_path, plan_out_path = dir_info
    assert(args.downward is not None)
    pf_path = os.path.join(plan_out_path, "sas_plan")
    sas_path = os.path.join(plan_out_path, "output.sas")
    cmd = [sys.executable, args.downward, "--alias", "lama-first", "--overall-time-limit", "900", "--plan-file", pf_path, "--sas-file", sas_path, df_path, tf_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    outs, errs = proc.communicate()
    with open(os.path.join(plan_out_path, "downward_meta_info"), "w") as f:
        f.write(outs)
        f.write(errs)
    if proc.returncode != 0:
        return False
    else:
        return True

def start_downward(dir_infos):

    num_cpus = multiprocessing.cpu_count()
    num_workers = args.num_workers if args.num_workers is not None else num_cpus
    print("===== Starting Running Fast Downward =====" + "\n")
    print("- Number of workers: {}\n".format(num_workers))
    print("- Number of fuzzed tasks: {}\n".format(len(dir_infos)))
    with multiprocessing.Pool(num_workers) as p:
        r = list(tqdm(p.imap(run_downward, dir_infos), total=len(dir_infos)))
    print("- Number of tasks whose solution have been found: {}\n".format(len([t for t in r if t])))


if __name__ == "__main__":
    args = arg_parser.parse_args()
    benchmark_dir = args.benchmark_dir
    fuzzed_tasks = []
    print("==== Starting fuzzing domains =====\n")
    for d in os.listdir(benchmark_dir):
        if not os.path.isdir(os.path.join(benchmark_dir, d)):
            continue

        domain_name = d
        domain_dir = os.path.join(benchmark_dir, d)
        domain_files = [fn for fn in os.listdir(domain_dir) if "domain" in fn and ".pddl" in fn]
        task_files = [fn for fn in os.listdir(domain_dir) if "domain" not in fn and ".pddl" in fn]

        domain_out_dir = os.path.join(args.output_dir, domain_name)

        if len(domain_files) != 1:
            continue

        domain_file = domain_files.pop()
        for task_file in task_files:
            task_name = task_file.split(".")[0]

            df_path = os.path.join(domain_dir, domain_file)
            tf_path = os.path.join(domain_dir, task_file)
            fuzzer = FuzzerNegPrec(df_path, tf_path)

            unsupport_features = [":disjunctive-preconditions",":existential-preconditions", ":universal-preconditions", ":quantified-preconditions",":conditional-effects", ":derived-predicates"]
            has_uf = False
            for uf in unsupport_features:
                if uf in fuzzer.task.requirements.requirements:
                    has_uf = True
                    break
            if has_uf:
                continue

            has_unsp_prec = False
            has_neg_prec = False
            for a in fuzzer.task.actions:
                if has_unsp_prec:
                    break
                if not (isinstance(a.precondition, Conjunction) or isinstance(a.precondition, Atom)):
                    has_unsp_prec = True
                    break 
                atoms = (a.precondition,)
                if isinstance(a.precondition, Conjunction):
                    atoms = a.precondition.parts
                for atom in atoms:
                    if not (isinstance(atom, Atom) or isinstance(atom, NegatedAtom)):
                        has_unsp_prec = True
                        break
                    if atom.negated:
                        has_neg_prec = True
                        break
            if has_unsp_prec:
                continue
            if not has_neg_prec:
                continue

            has_unsp_effs = False
            for a in fuzzer.task.actions:
                if has_unsp_effs:
                    break
                for eff in a.effects:
                    if not isinstance(eff, Effect):
                        has_unsp_effs = True
                        break
                    if eff.condition != Truth() or len(eff.parameters) != 0:
                        has_unsp_effs = True
                        break
            if has_unsp_effs:
                continue

            task_out_dir = os.path.join(domain_out_dir, task_name)
            task_out_fuzzed_dir = os.path.join(task_out_dir, "err-rate-{}".format(args.err_rate))
            num_fuzzed_actions = math.ceil(len(fuzzer.task.actions) * args.err_rate)
            try:
                fuzzer.fuzz(num_fuzzed_actions)
                if not os.path.exists(domain_out_dir):
                    os.mkdir(domain_out_dir)
                if not os.path.exists(task_out_dir):
                    os.mkdir(task_out_dir)
                if not os.path.exists(task_out_fuzzed_dir):
                    os.mkdir(task_out_fuzzed_dir)

                fuzzer.write_domain(task_out_fuzzed_dir)
                fuzzer.write_ops(task_out_fuzzed_dir)
            except Exception as e:
                logging.error(traceback.format_exc())
                shutil.rmtree(task_out_dir)
                if len(os.listdir(domain_out_dir)) == 0:
                    shutil.rmtree(domain_out_dir)
                continue
            subprocess.run(["cp", tf_path, os.path.join(task_out_dir, task_file)])
            fuzzed_tasks.append((df_path, tf_path, task_out_dir))
    print("- Finished\n")

    if args.downward is not None:
        start_downward(fuzzed_tasks)