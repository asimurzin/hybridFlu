## Copyright (C) 2007-2009 OPEN CASCADE
## 
## This library is free software; you can redistribute it and/or 
## modify it under the terms of the GNU Lesser General Public 
## License as published by the Free Software Foundation; either 
## version 2.1 of the License. 
## 
## This library is distributed in the hope that it will be useful, 
## but WITHOUT ANY WARRANTY; without even the implied warranty of 
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
## Lesser General Public License for more details. 
## 
## You should have received a copy of the GNU Lesser General Public 
## License along with this library; if not, write to the Free Software 
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA 
## 
## See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
##
## ---
##
## File:        foam_smesh_tools.py
## Author:      Sergey LITONIN, Open CASCADE S.A.S. (sergey.litonin@opencascade.com)
##
## ---

import SMESH
import smesh

def group_create( theMesh, theFacesList, theGroupName):
    #^Create group functor and Filter for faces^
    ids = []
    for face in theFacesList:
  		aFilter=smesh.GetFilter(SMESH.FACE,SMESH.FT_BelongToGeom,'=',face)
		anIds = aFilter.GetElementsId( theMesh )
		ids.extend( anIds )
    gg = theMesh.CreateGroup( SMESH.FACE, theGroupName )
    nbAdd = gg.Add(ids)
    return gg
