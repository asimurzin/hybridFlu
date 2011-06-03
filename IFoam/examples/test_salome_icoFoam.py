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
        from examples import test_create_smesh
        [aMesh, GroupList] = test_create_smesh.createMesh()

        # load foam engine
        import FOAM
        from batchmode_salome import lcc
        aFOAM = lcc.FindOrLoadComponent("FactoryServer", "FOAM")

        aFOAM.OpenTransaction(aStudyId)

        # Restoring values for the "root" and OpenFOAM "case" directories
        import os, os.path   
        a_root_dir, a_case = os.path.split( str( self.run_time.path() ) )
        a_root_dir, a_solver = os.path.split( str( a_root_dir ) )

        import tempfile
        a_root_dir = tempfile.mkdtemp()

        print_d( "a_root_dir = \"%s\"" % a_root_dir )
        print_d( "a_solver = \"%s\"" % a_solver )
        print_d( "a_case = \"%s\"" % a_case )

        # It is necessary to create a solver instance (it does not matter what)
        icoFoam = aFOAM.AddSolver( aStudyId, FOAM.ST_Ico )
        icoFoam.SetName( a_solver )

        # It is necessary to create a case instance (it does not matter what)
        aCase = icoFoam.AddCase( a_case )
        #aCase.GenerateDictionaries()

        # set MESH
        aCase.SetMesh( aMesh.GetMesh(), False )

        # add boundary condition foam_inlet_F
        foam_inlet_F = aCase.AddBndCondition()
        foam_inlet_F.SetName( "inlet_F" )
        foam_inlet_F.SetBaseType( FOAM.BASETYPE_PATCH )
        foam_inlet_F.SetPhysicalType( FOAM.PHTYPE_INLET )
        foam_inlet_F.SetGroup( GroupList[ 0 ] )

        # add boundary condition foam_outlet_F1
        foam_outlet_F1 = aCase.AddBndCondition()
        foam_outlet_F1.SetName( "outlet_F1" )
        foam_outlet_F1.SetBaseType( FOAM.BASETYPE_PATCH )
        foam_outlet_F1.SetPhysicalType( FOAM.PHTYPE_OUTLET )
        foam_outlet_F1.SetGroup( GroupList[ 1 ] )

        # add boundary condition foam_outlet_F2
        foam_outlet_F2 = aCase.AddBndCondition()
        foam_outlet_F2.SetName( "outlet_F2" )
        foam_outlet_F2.SetBaseType( FOAM.BASETYPE_PATCH )
        foam_outlet_F2.SetPhysicalType( FOAM.PHTYPE_OUTLET )
        foam_outlet_F2.SetGroup( GroupList[ 2 ] )

        # add boundary condition foam_pipe
        foam_pipe = aCase.AddBndCondition()
        foam_pipe.SetName( "pipe" )
        foam_pipe.SetBaseType( FOAM.BASETYPE_WALL )
        foam_pipe.SetGroup( GroupList[ 3 ] )

        # ============
        # publish case
        aFOAM.PublishCase( salome.myStudy, aCase, aMesh.GetMesh(), GroupList )
        aFOAM.CommitTransaction( aStudyId )

        salome.sg.updateObjBrowser( 1 )
        # ============

        # creates case folder with all corresponding dictionaries 
        aFOAM.CreateCaseFolder( aCase, a_root_dir )

        # extracts only "constant" file structure 
        import shutil, os, os.path

        a_source = os.path.join( a_root_dir, a_solver, a_case )

        # removes the temporal "system" file structure 
        shutil.rmtree( os.path.join( a_source, str( self.run_time.caseSystem() ) ) )

        a_source = os.path.join( a_source, str( self.run_time.caseConstant() ) )
        print_d( "a_source = \"%s\"" % a_source )

        a_path = str( self.run_time.path() )
        a_destination = os.path.join( a_path, str( self.run_time.caseConstant() ) )
        print_d( "a_destination = \"%s\"" % a_destination )

        # moves the "constant" file structure to the proper location
        if os.path.exists( a_destination ) :
            shutil.rmtree( a_destination )
            pass
        shutil.copytree( a_source, a_destination )
        #shutil.move( a_source, a_destination )

        # removes the root of the temporal file structure
        shutil.rmtree( a_root_dir )

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
    import tempfile, shutil, os
    a_case_dir = tempfile.mkdtemp()

    # To instantiate the solver
    a_solver = TIcoFoamSolver( a_case_dir )

    # To start the solver execution
    if a_solver.run() :
        shutil.rmtree( a_case_dir )
        os._exit( os.EX_OK )
        pass

    shutil.rmtree( a_case_dir )
    os._exit( os.EX_USAGE )
    pass


#--------------------------------------------------------------------------------------
