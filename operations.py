from fd.pddl.conditions import Conjunction
from fd.pddl.conditions import Truth
from fd.pddl.effects import Effect


class InvalidOperationError(Exception):
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        return self.msg
    
    def __repr__(self):
        return str(self)


class InvalidDomainError(Exception):
    def __init__(self):
        self.msg = "Unsupport Features"
    
    def __str__(self):
        return self.msg
    
    def __repr__(self):
        return str(self)


class Operation:
    def __init__(self, action, atom):
        self.action = action
        self.atom = atom
    
    def apply(self) -> None:
        raise NotImplementedError


class EffInsertion(Operation):
    def __str__(self) -> str:
        # msg = "Add {} to Effects: {}".format(
        #         self.atom,
        #         self.action.name)
        component = "effPos"
        if self.atom.negated:
            component = "effNeg"
        paras = [self.action.name, self.atom.predicate, component, "1"]
        msg = ",".join(paras)
        return msg
    
    def __repr__(self) -> str:
        return str(self)

    def apply(self) -> None:
        action_args = set()
        for p in self.action.parameters:
            action_args.add(p.name)
        for arg in self.atom.args:
            if arg not in action_args:
                msg = "Inconsistent Arguments: {} and {}".format(
                        self.atom, self.action.name)
                raise InvalidOperationError(msg)
        eff = Effect([], Truth(), self.atom)
        self.action.effects.append(eff)


class EffDeletion(Operation):
    def __str__(self) -> str:
        # msg = "Delete {} from Effects: {}".format(
        #         self.atom, self.action.name)
        component = "effPos"
        if self.atom.negated:
            component = "effNeg"
        paras = [self.action.name, self.atom.predicate, component, "-1"]
        msg = ",".join(paras)
        return msg
    
    def __repr__(self) -> str:
        return str(self)
    
    def apply(self) -> None:
        pop_idx = -1
        for idx, eff in enumerate(self.action.effects):
            if eff.literal == self.atom:
                pop_idx = idx
                break
        if pop_idx == -1:
            msg = "Invalid effect: {} and {}".format(
                    self.atom, self.action.name)
            raise InvalidOperationError(msg)
        self.action.effects.pop(pop_idx)


class PrecondInsertion(Operation):
    def __str__(self) -> str:
        # msg = "Add {} to Precondition: {}".format(
        #         self.atom, self.action.name)
        component = "precPos"
        if self.atom.negated:
            component = "precNeg"
        paras = [self.action.name, self.atom.predicate, component, "1"]
        msg = ",".join(paras)
        return msg
    
    def __repr__(self) -> str:
        return str(self)
    
    def apply(self) -> None:
        action_args = set(p.name for p in self.action.parameters)
        for arg in self.atom.args:
            if arg not in action_args:
                msg = "Inconsistent Arguments: {} and {}".format(
                        self.atom, self.action.name)
                raise InvalidOperationError(msg)
        atoms = (self.action.precondition,)
        if isinstance(self.action.precondition, Conjunction):
            atoms = self.action.precondition.parts
        new_prec = [a for a in atoms]
        new_prec.append(self.atom)
        self.action.precondition = Conjunction(new_prec)

class PrecondDeletion(Operation):
    def __str__(self) -> str:
        # msg = "Delete {} from Precondition: {}".format(
        #         self.atom, self.action.name)
        component = "precPos"
        if self.atom.negated:
            component = "precNeg"
        paras = [self.action.name, self.atom.predicate, component, "-1"]
        msg = ",".join(paras)
        return msg

    def __repr__(self):
        return str(self)

    def apply(self) -> None:
        pop_idx = -1
        atoms = (self.action.precondition,)
        if isinstance(self.action.precondition, Conjunction):
            atoms = self.action.precondition.parts
        atoms = list(atoms)
        for idx, atom in enumerate(atoms):
            if atom == self.atom:
                pop_idx = idx
                break
        if pop_idx == -1:
            msg = "Invalid precondition: {} in {}".format(
                    self.atom, self.action.name)
            raise InvalidOperationError(msg)
        atoms.pop(pop_idx)
        self.action.precondition = Conjunction(atoms)
