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
            dx: Domain,
            dy: Domain):
        self._pred_mapping = dict()
        action_mapping = dict()
        for y_action in dy.actions:
            for a in dx.actions:
                if y_action.name == a.name:
                    action_mapping[y_action] = a
        for pred in dy.predicates:
            self._pred_mapping[pred.name] = Predicate(
                    pred.name+"-copy",
                    pred.arguments)
        extended_preds = list(self._pred_mapping.values())
        extended_preds.append(Predicate("invalid", []))
        x_atom = Atom("unlock-origin-domain", [])
        extended_preds.append(Predicate(x_atom.predicate, x_atom.args))
        extended_actions = list()
        for y_action in dy.actions:
            x_action = action_mapping[y_action]
            y_atom = Atom(y_action.name+"-lock", y_action.parameters)
            extended_preds.append(Predicate(y_atom.predicate, y_atom.args))
            new_eff = Effect([], Truth(), y_atom)
            x_action.effects.append(new_eff)
            new_eff = Effect([], Truth(), x_atom.negate())
            x_action.effects.append(new_eff)
            x_prec = (x_action.precondition,)
            if isinstance(x_action.precondition, Conjunction):
                x_prec = x_action.precondition.parts
            x_prec = list(x_prec)
            x_prec.append(x_atom)
            x_action.precondition = Conjunction(x_prec)
            atoms = (y_action.precondition,)
            if isinstance(y_action.precondition, Conjunction):
                atoms = y_action.precondition.parts
            atoms = list(atoms)
            new_prec = [y_atom]
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
                        y_action.name + "-stop-{}".format(idx),
                        y_action.parameters,
                        y_action.num_external_parameters,
                        Conjunction([negation, y_atom]),
                        [Effect([], Truth(), Atom("invalid", []))],
                        y_action.cost)
                extended_actions.append(invalidation)
            new_prec = Conjunction(new_prec)
            new_effs = [y_atom.negate(), x_atom]
            for eff in y_action.effects:
                atom = eff.literal
                if atom == y_atom or atom == x_atom.negate():
                    continue
                name = self._pred_mapping[atom.predicate].name
                new_atom = Atom(name, list(atom.args))
                if atom.negated:
                    new_atom = new_atom.negate()
                new_effs.append(Effect([], Truth(), new_atom))
            new_action = Action(
                    y_action.name + "-copy",
                    y_action.parameters,
                    y_action.num_external_parameters,
                    new_prec, new_effs, y_action.cost)
            extended_actions.append(new_action)
        turn_action = Action(
                "turning", [],
                0,
                Conjunction([Atom("invalid", [])]),
                [Effect([], Truth(), x_atom)],
                dx.actions[-1].cost)
        extended_actions.append(turn_action)
        self._domain_name = dx.domain_name
        self._requirements = dx.requirements
        self._types = dx.types
        self._constants = dx.constants
        self._actions = dx.actions + extended_actions
        self._predicates = dx.predicates + extended_preds
        self._functions = dx.functions
        self._axioms = dx.axioms

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