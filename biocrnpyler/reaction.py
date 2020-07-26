#  Copyright (c) 2020, Build-A-Cell. All rights reserved.
#  See LICENSE file in the project root directory for details.

from .sbmlutil import *
from .propensities import Propensity, MassAction, HillNegative
from.species import *
import warnings
import numpy as np
from typing import List, Union, Dict
import itertools
import copy


class Reaction(object):
    """ An abstract representation of a chemical reaction in a CRN
    A reaction has the form:
    .. math::
       \sum_i n_i I_i --> \sum_i m_i O_i @ rate = k
       where n_i is the count of the ith input, I_i, and m_i is the count of the
       ith output, O_i.
    If the reaction is reversible, the reverse reaction is also included:
    .. math::
       \sum_i m_i O_i  --> \sum_i n_i I_i @ rate = k_rev
    """
    def __init__(self, *args, **kwargs):
        # This is to have backward compatibility for now, should be removed!
        if args:
            kwargs['inputs'] = args[0]
            kwargs['outputs'] = args[1]
        if 'k' in kwargs:
            self.old_interface(**kwargs)
        else:
            self.new_interface(**kwargs)

    def old_interface(self,inputs, outputs, k = 0, input_coefs = None,
                      output_coefs = None, k_rev = 0, propensity_type = "massaction",
                      rate_formula = None, propensity_params = None):
        warnings.warn('This way to initialize a reaction object is deprecated, please refactor your code!', DeprecationWarning)

        if propensity_type == 'hillpositve':
            prop_dict = {}
            prop_dict['parameters'] = propensity_params
            prop_dict['species'] = {}
            HillNegative.from_dict(prop_dict)

        if input_coefs:
            reactants = [WeightedSpecies(species=s, stoichiometry=v) for s,v in zip(inputs, input_coefs, strict=True)]
        else:
            reactants = [WeightedSpecies(species=s) for s in inputs]

        if output_coefs:
            products = [WeightedSpecies(species=s, stoichiometry=v) for s,v in zip(outputs, output_coefs, strict=True)]
        else:
            products = [WeightedSpecies(species=s) for s in outputs]

        if k_rev:
            mak = MassAction(k_forward=k, k_reverse=k_rev)
        else:
            mak = MassAction(k_forward=k)

        self.new_interface(inputs=reactants, outputs=products, propensity_type=mak)

    def new_interface(self, inputs: Union[List[Species], List[WeightedSpecies]],
                 outputs: Union[List[Species], List[WeightedSpecies]],
                 propensity_type: Propensity):

        if len(inputs) == 0 and len(outputs) == 0:
            warn("Reaction Inputs and Outputs both contain 0 Species.")

        self.inputs = Species.flatten_list(inputs)
        self.outputs = Species.flatten_list(outputs)
        self.propensity_type = propensity_type

    @property
    def propensity_type(self) -> Propensity:
        return self._propensity_type

    @propensity_type.setter
    def propensity_type(self, new_propensity_type: Propensity):
        """ Replace the propensity type associated with the reaction object

        :param new_propensity_type: Valid propensity type
        """
        if not Propensity.is_valid_propensity(new_propensity_type):
            raise ValueError(f'unknown propensity type: {new_propensity_type} '
                             f'({type(new_propensity_type)})!')

        self._propensity_type = new_propensity_type

    @classmethod
    def from_massaction(cls, inputs: Union[List[Species], List[WeightedSpecies]],
                        outputs: Union[List[Species], List[WeightedSpecies]],
                        k_forward: float, k_reverse: float = None):
        """ Initialize a Reaction object with mass action kinetics
        :param inputs:
        :param outputs:
        :param k_forward:
        :param k_reverse:
        :return: Reaction object
        """
        mak = MassAction(k_forward=k_forward, k_reverse=k_reverse)

        return cls(inputs=inputs, outputs=outputs, propensity_type=mak)

    @property
    def is_reversible(self) -> bool:
        return self.propensity_type.is_reversible

    @property
    def inputs(self) -> List[WeightedSpecies]:
        return self._input_complexes

    @inputs.setter
    def inputs(self, new_input_complexes: List[WeightedSpecies]):
        self._input_complexes = Reaction._check_and_convert_complex_list(complexes=new_input_complexes)

    @property
    def outputs(self) -> List[WeightedSpecies]:
        return self._output_complexes

    @outputs.setter
    def outputs(self, new_output_complexes: List[WeightedSpecies]):
        self._output_complexes = Reaction._check_and_convert_complex_list(complexes=new_output_complexes)

    @staticmethod
    def _check_and_convert_complex_list(complexes: Union[List[Species], List[WeightedSpecies]]) -> List[WeightedSpecies]:
        if all([isinstance(one_complex, Species) for one_complex in complexes]):
            # we wrap each Species object to WeightedSpecies
            complexes = [WeightedSpecies(species=species) for species in complexes]
        else:
            if not all([isinstance(one_complex, WeightedSpecies) for one_complex in complexes]):
                raise TypeError(f'inputs must be list of Species or list of ChemicalComplexes! Recieved {complexes}')

        # filter out duplicates and adjust stoichiometry
        out_list = []
        # Create a dictionary of unique species and their stoichiometry count
        stoichiometry_count = WeightedSpecies._count_weighted_species(complexes)
        for one_complex, stoichiometry in stoichiometry_count.items():
            new_complex = WeightedSpecies(species=one_complex.species, stoichiometry=stoichiometry)
            out_list.append(new_complex)

        return out_list

    #@property
    #def k_forward(self):
    #    return self.propensity_type.k_forward

    #@property
    #def k_reverse(self):
    #    return self.propensity_type.k_reverse

    def replace_species(self, species: Species, new_species: Species):
        """Replaces species with new_species in the reaction
        :param species: species to be replaced
        :param new_species: the new species the old species is replaced with
        :return: a new Reaction instance
        """
        if not isinstance(species, Species) or not isinstance(new_species, Species):
            raise ValueError('both species and new_species argument must be an instance of Species!')

        new_inputs = []
        for s in self.inputs:
            new_s = s.replace_species(species, new_species)
            new_inputs.append(new_s)

        new_outputs = []
        for s in self.outputs:
            new_s = s.replace_species(species, new_species)
            new_outputs.append(new_s)

        # get a shallow copy of the parameters and species, so we can replace some of them
        propensity_type_dict = copy.copy(self.propensity_type.propensity_dict)
        for key, prop_species in propensity_type_dict['species'].items():
            propensity_type_dict['species'][key] = prop_species.replace_species(species, new_species)

        new_propensity_type = self.propensity_type.from_dict(propensity_type_dict)
        print(new_propensity_type.propensity_dict)

        new_r = Reaction(inputs=new_inputs, outputs=new_outputs, propensity_type=new_propensity_type)
        return new_r

    def __repr__(self):
        """Helper function to print the text of a rate function"""
        return self.pretty_print(show_rates=False, show_material=True, show_attributes=True, show_parameters = False)

    def pretty_print(self, show_rates=True, show_material=True, show_attributes=True, show_parameters = True, **kwargs):

        kwargs['show_rates'] = show_rates
        kwargs['show_material'] = show_material
        kwargs['show_attributes'] = show_attributes

        txt = '+'.join([s.pretty_print(**kwargs) for s in self.inputs])

        if self.is_reversible:
            txt += " <--> "
        else:
            txt += " --> "

        txt += '+'.join([s.pretty_print(**kwargs) for s in self.outputs])
        if show_rates:

            #These kwargs are essential for massaction propensities
            kwargs["reaction"] = self
            if "stochastic" not in kwargs:
                kwargs["stochastic"] = False

            txt += "\n"+f'{self.propensity_type.pretty_print(**kwargs)}'

        return txt

    def __eq__(self, other):
        """Two reactions are equivalent if they have the same inputs, outputs,
           and propensity."""
        if not isinstance(other, Reaction):
            raise TypeError(f'Only reactions can be compared with reaction! We got {type(other)}.')

        if len(self.inputs) != len(other.inputs) or len(self.outputs) != len(other.outputs):
            return False

        return (set(self.inputs), set(self.outputs), self.propensity_type) == (set(other.inputs), set(other.outputs), other.propensity_type)

    def __contains__(self, item: Species):
        """It checks whether a species is part of a reaction.

         it checks the input and output lists as well as the propensity type for the species

        :param item: a Species instance
        :return: bool
        :exception NotImplementedError for non-Species objects
        """
        if isinstance(item, Species):
            if item in self.inputs \
                    or item in self.outputs \
                    or item in self.propensity_type.species:
                return True
        else:
            raise NotImplementedError
        return False

    @property
    def species(self) -> List[Species]:
        """returns a list of species in the reactions collected from the inputs
        and outputs and the propensity (e.g. Hill kinetics has species in it)

        :return: list of species in the reactions
        """
        in_part = []
        for s in self.inputs:
            in_part.extend(Species.flatten_list(s.species))
        out_part = []
        for s in self.outputs:
            out_part.extend(Species.flatten_list(s.species))

        return list(itertools.chain(in_part, out_part, self.propensity_type.species))