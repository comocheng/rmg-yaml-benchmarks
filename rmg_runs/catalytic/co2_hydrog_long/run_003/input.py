# Template input file for heterogeneous catalysis 

# Data sources
database(
    # thermo libraries: order matters (first most important)
    # properties of species determined by Benson additivity formulas unless specified here
    # 'surfaceThermoPt' is the default. Thermo data is derived using bindingEnergies for other metals 
    # three other libraries with thermo data for related species
    thermoLibraries=['surfaceThermoPt111', 'primaryThermoLibrary', 'thermo_DFT_CCSDTF12_BAC','DFT_QCI_thermo'], 
    
    # adds all relevant reactions to the core
    # only include reaction library if you have reason to believe the reaction will occur
    # true or false indicates whether unused reactions from edge will go into chemkin file
    # reactionLibraries = [('Surface/CPOX_Pt/Deutschmann2006_adjusted', False)],
    # good to have matching kinetics library to thermo library - not good for them to be conflicting
    reactionLibraries = [
         ('Surface/CPOX_Pt/Deutschmann2006_adjusted', False),
         ('Surface/Methane/Deutschmann_Pt', False),
         ('Surface/Methane/Vlachos_Pt111', False),
         ('Surface/Methane/Vlachos_Rh', False),
         ('Surface/Methane/Deutschmann_Ni', False),
         ('Surface/Methane/Deutschmann_Ni_full', False),
         ],
    
    # seed mechanism: all species and reactions in this file are included in the core
    # essentially a forced reaction library
    seedMechanisms = [],
    
    # not usually changed, could be 'training'
    kineticsDepositories = ['training'],
    
    # keep surface and default for heterogeneous catalysis, look in reccomended.py in kinetics families for more to add
    # maybe add surface development 
    kineticsFamilies = ['surface','default'],
    
    # only option
    kineticsEstimator = 'rate rules',

)

generatedSpeciesConstraints(
    # always have this so that the things you specified are allowed
    allowed=['input species','seed mechanisms','reaction libraries'],
    # makes it so that we do not have all the carbons attached to the surface and each other stuck
    maximumCarbonAtoms=12,
    maximumSurfaceSites=2,
)

# this is for platinum (111) surface, energies and site density can be changed for other surfaces
# we only will change the H, O, and C binding energies
catalystProperties(
    bindingEnergies = {
                        'H': (-2.138796989095516,'eV/molecule'),
                        'C': (-5.659485026180109,'eV/molecule'),
                        'N': (-4.63225,'eV/molecule'), # will not be changing
                        'O': (-5.057377746038682,'eV/molecule'),
                    },
    surfaceSiteDensity=(2.48e-09, 'mol/cm^2'),
)

# this would be used in the case of a metal already known from previous DFT calculations
'''catalystProperties(
    metal = 'Co211',
    # to examine coverage dependence
    #coverageDependence=True,
)'''

# now we list the species to be included in the model
# gas species and vacant sites in the model

species(
    label='H2',
    reactive=True,
    structure=SMILES("[HH]"),
)


species(
    label='CO2',
    reactive=True,
    structure=SMILES("C(=O)=O"),
)

species(
    label='CO',
    reactive=True,
    structure=SMILES("[C-]#[O+]"),
)

species(
    label='CH4',
    reactive=True,
    structure=SMILES("[CH4]"),
)

species(
   label='O2',
   reactive=True,
   structure=SMILES("[O][O]"),
)

species(
    label='N2',
    reactive=False,
    structure=SMILES("N#N"),
)

species(
    label='vacantX',
    reactive=True,
    structure=adjacencyList("1 X u0"),
)

# observed products
# species found from GC-MS

#CH3CH2COOCH2CH3
species(
    label='ethlpropnot',
    reactive=True,
    structure=SMILES("CCOC(=O)CC"),
)

#CH3CHO
species(
    label='acetaldehyde',
    reactive=True,
    structure=SMILES("CC=O"),
)

#CH3OH
species(
    label='methanol',
    reactive=True,
    structure=SMILES("CO"),
)

