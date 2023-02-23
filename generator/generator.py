import os
import subprocess
import multiprocessing

from typing import Dict, Any
from tqdm import tqdm

class Generator:
    def __init__(
            self, 
            args : Dict[str, Any]) -> None:
        self.instances = []
        self.args = args
        benchmarkDir = self.args.benchmarks
        for domain in os.listdir(benchmarkDir):
            domainDir = os.path.join(
                    benchmarkDir, domain)
            if not os.path.isdir(domainDir):
                continue
            files = list(os.listdir(domainDir))
            files = list(filter(
                    lambda x : x[-5:] == ".pddl",
                    files))
            domainFiles = list(filter(
                    lambda x : "domain" in x,
                    files))
            taskFiles = list(filter(
                    lambda x : "domain" not in x,
                    files))
            if not len(domainFiles):
                msg = "No file for {}".format(
                        domain)
                raise NameError(msg)
            if len(domainFiles) > 1:
                print(("Warning: more than one "
                       "domain file for {}").format(
                            domain))
            domainFile = domainFiles.pop()
            self.instances.append(
                    (domain, domainFile, taskFiles))
    
    def _run(self, instance):
        domain, domainFile, taskFiles = instance
        outDomainDir = os.path.join(
                self.args.outDir, domain)
        if not os.path.exists(outDomainDir):
            os.mkdir(outDomainDir)
        

    def _start(self) -> None:
        for instance in tqdm(self.instances):
            self._run(instance)
