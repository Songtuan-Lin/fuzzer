from fd.pddl.pddl_file import parse_pddl_file
from fd.pddl.tasks import parse_domain, parse_task


class Domain:
    def __init__(self, domainFile) -> None:
        domainPDDL = parse_pddl_file(
            "domain", domainFile)
        (self.domain_name,
         self.requirements,
         self.types, self.constants,
         self.predicates, self.functions,
         self.actions, self.axioms) = parse_domain(domainPDDL)

    def domain(self):
        return ("(define (domain {domain_name})\n"
                "{requirements}\n"
                "(:types\n\t{types})\n"
                "(:constants {constants})\n"
                "(:predicates\n\t{predicates})\n"
                "(:functions {functions})\n"
                "{actions} )").format(
            predicates='\n\t'.join(x.pddl() for x in self.predicates),
            functions='\n\t'.join(x.pddl() for x in self.functions),
            actions='\n\n'.join(x.pddl() for x in self.actions),
            types='\n\t'.join(x.pddl() for x in self.types),
            constants=' '.join(x.pddl() for x in self.constants),
            domain_name=self.domain_name,
            requirements=self.requirements.pddl())


class Task:
    def __init__(self, task_file):
        parsed_file = parse_pddl_file(
            "task", task_file)
        (self.task_name,
         self.task_domain_name,
         self.task_requirements,
         self.objects, self.init,
         self.goal, _) = parse_task(parsed_file)
