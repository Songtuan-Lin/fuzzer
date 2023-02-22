import os
import random
import util
from fd.pddl import pddl_file
from fd.pddl.conditions import Atom
from fd.pddl.conditions import Conjunction
from fd.pddl.conditions import Truth
from fd.pddl.effects import Effect

class InvalidFuzzError(Exception):
    def __init__(self, err_msg):
        self.err_msg = err_msg
    
    def __str__(self):
        return self.err_msg
    
    def __repr__(self):
        return str(self)

class InvalidOperationError(Exception):
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        return self.msg
    
    def __repr__(self):
        return str(self)

class Operation:
    def __init__(self, action, atom):
        self.action = action
        self.atom = atom
    
    def apply(self):
        raise NotImplementedError

class EffInsertion(Operation):
    def __str__(self) -> str:
        msg = "<Add {} to Effs: {}>".format(
                self.atom, 
                self.action.name)
        return msg
    
    def __repr__(self) -> str:
        return str(self)

    def apply(self) -> None:
        action_args = set()
        for p in self.action.parameter:
            action_args.add(p.name)
        for arg in self.atom.args:
            if arg not in action_args:
                msg = "Inconsistent Arguments: {} and {}".format(
                        self.atom, self.action.name)
                raise InvalidOperationError(msg)
        eff = Effect([], Truth(), self.atom)
        self.action.effects.append(eff)

class EffDeletion(Operation):
    def __str__(self):
        msg = "<Remove {} from Effs: {}>".format(
                self.atom, self.action.name)
        return msg
    
    def __repr__(self):
        return str(self)

class Fuzz:
    def __init__(self, action, atom):
        self.action = action
        self.atom = atom
    
    def apply(self):
        pass

class FuzzAddEff(Fuzz):
    def __str__(self):
        return "<Add {} to Effs: {}>".format(self.atom, self.action.name)

    def __repr__(self):
        return str(self)

    def apply(self):
        action_args = set(p.name for p in self.action.parameters)
        for arg in self.atom.args:
            if arg not in action_args:
                raise InvalidFuzzError("Patameter types: {} not matching Neg-effs: {}".format(self.atom, self.action.name))
        self.action.effects.append(Effect([], Truth(), self.atom))

class FuzzDelEff(Fuzz):
    def __str__(self):
        return "<Remove {} from Effs: {}>".format(self.atom, self.action.name)
    
    def __repr__(self):
        return str(self)

    def apply(self):
        pop_idx = -1
        for idx, eff in enumerate(self.action.effects):
            if eff.literal == self.atom:
                pop_idx = idx
                break
        if pop_idx == -1:
            raise InvalidFuzzError("{} not in Effs:{}".format(self.atom, self.action.name))
        self.action.effects.pop(pop_idx)

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

class Fuzzer:
    def __init__(self, domain_file, task_file):
        self.task = pddl_file.open(task_file, domain_file)
        self._fuzz_ops = []

    def _matched_atoms(self, action):
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

    def _filter_preds_neg(self, action, atoms):
        neg_atoms = [eff.literal.negate() for eff in action.effects if eff.literal.negated]
        r = []
        for a in atoms:
            if a not in neg_atoms:
                r.append(a)
        return r

    def _fuzz_prec(self, action):
        atoms = self._matched_atoms(action)
        atom = random.choice(atoms)
        op = FuzzPrec(action, atom)
        op.apply()
        self._fuzz_ops.append(op)
    
    def _fuzz_neg_effs(self, action):
        atoms = self._matched_atoms(action)
        atoms = self._filter_preds_neg(action, atoms)
        atom = random.choice(atoms)
        op = FuzzNegEff(action, atom)
        op.apply()
        self._fuzz_ops.append(op)

    def _fuzz_pos_effs(self, action):
        atoms = [eff.literal for eff in action.effects if not eff.literal.negated]
        if len(atoms) != 0:
            atom = random.choice(atoms)
            op = FuzzPosEff(action, atom)
            op.apply()
            self._fuzz_ops.append(op)

    def fuzz(self, k = 1):
        ops = [self._fuzz_prec, self._fuzz_pos_effs, self._fuzz_neg_effs]
        actions = random.sample(self.task.actions, k)
        for action in actions:
            op = random.choice(ops)
            op(action)
    
    def write_domain(self, output_dir):
        with open(os.path.join(output_dir, "domain.pddl"), "w") as f:
            f.write(self.task.domain())

    def write_ops(self, output_dir):
        with open(os.path.join(output_dir, "fuzz_ops.txt"), "w") as f:
            for op in self._fuzz_ops:
                f.write("{}\n".format(op))

class FuzzerNegPrec(Fuzzer):
    def _filter_preds_pos(self, action, atoms):
        pos_atoms = [eff.literal for eff in action.effects if not eff.literal.negated]
        r = []
        for a in atoms:
            if a not in pos_atoms:
                r.append(a)
        return r

    def _fuzz_prec_neg(self, action):
        atoms = self._matched_atoms(action)
        atom = random.choice(atoms)
        op = FuzzPrec(action, atom.negate())
        op.apply()
        self._fuzz_ops.append(op)
    
    def _fuzz_neg_effs_del(self, action):
        atoms = [eff.literal for eff in action.effects if eff.literal.negated]
        if len(atoms) != 0:
            atom = random.choice(atoms)
            op = FuzzDelEff(action, atom)
            op.apply()
            self._fuzz_ops.append(op)

    def _fuzz_pos_effs_add(self, action):
        atoms = self._matched_atoms(action)
        atoms = self._filter_preds_pos(action, atoms)
        atom = random.choice(atoms)
        op = FuzzAddEff(action, atom)
        op.apply()
        self._fuzz_ops.append(op)

    def fuzz(self, k = 1):
        ops = [self._fuzz_prec, self._fuzz_pos_effs, self._fuzz_pos_effs_add, self._fuzz_neg_effs, self._fuzz_neg_effs_del]
        actions = random.sample(self.task.actions, k)
        for action in actions:
            op = random.choices(population=ops, weights=[0.1, 0.2, 0.5, 0.1, 0.1], k=1)
            op[0](action)

if __name__ == "__main__":
    domain_file = "/home/users/u6162630/Datasets/downward-benchmarks/woodworking-opt11-strips/domain.pddl"
    task_file = "/home/users/u6162630/Datasets/downward-benchmarks/woodworking-opt11-strips/p01.pddl"
    fuzzer = Fuzzer(domain_file, task_file)
    fuzzer.fuzz(3)