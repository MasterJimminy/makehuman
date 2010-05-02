#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Module containing classes to handle modelling mode GUI operations.

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    http://code.google.com/p/makehuman/

**Authors:**           Marc Flerackers, Jose Capco

**Copyright(c):**      MakeHuman Team 2001-2010

**Licensing:**         GPL3 (see also http://sites.google.com/site/makehumandocs/licensing)

**Coding Standards:**  See http://sites.google.com/site/makehumandocs/developers-guide

Abstract
--------

This module implements the 'guiadvance' class structures and methods to support GUI
Advance mode operations.
Advance mode is invoked by selecting the Advance mode icon from the main GUI control
bar at the top of the screen.
While in this mode, user actions (keyboard and mouse events) are passed into
this class for processing. Having processed an event this class returns control to the
main OpenGL/SDL/Application event handling loop.


"""

__docformat__ = 'restructuredtext'

import gui3d
import events3d

class MakeHairTaskView(gui3d.TaskView):
    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'MakeHair', category.app.getThemeResource('images', 'makehair.png'), category.app.getThemeResource('images', 'makehair_on.png'))


class AdvancedCategory(gui3d.Category):

    def __init__(self, category):
        gui3d.Category.__init__(self, category, 'Advance', category.app.getThemeResource('images', 'button_advance.png'), category.app.getThemeResource('images', 'button_advance_on.png'))
        
        MakeHairTaskView(self);
