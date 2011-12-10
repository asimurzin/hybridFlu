#!/usr/bin/env python

#---------------------------------------------------------------------------
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
## Author : Ivor CLIFFORD
##


#---------------------------------------------------------------------------
"""
Example of how we can create and run an icoFoam case from scratch
No pre-existing case files are required
"""

from salome_version import getVersion as SalomeVersion
if SalomeVersion() > '5.1.4':
    import os
    print "Not supported Salome version. Use Salome 5.1.4 or 5.1.3"
    os._exit( os.EX_OK )
    pass


from Foam import man, ref 

from Tkinter import *
import Pmw

# Helper function
# Convert a python string array to ITstream
def createITstream(pyList):
    size = len(pyList)
    ret = ref.tokenList(size)
    for i in xrange(size):
        ret[i] = ref.token(ref.word(pyList[i]))
        pass
    
    stream = ref.ITstream( ref.word( "dummy"), ret )
    return stream

# Convert a python string array to wordList
def pyWordList(pyList):
    size = len(pyList)
    ret = ref.wordList(size)
    for i in xrange(size):
        ret[i] = ref.word(pyList[i])
    return ret

# Create fvSchemes dictionary
def createFvSchemesDict(runTime):
    fvSchemesDict = ref.IOdictionary( ref.IOobject(ref.word("fvSchemes"),
                                      runTime.caseSystem(),
                                      runTime,
                                      ref.IOobject.NO_READ,
                                      ref.IOobject.AUTO_WRITE))
    
    
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


# Create fvSolution dictionary
def createFvSolution(runTime):
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
    
    soln=ref.ext_solution(runTime, ref.fileName("fvSolution"), fvSolnDict)
    soln.setWriteOpt(ref.IOobject.AUTO_WRITE)
    soln.addSolver(ref.word("U"), ref.word("PBiCG"), USolver)
    soln.addSolver(ref.word("p"), ref.word("PCG"), pSolver)
    
    return soln


# Create fvMesh
def createFvMesh(runTime):
    # Read temporary mesh from file - done only so we can get the list of points, faces and cells
    tmpMesh = man.fvMesh( man.IOobject( ref.word("tmp"),
                                        runTime.caseConstant(),
                                        runTime,
                                        ref.IOobject.NO_READ,
                                        ref.IOobject.NO_WRITE))
    
    # Get points, faces & Cells - SFOAM implementation should populate these lists from Salome mesh
    points = tmpMesh.points()
    faces = tmpMesh.faces()
    cells = tmpMesh.cells()
    
    #  Now create the mesh - Nothing read from file, although fvSchemes and fvSolution created above must be present
    #  It is necessary to store tmpMesh, because fvMesh::points(), faces(), and cells() return const T&
    #  and fvMesh in next line will be broken, after exiting from this function (tmpMesh are deleted) 
    mesh = man.fvMesh( ref.fvMesh( ref.IOobject( ref.word("region0"),
                                                 runTime.caseConstant(),
                                                 runTime,
                                                 ref.IOobject.MUST_READ,
                                                 ref.IOobject.AUTO_WRITE ),
                                   points, faces, cells ),
                       man.Deps( tmpMesh ) )
    
    # Create boundary patches
    patches = ref.polyPatchListPtr( 4, ref.polyPatch.nullPtr() )
    patches.set(0, ref.polyPatch.New(
                    ref.word("patch"),
                    ref.word("inlet_F"),
                    606,
                    102308,
                    0,
                    mesh.boundaryMesh()
                    ))
    
    patches.set(1, ref.polyPatch.New(
                    ref.word("patch"),
                    ref.word("outlet_F1"),
                    818,
                    102914,
                    1,
                    mesh.boundaryMesh()
                    ))
    
    patches.set(2, ref.polyPatch.New(
                    ref.word("patch"),
                    ref.word("outlet_F2"),
                    522,
                    103732,
                    2,
                    mesh.boundaryMesh()
                    ))
    
    patches.set(3, ref.polyPatch.New(
                    ref.word("wall"),
                    ref.word("pipe"),
                    5842,
                    104254,
                    3,
                    mesh.boundaryMesh()
                    ))
    
    mesh.addFvPatches(patches)
    
    return mesh, patches

def _createControlDict() :
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

# Create root and case
import os
from Foam import ref
root = ref.fileName( os.path.join( os.environ[ "HYBRIDFLU_ROOT_DIR" ], 'hybridFlu', 'examples' ) )
case = ref.fileName( "case_icoFoam_scratch" )


