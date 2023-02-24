import os
import sys
import logging
import subprocess
import options
from subprocess import CalledProcessError
import multiprocessing

from typing import Dict, List, Tuple, Any
from tqdm import tqdm

class Generator:
    def __init__(
            self, 
            args : Dict[str, Any]) -> None:
        self._instances = []
        self._args = args
        benchmarkDir = self._args.benchmarks
        if os.path.exists("err-log"):
            subprocess.run(["rm", "err-log"])
        loggingFormat = ("{asctime:s} - "
                         "{funcName:s} - " 
                         "{message:s}")
        logging.basicConfig(
                filename="err-log",
                style="{",
                format=loggingFormat)
        self._logger = logging.getLogger(__name__)
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
            taskFiles = list(map(
                    lambda x : os.path.join(
                            domainDir, x),
                    taskFiles))
            if not len(domainFiles):
                msg = ("No domain file in {}").format(
                        domainDir)
                self._logger.error(msg)
            if len(domainFiles) > 1:
                msg = ("More than one domain file"
                       " in {}".format(domainDir))
                self._logger.warning(msg)
                continue
            domainFile = domainFiles.pop()
            domainFile = os.path.join(
                    domainDir, domainFile)
            self._instances.append(
                    (domain, domainFile, taskFiles))
        self._tasks = list()

    def _copyTasks(
            self, 
            outTaskDir : str, 
            taskFile : str) -> None:
        cmd = ["cp", taskFile, outTaskDir]
        try:
            proc = subprocess.run(
                    cmd, capture_output=True)
            proc.check_returncode()
        except CalledProcessError as err:
            msg = "{} - {}".format(
                    err.cmd, err.output)
            self._logger.error(msg)
        except Exception as err:
            msg = "{} - {}".format(
                    cmd,
                    type(err))
            self._logger.error(msg)

    def _single(
            self, 
            instance : Tuple[str, str, List[str]]) -> None:
        domain, domainFile, taskFiles = instance
        outDomainDir = os.path.join(
                self._args.out, domain)
        for taskFile in taskFiles:
            taskName = os.path.basename(taskFile)
            taskName = taskName.split(".")[0]
            outTaskDir = os.path.join(
                    outDomainDir,
                    taskName)
            if not os.path.exists(outTaskDir):
                os.mkdir(outTaskDir)
            self._copyTasks(outTaskDir, taskFile)
            for rate in self._args.rates:
                outFileDir = "err-rate-{}".format(rate)
                outFileDir = os.path.join(
                        outTaskDir, outFileDir)
                if not os.path.exists(outFileDir):
                    os.mkdir(outFileDir)
                pathFuzzer = "../fuzzer.py"
                if self._args.fuzzer is not None:
                    pathFuzzer = self._args.fuzzer
                cmd = [sys.executable, 
                       pathFuzzer,
                       "--rate",
                       str(rate),
                       "--domain",
                       domainFile,
                       "--outDomain",
                       outFileDir,
                       "--outOperations",
                       outFileDir]
                proc = subprocess.run(
                    cmd, capture_output=True)
                try:
                    proc.check_returncode()
                except CalledProcessError as err:
                    msg = "{} - {}".format(
                            err.cmd, err.output)
                    self._logger.error(msg)
            self._tasks.append(
                    (domainFile, taskFile, outTaskDir))

    def _batch(
            self, 
            instance : Tuple[str, str, List[str]]) -> None:
        domain, domainFile, taskFiles = instance
        outDomainDir = os.path.join(
                self._args.out, domain)
        for rate in self._args.rates:
            outFileDir = "err-rate-{}".format(rate)
            outFileDir = os.path.join(
                    outDomainDir, outFileDir)
            if not os.path.exists(outFileDir):
                os.mkdir(outFileDir)
            pathFuzzer = "../fuzzer.py"
            if self._args.fuzzer is not None:
                    pathFuzzer = self._args.fuzzer
            cmd = [sys.executable, 
                    pathFuzzer,
                    "--rate",
                    str(rate),
                    "--domain",
                    domainFile,
                    "--outDomain",
                    outFileDir,
                    "--outOperations",
                    outFileDir]
            proc = subprocess.run(
                    cmd, capture_output=True)
            try:
                proc.check_returncode()
            except CalledProcessError as err:
                msg = "{} - {}".format(
                        err.cmd, err.output)
                self._logger.error(msg)
        for taskFile in taskFiles:
            taskName = os.path.basename(taskFile)
            taskName = taskName.split(".")[0]
            outTaskDir = os.path.join(
                    outDomainDir,
                    taskName)
            if not os.path.exists(outTaskDir):
                os.mkdir(outTaskDir)
            self._copyTasks(outTaskDir, taskFile)
            self._tasks.append(
                    (domainFile, taskFile, outTaskDir))

    def _run(
            self, 
            instance : Tuple[str, str, List[str]]) -> None:
        domain, _, _ = instance
        outDomainDir = os.path.join(
                self._args.out, domain)
        if not os.path.exists(outDomainDir):
            os.mkdir(outDomainDir)
        if self._args.single:
            self._single(instance)
        if self._args.multiple:
            self._batch(instance)

    def _solve(
            self, 
            task : Tuple[str, str, str]) -> bool:
        domainFile, taskFile, outDir = task
        planFile = os.path.join(
                outDir, "sas_plan")
        sasFile = os.path.join(
                outDir, "output.sas")
        cmd = [sys.executable, 
               self._args.downward, 
               "--alias", 
               "lama-first", 
               "--overall-time-limit", 
               "900", 
               "--plan-file", 
               planFile, 
               "--sas-file",
               sasFile,
               domainFile, 
               taskFile]
        proc = subprocess.run(
                cmd, capture_output=True)
        try:
            proc.check_returncode()
        except CalledProcessError as err:
            msg = "{} - {}".format(
                    err.cmd, err.output)
            self._logger.error(msg)
            return False
        return True

    def start(self) -> None:
        print("- Generating corrupted domains")
        if self._args.single:
            print("- Each domain is paried with one task")
        if self._args.multiple:
            print("- Each domain is paired with multiple tasks")
        for instance in tqdm(self._instances):
            self._run(instance)
        if not self._args.solve:
            return
        assert(self._args.downward is not None)
        print("- Solving the planning tasks")
        numCPUs = multiprocessing.cpu_count()
        print("- Num avaliable CPUs: {}".format(
                numCPUs))
        if self._args.numCPUs is not None:
            numCPUs = self._args.numCPUs
        print("- Using {} CPUs".format(numCPUs))
        with multiprocessing.Pool(numCPUs) as p:
            _ = list(tqdm(p.imap(self._solve, self._tasks), 
                          total=len(self._tasks)))
        print("- Done!")

if __name__ == "__main__":
    args = options.setup()
    generator = Generator(args)
    generator.start()