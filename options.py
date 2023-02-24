import argparse

parser = argparse.ArgumentParser(
        description="Options for the Fuzzer")
parser.add_argument(
        "--domain", type=str,
        help="path to the domain")
parser.add_argument(
        "--rate", type=float,
        help="error rate")
parser.add_argument(
        "--outDomain", type=str,
        help="output directory of the domain")
parser.add_argument(
        "--outOperations", type=str,
        help="output directory of the operations")


def setup():
    return parser.parse_args()