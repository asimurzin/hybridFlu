#!/usr/bin/env ipython

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
This Python packages simplifies usage SALOME through Python.
Loading of this packages whether connects to already existing SALOME session  
or automatically launch a new one
"""

#--------------------------------------------------------------------------------------
import os
import sys


#--------------------------------------------------------------------------------------
# Python completion and others if you want
# You should have set PYTHONSTARTUP env variable
# or import user should try to import $HOME/.pythonrc.py
#--------------------------------------------------------------------------------------
import user


#--------------------------------------------------------------------------------------
# Get major CORBA objects
#--------------------------------------------------------------------------------------
import CORBA
import CosNaming

# There are cyclic dependencies between Engines, SALOME and SALOMEDS.
# import first Engines, then SALOME and then SALOMEDS
# Or use reload(Engines) to be safe.
import Engines
import SALOME
import SALOMEDS
import SALOME_ModuleCatalog

reload(Engines)
reload(SALOME)
reload(SALOMEDS)


#--------------------------------------------------------------------------------------
def get_SALOME_CORBA_port( the_user, the_hostname ) :
  import re
  a_pattern = "\." + the_user + "_" + the_hostname + "_(\d+)_SALOME_pidict"
  a_regexp = re.compile( a_pattern )

  # To find a default value for CORBA port
  args = { "port" : 2810 }
  from runSalome import searchFreePort
  searchFreePort( args, 0 )
  a_SALOME_CORBA_port = int( args[ "port" ] )

  a_latest_time = -1
  
  import tempfile 
  a_dir = os.path.join( tempfile.gettempdir(), "logs", the_user )
  a_files = os.listdir( a_dir )
  for a_file in a_files :
    a_match = a_regexp.match( a_file )
    if a_match :
      # To chose the most recent instance of the SALOME
      a_full_filename = os.path.join( a_dir, a_file )
      a_creation_time = os.stat( a_full_filename )[-1]
      if a_creation_time > a_latest_time :
        a_SALOME_CORBA_port = int( a_match.group( 1 ) )
        a_latest_time = a_creation_time
        pass
      pass
    pass
  

  return a_SALOME_CORBA_port


#--------------------------------------------------------------------------------------
import orbmodule

class TClient( orbmodule.client ) :
  """
  Redefines of the basic class for intialization SALOME CORBA clients 
  """
  def __init__( self, the_user, the_hostname, the_argv = [] ) :
    """
    The contructor of the class
    """
    # To redefine the command line arguments by the input argument
    import sys, copy
    an_argv = copy.copy( sys.argv )
    sys.argv = the_argv

    # To fill the mandatory name of the executable
    sys.argv.insert( 0, "dummy" )

    # To precise the CORBA NameService deatails
    a_port = get_SALOME_CORBA_port( the_user, the_hostname )
    an_init_ref = ( 'NameService=corbaname::%s:%d' % ( the_hostname, a_port ) )
    sys.argv.extend( [ "-ORBInitRef", an_init_ref ] )

    print sys.argv

    # To call constructor for the base class 
    orbmodule.client.__init__( self, None )

    # Restores initial set of command line arguments
    sys.argv = an_argv
    pass

  def initNS( self, args ) :
    """
    Obtains a reference to the root naming context
    """
    try :
      # Try to connect to the existing SALOME session 
      obj = self.orb.resolve_initial_references( "NameService" )
      self.rootContext = obj._narrow( CosNaming.NamingContext )

      # Try to connect to already existing SALOME study
      from salome import salome_init
      salome_init( theStudyId = 1 )
    except :
      # Try to launch a new session of SALOME 

      # Obtain SALOME configuration parameters
      from setenv import get_config
      args, modules_list, modules_root_dir = get_config()

      from runSalome import kill_salome
      kill_salome( args )

      # To generate a new SALOME configuration
      from runSalome import searchFreePort
      searchFreePort( args, 0 )

      # Starting of SALOME application 
      from runSalome import startSalome
      startSalome( args, modules_list, modules_root_dir )

      # To call the carresponding method of base class
      orbmodule.client.initNS( self, args )

      # Try to create a new SALOME study
      from salome import salome_init
      salome_init( theStudyId = 0 )
      pass

    self.showNS() # Prints debug information (can be commented)

    # It is necessary to wait untill it will be possible 
    # to get access to some important SALOME services
    self.waitNS( "/Kernel/Session" )
    self.waitNS( "/Kernel/ModulCatalog" )
    self.waitNS( "/myStudyManager" )

    pass

  pass


#--------------------------------------------------------------------------------------
a_salome_argv = [ ]
a_salome_argv.append( '--gui' )
a_salome_argv.append( '--killall' )
a_salome_argv.append( '--splash=0' )
a_salome_argv.append( '--modules=GUI,GEOM,MED,SMESH,FOAM,VISU' )

TClient( os.getenv( "USER" ), os.getenv( "HOSTNAME" ), a_salome_argv ) # Start the main function

from killSalome import killAllPorts as kill_salome


#--------------------------------------------------------------------------------------
