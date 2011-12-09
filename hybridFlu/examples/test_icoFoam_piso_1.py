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


#--------------------------------------------------------------------------------------
from Foam import ref, man
from salome_version import getVersion as SalomeVersion
if SalomeVersion() > '5.1.4':
    import os
    print "Not supported Salome version. Use Salome 5.1.4 or 5.1.3"
    os._exit( os.EX_OK )
    pass

from Tkinter import *
import Pmw

# Create root and case
import os
root = ref.fileName( os.path.join( os.environ[ "HYBRIDFLU_ROOT_DIR" ], 'hybridFlu', 'examples' ) )
case = ref.fileName( "case_icoFoam_piso" )

# Create time
runTime = man.Time( ref.word("controlDict"), root, case)

# Create mesh
mesh = man.fvMesh( man.IOobject( ref.word("region0"),
                                 ref.fileName(runTime.timeName()),
                                 runTime,
                                 ref.IOobject.MUST_READ,
                                 ref.IOobject.NO_WRITE ) )

# Create transport properties
transportProperties = ref.IOdictionary( ref.IOobject( ref.word("transportProperties"),
                                                      ref.fileName(runTime.constant()),
                                                      mesh, ref.IOobject.MUST_READ,
                                                      ref.IOobject.AUTO_WRITE))

nu = ref.dimensionedScalar( transportProperties.lookup( ref.word( "nu" ) ) )
print nu.value()

nu.setValue(0.05)
transportProperties.remove( ref.word( "nu" ) )
transportProperties.add( ref.word( "nu" ), nu )

# Create pressure field: read
p = man.volScalarField( man.IOobject( ref.word("p"),
                                      ref.fileName(runTime.timeName()),
                                      mesh,
                                      ref.IOobject.MUST_READ,
                                      ref.IOobject.AUTO_WRITE),
                        mesh )

# Create velocity field: read
U = man.volVectorField( man.IOobject( ref.word( "U" ),
                                      ref.fileName(runTime.timeName()),
                                      mesh,
                                      ref.IOobject.MUST_READ,
                                      ref.IOobject.AUTO_WRITE),
                        mesh )

phi = man.createPhi( runTime, mesh, U )

cd = runTime.controlDict()

cd.remove( ref.word( "startTime" ) )
cd.add( ref.word( "startTime" ), 0)
cd.remove(ref.word( "endTime" ) )
cd.add(ref.word( "endTime" ), 0.5 )
cd.remove( ref.word( "deltaT" ) )
cd.add( ref.word( "deltaT" ), 0.005)

runTime.read()

print runTime.timeName()

from icoFlux.embedded import solver as icoFoam
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
