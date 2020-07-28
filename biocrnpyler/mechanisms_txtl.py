from .mechanism import *
from .species import Species, Complex
from .reaction import Reaction
from .propensities import ProportionalHillPositive, ProportionalHillNegative
from .mechanisms_enzyme import *


class OneStepGeneExpression(Mechanism):
    """
    A mechanism to model gene expression without transcription or translation
    G --> G + P
    """
    def __init__(self, name="gene_expression",
                 mechanism_type="transcription"):
        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type)

    def update_species(self, dna, protein, transcript=None, **keywords):
        species = [dna]
        if protein is not None:
            species += [protein]

        return species

    def update_reactions(self, dna, component = None, kexpress = None,
                         protein=None, transcript = None, part_id = None, **keywords):

        if kexpress is None and component is not None:
            kexpress = component.get_parameter("kexpress", part_id = part_id, mechanism = self)
        elif component is None and kexpress is None:
            raise ValueError("Must pass in component or a value for kexpress")

        if protein is not None:
            return [Reaction.from_massaction(inputs=[dna], outputs=[dna, protein], k_forward=kexpress)]
        else:
            return []


class SimpleTranscription(Mechanism):
    """
    A Mechanism to model simple catalytic transcription.
    G --> G + T
    """
    def __init__(self, name = "simple_transcription", mechanism_type = "transcription"):
        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type)

    def update_species(self, dna, transcript = None, protein = None, **keywords):

        species = [dna]
        if transcript is not None:
            species += [transcript]
        if protein is not None:
            species += [protein]

        return species

    def update_reactions(self, dna, component = None, ktx = None, part_id = None, transcript = None, protein = None, **keywords):

        if ktx == None and component != None:
            ktx = component.get_parameter("ktx", part_id = part_id, mechanism = self)
        elif component == None and ktx == None:
            raise ValueError("Must pass in component or a value for ktx")

        #First case only true in Mixtures without transcription (eg Expression Mixtures)
        if transcript is None and protein is not None:
            ktl = component.get_parameter("ktl", part_id = part_id, mechanism = self)
            rxns = [Reaction.from_massaction(inputs = [dna], outputs = [dna, protein], k_forward=ktx * ktl)]
        else:
            rxns = [Reaction.from_massaction(inputs = [dna], outputs = [dna, transcript], k_forward=ktx)]

        return rxns

class SimpleTranslation(Mechanism):
    """
    A mechanism to model simple catalytic translation.
    T --> T + P
    """
    def __init__(self, name = "simple_translation", mechanism_type = "translation"):
        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type)

    def update_species(self, transcript, protein = None,  **keywords):
        if protein is None:
            protein = Species(transcript.name, material_type="protein")

        return [transcript, protein]

    def update_reactions(self, transcript, component = None, ktl = None, part_id = None, protein = None, **keywords):

        if ktl is None and component is not None:
            ktl = component.get_parameter("ktl", part_id = part_id, mechanism = self)
        elif component is None and ktl is None:
            raise ValueError("Must pass in component or a value for ktl")

        #First case only true in Mixtures without transcription (eg Expression Mixtures)
        if transcript is None and protein is not None:
            rxns = []
        else:
            rxns = [Reaction.from_massaction(inputs = [transcript], outputs = [transcript, protein], k_forward=ktl)]

        return rxns


