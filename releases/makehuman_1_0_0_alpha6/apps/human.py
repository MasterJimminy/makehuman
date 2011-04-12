#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    http://code.google.com/p/makehuman/

**Authors:**           Manuel Bastioni

**Copyright(c):**      MakeHuman Team 2001-2011

**Licensing:**         GPL3 (see also http://sites.google.com/site/makehumandocs/licensing)

**Coding Standards:**  See http://sites.google.com/site/makehumandocs/developers-guide

Abstract
--------

TO DO

"""

__docformat__ = 'restructuredtext'

import algos3d
import gui3d
import time
from catmull_clark_subdivision import createSubdivisionObject, updateSubdivisionObject
import files3d
import os
import mh
import humanmodifier
import math
import hair
import events3d

class HumanEvent(events3d.Event):

    def __init__(self, human, change):
        self.human = human
        self.change = change

    def __repr__(self):
        return 'event: %s, %s' % (self.human, self.change)

class Human(gui3d.Object):

    def __init__(self, globalScene, objFilePath, hairObj=None):

        gui3d.Object.__init__(self, globalScene.application, [0, 0, 0], objFilePath, visible=True)
        self.mesh.setCameraProjection(0)
        self.mesh.setShadeless(0)
        self.meshData = self.mesh

        self.scene = globalScene
        self.hairModelling = False #temporary variable for easier integration of makehair, will be cleaned later.
        self.hairObj = hairObj
        self.targetsDetailStack = {}  # All details targets applied, with their values
        self.symmetryModeEnabled = False

        self.enableUVInterpolation = 0
        self.targetUVBuffer = {}

        self.detailTargetX1a = None
        self.detailTargetX2a = None
        self.detailTargetY1a = None
        self.detailTargetY2a = None
        self.detailTargetZ1a = None
        self.detailTargetZ2a = None
        self.detailTargetX1b = None
        self.detailTargetX2b = None
        self.detailTargetY1b = None
        self.detailTargetY2b = None
        self.detailTargetZ1b = None
        self.detailTargetZ2b = None

        self.meshStored = []
        self.hairs = hair.Hairs(self)
        self.hairFile = 'data/hairs/default.hair'
        self.hairColor = [0.41, 0.23, 0.04]

        self.childVal = 0.0  # child
        self.oldVal = 0.0  # old
        self.youngVal = 1.0
        self.femaleVal = 0.5  # female
        self.maleVal = 0.5  # male
        self.flaccidVal = 0.0
        self.muscleVal = 0.0
        self.overweightVal = 0.0
        self.underweightVal = 0.0
        self.genitals = 0.0
        self.breastSize = 0.5
        self.breastFirmness = 0.5
        self.nose = 0.0
        self.mouth = 0.0
        self.eyes = 0.0
        self.ears = 0.0
        self.jaw = 0.0
        self.head = 0.0
        self.headAge = 0.0
        self.faceAngle = 0.0
        self.pelvisTone = 0.0
        self.buttocks = 0.0
        self.stomach = 0.0
        self.bodyZones = ['l-eye','r-eye', 'jaw', 'nose', 'mouth', 'head', 'neck', 'torso', 'hip', 'pelvis', 'r-upperarm', 'l-upperarm', 'r-lowerarm', 'l-lowerarm', 'l-hand',
                          'r-hand', 'r-upperleg', 'l-upperleg', 'r-lowerleg', 'l-lowerleg', 'l-foot', 'r-foot', 'ear']

        self.muscleWeightModifier = humanmodifier.GenderAgeMuscleWeightModifier('data/targets/macrodetails/universal-${gender}-${age}-${tone}-${weight}.target')
        self.baseModifier = humanmodifier.GenderAgeModifier('data/targets/macrodetails/neutral-${gender}-${age}.target')
        
        self.__subdivisionMesh = None
        
        self.setTexture("data/textures/texture.png")

    # Overriding hide and show to account for both human base and the hairs!

    def show(self):
        self.visible = True
        if self.hairObj: self.hairObj.setVisibility(1)
        self.setVisibility(True)

    def hide(self):

      # print("hiding ", self.meshName)

        self.visible = False
        if self.hairObj: self.hairObj.setVisibility(0)
        self.setVisibility(False)

    # Overriding setPosition and setRotation to account for both hair and base object

    def setPosition(self, position):
        gui3d.Object.setPosition(self, position)
        if self.hairObj:
            self.hairObj.setLoc(position[0], position[1], position[2])
        if self.isSubdivided():
            self.meshData.setLoc(position[0], position[1], position[2])
        elif self.__subdivisionMesh:
            self.__subdivisionMesh.setLoc(position[0], position[1], position[2])

    def setRotation(self, rotation):
        gui3d.Object.setRotation(self, rotation)
        if self.hairObj:
            self.hairObj.setRot(rotation[0], rotation[1], rotation[2])
        if self.isSubdivided():
            self.meshData.setRot(rotation[0], rotation[1], rotation[2])
        elif self.__subdivisionMesh:
            self.__subdivisionMesh.setRot(rotation[0], rotation[1], rotation[2])

    def setTexture(self, texturePath):
        self.meshData.setTexture(texturePath)
        if self.__subdivisionMesh:
            self.__subdivisionMesh.setTexture(texturePath)

    def setVisibility(self, flag):
        
        self.mesh.setVisibility(flag)
        
    def getSubdivisionMesh(self, update=True, progressCallback=None):
        
        if not self.__subdivisionMesh:
            print 'creating subdiv'
            self.__subdivisionMesh = createSubdivisionObject(self.scene, self.meshData, progressCallback)
        elif update:
            updateSubdivisionObject(self.__subdivisionMesh, progressCallback)
            
        return self.__subdivisionMesh

    def isSubdivided(self):

        return self.mesh == self.__subdivisionMesh
            
    def setSubdivided(self, flag, update=True, progressCallback=None):
        """
        This method toggles between displaying the standard mesh and a
        subdivided mesh. The subdivided mesh contains 4 times the number of
        faces as the standard mesh.

        **Parameters:** None.

        """

        if flag == self.isSubdivided():
            return
            
        if flag:
            self.mesh = self.getSubdivisionMesh(update, progressCallback)
            self.meshData.setVisibility(0)
            self.mesh.setVisibility(1)
        else:
            self.mesh = self.meshData
            if update:
                self.mesh.calcNormals()
                self.mesh.update()
            self.__subdivisionMesh.setVisibility(0)
            self.mesh.setVisibility(1)
        self.app.redraw()

    def setGender(self, gender):
        """
        Sets the gender of the model. 0 is female, 1 is male.

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        """

        gender = min(max(gender, 0.0), 1.0)
        self._setGenderVals(gender)
        self.callEvent('onChanged', HumanEvent(self, 'gender'))

    def getGender(self):
        return self.maleVal

    def _setGenderVals(self, amount):
        if self.maleVal == amount:
            return
        self.maleVal = amount
        self.femaleVal = 1 - amount

    def setAge(self, age):
        """
        Sets the age of the model. 0 if 12 years old, 1 is 70. To set a particular age in years, use the
        formula age_value = (age_in_years - 12) / (70 - 12).

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        """

        age = min(max(age, 0.0), 1.0)
        self._setAgeVals(-1 + 2 * age)
        self.callEvent('onChanged', HumanEvent(self, 'age'))

    def getAge(self):
        if self.oldVal:
            return 0.5 + self.oldVal / 2.0
        elif self.childVal:
            return 0.5 - self.childVal / 2.0
        else:
            return 0.5

    def _setAgeVals(self, amount):
        if amount >= 0:
            if self.oldVal == amount and self.childVal == 0:
                return
            self.oldVal = amount
            self.childVal = 0
        else:
            if self.childVal == -amount and self.oldVal == 0:
                return
            self.childVal = -amount
            self.oldVal = 0
        self.youngVal = 1 - (self.oldVal + self.childVal)

    def setWeight(self, weight):
        """
        Sets the amount of weight of the model. 0 for underweight, 1 for overweight.

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        """

        weight = min(max(weight, 0.0), 1.0)
        self._setWeightVals(-1 + 2 * weight)
        self.callEvent('onChanged', HumanEvent(self, 'weight'))

    def getWeight(self):
        if self.overweightVal:
            return 0.5 + self.overweightVal / 2.0
        elif self.underweightVal:
            return 0.5 - self.underweightVal / 2.0
        else:
            return 0.5

    def _setWeightVals(self, amount):
        if amount >= 0:
            if self.overweightVal == amount and self.underweightVal == 0:
                return
            self.overweightVal = amount
            self.underweightVal = 0
        else:
            if self.underweightVal == -amount and self.overweightVal == 0:
                return
            self.underweightVal = -amount
            self.overweightVal = 0

    def setMuscle(self, muscle):
        """
        Sets the amount of muscle of the model. 0 for flacid, 1 for muscular.

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        """

        muscle = min(max(muscle, 0.0), 1.0)
        self._setMuscleVals(-1 + 2 * muscle)
        self.callEvent('onChanged', HumanEvent(self, 'muscle'))

    def getMuscle(self):
        if self.muscleVal:
            return 0.5 + self.muscleVal / 2.0
        elif self.flaccidVal:
            return 0.5 - self.flaccidVal / 2.0
        else:
            return 0.5

    def _setMuscleVals(self, amount):
        if amount >= 0:
            if self.muscleVal == amount and self.flaccidVal == 0:
                return
            self.muscleVal = amount
            self.flaccidVal = 0
        else:
            if self.flaccidVal == -amount and self.muscleVal == 0:
                return
            self.flaccidVal = -amount
            self.muscleVal = 0
            
    def setHeight(self, height):
        modifier = humanmodifier.Modifier(
            'data/targets/macrodetails/universal-stature-dwarf.target',
            'data/targets/macrodetails/universal-stature-giant.target')
        modifier.setValue(self, height, 0)
        self.callEvent('onChanged', HumanEvent(self, 'height'))
        
    def getHeight(self):
        modifier = humanmodifier.Modifier(
            'data/targets/macrodetails/universal-stature-dwarf.target',
            'data/targets/macrodetails/universal-stature-giant.target')
        return modifier.getValue(self)

    def setDetail(self, name, value):
        if value:
            self.targetsDetailStack[name] = value
        elif name in self.targetsDetailStack:
            del self.targetsDetailStack[name]

    def getDetail(self, name):
        return self.targetsDetailStack.get(name, 0.0)

    def setHairFile(self, filename):
        self.hairFile = filename

    def getSymmetryGroup(self, group):
        if group.name.find('l-', 0, 2) != -1:
            return self.mesh.getFaceGroup(group.name.replace('l-', 'r-', 1))
        elif group.name.find('r-', 0, 2) != -1:
            return self.mesh.getFaceGroup(group.name.replace('r-', 'l-', 1))
        else:
            return None

    def getSymmetryPart(self, name):
        if name.find('l-', 0, 2) != -1:
            return name.replace('l-', 'r-', 1)
        elif name.find('r-', 0, 2) != -1:
            return name.replace('r-', 'l-', 1)
        else:
            return None
    
    def applyAllTargets(self, progressCallback=None, update=True):
        """
        This method applies all targets, in function of age and sex

        **Parameters:** None.

        """
        
        self.muscleWeightModifier.setValue(self, 1.0)
        self.baseModifier.setValue(self, 1.0)

        targetName = None
        algos3d.resetObj(self.meshData)

        if progressCallback:
            progressCallback(0.0)
        progressVal = 0.0
        progressIncr = 0.5 / (len(self.targetsDetailStack) + 1)

        for (k, v) in self.targetsDetailStack.iteritems():
            algos3d.loadTranslationTarget(self.meshData, k, v, None, 0, 0)
            progressVal += progressIncr
            if progressCallback:
                progressCallback(progressVal)

        # Update all verts
        if self.isSubdivided():
            updateSubdivisionObject(self.__subdivisionMesh)
            if progressCallback:
                progressCallback(0.7)
            self.mesh.calcNormals()
            if progressCallback:
                progressCallback(0.8)
            self.mesh.update()
        else:
            self.meshData.calcNormals(1, 1)
            if progressCallback:
                progressCallback(0.8)
            if update:
                self.meshData.update()
                
        if progressCallback:
            progressCallback(1.0)

    def getPartNameForGroupName(self, groupName):
        for k in self.bodyZones:
            if k in groupName:
                return k
        return None

    def applySymmetryLeft(self):
        """
        This method applies right to left symmetry to the currently selected
        body parts.

        **Parameters:** None.

        """

        self.symmetrize('l')

    def applySymmetryRight(self):
        """
        This method applies left to right symmetry to the currently selected
        body parts.

        **Parameters:** None.

        """

        self.symmetrize('r')

    def symmetrize(self, direction='r'):
        """
        This method applies either left to right or right to left symmetry to
        the currently selected body parts.


        Parameters
        ----------

        direction:
            *string*. A string indicating whether to apply left to right
            symmetry (\"r\") or right to left symmetry (\"l\").

        """

        if direction == 'l':
            prefix1 = 'l-'
            prefix2 = 'r-'
        else:
            prefix1 = 'r-'
            prefix2 = 'l-'

        # Remove current values

        for target in self.targetsDetailStack.keys():
            targetName = os.path.basename(target)

            # Reset previous targets on symm side

            if targetName[:2] == prefix2:
                targetVal = self.targetsDetailStack[target]
                algos3d.loadTranslationTarget(self.meshData, target, -targetVal, None, 1, 0)
                del self.targetsDetailStack[target]

        # Apply symm target. For horiz movement the value must be inverted

        for target in self.targetsDetailStack.keys():
            targetName = os.path.basename(target)
            if targetName[:2] == prefix1:
                targetSym = os.path.join(os.path.dirname(target), prefix2 + targetName[2:])
                targetSymVal = self.targetsDetailStack[target]
                if 'trans-in' in targetSym:
                    targetSym = targetSym.replace('trans-in', 'trans-out')
                elif 'trans-out' in targetSym:
                    targetSym = targetSym.replace('trans-out', 'trans-in')

                algos3d.loadTranslationTarget(self.meshData, targetSym, targetSymVal, None, 1, 1)
                self.targetsDetailStack[targetSym] = targetSymVal
                
        if self.isSubdivided():
            self.getSubdivisionMesh()

        self.app.redraw()

    def rotateLimb(self, targetPath, morphFactor):
        targetPath1 = targetPath+".target"
        targetPath2 = targetPath+".rot"
        algos3d.loadTranslationTarget(self.meshData, targetPath1, morphFactor, None, 1, 0)
        algos3d.loadRotationTarget(self.meshData, targetPath2, morphFactor)


    def storeMesh(self):
        print "Storing mesh status"
        self.meshStored = []
        for v in self.meshData.verts:
            self.meshStored.append((v.co[0],v.co[1],v.co[2]))

    def restoreMesh(self):
        for i,v in enumerate(self.meshData.verts):
            v.co[0] = self.meshStored[i][0]
            v.co[1] = self.meshStored[i][1]
            v.co[2] = self.meshStored[i][2]

    def resetMeshValues(self):
        self.childVal = 0.0
        self.youngVal = 1.0
        self.oldVal = 0.0
        self.femaleVal = 0.5
        self.maleVal = 0.5
        self.flaccidVal = 0.0
        self.muscleVal = 0.0
        self.overweightVal = 0.0
        self.underweightVal = 0.0
        self.genitals = 0.0
        self.breastSize = 0.5
        self.breastFirmness = 0.5
        self.stomach = 0.0
        self.nose = 0.0
        self.mouth = 0.0
        self.eyes = 0.0
        self.ears = 0.0
        self.head = 0.0
        self.headAge = 0.0
        self.faceAngle = 0.0
        self.jaw = 0.0
        self.pelvisTone = 0.0
        self.buttocks = 0.0

        self.targetsDetailStack = {}
        
        self.setTexture("data/textures/texture.png")
        
        self.callEvent('onChanged', HumanEvent(self, 'reset'))

    def load(self, filename, update=True, progressCallback=None):
        self.resetMeshValues()

        f = open(filename, 'r')

        for data in f.readlines():
            lineData = data.split()

            if len(lineData) > 0 and not lineData[0] == '#':
                if lineData[0] == 'version':
                    print 'Version ' + lineData[1]
                elif lineData[0] == 'tags':
                    for tag in lineData:
                        print 'Tag ' + tag
                elif lineData[0] == 'gender':
                    self.setGender(float(lineData[1]))
                elif lineData[0] == 'age':
                    self.setAge(float(lineData[1]))
                elif lineData[0] == 'muscle':
                    self.setMuscle(float(lineData[1]))
                elif lineData[0] == 'weight':
                    self.setWeight(float(lineData[1]))
                elif lineData[0] == 'height':
                    modifier = humanmodifier.Modifier('data/targets/macrodetails/universal-stature-dwarf.target',
                                                      'data/targets/macrodetails/universal-stature-giant.target')
                    modifier.setValue(self, float(lineData[1]), 0)
                elif lineData[0] == 'asymmetry':
                    self.targetsDetailStack['data/targets/asym/' + lineData[1] + '.target'] = float(lineData[2])
                elif lineData[0] in self.app.loadHandlers:
                    self.app.loadHandlers[lineData[0]](self, lineData)
                else:
                    print('Could not load %s' % lineData)

        f.close()

        if update:
            self.applyAllTargets(progressCallback)

    def save(self, filename, tags):
        f = open(filename, 'w')
        f.write('# Written by makehuman 1.0.0 alpha 6\n')
        f.write('version 1.0.0\n')
        f.write('tags %s\n' % tags)
        f.write('gender %f\n' % self.getGender())
        f.write('age %f\n' % self.getAge())
        f.write('muscle %f\n' % self.getMuscle())
        f.write('weight %f\n' % self.getWeight())

        modifier = humanmodifier.Modifier('data/targets/macrodetails/universal-stature-dwarf.target', 'data/targets/macrodetails/universal-stature-giant.target')
        f.write('height %f\n' % modifier.getValue(self))

        for t in self.targetsDetailStack.keys():
            if '/asym' in t:
               f.write('asymmetry %s %f\n' % (os.path.basename(t).replace('.target', ''), self.targetsDetailStack[t]))
               
        for handler in self.app.saveHandlers:
            handler(self, f)
               
        f.close()