#CH3CH2OH
species(
    label='ethanol',
    reactive=True,
    structure=SMILES("CCO"),
)

#CH3COCH3
species(
    label='acetone',
    reactive=True,
    structure=SMILES("CC(=O)C"),
)

#CH3CH2CHO
species(
    label='propanal',
    reactive=True,
    structure=SMILES("CCC=O"),
)

#CH3(CH2)2CHO
species(
    label='butanal',
    reactive=True,
    structure=SMILES("CCCC=O"),
)

#C3OH
species(
    label='propanol',
    reactive=True,
    structure=SMILES("CCCO"),
) 


#2-butanone
species(
    label='2-butanone',
    reactive=True,
    structure=SMILES("CC(=O)CC"),
)

#CH3COOCH2CH3
species(
    label='ethylacetate',
    reactive=True,
    structure=SMILES("CCOC(=O)C"),
)

# from common surf species observed from first few runs
# CO2X
species(
    label='CO2.X',
    reactive=True,
    structure=adjacencyList(
    '''
    1 O u0 p2 c0 {3,D}
    2 O u0 p2 c0 {3,D}
    3 C u0 p0 c0 {1,D} {2,D}
    4 X u0 p0 c0
    '''
    )
)

species(
    label='CH4.X',
    reactive=True,
    structure=adjacencyList(
    '''
    1 C u0 p0 c0 {2,S} {3,S} {4,S} {5,S}
    2 H u0 p0 c0 {1,S}
    3 H u0 p0 c0 {1,S}
    4 H u0 p0 c0 {1,S}
    5 H u0 p0 c0 {1,S}
    6 X u0 p0 c0
    '''
    )
)

species(
    label='OCX',
    reactive=True,
    structure=adjacencyList(
    '''
    1 O u0 p2 c0 {2,D}
    2 C u0 p0 c0 {1,D} {3,D}
    3 X u0 p0 c0 {2,D}
    '''
    )
)

species(
    label='HX',
    reactive=True,
    structure=adjacencyList(
    '''
    1 H u0 p0 c0 {2,S}
    2 X u0 p0 c0 {1,S}
    '''
    )
)

species(
    label='H2O.X',
    reactive=True,
    structure=adjacencyList(
    '''
    1 O u0 p2 c0 {2,S} {3,S}
    2 H u0 p0 c0 {1,S}
    3 H u0 p0 c0 {1,S}
    4 X u0 p0 c0
    '''
    )
)

species(
    label='OXCXCH2',
    reactive=True,
    structure=adjacencyList(
    '''
    1 O u0 p2 c0 {2,S} {7,S}
    2 C u0 p0 c0 {1,S} {3,D} {6,S}
    3 C u0 p0 c0 {2,D} {4,S} {5,S}
    4 H u0 p0 c0 {3,S}
    5 H u0 p0 c0 {3,S}
    6 X u0 p0 c0 {2,S}
    7 X u0 p0 c0 {1,S}
    '''
    )
)

species(
    label='OXCXCH3',
    reactive=True,
    structure=adjacencyList(
    '''
    1 O u0 p2 c0 {2,S} {9,S}
    2 C u0 p0 c0 {1,S} {3,S} {4,S} {8,S}
    3 C u0 p0 c0 {2,S} {5,S} {6,S} {7,S}
    4 H u0 p0 c0 {2,S}
    5 H u0 p0 c0 {3,S}
    6 H u0 p0 c0 {3,S}
    7 H u0 p0 c0 {3,S}
    8 X u0 p0 c0 {2,S}
    9 X u0 p0 c0 {1,S}
    '''
    )
)

species(
    label='CXOH',
    reactive=True,
    structure=adjacencyList(
    '''
    1 O u0 p2 c0 {2,S} {3,S}
    2 C u0 p0 c0 {1,S} {4,T}
    3 H u0 p0 c0 {1,S}
    4 X u0 p0 c0 {2,T}
    '''
    )
) 

