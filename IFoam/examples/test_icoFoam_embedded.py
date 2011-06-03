#!/usr/bin/env python

#---------------------------------------------------------------------------
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
## Author : Ivor CLIFFORD
##


#--------------------------------------------------------------------------------------

from Foam.OpenFOAM import *
from Foam.finiteVolume import *

# Helper function
def pyTokenList(pyList):
    size = len(pyList)
    ret = tokenList(size)
    for i in xrange(size):
        ret[i] = token(word(pyList[i]))
    return ret

def pyWordList(pyList):
    size = len(pyList)
    ret = wordList(size)
    for i in xrange(size):
        ret[i] = word(pyList[i])
    return ret

# Create fvSchemes dictionary
def createFvSchemesDict(runTime):
    # Create schemes dictionary
    fvSchemesDict = IOdictionary(IOobject(word("fvSchemes"),
                            runTime.caseSystem(),
                            runTime,
                            IOobject.NO_READ,
                            IOobject.AUTO_WRITE))
    
    
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


# Create fvSolution dictionary
# Currently not fully functional, format of "solvers" entries currently
#   can't be written to file unless using stream objects. We need a
#   workaround for this.
def createFvSolution(runTime):
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
    
    soln=ext_solution(runTime, fileName("fvSolution"), fvSolnDict)
    soln.setWriteOpt(IOobject.AUTO_WRITE)
    soln.addSolver(word("U"), word("PBiCG"), USolver)
    soln.addSolver(word("p"), word("PCG"), pSolver)
    
    return soln


# Create fvMesh
def createFvMesh(runTime):
    # Read temporary mesh from file - done only so we can get the list of points, faces and cells
    tmpMesh = fvMesh(IOobject(word("tmp"),
                        runTime.caseConstant(),
                        runTime,
                        IOobject.NO_READ,
                        IOobject.NO_WRITE))
    
    # Get points, faces & Cells - SFOAM implementation should populate these lists from Salome mesh
    points = tmpMesh.points()
    faces = tmpMesh.faces()
    cells = tmpMesh.cells()
    
    #  Now create the mesh - Nothing read from file, although fvSchemes and fvSolution created above must be present
    mesh = fvMesh(IOobject(word("region0"),
                        runTime.caseConstant(),
                        runTime,
                        IOobject.NO_READ,
                        IOobject.AUTO_WRITE),
                points,
                faces,
                cells
                )
    
    # Create boundary patches
    patches = pPolyPatchList(4, polyPatch.nullPtr())
    patches.set(0, polyPatch.New(
                    word("patch"),
                    word("inlet_F"),
                    606,
                    102308,
                    0,
                    mesh.boundaryMesh()
                    ))
    
    patches.set(1, polyPatch.New(
                    word("patch"),
                    word("outlet_F1"),
                    818,
                    102914,
                    1,
                    mesh.boundaryMesh()
                    ))
    
    patches.set(2, polyPatch.New(
                    word("patch"),
                    word("outlet_F2"),
                    522,
                    103732,
                    2,
                    mesh.boundaryMesh()
                    ))
    
    patches.set(3, polyPatch.New(
                    word("wall"),
                    word("pipe"),
                    5842,
                    104254,
                    3,
                    mesh.boundaryMesh()
                    ))
    
    mesh.addFvPatches(patches)
    
    return mesh, patches


# Create root and case
import os
root = fileName( os.path.join( os.environ[ "IFOAM_ROOT_DIR" ], 'IFoam', 'examples' ) )
case = fileName( "case_icoFoam_embedded" )


# Create time - without reading controlDict from file
# Note - controlDict not written to file using this method
runTime = Time(root, case)
runTime.setTime(0.0, 0)
runTime.setDeltaT(0.001)
runTime.setEndTime(0.05)


# Create transport properties
transportProperties = IOdictionary(IOobject(word("transportProperties"),
                                            runTime.caseConstant(),
                                            runTime,
                                            IOobject.NO_READ,
                                            IOobject.NO_WRITE))

nu = dimensionedScalar(word("nu"), dimensionSet(0, 2, -1, 0, 0, 0, 0), 1e-6)
transportProperties.add(word("nu"), nu);


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
# mesh.write()

# Create pressure field
pPatchTypes = pyWordList(['zeroGradient', 'fixedValue', 'fixedValue', 'zeroGradient'])

p = volScalarField(IOobject(word("p"),
                            fileName(runTime.timeName()),
                            mesh,
                            IOobject.NO_READ,
                            IOobject.AUTO_WRITE),
                   mesh,
                   dimensionedScalar(word(), dimensionSet(0, 2, -2, 0, 0, 0, 0), 101.325),
                   pPatchTypes
                   )

p.ext_boundaryField()[1].ext_assign( 101.325 )
p.ext_boundaryField()[2].ext_assign( 101.325 )

# Create velocity field
UPatchTypes = pyWordList(['fixedValue', 'zeroGradient', 'zeroGradient', 'fixedValue'])

U = volVectorField(IOobject(word("U"),
                            fileName(runTime.timeName()),
                            mesh,
                            IOobject.NO_READ,
                            IOobject.AUTO_WRITE),
                   mesh,
                   dimensionedVector(word(), dimensionSet(0, 1, -1, 0, 0, 0, 0), vector(0,0,0)),
                   UPatchTypes
                   )

U.ext_boundaryField()[0].ext_assign( vector(0, 0.1, 0) )
U.ext_boundaryField()[3].ext_assign( vector(0, 0.0, 0) )

from Foam.finiteVolume.cfdTools.incompressible import createPhi
phi = createPhi( runTime, mesh, U )

# Write all dictionaries to file
runTime.writeNow()

from Foam.applications.solvers.incompressible.emb_icoFoam import solver as icoFoam
icoSolver = icoFoam(runTime, U, p, phi, transportProperties)

pRes = [] #initial pressure residual
uRes = [] #initial velocity residual
it   = []
iteration = []
iteration.append(0)


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
    iteration[0] += niter

print "NOTE - The fvSolution dictionary must be manually edited before calling iterate"
print "       See comments for createFvSolutionDict"
iterate(50)

#runTime.writeNow()
