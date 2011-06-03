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
        # Connect to SALOME
        import IFoam.pysalome

        import salome
        aStudyId = salome.myStudy._get_StudyId()

        # Generation of the mesh
        from IFoam.examples import test_create_smesh
        [ aMesh, GroupList ] = test_create_smesh.createMesh()

        # Restoring values for the "root" and OpenFOAM "case" directories
        import os, os.path
        a_path = str( self.run_time.path() )
        a_root_dir, a_case = os.path.split( a_path )

        print_d( "a_root_dir = \"%s\"" % a_root_dir )
        print_d( "a_case = \"%s\"" % a_case )

        import tempfile
        a_tmp_file = tempfile.NamedTemporaryFile()
        an_unv_file_name = a_tmp_file.name
        
        aMesh.ExportUNV( an_unv_file_name )

        if os.environ[ "WM_PROJECT_VERSION" ] < "1.5" :
            os.system( "unv2foam %s %s %s" %( a_root_dir, a_case, an_unv_file_name ))
            pass
        else :
            os.system( "unv2foam %s -case %s" %( an_unv_file_name, a_path ))
            pass

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
    import tempfile, shutil, os
    a_case_dir = tempfile.mkdtemp()

    # To instantiate the solver
    from IFoam.foam2visu import TSalomePostProcessor as TPostProcessor
    a_solver = TIcoFoamSolver( a_case_dir, TPostProcessor )

    # To start the solver execution
    if a_solver.run() :
        shutil.rmtree( a_case_dir )
        os._exit( os.EX_OK )
        pass

    shutil.rmtree( a_case_dir )
    os._exit( os.EX_USAGE )
    pass


#--------------------------------------------------------------------------------------
