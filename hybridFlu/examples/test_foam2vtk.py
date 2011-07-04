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
def main_standalone( argc, argv ):
    from Foam.OpenFOAM.include import setRootCase
    args = setRootCase( argc, argv )

    from Foam.OpenFOAM.include import createTime
    runTime = createTime( args )

    from Foam.OpenFOAM.include import createMesh
    mesh = createMesh( runTime )

    # Read pressure field
    from Foam.OpenFOAM import IOobject, word, fileName
    from Foam.finiteVolume import volScalarField
    p = volScalarField( IOobject( word( "p" ),
                                  fileName( runTime.timeName() ),
                                  mesh,
                                  IOobject.MUST_READ,
                                  IOobject.NO_WRITE ),
                        mesh )
    
    # Read velocity field
    from Foam.OpenFOAM import IOobject, word, fileName
    from Foam.finiteVolume import volVectorField
    U = volVectorField( IOobject( word( "U" ),
                                  fileName( runTime.timeName() ),
                                  mesh,
                                  IOobject.MUST_READ,
                                  IOobject.NO_WRITE ),
                        mesh )

    from hybridFlu.vtkPlotter import field_plotter
    pPlot = field_plotter( p )

    tmp = U.mag()
    UPlot = field_plotter( tmp() )

    import os
    return os.EX_OK


#--------------------------------------------------------------------------------------
if __name__ == "__main__" :
    import os
    argv = None
    
    from salome_version import getVersion as SalomeVersion
    if SalomeVersion() > '5.1.4':
       import os
       print "Not supported Salome version. Use Salome 5.1.4 or 5.1.3"
       os._exit( os.EX_OK )
       pass
    
    from Foam import FOAM_VERSION
    if FOAM_VERSION( "<=", "010400" ):
        a_dir = os.path.join( os.environ[ "HYBRIDFLU_ROOT_DIR" ], 'hybridFlu', 'examples' )
        argv = [ __file__, a_dir, 'case_foam2vtk' ]
    else:
        a_dir = os.path.join( os.environ[ "HYBRIDFLU_ROOT_DIR" ], 'hybridFlu', 'examples', 'case_foam2vtk' )
        argv = [ __file__, '-case', a_dir ]
        pass
    
    try:
        os._exit( main_standalone( len( argv ), argv ) )
    except Exception:
        import sys, traceback
        traceback.print_exc( file = sys.stdout )
        pass
    pass

    
#--------------------------------------------------------------------------------------
