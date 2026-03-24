#! /usr/bin/env python3

_HEADER_ = """
(import (rnrs) (emodl cmslib))

(start-model "{0}")
"""

_FOOTER_ = """
(end-model)
"""

class CmsModel(object):

    def __init__(self, name="unnamed model"):
        self.name = name
        self.species = {}
        self.parameters = {}
        self.functions = {}
        self.reactions = {}
        self.observables = {}
        return

    def add_species(self, name, population=0, observe=False):
        if name in self.species:
            print(f"Model already contains a species '{name}'")
        self.species[name] = population
        if observe:
            self.add_observable(name, name)
        return self

    def add_parameter(self, name, value):
        assert(isinstance(value, (int, float)))
        if name in self.parameters:
            print(f"Model already contains a parameters '{name}' with value {self.parameters[name]}")
        self.parameters[name] = value
        return self

    def add_function(self, name, expression):
        if name not in self.functions:
            self.functions[name] = expression
        else:
            print(f"Model already contains a function called '{name}' ('{self.functions[name]}')")
        return self

    def add_reaction(self, name, reactants, products, propensity, delay=0):
        if name not in self.reactions:
            self.reactions[name] = {"reactants": reactants, "products": products, "propensity": propensity, "delay": delay}
        else:
            print(f"Model already contains a reaction called '{name}'")
        return self

    def add_observable(self, name, expression):
        if name not in self.observables:
            self.observables[name] = expression
        else:
            print(f"Model already contains an observable '{name}' ('{self.observables[name]}')")
        return self

    def __str__(self):

        species = "\n".join([f"(species {name} {population})" for name, population in self.species.items()])
        parameters = "\n".join([f"(param {name} {value})" for name, value in self.parameters.items()])
        functions = "\n".join([f"(func {name} {expression})" for name, expression in self.functions.items()])
        reactions = "\n".join([f"(reaction {name} ({' '.join(reaction['reactants'])}) ({' '.join(reaction['products'])}) {reaction['propensity']} {reaction['delay']})" for name, reaction in self.reactions.items()])
        observables = "\n".join([f"(observe {name} {expression})" for name, expression in self.observables.items()])

        emodl = "\n\n".join([_HEADER_.format(self.name), species, parameters, functions, reactions, observables, _FOOTER_])

        return emodl
