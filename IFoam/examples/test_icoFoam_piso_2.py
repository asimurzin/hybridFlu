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


#---------------------------------------------------------------------------
"""
Example icoFoam PISO algorithm
"""

from Foam.OpenFOAM import *
from Foam.finiteVolume import *
from Foam import fvm, fvc

from Tkinter import *
import Pmw

class pyIcoFoam:
    def __init__(self, runTime, U, p, phi, transportProperties, pRefCell=0, pRefValue=0.0):
        self.runTime = runTime
        self.U = U
        self.p = p
        self.phi = phi
        self.transportProperties = transportProperties
        self.pRefCell=pRefCell
        self.pRefValue=pRefValue
        self.pressureRes = 0.0
        self.velocityRes = 0.0
    
    def step(self, nCorr=1, nNonOrthCorr=1):
        U_ = self.U
        p_ = self.p
        phi_ = self.phi
        runTime_ = self.runTime
        mesh_ = U_.mesh()
        
        runTime_.step()
        
        # Read transport properties
        nu = dimensionedScalar(self.transportProperties.lookup(word("nu")))

        tmp_UEqn = ( fvm.ddt( U_ ) + fvm.div( phi_, U_ ) - fvm.laplacian( nu, U_ ) )
        UEqn = tmp_UEqn()
        
        self.velocityRes = solve( UEqn == -fvc.grad( p_ ) ).initialResidual()
        
        # --- PISO loop
        for corr in range(nCorr):
            tmp_rUA = 1.0 / UEqn.A()
            rUA = tmp_rUA()
            
            U_.ext_assign( rUA * UEqn.H() )
            
            phi_.ext_assign( fvc.interpolate(U_) & mesh_.Sf() )
            
            for nonOrth in range(nNonOrthCorr):
                tmp_pEqn = ( fvm.laplacian( rUA, p_ ) == fvc.div( phi_ ) )
                pEqn = tmp_pEqn()
                
                pEqn.setReference( self.pRefCell, self.pRefValue )
                pressureRes = pEqn.solve().initialResidual()
                
                if nonOrth == 0:
                    self.pressureRes = pressureRes
                
                if nonOrth == nNonOrthCorr:
                    phi_.ext_assign( phi_ - pEqn.flux() )
            
            # Continuity errors
            tmp_contErr = fvc.div( phi_ );
            contErr = tmp_contErr()

            sumLocalContErr = (
                runTime_.deltaT().value()
                * contErr.mag().weightedAverage( mesh_.V() ).value()
            )

            globalContErr = (
                runTime_.deltaT().value()
                * contErr.weightedAverage( mesh_.V() ).value()
            )
            
            print "time step continuity errors : sum local = " + str(sumLocalContErr) + ", global = " + str(globalContErr)
            
            # Correct velocity
            U_.ext_assign( U_ - rUA * fvc.grad( p_ ) )
            U_.correctBoundaryConditions()


# Create root and case
import os
root = fileName( os.path.join( os.environ[ "IFOAM_ROOT_DIR" ], 'IFoam', 'examples' ) )
case = fileName( "case_icoFoam_piso" )

# Create time
runTime = Time(word("controlDict"), root, case)

runTime.controlDict().remove(word("startTime"))
runTime.controlDict().remove(word("endTime"))
runTime.controlDict().remove(word("deltaT"))
runTime.controlDict().add(word("startTime"), 0)
runTime.controlDict().add(word("endTime"), 0.5)
runTime.controlDict().add(word("deltaT"), 0.005)

runTime.read()

# Create mesh
mesh = fvMesh(IOobject(word("region0"),
                       fileName(runTime.timeName()),
                       runTime,
                       IOobject.NO_READ,
                       IOobject.NO_WRITE))

# Create transport properties
transportProperties = IOdictionary(IOobject(word("transportProperties"),
                                            fileName(runTime.constant()),
                                            mesh,
                                            IOobject.MUST_READ,
                                            IOobject.AUTO_WRITE))

nu = dimensionedScalar(transportProperties.lookup(word("nu")))
nu.setValue(0.05)

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

print "Time: " + str(runTime.timeName())

solver = pyIcoFoam(runTime, U, p, phi, transportProperties, 0, 0.0)


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
        solver.step(2,1)
        runTime.value()
        pRes.append(solver.pressureRes)
        uRes.append(solver.velocityRes)
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
