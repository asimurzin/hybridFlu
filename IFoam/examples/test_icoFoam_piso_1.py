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

from Tkinter import *
import Pmw

# Create root and case
import os
root = fileName( os.path.join( os.environ[ "IFOAM_ROOT_DIR" ], 'IFoam', 'examples' ) )
case = fileName( "case_icoFoam_piso" )

# Create time
runTime = Time(word("controlDict"), root, case)

# Create mesh
mesh = fvMesh(IOobject(word("region0"),
                       fileName(runTime.timeName()),
                       runTime,
                       IOobject.NO_READ,
                       IOobject.NO_WRITE))

# Create transport properties
transportProperties = IOdictionary(IOobject(word("transportProperties"),
                                            fileName(runTime.constant()),
                                            mesh, IOobject.MUST_READ,
                                            IOobject.AUTO_WRITE))

nu = dimensionedScalar(transportProperties.lookup(word("nu")))
print nu.value()

nu.setValue(0.05)
transportProperties.remove(word("nu"))
transportProperties.add(word("nu"), nu)

# Create pressure field: read
p = volScalarField(IOobject(word("p"),
                            fileName(runTime.timeName()),
                            mesh,
                            IOobject.MUST_READ,
                            IOobject.AUTO_WRITE),
                   mesh)

# Create velocity field: read
U = volVectorField(IOobject(word("U"),
                            fileName(runTime.timeName()),
                            mesh,
                            IOobject.MUST_READ,
                            IOobject.AUTO_WRITE),
                   mesh)

from Foam.finiteVolume.cfdTools.incompressible import createPhi
phi = createPhi( runTime, mesh, U )

cd = runTime.controlDict()

cd.remove(word("startTime"))
cd.add(word("startTime"), 0)
cd.remove(word("endTime"))
cd.add(word("endTime"), 0.5)
cd.remove(word("deltaT"))
cd.add(word("deltaT"), 0.005)

runTime.read()

print runTime.timeName()

from Foam.applications.solvers.incompressible.emb_icoFoam import solver as icoFoam
solver = icoFoam(runTime, U, p, phi, transportProperties)

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
        solver.step()
        runTime.value()
        pRes.append(solver.pressureRes())
        uRes.append(solver.velocityRes())
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


iterate(10)

runTime.writeNow()


#--------------------------------------------------------------------------------------
