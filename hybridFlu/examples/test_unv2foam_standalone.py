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
## Author : Alexey PETROV
##


#--------------------------------------------------------------------------------------
from Foam.finiteVolume import *


#--------------------------------------------------------------------------------------
if __name__ == "__main__" :
    import os
    from Foam import FOAM_VERSION
    
    argv = None
    if FOAM_VERSION( "<", "010500" ) :
        a_dir = os.path.join( os.environ[ "IFOAM_ROOT_DIR" ], 'hybridFlu', 'examples' )
        argv = [ __file__, a_dir, 'case_unv2foam' ]
    else:
        a_dir = os.path.join( os.environ[ "IFOAM_ROOT_DIR" ], 'hybridFlu', 'examples', 'case_unv2foam' )
        argv = [ __file__, '-case', a_dir ]
        pass
    
    from Foam.OpenFOAM.include import setRootCase
    args = setRootCase( len( argv ), argv )

    from Foam.OpenFOAM.include import createTime
    runTime = createTime( args )

    a_path = str( runTime.path() )
    a_root_dir, a_case = os.path.split( a_path )
    an_unv_file_name = os.path.join( a_path, "mesh" + os.path.extsep + "unv" )
    
    if FOAM_VERSION( "<", "010500" ) :
        os.system( "unv2foam %s %s %s" %( a_root_dir, a_case, an_unv_file_name ))
        pass
    else :
        os.system( "unv2foam %s -case %s" %( an_unv_file_name, a_path ))
        pass
    
    from Foam.OpenFOAM.include import createMesh
    mesh = createMesh( runTime )

    print "OK"
    os._exit( os.EX_OK )
    
    pass


#--------------------------------------------------------------------------------------
