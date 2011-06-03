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
## Author : Ivor CLIFFORD
##


#--------------------------------------------------------------------------------------
from Foam.finiteVolume import *
from Foam.applications.utilities.postProcessing.graphics.foam2vtk import *

import vtk
from math import sqrt

class field_plotter:
    def __init__(self, obj):
        self.vtkObj = volScalarFieldSource( obj )
        
        self.getVTKWindows()
        
        self.internalMesh = vtk.vtkObject( self.vtkObj.internalMesh().__hex__() )
        
        self.getVTKActor( self.internalMesh )
        
        self.mapper.SetScalarModeToUseCellData()
        
        self.istyle = vtk.vtkInteractorStyleSwitch()
        self.istyle.SetCurrentStyleToTrackballCamera()
        self.iren.SetInteractorStyle(self.istyle)
        
        self.update()
        self.iren.Start()
    
    def getVTKWindows(self):
        self.ren = vtk.vtkRenderer()
        self.renWin = vtk.vtkRenderWindow()
        self.iren = vtk.vtkRenderWindowInteractor()
        
        self.renWin.AddRenderer(self.ren)
        self.iren.SetRenderWindow(self.renWin)
        
        self.ren.SetBackground(0.5, 0.6, 1)
        self.renWin.SetSize(640, 480)
        self.ren.GetActiveCamera().ParallelProjectionOn()
        self.iren.Initialize()
    
    def getVTKActor(self, obj):
        self.triFilter = vtk.vtkDataSetTriangleFilter()
        self.mapper = vtk.vtkDataSetMapper()
        self.actor = vtk.vtkActor()
        
        self.triFilter.SetInput( obj )
        self.mapper.SetInput(self.triFilter.GetOutput())
        self.actor.SetMapper(self.mapper)
        self.ren.AddActor(self.actor)
    def xIn(self):
        self.centerCamera((-1,0,0), False)
        self.ren.GetActiveCamera().SetViewUp((0,1,0))
        self.update()
    def xOut(self):
        self.centerCamera((1,0,0), False)
        self.ren.GetActiveCamera().SetViewUp((0,1,0))
        self.update()
    def yIn(self):
        self.centerCamera((0,-1,0), False)
        self.ren.GetActiveCamera().SetViewUp((0,0,1))
        self.update()
    def yOut(self):
        self.centerCamera((0,1,0), False)
        self.ren.GetActiveCamera().SetViewUp((0,0,-1))
        self.update()
    def zIn(self):
        self.centerCamera((0,0,-1), False)
        self.ren.GetActiveCamera().SetViewUp((0,1,0))
        self.update()
    def zOut(self):
        self.centerCamera((0,0,1), False)
        self.ren.GetActiveCamera().SetViewUp((0,1,0))
        self.update()
    def centerCamera(self):
        self.centerCamera(
            self.ren.GetActiveCamera().GetDirectionOfProjection()
        )
    def centerCamera(self, dirn, redraw=True):
        bounds = self.actor.GetBounds()
        center = self.actor.GetCenter()
        dx = abs(bounds[3]-bounds[0])
        dy = abs(bounds[4]-bounds[1])
        dz = abs(bounds[5]-bounds[2])
        offset = 2*__builtins__.max(dx,dy,dz)
        camera = self.ren.GetActiveCamera()
        camera.SetPosition((
            center[0]+offset*dirn[0],
            center[1]+offset*dirn[1],
            center[2]+offset*dirn[2]
        ))
        camera.SetFocalPoint(center)
        if redraw:
            self.update()
    def update(self):
        self.ren.ResetCamera()
        self.renWin.Render()
        self.iren.Initialize()
    def render(self):
        self.renWin.Render()
    def interact(self):
        self.iren.Start()

