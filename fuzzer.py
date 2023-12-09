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
            self, harden_rate: float,
            relax_rate: float,
            domain_file: str) -> None:
        self.domain = Domain(domain_file)
        self.has_neg_prec = False
        if not self._validated():
            raise InvalidDomainError(domain_file)
        self._ops = []
        self._fetch = (
            lambda negated: lambda xs:
            list(filter(lambda y: y.negated == negated,
                        xs)))
        self._filter = lambda xs: lambda x: x not in xs
        num_errors = math.ceil(len(self.domain.actions) * harden_rate)
        self._harden(num_errors)
        num_errors = math.ceil(len(self.domain.actions) * relax_rate)
        self._relax(num_errors)

    def _atoms_for_insertion(
            self, negated: bool,
            action: Action) -> List[Atom]:
        atoms = [eff.literal for eff in action.effects]
        existing = self._fetch(negated)(atoms)
        atoms = self._atoms_matching_action(
            negated, action)
        atoms = list(filter(
            self._filter(existing),
            atoms))
        atoms = list(filter(
                lambda x: x.predicate != "=",
                atoms))
        return atoms

    def _matching_vars(self, arg, action):
        variables = [para for para in action.parameters]
        variables = filter(
            lambda v: v.type == arg.type,
            variables)
        variables = [v.name for v in variables]
        return variables

    def _parameters(self, predicate, action):
        parameters = list()
        for arg in predicate.arguments:
            variables = self._matching_vars(
                arg, action)
            if not len(variables):
                return None
            parameters.append(variables)
        return parameters

    def _atoms_matching_action(
            self,
            negated: bool,
            action: Action) -> List[Union[Atom, NegatedAtom]]:
        atoms = []
        for predicate in self.domain.predicates:
            args = self._parameters(predicate, action)
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
            atoms = list(filter(
                lambda x: x.predicate != "=",
                atoms))
        return atoms

    def _insert_eff(
            self,
            action: Action,
            atom: Atom) -> None:
        op = EffInsertion(action, atom)
        op.apply()
        self._ops.append(op)

    def _insert_pos_eff(self, action: Action) -> None:
        atoms = self._atoms_for_insertion(
            False, action)
        atom = random.choice(atoms)
        self._insert_eff(action, atom)

    def _insert_neg_eff(self, action: Action) -> None:
        atoms = self._atoms_for_insertion(
            True, action)
        atom = random.choice(atoms)
        self._insert_eff(action, atom)

    def _delete_eff(
            self,
            action: Action,
            atom: Atom) -> None:
        op = EffDeletion(action, atom)
        op.apply()
        self._ops.append(op)

    def _delete_pos_eff(self, action: Action) -> None:
        atoms = [eff.literal for eff in action.effects]
        atoms = list(filter(
            lambda x: not x.negated,
            atoms))
        atom = random.choice(atoms)
        self._delete_eff(action, atom)

    def _delete_neg_eff(self, action: Action) -> None:
        atoms = [eff.literal for eff in action.effects]
        atoms = list(filter(
            lambda x: x.negated,
            atoms))
        atom = random.choice(atoms)
        self._delete_eff(action, atom)

    def _insert_prec(
            self,
            action: Action,
            atom: Atom) -> None:
        op = PrecondInsertion(action, atom)
        op.apply()
        self._ops.append(op)

    def _insert_pos_prec(
            self,
            action: Action) -> None:
        atoms = self._atoms_for_insertion(
            False, action)
        atom = random.choice(atoms)
        self._insert_prec(action, atom)

    def _insert_neg_prec(
            self,
            action: Action) -> None:
        atoms = self._atoms_for_insertion(
            True, action)
        atom = random.choice(atoms)
        self._insert_prec(action, atom)

    def _delete_prec(
            self,
            action: Action) -> None:
        atoms = (action.precondition,)
        if isinstance(action.precondition, Conjunction):
            atoms = action.precondition.parts
        atoms = list(atoms)
        # candidates = []
        # for atom in atoms:
        #     for a in self.domain.actions:
        #         effs = {e.literal for e in a.effects}
        #         if atom in effs:
        #             candidates.append(atom)
        #             break
        # if len(candidates) == 0:
        #     return False
        # atom = random.choice(candidates)
        atom = random.choice(atoms)
        op = PrecondDeletion(action, atom)
        op.apply()
        self._ops.append(op)
        # return True

    def _harden(self, k=1):
        if self.has_neg_prec:
            ops = [self._insert_pos_prec,
                   self._insert_neg_prec,
                   self._insert_pos_eff,
                   self._insert_neg_eff,
                   self._delete_pos_eff,
                   self._delete_neg_eff]
        else:
            ops = [self._insert_pos_prec,
                   self._insert_neg_eff,
                   self._delete_pos_eff]
        actions = random.sample(self.domain.actions, k)
        for action in actions:
            op = random.choice(ops)
            op(action)

    def _relax(self, k=1):
        # count = 0
        # while True:
        #     action = random.choice(self.domain.actions)
        #     if self._delete_prec(action):
        #         count += 1
        #     if count == k:
        #         break
        # ops = [self._deleteNegEff, self._deletePrecond]
        actions = random.sample(self.domain.actions, k)
        for action in actions:
            self._delete_prec(action)

    def _validated(self) -> bool:
        illegalFeatures = [
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

    def output_domain(self, outfile):
        with open(outfile, "w") as f:
            f.write(self.domain.domain())

    def output_operations(self, outfile):
        with open(outfile, "w") as f:
            for op in self._ops:
                f.write("{}\n".format(op))


if __name__ == "__main__":
    args = setup()
    fuzzer = Fuzzer(args.rate, args.domain)
    if args.outDomain is not None:
        fuzzer.output_domain(args.outDomain)
    if args.outOperations is not None:
        fuzzer.output_operations(args.outOperations)
