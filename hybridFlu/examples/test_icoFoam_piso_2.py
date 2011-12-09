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
Example icoFoam PISO algorithm
"""

from salome_version import getVersion as SalomeVersion
if SalomeVersion() > '5.1.4':
    import os
    print "Not supported Salome version. Use Salome 5.1.4 or 5.1.3"
    os._exit( os.EX_OK )
    pass

from Foam import ref, man

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
        
        runTime_.increment()
        
        # Read transport properties
        nu = ref.dimensionedScalar(self.transportProperties.lookup(ref.word("nu")))

        tmp_UEqn = ( ref.fvm.ddt( U_ ) + ref.fvm.div( phi_, U_ ) - ref.fvm.laplacian( nu, U_ ) )
        UEqn = tmp_UEqn()
        
        self.velocityRes = ref.solve( UEqn == -ref.fvc.grad( p_ ) ).initialResidual()
        
        # --- PISO loop
        for corr in range(nCorr):
            tmp_rUA = 1.0 / UEqn.A()
            rUA = tmp_rUA()
            
            U_ << rUA * UEqn.H()
            
            phi_ << ( ref.fvc.interpolate(U_) & mesh_.Sf() )
            
            for nonOrth in range(nNonOrthCorr):
                tmp_pEqn = ( ref.fvm.laplacian( rUA, p_ ) == ref.fvc.div( phi_ ) )
                pEqn = tmp_pEqn()
                
                pEqn.setReference( self.pRefCell, self.pRefValue )
                pressureRes = pEqn.solve().initialResidual()
                
                if nonOrth == 0:
                    self.pressureRes = pressureRes
                
                if nonOrth == nNonOrthCorr:
                    phi_ -= pEqn.flux()
            
            # Continuity errors
            tmp_contErr = ref.fvc.div( phi_ );
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
            U_-= rUA * ref.fvc.grad( p_ )
            U_.correctBoundaryConditions()


# Create root and case
import os
root = ref.fileName( os.path.join( os.environ[ "HYBRIDFLU_ROOT_DIR" ], 'hybridFlu', 'examples' ) )
case = ref.fileName( "case_icoFoam_piso" )

# Create time
runTime = man.Time(ref.word("controlDict"), root, case)

runTime.controlDict().remove(ref.word("startTime"))
runTime.controlDict().remove(ref.word("endTime"))
runTime.controlDict().remove(ref.word("deltaT"))
runTime.controlDict().add(ref.word("startTime"), 0)
runTime.controlDict().add(ref.word("endTime"), 0.5)
runTime.controlDict().add(ref.word("deltaT"), 0.005)

runTime.read()

# Create mesh
mesh = man.fvMesh( man.IOobject( ref.word("region0"),
                                 ref.fileName(runTime.timeName()),
                                 runTime,
                                 ref.IOobject.MUST_READ,
                                 ref.IOobject.NO_WRITE))

# Create transport properties
transportProperties = ref.IOdictionary(ref.IOobject( ref.word("transportProperties"),
                                                     ref.fileName(runTime.constant()),
                                                     mesh,
                                                     ref.IOobject.MUST_READ,
                                                     ref.IOobject.AUTO_WRITE))

nu = ref.dimensionedScalar(transportProperties.lookup(ref.word("nu")))
nu.setValue(0.05)

# Create pressure field: read
p = man.volScalarField( man.IOobject( ref.word("p"),
                                      ref.fileName(runTime.timeName()),
                                      mesh,
                                      ref.IOobject.MUST_READ,
                                      ref.IOobject.AUTO_WRITE ),
                        mesh )

# Create velocity field: read
U = man.volVectorField( man.IOobject( ref.word("U"),
                                      ref.fileName(runTime.timeName()),
                                      mesh,
                                      ref.IOobject.MUST_READ,
                                      ref.IOobject.AUTO_WRITE ),
                        mesh)

phi = ref.createPhi( runTime, mesh, U )

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
