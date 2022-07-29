import unittest
from fuzzer import Fuzzer
from fd.pddl.conditions import Atom

class TestFuzzer(unittest.TestCase):
    def test_matched_atoms(self):
        domain_file = "/home/garrick/projects/diagnosis/domain.pddl"
        task_file = "/home/garrick/projects/diagnosis/p18.pddl"
        fuzzer = Fuzzer(domain_file, task_file)
        action = fuzzer.task.actions[0]
        atoms = fuzzer._Fuzzer__matched_atoms(action)
        ground_truth = {Atom("road", ("?l1", "?l1")), Atom("road", ("?l1", "?l2")), Atom("road", ("?l2", "?l1")), Atom("road", ("?l2", "?l2"))}
        self.assertEqual(set(atoms), ground_truth)

if __name__=="__main__":
    unittest.main()