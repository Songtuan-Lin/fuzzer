import os
import random
import math
from options import setup
from util import getAllTuples
from typing import List, Union
from domain import Domain
from operations import *
from fd.pddl.actions import Action
from fd.pddl.conditions import Atom, NegatedAtom
from fd.pddl.conditions import Conjunction


class Fuzzer:
    def __init__(
            self, rate: float,
            domain_file: str) -> None:
        self.domain = Domain(domain_file)
        self.has_neg_prec = False
        if not self._validated():
            raise InvalidDomainError
        self._ops = []
        self._fetch = (
            lambda negated: lambda xs:
            list(filter(lambda y: y.negated == negated,
                        xs)))
        self._filter = lambda xs: lambda x: x not in xs
        num_errors = math.ceil(len(self.domain.actions) * rate)
        self._fuzz(num_errors)
        self._relax(num_errors)

    def _getAtomsForInsertion(
            self, negated: bool,
            action: Action) -> List[Atom]:
        atoms = [eff.literal for eff in action.effects]
        existingAtoms = self._fetch(negated)(atoms)
        atoms = self._getAtomsMatchingAction(
            negated, action)
        atoms = list(filter(
            self._filter(existingAtoms),
            atoms))
        return atoms

    def _getMatchedVars(self, arg, action):
        vars = [para for para in action.parameters]
        vars = filter(
            lambda v: v.type == arg.type,
            vars)
        vars = [v.name for v in vars]
        return vars

    def _getArguments(self, predicate, action):
        args = list()
        for arg in predicate.arguments:
            vars = self._getMatchedVars(
                arg, action)
            if not len(vars):
                return None
            args.append(vars)
        return args

    def _getAtomsMatchingAction(
            self,
            negated: bool,
            action: Action) -> List[Union[Atom, NegatedAtom]]:
        atoms = []
        for predicate in self.domain.predicates:
            args = self._getArguments(predicate, action)
            if args is None:
                continue
            combinations = getAllTuples(args)
            if negated:
                constructor = (
                    lambda n: lambda t:
                    NegatedAtom(n, t))
            else:
                constructor = (
                    lambda n: lambda t:
                    Atom(n, t))
            for t in combinations:
                atom = constructor(predicate.name)(t)
                atoms.append(atom)
        return atoms

    def _insertEff(
            self,
            action: Action,
            atom: Atom) -> None:
        op = EffInsertion(action, atom)
        op.apply()
        self._ops.append(op)

    def _insertPosEff(self, action: Action) -> None:
        atoms = self._getAtomsForInsertion(
            False, action)
        atom = random.choice(atoms)
        self._insertEff(action, atom)

    def _insertNegEff(self, action: Action) -> None:
        atoms = self._getAtomsForInsertion(
            True, action)
        atom = random.choice(atoms)
        self._insertEff(action, atom)

    def _deleteEff(
            self,
            action: Action,
            atom: Atom) -> None:
        op = EffDeletion(action, atom)
        op.apply()
        self._ops.append(op)

    def _deletePosEff(self, action: Action) -> None:
        atoms = [eff.literal for eff in action.effects]
        atoms = list(filter(
            lambda x: not x.negated,
            atoms))
        atom = random.choice(atoms)
        self._deleteEff(action, atom)

    def _deleteNegEff(self, action: Action) -> None:
        atoms = [eff.literal for eff in action.effects]
        atoms = list(filter(
            lambda x: x.negated,
            atoms))
        atom = random.choice(atoms)
        self._deleteEff(action, atom)

    def _insertPrecond(
            self,
            action: Action,
            atom: Atom) -> None:
        op = PrecondInsertion(action, atom)
        op.apply()
        self._ops.append(op)

    def _insertPosPrecond(
            self,
            action: Action) -> None:
        atoms = self._getAtomsForInsertion(
            False, action)
        atom = random.choice(atoms)
        self._insertPrecond(action, atom)

    def _insertNegPrecond(
            self,
            action: Action) -> None:
        atoms = self._getAtomsForInsertion(
            True, action)
        atom = random.choice(atoms)
        self._insertPrecond(action, atom)

    def _deletePrecond(
            self,
            action: Action) -> None:
        atoms = (action.precondition,)
        if isinstance(action.precondition, Conjunction):
            atoms = action.precondition.parts
        atoms = list(atoms)
        atom = random.choice(atoms)
        op = PrecondDeletion(action, atom)
        op.apply()
        self._ops.append(op)

    def _fuzz(self, k=1):
        if self.has_neg_prec:
            ops = [self._insertPosPrecond,
                   self._insertNegPrecond,
                   self._insertPosEff,
                   self._insertNegEff,
                   self._deletePosEff,
                   self._deleteNegEff]
        else:
            ops = [self._insertPosPrecond,
                   self._insertNegEff,
                   self._deletePosEff]
        actions = random.sample(self.domain.actions, k)
        for action in actions:
            op = random.choice(ops)
            op(action)

    def _relax(self, k=1):
        actions = random.sample(self.domain.actions, k)
        for action in actions:
            self._deletePrecond(action)

    def _validated(self) -> bool:
        illegalFeatures = [
            ":negative-preconditions",
            ":disjunctive-preconditions",
            ":existential-preconditions",
            ":universal-preconditions",
            ":quantified-preconditions",
            ":conditional-effects",
            ":derived-predicates"]
        reqs = self.domain.requirements.requirements
        unsupport = list(filter(
            lambda x: x in illegalFeatures,
            reqs))
        if len(unsupport) > 0:
            return False
        for a in self.domain.actions:
            if isinstance(a.precondition, Atom):
                continue
            if isinstance(a.precondition, NegatedAtom):
                self.has_neg_prec = True
                continue
            if isinstance(a.precondition, Conjunction):
                atoms = a.precondition.parts
                for atom in atoms:
                    if isinstance(atom, Atom):
                        continue
                    if isinstance(atom, NegatedAtom):
                        self.has_neg_prec = True
                        continue
                    return False
                continue
            return False
        return True

    def writeDomain(self, out_dir):
        out_file = os.path.join(
            out_dir, "domain.pddl")
        with open(out_file, "w") as f:
            f.write(self.domain.domain())

    def writeOperations(self, out_dir):
        out_file = os.path.join(
            out_dir, "fuzz_ops.txt")
        with open(out_file, "w") as f:
            for op in self._ops:
                f.write("{}\n".format(op))


if __name__ == "__main__":
    args = setup()
    fuzzer = Fuzzer(args.rate, args.domain)
    if args.outDomain is not None:
        fuzzer.writeDomain(args.outDomain)
    if args.outOperations is not None:
        fuzzer.writeOperations(args.outOperations)
