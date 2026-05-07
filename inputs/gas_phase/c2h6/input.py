# ethane oxidation example

# Data sources
database(
    thermoLibraries = [
    'primaryThermoLibrary',
    'Klippenstein_Glarborg2016',
    'thermo_DFT_CCSDTF12_BAC',
    'DFT_QCI_thermo',
    'BurkeH2O2',
    'FFCM1(-)',
    'CBS_QB3_1dHR',
    ],
    reactionLibraries = [
    'FFCM1(-)',
    'C2H4+O_Klipp2017',
    ],
    seedMechanisms = [
    'BurkeH2O2inN2',
    ], 
    kineticsDepositories = ['training'], 
    kineticsFamilies = 'default',
    kineticsEstimator = 'rate rules',
)

# Fuel and oxidizer
species(
    label='ethane',
    reactive=True,
    structure=SMILES("CC"),
)

species(
    label='O2',
    reactive=True,
    structure=SMILES("[O][O]"),  
)

# Bath gas
species(
    label='Ar',
    reactive=False,
    structure=SMILES("[Ar]"),
)

# Key products 
species(
    label='H2O',
    reactive=True,
    structure=SMILES("O"),
)

species(
    label='CO2',
    reactive=True,
    structure=SMILES("O=C=O"),
)

species(
    label='CO',
    reactive=True,
    structure=SMILES("[C-]#[O+]"),
)

# Important C2 intermediates
species(
    label='ethylene',
    reactive=True,
    structure=SMILES("C=C"),
)

species(
    label='acetylene',
    reactive=True,
    structure=SMILES("C#C"),
)

# Key radical chain carriers
species(
    label='H2O2',
    reactive=True,
    structure=SMILES("OO"),
)

species(
    label='CH2O',
    reactive=True,
    structure=SMILES("C=O"),
)

# High T, stoichiometric 
simpleReactor(
    temperature=(1500,'K'),
    pressure=(1.0,'bar'),
    initialMoleFractions={
        "ethane": 0.05,
        "O2": 0.175,
        "Ar": 0.775,
    },
    terminationConversion={
        'ethane': 0.9,
    },
    terminationTime=(1,'s'),
)

# Mid T, fuel-lean for peroxy chemistry
simpleReactor(
    temperature=(1000,'K'),
    pressure=(20.0,'bar'),
    initialMoleFractions={
        "ethane": 0.05,
        "O2": 0.245,
        "Ar": 0.705,
    },
    terminationConversion={'ethane': 0.9},
    terminationTime=(1,'s'),
)

simulator(
    atol=1e-6,
    rtol=1e-6,
)

generatedSpeciesConstraints(
    maximumCarbeneRadicals=2,
)

model(
    toleranceKeepInEdge=0.0001,
    toleranceMoveToCore=0.05,      
    toleranceInterruptSimulation=0.05,
    maximumEdgeSpecies=2000,        
    filterReactions=True,           
)

pressureDependence(
    method='modified strong collision', 
    maximumGrainSize=(0.5,'kcal/mol'),
    minimumNumberOfGrains=250,
    temperatures=(300,2000,'K',8),
    pressures=(0.001,100,'bar',5),
    interpolation=('Chebyshev', 6, 4),
)

options(
    units='si',
    generateOutputHTML={'saveInterval':-1, 'saveEdge':True},
    generatePlots=True,
    generatePESDiagrams=True,
    saveEdgeSpecies=True,
    verboseComments=True, #might not want the output plots, pes diagrams, html -> for later decision 
    saveSimulationProfiles=True,
    generateChemkin={'verboseComments':True},
    generateRMSYAML={'saveInterval':1},
    generateCanteraYAML1={'verboseComments':True, 'saveEdge':False},
    generateCanteraYAML2={'verboseComments':True, 'saveEdge':False},
)