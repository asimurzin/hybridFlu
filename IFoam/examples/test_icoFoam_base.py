## VulaSHAKA (Simultaneous Neutronic, Fuel Performance, Heat And Kinetics Analysis)
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
## See https://vulashaka.svn.sourceforge.net/svnroot/vulashaka/ifoam
##
## Author : Alexey PETROV
##


#--------------------------------------------------------------------------------------
from Foam.OpenFOAM import *
from Foam.finiteVolume import *

from Foam.applications.solvers.incompressible.emb_icoFoam import solver as icoFoam

from IFoam.foam2visu import TDummyPostProcessor
from IFoam.foam2visu import print_d


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
def pyTokenList(pyList):
    size = len(pyList)
    ret = tokenList(size)
    for i in xrange(size):
        ret[i] = token(word(pyList[i]))
    return ret


#--------------------------------------------------------------------------------------
def pyWordList(pyList):
    size = len(pyList)
    ret = wordList(size)
    for i in xrange(size):
        ret[i] = word(pyList[i])
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

        # Create time - without reading controlDict from file
        # Note - controlDict not written to file using this method
        self.run_time = Time( fileName( a_root_dir ), fileName( a_case ) )
        self.run_time.setTime( 0.0, 0 )
        self.run_time.setDeltaT( 0.01 )
        self.run_time.setEndTime( 0.05 )

        print_d( "self.run_time.caseConstant() = %s" % self.run_time.caseConstant() )

        # Create transport properties
        self.transportProperties = IOdictionary( IOobject( word( "transportProperties" ),
                                                           self.run_time.caseConstant(),
                                                           self.run_time,
                                                           IOobject.NO_READ,
                                                           IOobject.NO_WRITE ) )

        nu = dimensionedScalar( word( "nu" ), dimensionSet( 0, 2, -1, 0, 0, 0, 0 ), 1e-6 )
        self.transportProperties.add( word( "nu" ), nu );
    
    
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

        a_value = dimensionedScalar( word(), 
                                     dimensionSet( 0, 2, -2, 0, 0, 0, 0 ), 
                                     101.325 )

        self.p = volScalarField( IOobject( word( "p" ),
                                           fileName( self.run_time.timeName() ),
                                           self.mesh,
                                           IOobject.NO_READ,
                                           IOobject.AUTO_WRITE),
                                 self.mesh,
                                 a_value,
                                 pPatchTypes
                                 )
    
        self.p.ext_boundaryField()[ 1 ].ext_assign( 101.325 )
        self.p.ext_boundaryField()[ 2 ].ext_assign( 101.325 )
    
        # Create velocity field
        UPatchTypes = pyWordList( [ 'fixedValue', 'zeroGradient', 'zeroGradient', 'fixedValue' ] )

        a_value = dimensionedVector( word(), 
                                     dimensionSet( 0, 1, -1, 0, 0, 0, 0 ), 
                                     vector( 0, 0, 0 ) )

        self.U = volVectorField( IOobject( word( "U" ),
                                           fileName( self.run_time.timeName() ),
                                           self.mesh,
                                           IOobject.NO_READ,
                                           IOobject.AUTO_WRITE ),
                                 self.mesh,
                                 a_value,
                                 UPatchTypes
                                 )

        self.U.ext_boundaryField()[ 0 ].ext_assign( vector( 0, 0.1, 0 ) )
        self.U.ext_boundaryField()[ 3 ].ext_assign( vector( 0, 0.0, 0 ) )

        from Foam.finiteVolume.cfdTools.incompressible import createPhi
        self.phi = createPhi( self.run_time, self.mesh, self.U )

        # Write all dictionaries to file
        self.run_time.writeNow()

        # Define the post processor engine
        if the_post_processor == None :
            the_post_processor = TDummyPostProcessor
            pass
        
        # Construction of the post processor engine
        self.post_processor = the_post_processor( the_case_dir, a_case )

        # To dump controlDict to be able to run "foamToVTK" utility
        self._createControlDict()
        
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
        a_controlDict = IOdictionary( IOobject( word( "controlDict" ),
                                                self.run_time.caseSystem(),
                                                self.run_time,
                                                IOobject.NO_READ,
                                                IOobject.AUTO_WRITE ) )
    
        a_controlDict.add( word( "startFrom" ), word( "startTime" ) )
        a_controlDict.add( word( "startTime" ), self.run_time.startTime().value() )

        a_controlDict.add( word( "stopAt" ), word( "endTime" ) )
        a_controlDict.add( word( "endTime" ), self.run_time.endTime().value() )

        a_controlDict.add( word( "deltaT" ), self.run_time.deltaT().value() )
        a_controlDict.add( word( "writeControl" ), word( "timeStep" ) )

        a_controlDict.add( word( "writeInterval" ), 5 )

        a_controlDict.write()
        pass


    #--------------------------------------------------------------------------------------
    def _createFvSchemesDict( self ) :
        """
        Creates fvSchemes dictionary
        """
        # Create schemes dictionary
        fvSchemesDict = IOdictionary( IOobject( word( "fvSchemes" ),
                                                self.run_time.caseSystem(),
                                                self.run_time,
                                                IOobject.NO_READ,
                                                IOobject.AUTO_WRITE ) )
    
        ddtSchemes = dictionary()
        ddtSchemes.add(word("default"), word("Euler"))
    
        interpolationSchemes = dictionary()
        interpolationSchemes.add(word("default"),word("linear"))
    
        gradSchemes = dictionary()
        gradSchemes.add(word("default"), pyTokenList(["Gauss","linear"]))
        gradSchemes.add(word("grad(p)"), pyTokenList(["Gauss","linear"]))
    
        snGradSchemes = dictionary()
        snGradSchemes.add(word("default"), word("corrected"))
    
        divSchemes = dictionary()
        divSchemes.add(word("default"), word("none"))
        divSchemes.add(word("div(phi,U)"), pyTokenList(["Gauss","linear"]))
    
        laplacianSchemes = dictionary()
        laplacianSchemes.add(word("default"), word("none"))
        laplacianSchemes.add(word("laplacian(nu,U)"), pyTokenList(["Gauss","linear","corrected"]))
        laplacianSchemes.add(word("laplacian((1|A(U)),p)"), pyTokenList(["Gauss","linear","corrected"]))
    
        fluxRequired = dictionary()
        fluxRequired.add(word("default"), word("no"))
        fluxRequired.add(word("p"), word())
    
        fvSchemesDict.add(word("ddtSchemes"), ddtSchemes)
        fvSchemesDict.add(word("interpolationSchemes"), interpolationSchemes)
        fvSchemesDict.add(word("gradSchemes"), gradSchemes)
        fvSchemesDict.add(word("snGradSchemes"), snGradSchemes)
        fvSchemesDict.add(word("laplacianSchemes"), laplacianSchemes)
        fvSchemesDict.add(word("divSchemes"), divSchemes)
        fvSchemesDict.add(word("fluxRequired"), fluxRequired)
    
        return fvSchemesDict


    #--------------------------------------------------------------------------------------
    def _createFvSolution( self ) :
        """
        Creates fvSolution dictionary
        Currently not fully functional, format of "solvers" entries currently
        can't be written to file unless using stream objects. We need a
        workaround for this.
        """
        USolver = dictionary()
        USolver.add(word("preconditioner"), word("DILU"))
        USolver.add(word("minIter"), 0)
        USolver.add(word("maxIter"), 1000)
        USolver.add(word("tolerance"), 1E-5)
        USolver.add(word("relTol"), 0)
    
        pSolver = dictionary()
        pSolver.add(word("preconditioner"), word("DIC"))
        pSolver.add(word("minIter"), 0)
        pSolver.add(word("maxIter"), 1000)
        pSolver.add(word("tolerance"), 1E-6)
        pSolver.add(word("relTol"), 0)
    
        piso = dictionary()
        piso.add(word("nCorrectors"), 2)
        piso.add(word("nNonOrthogonalCorrectors"), 0)
    
        fvSolnDict = dictionary()
        fvSolnDict.add(word("PISO"), piso)
    
        soln = ext_solution( self.run_time, 
                             fileName( "fvSolution" ), 
                             fvSolnDict )
        soln.setWriteOpt( IOobject.AUTO_WRITE )

        soln.addSolver(word("U"), word("PBiCG"), USolver)
        soln.addSolver(word("p"), word("PCG"), pSolver)
    
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
