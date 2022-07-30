import os
import math
import argparse
import subprocess
import logging
import traceback
from fuzzer import Fuzzer

arg_parser = argparse.ArgumentParser(description="CMD Arguments for Fuzzer")
arg_parser.add_argument("benchmark_dir", type=str, help="Directory of the benchmark")
arg_parser.add_argument("output_dir", type=str, help="Directory of the output")
arg_parser.add_argument("err_rate", type=float, help="Percentage of actions modified")

if __name__ == "__main__":
    args = arg_parser.parse_args()
    benchmark_dir = args.benchmark_dir
    for d in os.listdir(benchmark_dir):
        if not os.path.isdir(os.path.join(benchmark_dir, d)):
            continue

        domain_name = d
        domain_dir = os.path.join(benchmark_dir, d)
        domain_files = [fn for fn in os.listdir(domain_dir) if "domain" in fn and ".pddl" in fn]
        task_files = [fn for fn in os.listdir(domain_dir) if "domain" not in fn and ".pddl" in fn]

        domain_out_dir = os.path.join(args.output_dir, domain_name)

        if not os.path.exists(domain_out_dir):
            os.mkdir(domain_out_dir)

        if len(domain_files) != 1:
            continue

        domain_file = domain_files.pop()
        for task_file in task_files:
            task_name = task_file.split(".")[0]

            df_path = os.path.join(domain_dir, domain_file)
            tf_path = os.path.join(domain_dir, task_file)
            fuzzer = Fuzzer(df_path, tf_path)

            unsupport_features = [":negative-preconditions", ":disjunctive-preconditions",":existential-preconditions", ":universal-preconditions", ":quantified-preconditions",":conditional-effects", ":derived-predicates"]
            has_uf = False
            for uf in unsupport_features:
                if uf in fuzzer.task.requirements.requirements:
                    has_uf = True
                    break
            if has_uf:
                continue

            task_out_dir = os.path.join(domain_out_dir, task_name)
            if not os.path.exists(task_out_dir):
                os.mkdir(task_out_dir)
            task_out_fuzzed_dir = os.path.join(task_out_dir, "err-rate-{}".format(args.err_rate))
            if not os.path.exists(task_out_fuzzed_dir):
                os.mkdir(task_out_fuzzed_dir)
            num_fuzzed_actions = math.ceil(len(fuzzer.task.actions) * args.err_rate)
            try:
                fuzzer.fuzz(num_fuzzed_actions)
                fuzzer.write_domain(task_out_fuzzed_dir)
                fuzzer.write_ops(task_out_fuzzed_dir)
                subprocess.run(["cp", tf_path, os.path.join(task_out_dir, task_file)])
            except Exception as e:
                logging.error(traceback.format_exc())



