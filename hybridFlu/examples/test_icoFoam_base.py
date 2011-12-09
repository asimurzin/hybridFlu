## Copyright (C) 2010- Alexey Petrov
## Copyright (C) 2009-2010 Pebble Bed Modular Reactor (Pty) Limited (PBMR)
## 
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
## 
## See http://sourceforge.net/projects/pythonflu
##
## Author : Alexey PETROV
##


#--------------------------------------------------------------------------------------
from Foam import man, ref

from icoFlux.embedded import solver as icoFoam

from hybridFlu.foam2visu import TDummyPostProcessor
from hybridFlu.foam2visu import print_d


#--------------------------------------------------------------------------------------
def print_d( the_message, the_debug_mode = True ):
    """
    Helper function to control output debug information
    """
    if the_debug_mode :
        print the_message
        pass
    pass


#--------------------------------------------------------------------------------------
def createITstream(pyList):
    size = len(pyList)
    ret = ref.tokenList(size)
    for i in xrange(size):
        ret[i] = ref.token(ref.word(pyList[i]))
        pass
    
    stream = ref.ITstream( ref.word( "dummy"), ret )
    return stream


#--------------------------------------------------------------------------------------
def pyWordList(pyList):
    size = len(pyList)
    ret = ref.wordList(size)
    for i in xrange(size):
        ret[i] = ref.word(pyList[i])
    return ret


