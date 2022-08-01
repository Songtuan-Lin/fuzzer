import os
import argparse
import subprocess

arg_parser = argparse.ArgumentParser(description="CMD Arguments for Fuzzer")
arg_parser.add_argument("old_dir", type=str)
arg_parser.add_argument("new_dir", type=str)
args = arg_parser.parse_args()


for domain_name in os.listdir(args.new_dir):
    if domain_name not in os.listdir(args.old_dir):
        continue
    domain_dir = os.path.join(args.new_dir, domain_name)
    domain_dir_old = os.path.join(args.old_dir, domain_name)
    for task in os.listdir(domain_dir):
        if task not in os.listdir(domain_dir_old):
            continue
        task_dir = os.path.join(domain_dir, task)
        task_dir_old = os.path.join(domain_dir_old, task)
        if "sas_plan" not in os.listdir(task_dir_old):
            continue
        plan_path = os.path.join(task_dir_old, "sas_plan")
        subprocess.run(["cp", plan_path, task_dir])