class PositiveHillTranscription(Mechanism):
    """
    A mechanism to model transcription as a proprotional positive hill function:
    G --> G + P
    rate = k*G*(R^n)/(K+R^n)
    where R is a regulator (activator).
    Optionally includes a leak reaction
    G --> G + P @ rate kleak.
    """

    #Set the name and mechanism_type
    def __init__(self, name="positivehill_transcription", mechanism_type="transcription"):
        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type)

    #Overwrite update_species
    def update_species(self, dna, regulator, transcript = None, leak = False, protein = None, **keywords):

        species = [dna, regulator]
        if transcript is not None:
            species += [transcript]
        if protein is not None:
            species += [protein]

        return species #it is best to return all species that will be involved in the reactions


    #Overwrite update_reactions
    #This always requires the inputs component and part_id to find the relevant parameters
    def update_reactions(self, dna, regulator, component, part_id, transcript = None, leak = False, protein = None, **keywords):

        ktx = component.get_parameter("k", part_id = part_id, mechanism = self)
        n = component.get_parameter("n", part_id = part_id, mechanism = self)
        K = component.get_parameter("K", part_id = part_id, mechanism = self)
        kleak = component.get_parameter("kleak", part_id = part_id, mechanism = self)

        prophill = ProportionalHillPositive(k=ktx, K=K, s1=regulator, n=n, d=dna)

        reactions = []

        #First case only true in Mixtures without transcription (eg Expression Mixtures)
        if transcript is None and protein is not None:
            tx_output = protein
        else:
            tx_output = transcript

        reactions.append(Reaction(inputs=[dna], outputs=[dna, tx_output], propensity_type=prophill))

        if leak:
            reactions.append(Reaction.from_massaction(inputs=[dna], outputs=[dna, tx_output], k_forward=kleak))

        #In this case, we just return one reaction
        return reactions

class NegativeHillTranscription(Mechanism):
    """
    A mechanism to model transcription as a proprotional negative hill function:
    G --> G + P
    rate = k*G*(1)/(K+R^n)
    where R is a regulator (repressor).
    Optionally includes a leak reaction
    G --> G + P @ rate kleak.
    """

    def __init__(self, name="negativehill_transcription", mechanism_type="transcription"):
        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type)

    #Overwrite update_species
    def update_species(self, dna, regulator, transcript = None, leak = False, protein = None, **keywords):

        species = [dna, regulator]
        if transcript is not None:
            species += [transcript]
        if protein is not None:
            species += [protein]

        return species #it is best to return all species that will be involved in the reactions

    #Overwrite update_reactions
    #This always requires the inputs component and part_id to find the relevant parameters
    def update_reactions(self, dna, regulator, component, part_id, transcript = None, leak = False, protein = None, **keywords):

        ktx = component.get_parameter("k", part_id = part_id, mechanism = self)
        n = component.get_parameter("n", part_id = part_id, mechanism = self)
        K = component.get_parameter("K", part_id = part_id, mechanism = self)
        kleak = component.get_parameter("kleak", part_id = part_id, mechanism = self)

        prop_hill = ProportionalHillNegative(k=ktx, K=K, n=n, s1=regulator, d=dna)

        reactions = []

        #First case only true in Mixtures without transcription (eg Expression Mixtures)
        if transcript is None and protein is not None:
            tx_output = protein
        else:
            tx_output = transcript

        reactions.append(Reaction(inputs=[dna], outputs=[dna, tx_output], propensity_type=prop_hill))

        if leak:
            reactions.append(Reaction.from_massaction(inputs = [dna], outputs = [dna, tx_output], k_forward=kleak))

        #In this case, we just return one reaction
        return reactions


class Transcription_MM(MichaelisMentenCopy):
    """Michaelis Menten Transcription
        G + RNAP <--> G:RNAP --> G+RNAP+mRNA
    """

    def __init__(self, rnap, name="transcription_mm", **keywords):
        if isinstance(rnap, Species):
            self.rnap = rnap
        else:
            raise ValueError("'rnap' parameter must be a Species.")

        MichaelisMentenCopy.__init__(self=self, name=name,
                                       mechanism_type="transcription")

    def update_species(self, dna, transcript=None, protein = None, **keywords):
        species = [dna]

        if transcript is None and protein is not None:
            tx_output = protein
        else:
            tx_output = transcript

        species += MichaelisMentenCopy.update_species(self, Enzyme = self.rnap, Sub = dna, Prod = tx_output)

        return species

    def update_reactions(self, dna, component, part_id = None, complex=None, transcript=None, protein = None,
                         **keywords):

        #Get Parameters
        if part_id == None and component != None:
            part_id = component.name

        ktx = component.get_parameter("ktx", part_id = part_id, mechanism = self)
        kb = component.get_parameter("kb", part_id = part_id, mechanism = self)
        ku = component.get_parameter("ku", part_id = part_id, mechanism = self)

        rxns = []

        if transcript is None and protein is not None:
            tx_output = protein
        else:
            tx_output = transcript

        rxns += MichaelisMentenCopy.update_reactions(self, Enzyme = self.rnap, Sub = dna, Prod = tx_output, complex=complex, kb=kb, ku=ku, kcat=ktx)

        return rxns


