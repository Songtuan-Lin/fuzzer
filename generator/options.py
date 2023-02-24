import argparse

def setup():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(
            required=True)
    group.add_argument(
            "--single", action="store_true",
            default=False,
            help=("generate benchmarks where "
                  "one domain is paried with "
                  "one planning task"))
    group.add_argument(
            "--multiple", action="store_true",
            default=False,
            help=("generate benchmarks where "
                  "one domain is paried with "
                  "multiple planning tasks"))
    parser.add_argument(
                "-n", "--numCPUs", type=int,
                help="number of CPUs to be used")
    parser.add_argument(
            "--fuzzer", type=str,
            help="path to the fuzzer")
    parser.add_argument(
            "--benchmarks", required=True,
            help="the directory of the benchmarks")
    parser.add_argument(
            "--rates", nargs="+", 
            required=True, type=float,
            help="specify the error rates")
    parser.add_argument(
            "--out", required=True,
            help="output directory")
    parser.add_argument(
            "--solve", action="store_true",
            default=False,
            help="whether solve the planning tasks")
    parser.add_argument(
            "--downward", type=str,
            help="path to Fast-downward")
    return parser.parse_args()