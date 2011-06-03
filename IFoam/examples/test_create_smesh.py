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
## File:        test_create_smesh.py
## Author:      Sergey LITONIN, Open CASCADE S.A.S. (sergey.litonin@opencascade.com)
##
## ---

import salome
import geompy
import math
import smesh

from IFoam.foam_smesh_tools import group_create


def createMesh():
	L=0.1
	H=0.08
	T=0.006
	R=0.048
	R1=0.0385
	Vertex_1 = geompy.MakeVertex(0, -L, 0)
	Vertex_2 = geompy.MakeVertex(0, 0, 0)
	Vector_y = geompy.MakeVectorDXDYDZ(0, 1, 0)
	Vector_z = geompy.MakeVectorDXDYDZ(0, 0, 1)
	Cylinder_1 = geompy.MakeCylinder(Vertex_1, Vector_y, R, 2*L)
	Cylinder_2 = geompy.MakeCylinder(Vertex_2, Vector_z, R1, H)
	Fuse_1 = geompy.MakeFuse(Cylinder_1, Cylinder_2)
	[Face_1,Face_2,Face_3,Face_4,Face_5] = geompy.SubShapeAllSorted(Fuse_1, geompy.ShapeType["FACE"])
	[Edge_1,Edge_2,Edge_3,Edge_4,Edge_5,Edge_6,Edge_7,Edge_8,Edge_9,Edge_10] = geompy.SubShapeAllSorted(Fuse_1, geompy.ShapeType["EDGE"])
	geompy.addToStudy( Vertex_1, "Vertex_1" )
	geompy.addToStudy( Vertex_2, "Vertex_2" )
	geompy.addToStudy( Vector_y, "Vector_y" )
	geompy.addToStudy( Vector_z, "Vector_z" )
	geompy.addToStudy( Cylinder_1, "Cylinder_1" )
	geompy.addToStudy( Cylinder_2, "Cylinder_2" )
	geompy.addToStudy( Fuse_1, "Fuse_1" )
	geompy.addToStudyInFather( Fuse_1, Face_1, "Face_1" )
	geompy.addToStudyInFather( Fuse_1, Face_2, "Face_2" )
	geompy.addToStudyInFather( Fuse_1, Face_3, "Face_3" )
	geompy.addToStudyInFather( Fuse_1, Face_4, "Face_4" )
	geompy.addToStudyInFather( Fuse_1, Face_5, "Face_5" )
	
	NETGEN_3D_Parameters = smesh.smesh.CreateHypothesis('NETGEN_Parameters', 'NETGENEngine')
	NETGEN_3D_Parameters.SetMaxSize( 0.005 )
	NETGEN_3D_Parameters.SetSecondOrder( 0 )
	NETGEN_3D_Parameters.SetOptimize( 1 )
	NETGEN_3D_Parameters.SetFineness( 3 )
	Mesh_1 = smesh.Mesh(Fuse_1)
	status = Mesh_1.AddHypothesis(NETGEN_3D_Parameters)
	Netgen_1D_2D_3D = smesh.smesh.CreateHypothesis('NETGEN_2D3D', 'NETGENEngine')
	status = Mesh_1.AddHypothesis(Netgen_1D_2D_3D)
	isDone = Mesh_1.Compute()
	
	# create groups for boundaries
	Faces=[Face_1]
	inlet_F = group_create(Mesh_1.GetMesh(),Faces,"inlet_F")
	Faces=[Face_5]
	outlet_F1 = group_create(Mesh_1.GetMesh(),Faces,"outlet_F1")
	Faces=[Face_3]
	outlet_F2 = group_create(Mesh_1.GetMesh(),Faces,"outlet_F2")
	Faces=[ Face_2, Face_4]
	pipe = group_create(Mesh_1.GetMesh(),Faces,"pipe")

        return [Mesh_1,[inlet_F,outlet_F1,outlet_F2,pipe]]
	
