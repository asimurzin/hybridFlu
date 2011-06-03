#!/usr/bin/env python

#--------------------------------------------------------------------------------------
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

"""
This utility provides functionality to convert OpenFOAM data the MED format. 
To obtain more detail information on this account it is possible to
run this script with '--help' command line option.
"""

#--------------------------------------------------------------------------------------
def execute( the_smesh_mesh, the_foam_time ):
    """
    This function defines procedure like Python API for this utility
    """
    import os, os.path   

    import tempfile
    a_tmp_file = tempfile.NamedTemporaryFile()
    a_tmp_file_name = a_tmp_file.name

    the_smesh_mesh.ExportUNV( a_tmp_file_name )

    from Foam.applications.utilities.mesh.conversion.unv2foam import unv2foam
    from Foam.finiteVolume import fileName
    
    return unv2foam( fileName( a_tmp_file_name), the_foam_time )



#--------------------------------------------------------------------------------------
# This piece of code will be perfomed only in case of invoking this script directly from shell
if __name__ == '__main__' :
    import os

    an_usage = \
    """
    %prog \\
          --unv-file=./cavity.unv \\
          --case-dir=${WM_PROJECT_USER_DIR}/run/tutorials/icoFoam/cavity
    """

    from optparse import IndentedHelpFormatter
    a_help_formatter = IndentedHelpFormatter( width = 127 )
    
    from optparse import OptionParser
    a_parser = OptionParser( usage = an_usage, version="%prog 0.1", formatter = a_help_formatter )
    
    # Definition of the command line arguments
    a_parser.add_option( "--case-dir",
                         metavar = "< OpenFOAM case directory >",
                         action = "store",
                         dest = "case_dir",
                         help = "location of OpenFOAM case directory" +
                         " (\"%default\", by default)",
                         default = "." )

    an_options, an_args = a_parser.parse_args() 

    # Connect to SALOME
    import pysalome
    
    import salome
    aStudyId = salome.myStudy._get_StudyId()
    
    # Generation of the mesh
    import test_icoFoam_mesh
    [ aMesh, GroupList ] = test_icoFoam_mesh.createMesh()

    # Create corresponding Foam.Time object
    import os
    a_case_dir = os.path.realpath( an_options.case_dir )
    a_root_dir, a_case = os.path.split( a_case_dir )

    from Foam.finiteVolume import fileName, Time
    a_Time = Time( fileName( a_root_dir ), fileName( a_case ) )

    # Calling the core functionality
    an_ext_autoPtr_fvMesh = execute( aMesh, a_Time )

    # Writing the produced Foam.fvMesh on disk
    a_fvMesh = an_ext_autoPtr_fvMesh()
    a_fvMesh.write()
    
    os._exit( os.EX_OK )

    pass


#--------------------------------------------------------------------------------------