#--------------------------------------------------------------------------------------
class TIcoFoamSolverBase :
    """
    Incapsulates all the basic features for icoFoam solver
    """
    def __init__( self, the_case_dir, the_post_processor = None ) :
        """
        Constructs instance of this class
        """
        import os, os.path   
        #  To identify the canonical pathes of the specified filenames, 
        # eliminating any symbolic links encountered in the pathes
        the_case_dir = os.path.realpath( the_case_dir )

        # Definiton of the "root" and OpenFOAM "case"
        a_root_dir, a_case = os.path.split( the_case_dir )
        print_d( "a_root_dir = \"%s\", a_case = \"%s\"" % ( a_root_dir, a_case ) )
        
        a_controlDict = self._createControlDict()
        # Create time - without reading controlDict from file
        # Note - controlDict not written to file using this method
        
        self.run_time = ref.Time( a_controlDict, ref.fileName( a_root_dir ), ref.fileName( a_case ) )

        print_d( "self.run_time.caseConstant() = %s" % self.run_time.caseConstant() )

        # Create transport properties
        self.transportProperties = ref.IOdictionary( ref.IOobject( ref.word( "transportProperties" ),
                                                                   self.run_time.caseConstant(),
                                                                   self.run_time,
                                                                   ref.IOobject.NO_READ,
                                                                   ref.IOobject.NO_WRITE ) )

        nu = ref.dimensionedScalar( ref.word( "nu" ), ref.dimensionSet( 0.0, 2.0, -1.0, 0.0, 0.0, 0.0, 0.0 ), 1e-6 )
        self.transportProperties.add( ref.word( "nu" ), nu );
    
    
        # Create fvSchemes and fvSolution dictionaries
        fvSchemesDict = self._createFvSchemesDict()
        fvSoln = self._createFvSolution()
        
        # Write all dictionaries to file
        # Note, we currently need fvSchemes and fvSolution to reside in the case directory
        # since it is used during the solution... so we now write them to file
        self.run_time.writeNow()

        # Clean up unused variables
        fvSchemesDict = 0
        fvSoln = 0

        # Create mesh
        self.mesh, self.patches = self._createFvMesh()
        # mesh.write()

        # Create pressure field
        pPatchTypes = pyWordList( [ 'zeroGradient', 'fixedValue', 'fixedValue', 'zeroGradient' ] )

        a_value = ref.dimensionedScalar( ref.word(), 
                                         ref.dimensionSet( 0.0, 2.0, -2.0, 0.0, 0.0, 0.0, 0.0 ), 
                                         101.325 )

        self.p = ref.volScalarField( ref.IOobject( ref.word( "p" ),
                                                   ref.fileName( self.run_time.timeName() ),
                                                   self.mesh,
                                                   ref.IOobject.NO_READ,
                                                   ref.IOobject.AUTO_WRITE),
                                     self.mesh,
                                     a_value,
                                     pPatchTypes )
    
        self.p.ext_boundaryField()[ 1 ] << 101.325
        self.p.ext_boundaryField()[ 2 ] << 101.325
    
        # Create velocity field
        UPatchTypes = pyWordList( [ 'fixedValue', 'zeroGradient', 'zeroGradient', 'fixedValue' ] )

        a_value = ref.dimensionedVector( ref.word(), 
                                         ref.dimensionSet( 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0 ), 
                                         ref.vector( 0.0, 0.0, 0.0 ) )

        self.U = ref.volVectorField( ref.IOobject( ref.word( "U" ),
                                                   ref.fileName( self.run_time.timeName() ),
                                                   self.mesh,
                                                   ref.IOobject.NO_READ,
                                                   ref.IOobject.AUTO_WRITE ),
                                     self.mesh,
                                     a_value,
                                     UPatchTypes )

        self.U.ext_boundaryField()[ 0 ] << ref.vector( 0.0, 0.1, 0.0 )
        self.U.ext_boundaryField()[ 3 ] << ref.vector( 0.0, 0.0, 0.0 )

        self.phi = ref.createPhi( self.run_time, self.mesh, self.U )

        # Write all dictionaries to file
        self.run_time.writeNow()

        # Define the post processor engine
        if the_post_processor == None :
            the_post_processor = TDummyPostProcessor
            pass
        
        # Construction of the post processor engine
        self.post_processor = the_post_processor( the_case_dir, a_case )

        # To dump controlDict to be able to run "foamToVTK" utility
        self._writeControlDict( a_controlDict )
        
        # Post processing of the first step
        self.post_processor.process( self.run_time.value() )

        # Initialization of the engine
        self.solver = icoFoam( self.run_time, self.U, self.p, self.phi, self.transportProperties )
        pass


    #--------------------------------------------------------------------------------------
    def _createFvMesh( self ) :
        """
        Creates fvMesh (should be overriden in the class descendants)
        """
        raise "This method should be overriden"


    #--------------------------------------------------------------------------------------
    def _createControlDict( self ) :
        """
        Creates controlDict dictionary
        """
        a_controlDict = ref.dictionary()
        a_controlDict.add( ref.word( "startFrom" ), ref.word( "startTime" ) )
        a_controlDict.add( ref.word( "startTime" ), 0.0 )

        a_controlDict.add( ref.word( "stopAt" ), ref.word( "endTime" ) )
        a_controlDict.add( ref.word( "endTime" ), 0.05 )

        a_controlDict.add( ref.word( "deltaT" ), 0.01 )
        a_controlDict.add( ref.word( "writeControl" ), ref.word( "timeStep" ) )

        a_controlDict.add( ref.word( "writeInterval" ), 5 )

        return a_controlDict
        pass


    #--------------------------------------------------------------------------------------
    def _writeControlDict( self, the_dict ) :
        """
        write controlDict dictionary
        """
        a_controlDict = ref.IOdictionary( ref.IOobject( ref.word( "controlDict" ),
                                                        self.run_time.caseSystem(),
                                                        self.run_time,
                                                        ref.IOobject.NO_READ,
                                                        ref.IOobject.AUTO_WRITE ), the_dict )
        a_controlDict.write()
        pass


    #--------------------------------------------------------------------------------------

    def _createFvSchemesDict( self ) :
        """
        Creates fvSchemes dictionary
        """
        # Create schemes dictionary
        fvSchemesDict = ref.IOdictionary( ref.IOobject( ref.word( "fvSchemes" ),
                                                        self.run_time.caseSystem(),
                                                        self.run_time,
                                                        ref.IOobject.NO_READ,
                                                        ref.IOobject.AUTO_WRITE ) )
    
        ddtSchemes = ref.dictionary()
        ddtSchemes.add(ref.word("default"), ref.word("Euler"))
    
        interpolationSchemes = ref.dictionary()
        interpolationSchemes.add(ref.word("default"),ref.word("linear"))
    
        gradSchemes = ref.dictionary()
        gradSchemes.add(ref.word("default"), createITstream(["Gauss","linear"]))
        gradSchemes.add(ref.word("grad(p)"), createITstream(["Gauss","linear"]))
    
        snGradSchemes = ref.dictionary()
        snGradSchemes.add(ref.word("default"), ref.word("corrected"))
    
        divSchemes = ref.dictionary()
        divSchemes.add(ref.word("default"), ref.word("none"))
        divSchemes.add(ref.word("div(phi,U)"), createITstream(["Gauss","linear"]))
    
        laplacianSchemes = ref.dictionary()
        laplacianSchemes.add(ref.word("default"), ref.word("none"))
        laplacianSchemes.add(ref.word("laplacian(nu,U)"), createITstream(["Gauss","linear","corrected"]))
        laplacianSchemes.add(ref.word("laplacian((1|A(U)),p)"), createITstream(["Gauss","linear","corrected"]))
    
        fluxRequired = ref.dictionary()
        fluxRequired.add(ref.word("default"), ref.word("no"))
        fluxRequired.add(ref.word("p"), ref.word())
    
        fvSchemesDict.add(ref.word("ddtSchemes"), ddtSchemes)
        fvSchemesDict.add(ref.word("interpolationSchemes"), interpolationSchemes)
        fvSchemesDict.add(ref.word("gradSchemes"), gradSchemes)
        fvSchemesDict.add(ref.word("snGradSchemes"), snGradSchemes)
        fvSchemesDict.add(ref.word("laplacianSchemes"), laplacianSchemes)
        fvSchemesDict.add(ref.word("divSchemes"), divSchemes)
        fvSchemesDict.add(ref.word("fluxRequired"), fluxRequired)
    
        return fvSchemesDict


    #--------------------------------------------------------------------------------------
    def _createFvSolution( self ) :
        """
        Creates fvSolution dictionary
        Currently not fully functional, format of "solvers" entries currently
        can't be written to file unless using stream objects. We need a
        workaround for this.
        """
        USolver = ref.dictionary()
        USolver.add(ref.word("preconditioner"), ref.word("DILU"))
        USolver.add(ref.word("minIter"), 0)
        USolver.add(ref.word("maxIter"), 1000)
        USolver.add(ref.word("tolerance"), 1E-5)
        USolver.add(ref.word("relTol"), 0)
    
        pSolver = ref.dictionary()
        pSolver.add(ref.word("preconditioner"), ref.word("DIC"))
        pSolver.add(ref.word("minIter"), 0)
        pSolver.add(ref.word("maxIter"), 1000)
        pSolver.add(ref.word("tolerance"), 1E-6)
        pSolver.add(ref.word("relTol"), 0)
    
        piso = ref.dictionary()
        piso.add(ref.word("nCorrectors"), 2)
        piso.add(ref.word("nNonOrthogonalCorrectors"), 0)
    
        fvSolnDict = ref.dictionary()
        fvSolnDict.add(ref.word("PISO"), piso)
    
        soln = ref.ext_solution( self.run_time, 
                             ref.fileName( "fvSolution" ), 
                             fvSolnDict )
        soln.setWriteOpt( ref.IOobject.AUTO_WRITE )

        soln.addSolver(ref.word("U"), ref.word("PBiCG"), USolver)
        soln.addSolver(ref.word("p"), ref.word("PCG"), pSolver)
    
        return soln


    #--------------------------------------------------------------------------------------
    def run( self, the_number_iterations = 5 ) :
        """
        Runs the solver execution
        The fvSolution dictionary must be manually edited before calling this function
        (see comments for createFvSolutionDict)
        """
        pRes = [] #initial pressure residual
        uRes = [] #initial velocity residual
        it   = []
        iteration = []
        iteration.append( 0 )
    
        for i in xrange( the_number_iterations ) :
            i += iteration[0]
            it.append(i)
            self.solver.step()
            pRes.append( self.solver.pressureRes() )
            uRes.append( self.solver.velocityRes() )
            pResTpl = tuple( pRes )
            uResTpl = tuple( uRes )

            self.run_time.writeNow()

            print_d( "runTime.value() = %g" % ( self.run_time.value() ) )
            self.post_processor.process( self.run_time.value() )

            pass

        iteration[0] += the_number_iterations

        return True

    pass


#--------------------------------------------------------------------------------------
