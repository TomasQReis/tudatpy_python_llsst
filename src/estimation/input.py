# Contains functions related to reading and writing input yaml files.


# Library imports
import yaml

# Constants
# Template file path.
TEMPLATEPATH = 'src/estimation/input_template.yaml'

class yamlInput ():

    def __init__(
        self,
        data: dict,
        path: str= '',
    ) -> None: 
        
        self.data = data
        self.path = path    # Path of loaded data. 

        # Loads template (standard) keys into a list. 
        self.templateKeys = self.load_template()
        # Checks keys in loaded data. 
        self.check_keys()
        # Flag for parsed data. 
        self.parsed = False
        

    @classmethod
    def from_file( cls, inputPath: str ):

        # Extract data from file. 
        # NOTE: Should match template file. 
        # TODO: Add check for template keys. 
        with open( inputPath, 'r' ) as file:
            return cls( yaml.safe_load( file ), inputPath )

    @classmethod
    def from_args( cls, inputDict: dict ): pass 

    # Check all template keys are present in data.
    def check_keys( self ):
        """Checks that the loaded data contains every top and 2nd level key
        of the template. 

        Raises:
            KeyError: If any template keys are missing from self.data. The message
                lists all missing keys and the file they were loaded from (self.path).
        """

        missing = []

        #for key in self.templateKeys:
        for key in self.templateKeys:
            for dataKey, value in self.data.items(): 
                # Checks first layer of data keys. 
                if key == dataKey: 
                    break
                # Checks second layer of data keys. 
                elif isinstance( value, dict ) and key in value.keys():
                    break
            else:
                # If key is not found, add to list. 
                missing.append( key )

        # Raises key error on missing keys. 
        if len( missing ) > 0:
            raise KeyError(
                f'Template keys {missing} not found in loaded data.\n'
                f'From {self.path}'
            )

    # Parse data into useful variables. 
    def parse_data( self ) -> None:         

        # Estimation properties. 
        self.estProperties = self.data[ self.templateKeys[0] ]

        # Environment properties.
        envProperties = self.data[ self.templateKeys[1] ]
        self.centralBody = envProperties[ 'central_body' ]
        self.envRealProperties = envProperties[ 'real_env' ]
        self.envRefProperties = envProperties[ 'ref_env' ]

        # Spacecraft properties.
        scProperties = self.data[ self.templateKeys[2] ]
        self.scList = self.load_items( data= scProperties, prefix= 'sc' )

        # Ground station properties. 
        gsProperties = self.data[ self.templateKeys[3] ]
        self.gsList = self.load_items( data= gsProperties, prefix= 'gs' )

        # Observation properties. 
        obsProperties = self.data[ self.templateKeys[4] ]
        self.obsList = self.load_items( data= obsProperties, prefix= 'obs' )

        # Parsed flag. 
        self.parsed = True

    # Bunch of getter functions for specific parts of input data. 
    def get_estimation( self ):
        if not self.parsed: self.parse_data()
        return self.estProperties

    def get_environment( self ): 
        if not self.parsed: self.parse_data()
        return self.centralBody, self.envRealProperties, self.envRefProperties
    
    def get_spacecraft( self ):
        if not self.parsed: self.parse_data()
        return self.scList

    def get_ground_stations( self ):
        if not self.parsed: self.parse_data()
        return self.gsList

    def get_observations( self ):
        if not self.parsed: self.parse_data()
        return self.obsList

    # Sweep through variable number items (spacecraft, ground stations and 
    # observables)
    def load_items( 
        self,
        data: dict, 
        prefix: str 
    ) -> list[ dict ]:
        """Collects numbered items from a dictionary loaded from a config file.

        The dictionary must contain a count entry '<prefix>_num' and one entry per
        item, named '<prefix>_1' to '<prefix>_<count>'.

        Args:
            data (dict): Data from loaded yaml file containing count and numbered
                items. e.g. the output of yaml.safe_load.
            prefix (str): Name shared by the count and item keys, e.g. "sc" for
                sc_num, sc_1, sc_2, ...

        Returns:
            list[dict]: The items in numbered order, '<prefix>_1' first.

        Raises:
            KeyError: If '<prefix>_num' or one of the numbered items is missing.

        Examples:
            >>> data = { "sc_num": 2,
            ...          "sc_1": { "name": "rociA" },
            ...          "sc_2": { "name": "rociB" } }
            >>> load_items( data, "sc" )
            [{'name': 'rociA'}, {'name': 'rociB'}]
        """

        count = data[ f'{prefix}_num' ]
        items = []

        for i in range( 1, count + 1 ):
        
            # Key for numbered prefix item. 
            key = f'{prefix}_{i}'
            if key not in data:
                raise KeyError(
                    f'{key} not found in data. Check prefix: {prefix}.'
                )
            # Add to list. 
            items.append( data[ key ] )

        return items
        
    # Load template file. 
    def load_template( self, templatePath: str= TEMPLATEPATH ):
        '''Loads template path and keys. This function should not be accessed outside
        of the class.

        Args:
            templatePath (str): Local path of template file. Defaults to 
                locally defined constant TEMPLATEPATH.
        Returns:
            yaml.safe_load of templatePath file.         
        '''
        with open( templatePath, 'r' ) as file:
            template = yaml.safe_load( file )

        # Adds top level keys. 
        keys = [ *template.keys() ]
        secondKeys = []
        # Add second layer of keys. 
        for value in template.values():
            secondKeys.extend( [ *value.keys() ] )

        keys.extend( secondKeys )

        return keys

    # Save input data to file. 
    def save_input( self, filePath: str, fileName: str= 'input.yaml' ):
        with open( filePath + fileName, 'w' ) as file: 
            yaml.dump( self.data, file, sort_keys= False )