class Translation_MM(MichaelisMentenCopy):
    """ Michaelis Menten Translation
        mRNA + Rib <--> mRNA:Rib --> mRNA + Rib + Protein
    """

    def __init__(self, ribosome, name="translation_mm", **keywords):
        if isinstance(ribosome, Species):
            self.ribosome = ribosome
        else:
            raise ValueError("ribosome must be a Species!")
        MichaelisMentenCopy.__init__(self=self, name=name,
                                       mechanism_type="translation")

    def update_species(self, transcript, protein, **keywords):
        species = []

        #This can only occur in expression mixtures
        if transcript is None and protein is not None:
            species += [protein]
        else:
            species += MichaelisMentenCopy.update_species(self, Enzyme = self.ribosome, Sub = transcript, Prod = protein)

        return species

    def update_reactions(self, transcript, protein, component, part_id = None, complex=None, **keywords):
        rxns = []

        #Get Parameters
        if part_id == None and component != None:
            part_id = component.name

        ktl = component.get_parameter("ktl", part_id = part_id, mechanism = self)
        kb = component.get_parameter("kb", part_id = part_id, mechanism = self)
        ku = component.get_parameter("ku", part_id = part_id, mechanism = self)


        #This can only occur in expression mixtures
        if transcript is None and protein is not None:
            pass
        else:
            rxns += MichaelisMentenCopy.update_reactions(self, Enzyme = self.ribosome, Sub = transcript, Prod = protein, complex=complex, kb=kb, ku=ku, kcat=ktl)
        return rxns


class Degredation_mRNA_MM(MichaelisMenten):
    """Michaelis Menten mRNA Degredation by Endonucleases
       mRNA + Endo <--> mRNA:Endo --> Endo
    """
    def __init__(self, nuclease, name="rna_degredation_mm", **keywords):
        if isinstance(nuclease, Species):
            self.nuclease = nuclease
        else:
            raise ValueError("'nuclease' must be a Species.")
        MichaelisMenten.__init__(self=self, name=name,
                                 mechanism_type="rna_degredation")

    def update_species(self, rna, return_nuclease=True, **keywords):
        species = [rna]
        if return_nuclease:
            species += [self.nuclease]
        species += MichaelisMenten.update_species(self, Enzyme = self.nuclease, Sub = rna, Prod = None)
        return species

    def update_reactions(self, rna, component, part_id = None, complex=None, **keywords):

        #Get Parameters
        if part_id == None and component != None:
            part_id = component.name

        kdeg = component.get_parameter("kdeg", part_id = part_id, mechanism = self)
        kb = component.get_parameter("kb", part_id = part_id, mechanism = self)
        ku = component.get_parameter("ku", part_id = part_id, mechanism = self)

        rxns = []
        rxns += MichaelisMenten.update_reactions(self, Enzyme = self.nuclease, Sub = rna, Prod=None, complex=complex, kb=kb, ku=ku, kcat=kdeg)
        return rxns


