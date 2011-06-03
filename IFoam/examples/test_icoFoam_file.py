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
from IFoam.examples.test_icoFoam_base import *


#--------------------------------------------------------------------------------------
class TIcoFoamSolver( TIcoFoamSolverBase ) :
    """
    Implementation of the file based createFvMesh version of TIcoFoamSolverBase
    """
    def __init__( self, the_case_dir, the_post_processor = None ) :
        """
        Constructs instance of this class
        """
        TIcoFoamSolverBase.__init__( self, the_case_dir, the_post_processor )
        pass


    #--------------------------------------------------------------------------------------
    def _createFvMesh( self ) :
        """
        Creates fvMesh
        """
        # Read temporary mesh from file - done only so we can get the list of points, faces and cells
        a_fvMesh = fvMesh( IOobject( word( "" ),
                                    self.run_time.caseConstant(),
                                    self.run_time,
                                    IOobject.NO_READ,
                                    IOobject.NO_WRITE ) )
    
        return a_fvMesh, None

    pass


#--------------------------------------------------------------------------------------
if __name__ == "__main__" :    
    # To define the solver parameters
    import os, os.path
    a_case_dir = os.path.join( os.environ[ "IFOAM_ROOT_DIR" ], 'IFoam', 'examples', "case_icoFoam" )

    # To instantiate the solver
    from IFoam.foam2visu import TSalomePostProcessor as TPostProcessor
    a_solver = TIcoFoamSolver( a_case_dir, TPostProcessor )

    # To start the solver execution
    if a_solver.run() :
        os._exit( os.EX_OK )
        pass

    os._exit( os.EX_USAGE )
    pass


#--------------------------------------------------------------------------------------
