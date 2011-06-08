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
This utility provides functionality to export OpenFOAM data to SALOME VISU module. 
To obtain more detail information on this account it is possible to
run this script with '--help' command line option.
"""

#--------------------------------------------------------------------------------------
from foam2med import TFilePostProcessor
from foam2med import print_d
 

#--------------------------------------------------------------------------------------
class TDummyPostProcessor :
    """
    This class defines an abstract interface for the post processing
    """
    def __init__( self, the_case_dir, the_output_mesh_name = None ) :
        print_d( "the_case_dir = \"%s\", the_output_mesh_name = \"%s\"" % 
                 ( the_case_dir, the_output_mesh_name ) )
        pass

    def process( self, the_foam_time = None, the_output_med_file = None ) :
        print_d( "the_foam_time = \"%s\", the_output_med_file = \"%s\"" % 
                 ( the_foam_time, the_output_med_file ) )
        return True

    pass


#--------------------------------------------------------------------------------------
class TSalomePostProcessor( TDummyPostProcessor, TFilePostProcessor ) :
    """
    This class provides SALOME VISU post processing capabilties
    """
    def __init__( self, the_case_dir = None, the_output_mesh_name = None ) :
        """
        Constructs instance of this class
        """
        # Construct the base class first
        TFilePostProcessor.__init__( self )
        
        self.output_mesh_name = the_output_mesh_name
        self.case_dir = the_case_dir
        pass

    def process( self, the_foam_time = None, the_output_med_file = None ) :
        """
        Runs the main functionality
        """
        an_is_ok = self.run( self.case_dir, 
                             the_output_med_file, 
                             self.output_mesh_name, 
                             the_foam_time )
        return an_is_ok

    def run( self, the_case_dir, the_output_med_file, the_output_mesh_name, the_foam_time ) :
        """
        Runs the main functionality
        """
        an_is_ok = TFilePostProcessor.run( self, 
                                           the_case_dir,
                                           the_output_med_file,
                                           the_output_mesh_name, 
                                           the_foam_time )
        if not an_is_ok :
            return False
        
        # Connect to SALOME
        import pysalome, VISU, visu
        from batchmode_salome import orb, naming_service, lcc, myStudyManager, myStudy

        aVisuGen = visu.Initialize( orb, naming_service, lcc, myStudyManager, myStudy, 0 )

        an_output_med_file = self.get_output_med_file()
        print_d( "an_output_med_file = \"%s\"" % an_output_med_file )

        aResult = aVisuGen.CopyAndImportFile( an_output_med_file )

        a_mesh_name = self.get_output_mesh_name()
        print_d( "a_mesh_name = \"%s\"" % a_mesh_name )

        aScalarMap = aVisuGen.ScalarMapOnField( aResult, a_mesh_name, VISU.NODE, 'Point U', 1 )
        aScalarMap.SetBarOrientation( VISU.ColoredPrs3d.HORIZONTAL )
        aScalarMap.SetPosition( 0.05, 0.01 )
        aScalarMap.SetSize( 0.90, 0.15 )
        aScalarMap.SetNbColors( 64 )
        aScalarMap.SetLabels( 5 )
        
        aViewManager = aVisuGen.GetViewManager()
        aView3D = aViewManager.Create3DView()
        aView3D.Display( aScalarMap );
        aView3D.FitAll()
        
        return True

    pass


#--------------------------------------------------------------------------------------
# This piece of code will be perfomed only in case of invoking this script directly from shell
if __name__ == '__main__' :
    import os

    if TSalomePostProcessor().process_args() == True :
        os._exit( os.EX_OK )
        pass

    os._exit( os.EX_USAGE )
    pass


#--------------------------------------------------------------------------------------