# Create time - without reading controlDict from file
# Note - controlDict not written to file using this method
runTime = man.Time( _createControlDict(), root, case )

# Create transport properties
transportProperties = ref.IOdictionary(ref.IOobject(ref.word("transportProperties"),
                                            runTime.caseConstant(),
                                            runTime,
                                            ref.IOobject.NO_READ,
                                            ref.IOobject.NO_WRITE))

nu = ref.dimensionedScalar(ref.word("nu"),ref.dimensionSet( 0.0, 2.0, -1.0, 0.0, 0.0, 0.0, 0.0), 1e-6)
transportProperties.add(ref.word("nu"), nu);


# Create fvSchemes and fvSolution dictionaries
fvSchemesDict = createFvSchemesDict(runTime);
fvSoln = createFvSolution(runTime);

# Write all dictionaries to file
# Note, we currently need fvSchemes and fvSolution to reside in the case directory
# since it is used during the solution... so we now write them to file
runTime.writeNow()

# Clean up unused variables
fvSchemesDict = 0
fvSoln = 0

# Create mesh
mesh, patches = createFvMesh(runTime)
mesh.write()

# Create pressure field
pPatchTypes = pyWordList(['zeroGradient', 'fixedValue', 'fixedValue', 'zeroGradient'])

p = man.volScalarField( man.IOobject( ref.word("p"),
                                      ref.fileName(runTime.timeName()),
                                      mesh,
                                      ref.IOobject.NO_READ,
                                      ref.IOobject.AUTO_WRITE),
                        mesh,
                        ref.dimensionedScalar( ref.word(), ref.dimensionSet( 0.0, 2.0, -2.0, 0.0, 0.0, 0.0, 0.0 ), 101.325),
                        pPatchTypes )

p.ext_boundaryField()[1] << 101.325
p.ext_boundaryField()[2] << 101.325

# Create velocity field
UPatchTypes = pyWordList(['fixedValue', 'zeroGradient', 'zeroGradient', 'fixedValue'])

U = man.volVectorField( man.IOobject( ref.word("U"),
                                      ref.fileName(runTime.timeName()),
                                      mesh,
                                      ref.IOobject.NO_READ,
                                      ref.IOobject.AUTO_WRITE),
                       mesh,
                       ref.dimensionedVector( ref.word(), ref.dimensionSet( 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0 ), ref.vector( 0.0, 0.0, 0.0 ) ),
                       UPatchTypes )

U.ext_boundaryField()[0] << ref.vector( 0.0, 0.1, 0.0 )
U.ext_boundaryField()[3] << ref.vector( 0.0, 0.0, 0.0 )

phi = man.createPhi( runTime, mesh, U )

# Write all dictionaries to file
runTime.writeNow()

# Create solver
from icoFlux.embedded import solver as icoFoam
icoSolver = icoFoam(runTime, U, p, phi, transportProperties)


pRes = [] #initial pressure residual
uRes = [] #initial velocity residual
it   = []
iteration = []
iteration.append(0)

# Graphics related stuff
master = Tk()
g = Pmw.Blt.Graph(master)
g.pack(expand=1,fill='both')


# Graph related commands:
g.line_create("p-Residual", xdata=iteration[0], ydata=None)
g.element_configure("p-Residual", color = "red", dashes = 1,
                    symbol = "", linewidth = 1)
g.line_create("u-Residual", xdata=iteration[0], ydata=None)
g.element_configure("u-Residual", color = "blue", dashes = 1,
                    symbol = "", linewidth = 1)
g.axis_configure("y",logscale = 1)


# Main iterate function
def iterate(niter):
    for i in xrange(niter):
        i += iteration[0]
        it.append(i)
        icoSolver.step()
        runTime.value()
        pRes.append(icoSolver.pressureRes())
        uRes.append(icoSolver.velocityRes())
        pResTpl = tuple(pRes)
        uResTpl = tuple(uRes)
        
        # Update residual plot
        g.axis_configure("y",logscale = 1)
        g.element_configure("p-Residual", xdata=tuple(it), ydata = pResTpl,
                            color = "red", dashes = 0,
                           symbol = "", linewidth = 1)
        g.element_configure("u-Residual", xdata=tuple(it), ydata = uResTpl,
                            color = "blue", dashes = 0,
                           symbol = "", linewidth = 1)
        master.update_idletasks()
    iteration[0] += niter

iterate(50)

runTime.writeNow()