species(
    label='CXHO',
    reactive=True,
    structure=adjacencyList(
    '''
    1 O u0 p2 c0 {2,D}
    2 C u0 p0 c0 {1,D} {3,S} {4,S}
    3 H u0 p0 c0 {2,S}
    4 X u0 p0 c0 {2,S}
    '''
    )
)

species(
    label='ethane',
    reactive=True,
    structure=SMILES("CC"),
)

species(
    label='propane',
    reactive=True,
    structure=SMILES("CCC"),
)

species(
    label='dimethlether',
    reactive=True,
    structure=SMILES("COC"),
)

species(
    label='H2O',
    reactive=True,
    structure=SMILES("O"),
)

species(
    label='OX',
    reactive=True,
    structure=adjacencyList(
    '''
    1 O u0 p2 c0 {2,D}
    2 X u0 p0 c0 {1,D}
    '''
    )
)

species(
    label='butane',
    reactive=True,
    structure=SMILES("CCCC"),
)

species(
    label='pentane',
    reactive=True,
    structure=SMILES("CCCCC"),
)

species(
    label='hexane',
    reactive=True,
    structure=SMILES("CCCCCC"),
)

species(
    label='heptane',
    reactive=True,
    structure=SMILES("CCCCCCC"),
)

species(
    label='octane',
    reactive=True,
    structure=SMILES("CCCCCCCC"),
)

species(
    label='nonane',
    reactive=True,
    structure=SMILES("CCCCCCCCC"),
)

species(
    label='ethene',
    reactive=True,
    structure=SMILES("C=C"),
)

species(
    label='propene',
    reactive=True,
    structure=SMILES("CC=C"),
)

species(
    label='butene',
    reactive=True,
    structure=SMILES("CCC=C"),
)

species(
    label='pentene',
    reactive=True,
    structure=SMILES("CCCC=C"),
)

species(
    label='hexene',
    reactive=True,
    structure=SMILES("CCCCC=C"),
)

species(
    label='heptene',
    reactive=True,
    structure=SMILES("CCCCCC=C"),
)

species(
    label='octene',
    reactive=True,
    structure=SMILES("CCCCCCC=C"),
)



# forbidden as it is not likely to happen due to more likely chance of H2 dissociation
forbidden(
    label='H2X',
    structure=adjacencyList(
    """
    1 H u0 p0 c0 {2,S}
    2 H u0 p0 c0 {1,S}
    3 X u0 p0 c0
    """
        ),
)

# intermediates 
# ideally, RMG will discover these, but we can give it some hints if nothing else is working 

#----------
# Reaction systems
surfaceReactor(
    # range of temps
    temperature=[(450,'K'),(800,'K')],
    # only works with one pressure, more stuff happening when higher
    initialPressure=(30.0, 'bar'),
    # number of simulations
    nSims = 4,
    # gas mole fractions, will be normalized
    # adding CO2 and H2 on their own 
    initialGasMoleFractions={
        "H2": 3,
        "CO2": 1,
    },
    # surface coverage, this is proportion, so this is wide open
    initialSurfaceCoverages={
        "vacantX": 1.0,
    },
    surfaceVolumeRatio=(1.e5, 'm^-1'),
    terminationConversion = {"CO2":0.5,},
    terminationTime=(1000, 's'),
    #terminationRateRatio=0.01,
)



simulator(
    atol=1e-18,
    rtol=1e-12,
)

# branching algorithm included
model(
    toleranceKeepInEdge=0.0,
    toleranceMoveToCore=0.001,
    toleranceInterruptSimulation=0.001,
    toleranceBranchReactionToCore=0.001,
    branchingIndex=0.5,
    branchingRatioMax=1.0,
    maximumEdgeSpecies=500000,
    # pruning will speed up simulation
    # minCoreSizeForPrune=50,
    # minSpeciesExistIterationsForPrune=2,
)


options(
    units='si',
    generateOutputHTML=True,
    generatePlots=False, # Enable to make plots of core and edge size etc. But takes a lot of the total runtime!
    saveEdgeSpecies=True,
    verboseComments=True,
    saveSimulationProfiles=True,
)
