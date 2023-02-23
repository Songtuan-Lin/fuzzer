from fd.pddl.pddl_file import parse_pddl_file
from fd.pddl.tasks import parse_domain

class Domain:
    def __init__(self, domainFile) -> None:
        domainPDDL = parse_pddl_file(
                "domain", domainFile)
        (self.domainName, 
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
                        domain_name=self.domainName,
                        requirements=self.requirements.pddl())
        
        