class multi_tx(Mechanism):
    """
    Multi-RNAp Transcription w/ Isomerization:
    Detailed transcription mechanism accounting for each individual
    RNAp occupancy states of gene.

    n ={0, max_occ}
    DNA:RNAp_n + RNAp <--> DNA:RNAp_n_c --> DNA:RNAp_n+1
    DNA:RNAp_n --> DNA:RNAp_0 + n RNAp + n mRNA
    DNA:RNAp_n_c --> DNA:RNAp_0_c + n RNAp + n mRNA

    n --> number of open configuration RNAp on DNA
    max_occ --> Physical maximum number of RNAp on DNA (based on RNAp and DNA dimensions)
    DNA:RNAp_n --> DNA with n open configuration RNAp on it
    DNA:RNAp_n_c --> DNA with n open configuration RNAp and 1 closed configuration RNAp on it

    For more details, see examples/MultiTX_Demo.ipynb
    """

    # initialize mechanism subclass
    def __init__(self, pol, name='multi_tx', mechanism_type='transcription', **keywords):

        if isinstance(pol,Species):
            self.pol = pol
        else:
            raise ValueError("'pol' must be a Species")

        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type, **keywords)

    # species update
    def update_species(self, dna, transcript, component, part_id, protein = None, **keywords):
        max_occ = int(component.get_parameter("max_occ", part_id = part_id, mechanism = self, return_numerical = True))
        cp_open = []
        cp_closed = []
        for n in range(1,max_occ + 1):
            name_open = self.pol.name + 'x' + dna.name + '_' + str(n)
            cp_open.append(Complex([dna]+[self.pol for i in range(n)],name=name_open))
            if n > 1:
                name_closed = self.pol.name + 'x' + dna.name + '_closed' + '_' + str(n-1)
                cp_closed.append(Complex([dna]+[self.pol for i in range(n-1)],name=name_closed))
            else:
                name_closed = self.pol.name + 'x' + dna.name + '_closed' + '_' + str(0)
                cp_closed.append(Complex([dna]+[self.pol for i in range(1)],name=name_closed))

        cp_misc = [self.pol,dna,transcript]


        return cp_open + cp_closed + cp_misc

    def update_reactions(self, dna, transcript, component, part_id, protein = None, **keywords):
        """
        DNA:RNAp_n + RNAp <--> DNA:RNAp_n_c --> DNA:RNAp_n+1
        kf1 = k1, kr1 = k2, kf2 = k_iso
        DNA:RNAp_n --> DNA:RNAp_0 + n RNAp + n mRNA
        kf = ktx_solo
        DNA:RNAp_n_c --> DNA:RNAp_0_c + n RNAp + n mRNA
        kf = ktx_solo

        max_occ =  maximum occupancy of gene (physical limit)
        """

        # parameter loading
        k1 = component.get_parameter("k1", part_id = part_id, mechanism = self)
        k2 = component.get_parameter("k2", part_id = part_id, mechanism = self)
        k_iso = component.get_parameter("k_iso", part_id = part_id, mechanism = self)
        ktx_solo = component.get_parameter("ktx_solo", part_id = part_id, mechanism = self)
        max_occ = int(component.get_parameter("max_occ", part_id = part_id, mechanism = self, return_numerical = True))

        # complex species instantiation
        cp_open = []
        cp_closed = []
        for n in range(1,max_occ + 1):
            name_open = self.pol.name + 'x' + dna.name + '_' + str(n)
            cp_open.append(Complex([dna]+[self.pol for i in range(n)],name=name_open))
            if n > 1:
                name_closed = self.pol.name + 'x' + dna.name + '_closed' + '_' + str(n-1)
                cp_closed.append(Complex([dna]+[self.pol for i in range(n-1)],name=name_closed))
            else:
                name_closed = self.pol.name + 'x' + dna.name + '_closed' + '_' + str(0)
                cp_closed.append(Complex([dna]+[self.pol for i in range(1)],name=name_closed))


        # Reactions
        # polymerase + complex(n) --> complex(n_closed)
        rxn_open_pf = [Reaction.from_massaction(inputs=[self.pol, cp_open[n]], outputs=[cp_closed[n + 1]], k_forward=k1) for n in range(0, max_occ - 1)]
        rxn_open_pr = [Reaction.from_massaction(inputs=[cp_closed[n + 1]], outputs=[self.pol, cp_open[n], ], k_forward=k2) for n in range(0, max_occ - 1)]

        # isomerization
        rxn_iso = [Reaction.from_massaction(inputs=[cp_closed[n]], outputs=[cp_open[n]], k_forward=k_iso) for n in range(0, max_occ)]

        # release/transcription from open and closed states
        rxn_release_open =  []
        rxn_release_closed = []
        for n in range(0,max_occ):
            rxn_temp1 = Reaction.from_massaction(inputs= [cp_open[n]], outputs=[self.pol for i in range(n + 1)] +
                                                                               [transcript for i in range(n+1)] + [dna], k_forward=ktx_solo)
            rxn_release_open.append(rxn_temp1)

        for n in range(1,max_occ):
            rxn_temp2 = Reaction.from_massaction(inputs= [cp_closed[n]], outputs=[self.pol for i in range(n)] +
                                                                                 [transcript for i in range(n)] + [cp_closed[0]], k_forward=ktx_solo)
            rxn_release_closed.append(rxn_temp2)

        # missing reactions (0 --> 0_closed and v.v. 0_closed --> 0)
        rxn_m1 = Reaction.from_massaction(inputs=[dna, self.pol], outputs=[cp_closed[0]], k_forward=k1)
        rxn_m2 = Reaction.from_massaction(inputs=[cp_closed[0]], outputs=[dna, self.pol], k_forward=k2)

        rxn_all = rxn_open_pf + rxn_open_pr + rxn_iso + rxn_release_open + rxn_release_closed + [rxn_m1, rxn_m2]

        return rxn_all


