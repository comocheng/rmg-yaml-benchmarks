#input file modified for a 5-10 minute run, intended to test the output structure 

database(
    thermoLibraries=[
        'primaryThermoLibrary',
        'Klippenstein_Glarborg2016',
        'thermo_DFT_CCSDTF12_BAC',
        'DFT_QCI_thermo',
        'FFCM1(-)',
    ],
    reactionLibraries=[
        ('BurkeH2O2inN2',               False),
        ('FFCM1(-)',                   False),
        ('Klippenstein_Glarborg2016', False),
    ],
    seedMechanisms=[
        'BurkeH2O2inN2',
        'Klippenstein_Glarborg2016',
    ],
    kineticsDepositories=['training'],
    kineticsFamilies='default',
    kineticsEstimator='rate rules',
)

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

species(
    label='Ar',
    reactive=False,
    structure=SMILES("[Ar]"),
)

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


# Reactor 1: High temperature, low pressure
simpleReactor(
    temperature=(1500, 'K'),
    pressure=(1.0, 'bar'),
    initialMoleFractions={
        "ethane":   0.050,
        "O2":       0.175,
        "Ar":       0.775,
    },
    terminationConversion={'ethane': 0.9},
    terminationTime=(1.0, 's'),
)

# Reactor 2: Intermediate temperature, high pressure
simpleReactor(
    temperature=(1000, 'K'),
    pressure=(20.0, 'bar'),
    initialMoleFractions={
        "ethane":   0.050,
        "O2":       0.245,
        "Ar":       0.705,
    },
    terminationConversion={'ethane': 0.9},
    terminationTime=(1.0, 's'),
)

simulator(
    atol=1e-6,
    rtol=1e-6,
)

#loose for fast termination
model(
    toleranceKeepInEdge=0.01,
    toleranceMoveToCore=0.5,
    toleranceInterruptSimulation=0.5,
    maximumEdgeSpecies=200,
    filterReactions=True,
)

generatedSpeciesConstraints(
    maximumCarbeneRadicals=2,
)

pressureDependence(
    method='modified strong collision',
    maximumGrainSize=(0.5, 'kcal/mol'),
    minimumNumberOfGrains=250,
    temperatures=(300, 2000, 'K', 8),
    pressures=(0.001, 100, 'bar', 5),
    interpolation=('Chebyshev', 6, 4),
)

options(
    units='si',
    generateOutputHTML=True,
    generatePlots=False,
    generatePESDiagrams=False,
    saveEdgeSpecies=True,
    verboseComments=True,
    saveSimulationProfiles=True,
)