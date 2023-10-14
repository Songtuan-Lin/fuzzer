from domain import Domain
from fd.pddl.predicates import *
from fd.pddl.actions import *
from fd.pddl.conditions import *
from fd.pddl.effects import *
from fd.pddl.pddl_file import parse_pddl_file
from fd.pddl.tasks import *


class Transformer:
    def __init__(
            self,
            origin: Domain,
            modified: Domain):
        self._pred_mapping = dict()
        action_mapping = dict()
        for action in modified.actions:
            for a in origin.actions:
                if action.name == a.name:
                    action_mapping[action] = a
        for pred in modified.predicates:
            self._pred_mapping[pred.name] = Predicate(
                    pred.name+"-copy",
                    pred.arguments)
        extended_preds = list(self._pred_mapping.values())
        extended_preds.append(Predicate("invalid", []))
        unlock_atom = Atom("unlock-origin-domain", [])
        extended_preds.append(Predicate(unlock_atom.predicate, unlock_atom.args))
        extended_actions = list()
        for action in modified.actions:
            origin_action = action_mapping[action]
            lock_atom = Atom(action.name+"-lock", action.parameters)
            extended_preds.append(Predicate(lock_atom.predicate, lock_atom.args))
            new_eff = Effect([], Truth(), lock_atom)
            origin_action.effects.append(new_eff)
            new_eff = Effect([], Truth(), unlock_atom.negate())
            origin_action.effects.append(new_eff)
            origin_prec = (origin_action.precondition,)
            if isinstance(origin_action.precondition, Conjunction):
                origin_prec = origin_action.precondition.parts
            origin_prec = list(origin_prec)
            origin_prec.append(unlock_atom)
            origin_action.precondition = Conjunction(origin_prec)
            atoms = (action.precondition,)
            if isinstance(action.precondition, Conjunction):
                atoms = action.precondition.parts
            atoms = list(atoms)
            new_prec = [lock_atom]
            for idx, atom in enumerate(atoms):
                name = self._pred_mapping[atom.predicate].name
                new_atom = Atom(name, list(atom.args))
                if not atom.negated:
                    new_prec.append(new_atom)
                    negation = new_atom.negate()
                else:
                    new_prec.append(new_atom.negate())
                    negation = new_atom
                # TODO: add unique precondition that can only be satisfied by the corresponding effect of
                # the action in the original domain
                invalidation = Action(
                        action.name + "-stop-{}".format(idx),
                        action.parameters,
                        action.num_external_parameters,
                        Conjunction([negation, lock_atom]),
                        [Effect([], Truth(), Atom("invalid", []))],
                        action.cost)
                extended_actions.append(invalidation)
            new_prec = Conjunction(new_prec)
            new_effs = [lock_atom.negate(), unlock_atom]
            for eff in action.effects:
                atom = eff.literal
                if atom == lock_atom or atom == unlock_atom.negate():
                    continue
                name = self._pred_mapping[atom.predicate].name
                new_atom = Atom(name, list(atom.args))
                if atom.negated:
                    new_atom = new_atom.negate()
                new_effs.append(Effect([], Truth(), new_atom))
            new_action = Action(
                    action.name + "-copy",
                    action.parameters,
                    action.num_external_parameters,
                    new_prec, new_effs, action.cost)
            extended_actions.append(new_action)
        turn_action = Action(
                "turning", [],
                0,
                Conjunction([Atom("invalid", [])]),
                [Effect([], Truth(), unlock_atom)],
                origin.actions[-1].cost)
        extended_actions.append(turn_action)
        self._domain_name = origin.domain_name
        self._requirements = origin.requirements
        self._types = origin.types
        self._constants = origin.constants
        self._actions = origin.actions + extended_actions
        self._predicates = origin.predicates + extended_preds
        self._functions = origin.functions
        self._axioms = origin.axioms

    def output_task(self, task_file, path):
        parsed_file = parse_pddl_file(
            "task", task_file)
        (task_name,
         task_domain_name,
         task_requirements,
         objects, init,
         goal, use_metric) = parse_task(parsed_file)
        goal = list(goal.parts)
        goal.append(Atom("invalid", []))
        goal = Conjunction(goal)
        extension = [Atom("unlock-origin-domain", [])]
        for atom in init:
            extension.append(
                    Atom(self._pred_mapping[atom.predicate].name, atom.args))
        init = init + extension
        metric = ""
        objects = set(objects) - set(self._constants)
        if use_metric:
            metric = "(:metric minimize (total-cost) )"
        body = "(define (problem {problem})\
                       (:domain {domain_name})\
                       (:objects {0}) \
                       (:init {1}) \
                       (:goal {2}) \
                       {metric})".format('\n'.join(x.pddl() for x in set(objects)),
                                         '\n'.join(x.pddl() for x in set(init)),
                                         goal.pddl(), metric=metric,
                                         problem=task_name,
                                         domain_name=self._domain_name)
        with open(path, "w") as f:
            f.write(body)

    def output_domain(self, path):
        body = ("(define (domain {domain_name})\n"
                "{requirements}\n"
                "(:types\n\t{types})\n"
                "(:constants {constants})\n"
                "(:predicates\n\t{predicates})\n"
                "(:functions {functions})\n"
                "{actions} )").format(
                    predicates='\n\t'.join(x.pddl() for x in self._predicates),
                    functions='\n\t'.join(x.pddl() for x in self._functions),
                    actions='\n\n'.join(x.pddl() for x in self._actions),
                    types='\n\t'.join(x.pddl() for x in self._types),
                    constants=' '.join(x.pddl() for x in self._constants),
                    domain_name=self._domain_name,
                    requirements=self._requirements.pddl())
        with open(path, "w") as f:
            f.write(body)



if __name__ == "__main__":
    domain_file_1 = "test/domain.pddl"
    domain_file_2 = "test/domain-2.pddl"
    task_file = "test/task.pddl"
    first = Domain(domain_file_1)
    second = Domain(domain_file_2)
    t = Transformer(first, second)
    t.output_domain("domain-new.pddl")
    t.output_task(task_file, "task-new.pddl")