class multi_tl(Mechanism):
    """
    Multi-RBZ Translation w/ Isomerization:
    Detailed translation mechanism accounting for each individual
    RBZ occupancy states of mRNA. Still needs some work, so use with caution,
    read all warnings and consult the example notebook.

    n ={0, max_occ}
    mRNA:RBZ_n + RBZ <--> mRNA:RBZ_n_c --> mRNA:RBZ_n+1
    mRNA:RBZ_n --> mRNA:RBZ_0 + n RBZ + n Protein
    mRNA:RBZ_n_c --> mRNA:RBZ_0_c + n RBZ + n Protein

    n --> number of open configuration RBZ on mRNA
    max_occ --> Physical maximum number of RBZ on mRNA (based on RBZ and mRNA dimensions)
    mRNA:RBZ_n --> mRNA with n open configuration RBZ on it
    mRNA:RBZ_n_c --> mRNA with n open configuration RBZ and 1 closed configuration RBZ on it

    For more details, see examples/MultiTX_Demo.ipynb
    """

    # initialize mechanism subclass
    def __init__(self, ribosome, name='multi_tl', mechanism_type='translation', **keywords):

        if isinstance(ribosome,Species):
            self.ribosome = ribosome
        else:
            raise ValueError("'ribosome' must be a Species.")

        warn('This mechanism still needs some extra validation, use at your own peril and read the warnings!')
        warn("To properly use this mechanism, set dilution for mRNA-RBZ complexes!")
        warn("I've set RBZ and mRNA-RBZ complexes as protein Species to apply dilution to them, edit if you want something else!")

        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type, **keywords)

    # species update
    def update_species(self, transcript, protein, component, part_id, **keywords):
        max_occ = int(component.get_parameter("max_occ", part_id = part_id, mechanism = self, return_numerical = True))
        cp_open = []
        cp_closed = []
        for n in range(1,max_occ + 1):
            name_open = self.ribosome.name + 'x' + transcript.name + '_' + str(n)
            cp_open.append(Complex([transcript]+[self.ribosome for i in range(n)],name=name_open))

            if n > 1:
                name_closed = self.ribosome.name + 'x' + transcript.name + '_closed' + '_' + str(n-1)
                cp_closed.append(Complex([transcript]+[self.ribosome for i in range(n-1)],name=name_closed))
            else:
                name_closed = self.ribosome.name + 'x' + transcript.name + '_closed' + '_' + str(0)
                cp_closed.append(Complex([transcript]+[self.ribosome for i in range(1)],name=name_closed))


        cp_misc = [self.ribosome,transcript,protein]

        return cp_open + cp_closed + cp_misc

    def update_reactions(self, transcript, protein, component, part_id, **keywords):
        """
        mRNA:RBZ_n + RBZ <--> mRNA:RBZ_n_c --> mRNA:RBZ_n+1
        kf1 = kbr, kr1 = kur, kf2 = k_iso_r
        mRNA:RBZ_n --> mRNA:RBZ_0 + n RBZ + n Protein
        kf = ktl_solo
        mRNA:RBZ_n_c --> mRNA:RBZ_0_c + n RBZ + n Protein
        kf = ktl_solo
        """

        # parameter loading
        kbr = component.get_parameter("kbr", part_id = part_id, mechanism = self)
        kur = component.get_parameter("kur", part_id = part_id, mechanism = self)
        k_iso_r = component.get_parameter("k_iso_r", part_id = part_id, mechanism = self)
        ktl_solo = component.get_parameter("ktl_solo", part_id = part_id, mechanism = self)
        max_occ = int(component.get_parameter("max_occ", part_id = part_id, mechanism = self, return_numerical = True))


        # complex species instantiation
        cp_open = []
        cp_closed = []
        for n in range(1,max_occ + 1):
            name_open = self.ribosome.name + 'x' + transcript.name + '_' + str(n)
            cp_open.append(Complex([transcript]+[self.ribosome for i in range(n)],name=name_open))

            if n > 1:
                name_closed = self.ribosome.name + 'x' + transcript.name + '_closed' + '_' + str(n-1)
                cp_closed.append(Complex([transcript]+[self.ribosome for i in range(n-1)],name=name_closed))
            else:
                name_closed = self.ribosome.name + 'x' + transcript.name + '_closed' + '_' + str(0)
                cp_closed.append(Complex([transcript]+[self.ribosome for i in range(1)],name=name_closed))

        # Reactions
        # ribosome + complex(n) --> complex(n_closed)
        rxn_open_pf = [Reaction.from_massaction(inputs=[self.ribosome, cp_open[n]], outputs=[cp_closed[n + 1]], k_forward=kbr) for n in range(0, max_occ - 1)]
        rxn_open_pr = [Reaction.from_massaction(inputs=[cp_closed[n + 1]], outputs=[self.ribosome, cp_open[n], ], k_forward=kur) for n in range(0, max_occ - 1)]

        # isomerization
        rxn_iso = [Reaction.from_massaction(inputs=[cp_closed[n]], outputs=[cp_open[n]], k_forward=k_iso_r) for n in range(0, max_occ)]

        # release/translation from open and closed states
        rxn_release_open =  []
        rxn_release_closed = []
        for n in range(0,max_occ):
            rxn_temp1 = Reaction.from_massaction(inputs= [cp_open[n]], outputs=[self.ribosome for i in range(n + 1)] +
                                                                               [protein for i in range(n+1)] + [transcript], k_forward=ktl_solo)
            rxn_release_open.append(rxn_temp1)

        for n in range(1,max_occ):
            rxn_temp2 = Reaction.from_massaction(inputs= [cp_closed[n]], outputs=[self.ribosome for i in range(n)] +
                                                                                 [protein for i in range(n)] + [cp_closed[0]], k_forward=ktl_solo)
            rxn_release_closed.append(rxn_temp2)

        # missing reactions (0 --> 0_closed and v.v. 0_closed --> 0)
        rxn_m1 = Reaction.from_massaction(inputs=[transcript, self.ribosome], outputs=[cp_closed[0]], k_forward=kbr)
        rxn_m2 = Reaction.from_massaction(inputs=[cp_closed[0]], outputs=[transcript, self.ribosome], k_forward=kur)

        rxn_all = rxn_open_pf + rxn_open_pr + rxn_iso + rxn_release_open + rxn_release_closed + [rxn_m1, rxn_m2]

        return rxn_all
