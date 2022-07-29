import os
import random
from fd.pddl import pddl_file
from fd.pddl.conditions import Atom
from fd.pddl.conditions import Conjunction
from fd.pddl.conditions import Truth
from fd.pddl.effects import Effect

def find_all_tuples(all_combs):
    if len(all_combs) == 0:
        return [tuple()]
    results = set()
    tail = all_combs.pop(-1)
    heads = find_all_tuples(all_combs)
    for e in tail:
        for t in heads:
            t= list(t)
            t.append(e)
            results.add(tuple(t))
    return results

class InvalidFuzzError(Exception):
    def __init__(self, err_msg):
        self.err_msg = err_msg
    
    def __str__(self):
        return self.err_msg
    
    def __repr__(self):
        return str(self)

class Fuzz:
    def __init__(self, action, atom):
        self.action = action
        self.atom = atom
    
    def apply(self):
        pass

class FuzzPosEff(Fuzz):
    def __str__(self):
        return "<Remove {} from Pos-effs: {}>".format(self.atom, self.action.name)
    
    def __repr__(self):
        return str(self)

    def apply(self):
        pop_idx = -1
        for idx, eff in enumerate(self.action.effects):
            if not eff.literal.negated and eff.literal == self.atom:
                pop_idx = idx
                break
        if pop_idx == -1:
            raise InvalidFuzzError("{} not in Pos-effs:{}".format(self.atom, self.action.name))
        self.action.effects.pop(pop_idx)
        print(self)
    
class FuzzNegEff(Fuzz):
    def __str__(self):
        return "<Add {} to Neg-effs: {}>".format(self.atom, self.action.name)

    def __repr__(self):
        return str(self)

    def apply(self):
        action_args = set(p.name for p in self.action.parameters)
        for arg in self.atom.args:
            if arg not in action_args:
                raise InvalidFuzzError("Patameter types: {} not matching Neg-effs: {}".format(self.atom, self.action.name))
        self.action.effects.append(Effect([], Truth(), self.atom.negate()))
        print(self)

class FuzzPrec(Fuzz):
    def __str__(self):
        return "<Add {} to Prec: {}>".format(self.atom, self.action.name)

    def __repr__(self):
        return str(self)

    def apply(self):
        action_args = set(p.name for p in self.action.parameters)
        for arg in self.atom.args:
            if arg not in action_args:
                raise InvalidFuzzError("Patameter types: {} not matching Prec: {}".format(self.atom, self.action.name))
        atoms = (self.action.precondition,)
        if isinstance(self.action.precondition, Conjunction):
            atoms = self.action.precondition.parts
        new_prec = [a for a in atoms]
        new_prec.append(self.atom)
        self.action.precondition = Conjunction(new_prec)
        print(self)

class Fuzzer:
    def __init__(self, domain_file, task_file):
        self.task = pddl_file.open(task_file, domain_file)

    def __matched_atoms(self, action):
        atoms = []
        for pred in self.task.predicates:
            matched_args = []
            valid_pred = True
            for arg in pred.arguments:
                matched_vars = []
                for para in action.parameters:
                    if para.type == arg.type:
                        matched_vars.append(para.name)
                if len(matched_vars) == 0:
                    valid_pred = False
                    break
                matched_args.append(matched_vars)
            if valid_pred:
                all_tuples = find_all_tuples(matched_args)
                for t in all_tuples:
                    atoms.append(Atom(pred.name, t))
        return atoms

    def __fuzz_prec(self, action):
        atoms = self.__matched_atoms(action)
        atom = random.choice(atoms)
        FuzzPrec(action, atom).apply()
    
    def __fuzz_neg_effs(self, action):
        atoms = self.__matched_atoms(action)
        atom = random.choice(atoms)
        FuzzNegEff(action, atom).apply()

    def __fuzz_pos_effs(self, action):
        atoms = [eff.literal for eff in action.effects if not eff.literal.negated]
        if len(atoms) != 0:
            atom = random.choice(atoms)
            FuzzPosEff(action, atom).apply()

    def fuzz(self, k = 1):
        ops = [self.__fuzz_prec, self.__fuzz_pos_effs, self.__fuzz_neg_effs]
        op = random.choice(ops)
        actions = random.sample(self.task.actions, k)
        for action in actions:
            op(action)
    
    def write_domain(self, output_dir):
        with open(os.path.join(output_dir, "domain.pddl"), "w") as f:
            f.write(self.task.domain())

if __name__ == "__main__":
    domain_file = "/home/garrick/projects/diagnosis/domain.pddl"
    task_file = "/home/garrick/projects/diagnosis/p18.pddl"
    fuzzer = Fuzzer(domain_file, task_file)
    fuzzer.fuzz(3)
    fuzzer.write_domain(os.getcwd())