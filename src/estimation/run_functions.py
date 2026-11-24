### File for scripts regarding running specific sets of values. Class for 
# run set is defined here as well as all children. Order of storage should
# always follow results -> day -> set -> run. 


### Library imports
from typing import Any

import numpy as np
import re
import time
import traceback
from numpy.typing import NDArray
from itertools import product
from datetime import date, datetime
from pathlib import Path

### Tudat Imports
from tudatpy.interface import spice
from tudatpy.dynamics.propagation_setup import dependent_variable

### Local imports
from src.estimation.estimator_class import estimatorClass
from src.observations.observation_class import observationsClass
from src.environment.harmonics_class import shModelClass, shPyshClass
from src.environment.environment import convert_to_date
from src.estimation.analysis import *



class runSet ():

    def __init__(    
        self,
        # Set parameters list of dictionaries. 
        setParamsList: list[dict],
        # Overall results path. 
        resultsPath: str            = 'results/',
        # Arguments for forcing number of... 
        forceSetNum: bool           = False,       # Starting set.
        setNumForced: int           = 0,
        forceRunNum: bool           = False,       # Starting run. 
        runNumForced: int           = 0
    ) -> None:

        # Paths
        self.resultsPath        = resultsPath 
        self.setPath            = ''
        self.runPath            = ''

        # List of parameter dictionaries. 
        self.setParamsList      = setParamsList
        
        # Run outcome. 0: Failure, 1: Success, 2: Warnings. 
        self.runOutcome: list[ int ] = []
        # Run durations. 
        self.runDuration: list[ float ] = []

        # Run info dictionary containing empty flag key list.
        self.runInfo= dict( )
        self.runInfo['flags'] = []
        self.runInfo['observParameters'] = []

        # Load spice kernels. Necessary for any run. 
        spice.load_standard_kernels()

        # Makes day folder on class creation if it does not exist. 
        self.make_day_folder()

        # Set number to forced. Otherwise reads highest.
        if forceSetNum: self.setNum = setNumForced
        else: self.setNum = self.get_highest_folder( 
            path= self.dayDir, prefix= SETPREFIX )

        # Run number to forced. 
        if forceRunNum: self.runNum = runNumForced
        else: self.runNum = 0

    def make_day_folder( self ):
        '''Creates a folder for the current date if one does not exist.'''

        # Creates directory for current day if not existing.
        self.dayDir = self.resultsPath + date.today().strftime( "%Y%m%d" ) + "/"
        Path( self.dayDir ).mkdir( parents= True, exist_ok= True ) 

    def make_folder( self, path:str, prefix: str, number: int ):
        '''Makes folder with input prefix and number in indicated path. 
        Outputs path to folder.
        
        Args:
            path (str): String. Path to create folder in. 
            prefix (str): String. Prefix of folder. Should be 'set_' or 'run_.
            number (int): Integer. Number of folder.
        '''
        # Folder path. 
        outPath = path + prefix + f'{number}/'
        # Create folder.
        Path( outPath ).mkdir( parents= True, exist_ok= True )

        return outPath

    def set_estimator( 
        self, 
        estimator: estimatorClass,
        observationsList: list[ observationsClass ] ): 

        self.estimator = estimator
        self.observationsList = observationsList

    def set_dependent_variables( 
        self,
        mainSpacecraftName: str= '',
        centralBodyName: str= '',
        extraVariables: list[ dependent_variable.SingleDependentVariableSaveSettings ]= [] ):
        '''Creates list of dependent variables. By default only adds latitude
        and longitude on the central body of the run. Additional variables must
        be fully defined according to tudatpy.dynamics.propagation_setup.dependent_variables.
        
        Args:
            mainSpacecraftName (str): Name of spacecraft to measure lat/lon of.
            centralBodyName (str): Name of central body.
            extraVariables (list[SingleDependentVariableSaveSettings]): List of additional dependent variable settings. 
        '''
        # Dependent variables list.
        self.dependentVariables = [
            dependent_variable.latitude(
                body= mainSpacecraftName,
                central_body= centralBodyName
            ),
            dependent_variable.longitude(
                body= mainSpacecraftName,
                central_body= centralBodyName
            )
        ]
        if extraVariables: self.dependentVariables += extraVariables
   
    def get_highest_folder( 
        self,
        path: str,
        prefix: str
    ) -> int: 
        '''Gets highest number N of folders named as 'prefixINT' in given path.
        
        Args:
            path (str): String with path where folders are stored.
            prefix (str): String with prefix of numbered folders. '''

        # Defines checking only for directories matching "prefixInt".
        pattern = re.compile( rf"{re.escape( prefix )}(\d+)" )
    
        # Obtains all the numbered values from the directories. 
        numberedFiles = [
            int( match.group( 1 ) )
            for path in Path( path ).iterdir()
            if path.is_dir() and ( match := pattern.fullmatch( path.name ) )
        ]
        # Returns highest. 
        return max(  numberedFiles, default= 0  )

    def save_set_info(
            self,
            misc: str= (''),
            setInfoFilename: str= SETINFO
        ) -> None:
            '''Writes description of set. Parameters and outcome of each run.
            
            Args:
                misc (list[str]): OPTIONAL. Additional information.
                setInfoFilename (str): String. Info file name. Defaults to 'set_info.txt
            ''' 
            # Description of set. 
            setDescription = (
                ' ==================== SET DESCRIPTION ====================\n'
                f' Set iterates through {[ *self.setParamsList[0].keys() ]}\n'
                ' === OUTCOMES: ===\n'
            )

            # Iterates through run outcomes and list. Assumes same arrangement.
            with open( self.setPath + setInfoFilename, "w" ) as file:
                # Write description. 
                for line in setDescription.splitlines():
                    file.write( f"#{line}\n")
                # Write run parameters and outcome. 
                for i, parameterDicts in enumerate( self.setParamsList ):
                    # If large run duration gives info in hours. 
                    if self.runDuration[i]/60 > 120: 
                        duration = self.runDuration[i] / 60**2
                        units = 'hrs'
                    else: 
                        duration = self.runDuration[i] / 60
                        units = 'mins'

                    # Writes info. 
                    file.write( 
                        f'# - RUN {i + 1}\n'
                        f'# Parameters: {[ *parameterDicts.values() ]}\n'
                        f'# Outcome: {self.runOutcome[i]}\n'
                        f'# Duration: {duration} {units}')
                    
                # Write miscellaneous additions. 
                if misc: 
                    assert misc is list[ str ]
                    for line in misc.splitlines():
                        file.write(f'# {line}\n')
 
    def save_run_info(
        self,
        runInfoFilename: str= RUNINFO,
        misc: str= ('')
    ): 
        runDescription = (
            ' ==================== RUN DESCRIPTION ====================\n'
            ' All units are given in SI base units unless indicated otherwise.\n'
            ' I.e meters, m/s, seconds, etc.\n'
            ' Dates are provided in DD-MM-YYYY and J2000.\n' \
            ' Observation parameters are given with each row corresponding to\n' 
            ' an observable. Columns given as: Name - Interval - Noise Sigma\n'
            ' === TIMELINE ===\n'
            f' Start Date (J2000):      {self.runInfo['startDate']} ({self.runInfo['startEpoch']})\n'
            f' End Date (J2000):        {self.runInfo['endDate']} ({self.runInfo['endEpoch']})\n'
            f' Arc Length:              {self.runInfo['arcLength']/60**2} hrs\n'
            ' === INTEGRATION PARAMETERS ===\n'
            f' Method:                  {self.runInfo['integMethod']}\n'
            f' Integration Time Step:   {self.runInfo['integStep']}\n'
            ' === ESTIMATION PARAMETERS ===\n'
            f' Real Environment:        {self.runInfo['environmentReal']}\n'
            f' - Harmonics Degree:      {self.runInfo['degreeReal']}\n'
            f' Reference Environment:   {self.runInfo['environmentReference']}\n'
            f' - Harmonics Degree:      {self.runInfo['degreeReference']}\n'
            f' State Offset:            {self.runInfo['stateOffset']}\n'
            f' Convergence Limit:       {self.runInfo['convergenceLimit']}\n'
            f' Max Iterations:          {self.runInfo['maxIters']}\n'
            f' Estimated Degree:        {self.runInfo['degreeEstimated']}\n'
            ' === OBSERVATION PARAMETERS ===\n'
        )

         # Iterates through run outcomes and list. Assumes same arrangement.
        with open( self.runPath + runInfoFilename, "w" ) as file:
            # Write description. 
            for line in runDescription.splitlines():
                file.write( f"#{line}\n")

            # Write observation parameters table. 
            for name, values in self.runInfo['observParameters']:
                file.write( f'# {name}: ' )
                np.savetxt( file, [ values ], fmt= ["%10.2f s", "%10.3e"], delimiter= "," )

            # Write flags and values. 
            file.write( ' === FLAGS ===\n' )
            for flag, value in self.runInfo['flags']:
                file.write(f'# -{flag}:{value}\n')

            # Write miscellaneous additions. 
            if misc: 
                assert misc is list[ str ]
                for line in misc.splitlines():
                    file.write(f'# {line}\n')

    def run_reality( self ): 

        # Saves relevant info into dict. 
        self.runInfo['startEpoch']= float( self.estimator.environmentReal.simStartEpoch ) 
        self.runInfo['startDate']= convert_to_date( self.runInfo['startEpoch'] )
        self.runInfo['endEpoch']= float( self.estimator.environmentReal.simEndEpoch )
        self.runInfo['endDate']= convert_to_date( self.runInfo['endEpoch'] )
        self.runInfo['arcLength']= self.estimator.arcLengthReal
        self.runInfo['environmentReal']= \
            f'{self.estimator.environmentReal.frameOriginBody} - {self.estimator.environmentReal.level}'
        self.runInfo['degreeReal'] = self.estimator.environmentReal.harmonicsMaxDegree

        # Propagate reality.  
        self.estimator.propagate_reality(
            dependentVariables= self.dependentVariables
        )
        # Saves reality propagation to overall run directory. 
        self.estimator.save_real_propagation(
            fileDir= self.setPath,
            fileName= REALSTATESFILE
        )
        # Creates shModelClass from reference harmonics.
        self.harmonicsReal = shModelClass.make_from_environment(
            environment= self.estimator.environmentReal
        )
        # Convert to pysh harmonics and save. 
        pyshReal = shPyshClass.from_shModelClass( self.harmonicsReal )
        pyshReal.plot_gravity_anomaly( 
            title= "Real Gravity Anomaly", show= False, save= True, 
            fileDir= self.setPath, fileName= REALMAPFILE 
        )

    def run_observations( 
        self, 
        observationClasses: list[ observationsClass ],
        observationDict: dict 
        ):
        
        for observation in observationClasses: 
            # Initializes observations objects 
            observation.initial_setup()

            # Sets noise of observations. 
            if observationDict[ observation.name ] > 0:
                observation.set_noise_sigma( noiseSigma= observationDict[ 
                    observation.name ] 
                )

            # Saves observation characteristics. 
            self.runInfo['observParameters'].append( [
                observation.name, [
                    observation.interval,
                    observation.noiseSigma 
                    ]
                ] 
            )

        # Create observation collection. 
        self.estimator.make_observations(
            observationsList= observationClasses,
            weighObservations= True
        )

        # Save observation values. 
        self.estimator.save_observations(
            fileDir= self.runPath,
            fileName= OBSERVATIONSFILE
        )

    def run_estimation( 
        self, 
        initialStateOffset: NDArray= np.zeros(6),
        maxIterations: int= 10,
        minResidualChange: float= 0.0,
        estimationDegree: int= 10,
        ): 

        # Save estimation degree.
        self.estimatedDegree = estimationDegree

        # Save relevant information.
        self.runInfo['stateOffset']     = initialStateOffset
        self.runInfo['maxIters']        = maxIterations
        self.runInfo['convergenceLimit']= minResidualChange
        self.runInfo['environmentReference'] = \
            f'{self.estimator.environmentReference.frameOriginBody} - {self.estimator.environmentReference.level}'
        self.runInfo['degreeReference'] = self.estimator.environmentReference.harmonicsMaxDegree
        self.runInfo['degreeEstimated'] = estimationDegree

        # For the time being these match through all environments but might be
        # a good idea to change that.
        self.runInfo['integMethod'] = 'rk_78_fixed_step'
        self.runInfo['integStep']   = self.estimator.environmentReal.timeStep

        # Apply initial state offset. 
        self.estimator.set_initial_state_offset(
            initialStateOffset= initialStateOffset
        )

        # Estimate
        self.estimator.make_estimation(
            maximumIterations= maxIterations,
            printEstimationOutput= False,
            estimationDegree= estimationDegree,

            covarianceAnalysis= True
        )
        self.harmonicsEstimated = shModelClass.make_from_estimate(
            estimator= self.estimator
        )
        # Save estimated harmonics. 
        self.harmonicsEstimated.save_coefficients(
            fileDir= self.runPath,
            fileName= ESTIMATEFILE
        )
        
    def run_analysis( self, fullCorrMatx: int= 0 ):

        # Save correlation matrix. 
        self.estimator.save_estimation_analysis(
            fileDir= self.runPath,
            analysisFileName= ANALYSISFILE,
            corrFileName= CORRMATXFILE,
            fullCorrMatx= fullCorrMatx
        )

        # Save Correlation matrix flag.
        self.runInfo['flags'].append( [ CORRMATXFLAG, fullCorrMatx ] )

        # Obtain difference between estimated and real harmonics.
        harmonicsDelta = self.harmonicsReal.make_from_difference(
            other= self.harmonicsEstimated
        )
        # Convert to pyshHarmonics
        pyshEstimated = shPyshClass.from_shModelClass( self.harmonicsEstimated )
        pyshDelta     = shPyshClass.from_shModelClass( harmonicsDelta )
        # Plot and save. 
        pyshEstimated.plot_gravity_anomaly( 
            title= "Estimated Gravity Anomaly", show= False,
            save= True, fileDir= self.runPath, fileName= ESTIMATEMAPFILE )
        pyshDelta.plot_gravity_anomaly(
            title= "Gravity Anomaly Error", show= False,
            save= True, fileDir= self.runPath, fileName= ERRORMAPFILE )

        # Saves analysis plots. 
        analysis = analysisLibrary( runDir= self.runPath )
        analysis.load_propagation( realStatesPath= self.setPath + REALSTATESFILE )
        analysis.plot_observation_density( title= "Observation Density", 
            degreeSlice= self.estimatedDegree + 20, save= True)
        analysis.load_correlation( corrFileName= CORRMATXFILE )
        analysis.plot_correlation( title= 'Correlation Matrix', save= True )
 
    def run_set( 
            self, 
            runPrefix: str= RUNPREFIX, 
            setPrefix: str= SETPREFIX,
            **kwargs ): 

            # Make set folder.
            self.setPath = self.make_folder( path= self.dayDir, prefix= setPrefix, 
                                             number= self.setNum + 1  )

            # Common elements in set. Specific to children classes.
            self.run_common( **kwargs )

            # Iterate through parameters.  
            for parameters in self.setParamsList:

                # Create run folder.
                self.runPath = self.make_folder( path= self.setPath, prefix= runPrefix,
                                                number= self.runNum + 1)

                # Start counting time. 
                startTime = time.process_time()
                
                # Catch exceptions to run attempts.
                try:

                    # Children classes single run function.
                    self.run_single( parameters, **kwargs )

                    # Save run info. 
                    self.save_run_info()

                    # Saves run as success.
                    self.runOutcome.append( 1 )
                    # End counting and save. 
                    self.runDuration.append( time.process_time() - startTime )

                    # Increase run number. 
                    self.runNum += 1

                except Exception:
                    exceptionFile = self.setPath + f'crash_log_{self.runNum+1}.txt'
                    # Crash log. 
                    with open(exceptionFile, 'w') as file:
                        file.write(f'Run failed at {datetime.now():%Y-%m-%d %H:%M:%S}\n') 
                        traceback.print_exc( file= file )

                    print( f"Run {self.runNum + 1} failed. See crash log.")
                    # Saves run as failed.
                    self.runOutcome.append( 0 )
                    # End counting and save. 
                    self.runDuration.append( time.process_time() - startTime )

                    # Increase run number. 
                    self.runNum += 1

                    continue

            # Save set info.
            self.save_set_info()
        
    def run_common( self, **kwargs ): pass # Specific to children classes.

    def run_single( self, parameters, **kwargs ): pass # Specific to children classes. 


class noiseSet ( runSet ):
    
    def __init__(
        self, 
        setParamsList: list[dict], 
        resultsPath: str = 'results/', 
        forceSetNum: bool = False, 
        setNumForced: int = 0, 
        forceRunNum: bool = False, 
        runNumForced: int = 0
        ) -> None:
        '''Class for sets of instrument noise estimates. Set parameter list
        must be a list of dictionaries whose keys are observation types and values 
        the noise sigmas.
        
        Args:
            resultsPath (str): String with path of overall results folder. 
            setParamsList (list[dict]): List of dictionary set parameters. 
            Should be formatted such that each dictionary's keys are the noise
            types and values the noise sigmas to be used for that specific combination.

        '''

        super().__init__(setParamsList, resultsPath, forceSetNum, setNumForced, 
                         forceRunNum, runNumForced)

    def run_common( self, **kwargs ) -> None: 

        # Only required to propagate reality once. 
        self.run_reality()

    def run_single(
        self, 
        parameters, 
        initialStateOffset: NDArray= np.zeros(6),
        maxIterations: int= 10,
        estimatedDegree: int= 10,

        **kwargs
    ) -> None:
        '''Single run for observation noise estimate set. Parameters here
        correspond to a dictionary whose keys are the observation types and
        values their noise sigma.'''

        # Requires computing observations on each new run. 
        self.run_observations( observationClasses= self.observationsList,
                               observationDict= parameters )

        self.run_estimation( initialStateOffset= initialStateOffset,
                             maxIterations= maxIterations,
                             estimationDegree= estimatedDegree )

        self.run_analysis( fullCorrMatx= 0 )


class simTimeSet ( runSet ):

    def __init__(
        self, 
        setParamsList: list[dict], 
        resultsPath: str = 'results/', 
        forceSetNum: bool = False, 
        setNumForced: int = 0, 
        forceRunNum: bool = False, 
        runNumForced: int = 0
        ) -> None:
        '''Class for set of estimates using different total simulation time.
        setParamsList should be given as a list of dictionaries, each of which
        has a single key and value attributed to it. 
        
        Args:
            resultsPath (str): String with path of overall results folder. 
            setParamsList (list[dict]): List of dictionary set parameters. 
            Should be formatted such that each dictionary has a single key and
            whose only value is the simulation duration in seconds.
        '''

        super().__init__(setParamsList, resultsPath, forceSetNum, setNumForced, 
                            forceRunNum, runNumForced)

    # No common items. 
    def run_single( 
        self, 
        parameters, 
        initialStateOffset: NDArray= np.zeros(6),
        maxIterations: int= 10,
        estimatedDegree: int= 10,
        observationsDict: dict= {'sst_range':0.0,'dsn_doppler':0.0},
        
        **kwargs ):

        # Sets new values for simulation time. 
        assert isinstance( parameters, dict )
        self.estimator.set_simulation_time( simTime= float( *parameters.values() ) )

        

        self.run_reality()

        self.run_observations( observationClasses= self.observationsList,
                               observationDict= observationsDict )
        
        self.run_estimation( initialStateOffset= initialStateOffset,
                             maxIterations= maxIterations,
                             estimationDegree= estimatedDegree )

        self.run_analysis( fullCorrMatx= 0 )


class degreeSet ( runSet ): pass

