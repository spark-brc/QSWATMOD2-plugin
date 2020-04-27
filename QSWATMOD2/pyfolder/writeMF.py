# -*- coding: utf-8 -*-

from builtins import str
import os
import os.path
from qgis.PyQt import QtCore, QtGui, QtSql
import processing
from qgis.core import (
                        QgsVectorLayer, QgsField,
                        QgsFeatureIterator, QgsVectorFileWriter,
                        QgsRasterLayer, QgsProject, QgsLayerTreeLayer
                        )
import glob
import posixpath
import ntpath
import shutil
from qgis.PyQt.QtCore import QVariant, QFileInfo, QSettings, QCoreApplication
from datetime import datetime
from PyQt5.QtWidgets import (
            QInputDialog, QLineEdit, QDialog, QFileDialog,
            QMessageBox
)
from QSWATMOD2.modules import flopy


def extentlayer(self): # ----> why is not working T,.T
    extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]

    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)
    return extent


def createBotElev(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + "Creating bottom elevation ... processing")
    self.label_mf_status.setText("Creating bottom elevation ... ")
    self.progressBar_mf_status.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()

    try:
        if provider.fields().indexFromName("bot_elev") != -1:
            attrIdx = provider.fields().indexFromName( "bot_elev" )
            provider.deleteAttributes([attrIdx])
            field = QgsField("bot_elev", QVariant.Double,'double', 20, 5)

        elif provider.fields().indexFromName("bot_elev" ) == -1:
            field = QgsField("bot_elev", QVariant.Double,'double', 20, 5)

        provider.addAttributes([field])
        self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()

        # Single value
        if (self.radioButton_aq_thic_single.isChecked() and self.lineEdit_aq_thic_single.text()):
            depth = float(self.lineEdit_aq_thic_single.text())
            for f in feats:
                f['bot_elev'] = - depth + f['elev_mf']
                self.layer.updateFeature(f)
            self.layer.commitChanges()
            self.time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(self.time+' -> ' + 'Aquifer thickness is entered ...')
        # Uniform value
        elif (self.radioButton_aq_thic_uniform.isChecked() and self.lineEdit_aq_thic_uniform.text()):
            elev = float(self.lineEdit_aq_thic_uniform.text())
            for f in feats:
                f['bot_elev'] = elev
                self.layer.updateFeature(f)
            self.layer.commitChanges()
            self.time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(self.time+' -> ' + 'Aquifer thickness is entered ...')
        else:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Oops!")
            msgBox.setText("Please, provide a value of the Aquifer thickness!")
            msgBox.exec_()
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_mf_log.append(time+' -> ' + "Creating bottom elevation ... passed")
        self.label_mf_status.setText('Step Status: ')
        self.progressBar_mf_status.setValue(100)
        QCoreApplication.processEvents()        
    except:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("ERROR!!!")
        msgBox.exec_()


def cvtBotElevToR(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + "Converting bottom elevation to raster ... processing")
    self.label_mf_status.setText("Converting bottom elevation to raster ... ")
    self.progressBar_mf_status.setValue(0)
    QCoreApplication.processEvents()

    QSWATMOD_path_dict = self.dirs_and_paths()

    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("bot_elev (MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

    extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
    
    # Get pixel size from top_elev raster
    delc = input2.rasterUnitsPerPixelX()
    delr = input2.rasterUnitsPerPixelY()
    
    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b = xmax, c = ymin, d = ymax)

    name = 'bot_elev'
    name_ext = "bot_elev.tif"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_raster = os.path.join(output_dir, name_ext)

    if (self.radioButton_aq_thic_raster.isChecked() and self.lineEdit_aq_thic_raster.text()):
        params = {
            'INPUT': input1,
            'FIELD': "bot_mean",
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': -9999,
            'DATA_TYPE': 5,
            'OUTPUT': output_raster
        }
    else:
        params = {
            'INPUT': input1,
            'FIELD': "bot_elev",
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': -9999,
            'DATA_TYPE': 5,
            'OUTPUT': output_raster
        }
    processing.run("gdal:rasterize", params)

    layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("bot_elev", "MODFLOW"))
        
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")    
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + "Converting bottom elevation to raster ... passed")
    self.label_mf_status.setText('Step Status: ')
    self.progressBar_mf_status.setValue(0)
    QCoreApplication.processEvents()

# navigate to the bot_elev raster
def loadBotElev(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Bottom Elevation Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = 'bot_elev'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)                    
            shutil.copy(f, outfile)
    
        if os.name == 'nt':
            bot_elev = ntpath.join(Out_folder, inName + ".tif")
        else:
            bot_elev = posixpath.join(Out_folder, inName + ".tif")

        # Delete existing "bot_elev (MODFLOW)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("bot_elev (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        layer = QgsRasterLayer(bot_elev, '{0} ({1})'.format("bot_elev", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_aq_thic_raster.setText(bot_elev)


def getBotfromR(self):
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("bot_elev (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()

    if provider1.fields().indexFromName("bot_mean") != -1:
        attrIdx = provider1.fields().indexFromName("bot_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'elev_',
        'STATS':[2]            
    }    
    processing.run("qgis:zonalstatistics", params)
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Extrating Bottom Elevation from Raster has been finished...')


# ----------------------------------------------------------------------------------------------
# def createHK(self):
#     self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
#     provider = self.layer.dataProvider()

#     try:
#         if provider.fields().indexFromName("hk") != -1:
#             attrIdx = provider.fields().indexFromName("hk")
#             provider.deleteAttributes([attrIdx])
#             field = QgsField("hk", QVariant.Double,'double', 20, 5)

#         elif provider.fields().indexFromName("hk") == -1:
#             field = QgsField("hk", QVariant.Double,'double', 20, 5)

#         provider.addAttributes([field])
#         self.layer.updateFields()
#         feats = self.layer.getFeatures()
#         self.layer.startEditing()

#         if (self.radioButton_hk_single.isChecked() and self.lineEdit_hk_single.text()):
#             hk = float(self.lineEdit_hk_single.text())
#             for f in feats:
#                 f['hk'] = hk
#                 self.layer.updateFeature(f)

#             self.layer.commitChanges()
#             self.time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
#             self.textEdit_mf_log.append(self.time+' -> ' + 'Horizantal Hydraulic Conductivity is entered ...')

#         else:
#             msgBox = QMessageBox()
#             msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#             msgBox.setWindowTitle("Oops!")
#             msgBox.setText("Please, provide a value of the Horizontal Hydraulic Conductivity!")
#             msgBox.exec_()
#     except:
#         msgBox = QMessageBox()
#         msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#         msgBox.setWindowTitle("Oops!")
#         msgBox.setText("ERROR!!!")
#         msgBox.exec_()


def cvtHKtoR(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + "Converting hydraulic conductivity to raster ... processing")
    self.label_mf_status.setText("Converting bottom elevation to raster ... ")
    self.progressBar_mf_status.setValue(0)
    QCoreApplication.processEvents()

    QSWATMOD_path_dict = self.dirs_and_paths()

    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("hk (MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

    extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]

    # Get pixel size from top_elev raster
    delc = input2.rasterUnitsPerPixelX()
    delr = input2.rasterUnitsPerPixelY()

    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)

    name = 'hk'
    name_ext = "hk.tif"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_raster = os.path.join(output_dir, name_ext)

    params = {
        'INPUT': input1,
        'FIELD': "elev_mf",
        'UNITS': 1,
        'WIDTH': delc,
        'HEIGHT': delr,
        'EXTENT': extent,
        'NODATA': -9999,
        'DATA_TYPE': 5,
        'OUTPUT': output_raster
    }
    processing.run("gdal:rasterize", params)
    layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("hk","MODFLOW"))

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")    
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + "Converting hydraulic conductivity to raster ... passed")
    self.label_mf_status.setText("Step Status: ")
    self.progressBar_mf_status.setValue(0)
    QCoreApplication.processEvents()


# navigate to the hk raster
def loadHK(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Hydraulic Conductivity Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = 'hk'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile)
    
        if os.name == 'nt':
            hk = ntpath.join(Out_folder, inName + ".tif")
        else:
            hk = posixpath.join(Out_folder, inName + ".tif")

        # Delete existing "bot_elev (MODFLOW)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("hk (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        layer = QgsRasterLayer(hk, '{0} ({1})'.format("hk", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_hk_raster.setText(hk)


def getHKfromR(self):
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("hk (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()

    if provider1.fields().indexFromName("hk_mean") != -1:
        attrIdx = provider1.fields().indexFromName("hk_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'hk_',
        'STATS':[2]            
        }      
    processing.run("qgis:zonalstatistics", params)
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Extrating Hydraulic Conductivity from Raster has been finished...')


# ----------------------------------------------------------------------------------------------
# def createSS(self):
#     self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
#     provider = self.layer.dataProvider()

#     try:
#         if provider.fields().indexFromName("ss") != -1:
#             attrIdx = provider.fields().indexFromName("ss")
#             provider.deleteAttributes([attrIdx])
#             field = QgsField("ss", QVariant.Double,'double', 20, 5)

#         elif provider.fields().indexFromName("ss") == -1:
#             field = QgsField("ss", QVariant.Double,'double', 20, 5)

#         provider.addAttributes([field])
#         self.layer.updateFields()
#         feats = self.layer.getFeatures()
#         self.layer.startEditing()

#         if (self.radioButton_ss_single.isChecked() and self.lineEdit_ss_single.text()):
#             ss = float(self.lineEdit_ss_single.text())
#             for f in feats:
#                 f['ss'] = ss
#                 self.layer.updateFeature(f)

#             self.layer.commitChanges()
#             time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
#             self.textEdit_mf_log.append(time+' -> ' + 'Specific Storage is entered ...')

#         else:
#             msgBox = QMessageBox()
#             msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#             msgBox.setWindowTitle("Oops!")
#             msgBox.setText("Please, provide a value of the Horizontal Hydraulic Conductivity!")
#             msgBox.exec_()

#     except:
#         msgBox = QMessageBox()
#         msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#         msgBox.setWindowTitle("Oops!")
#         msgBox.setText("ERROR!!")
#         msgBox.exec_()


def cvtSStoR(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("ss (MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

    extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
    
    # Get pixel size from top_elev raster
    delc = input2.rasterUnitsPerPixelX()
    delr = input2.rasterUnitsPerPixelY()
    
    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)

    name = 'ss'
    name_ext = "ss.tif"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_raster = os.path.join(output_dir, name_ext)


    params = {
        'INPUT': input1,
        'FIELD': "ss_mean",
        'UNITS': 1,
        'WIDTH': delc,
        'HEIGHT': delr,
        'EXTENT': extent,
        'NODATA': -9999,
        'DATA_TYPE': 5,
        'OUTPUT': output_raster
    }
    processing.run("gdal:rasterize", params)
    layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("ss","MODFLOW"))

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")    
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Specific Storage is converted to Raster ...')


def loadSS(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Specific Storage Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = 'ss'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)                    
            shutil.copy(f, outfile)
    
        if os.name == 'nt':
            ss = ntpath.join(Out_folder, inName + ".tif")
        else:
            ss = posixpath.join(Out_folder, inName + ".tif")

        # Delete existing "bot_elev (MODFLOW)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("ss (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        layer = QgsRasterLayer(ss, '{0} ({1})'.format("ss", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_ss_raster.setText(ss)


def getSSfromR(self):
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("ss (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()

    if provider1.fields().indexFromName("ss_mean") != -1:
        attrIdx = provider1.fields().indexFromName("ss_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'ss_',
        'STATS':[2]            
    }      
    processing.run("qgis:zonalstatistics", params)
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Extrating Specific Storage from Raster has been finished...')


# ----------------------------------------------------------------------------------------------
# def createSY(self):
#     self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
#     provider = self.layer.dataProvider()

#     try:
#         if provider.fields().indexFromName("sy") != -1:
#             attrIdx = provider.fields().indexFromName("sy")
#             provider.deleteAttributes([attrIdx])
#             field = QgsField("sy", QVariant.Double,'double', 20, 5)

#         elif provider.fields().indexFromName( "sy" ) == -1:
#             field = QgsField("sy", QVariant.Double,'double', 20, 5)

#         provider.addAttributes([field])
#         self.layer.updateFields()
#         feats = self.layer.getFeatures()
#         self.layer.startEditing()

#         if (self.radioButton_sy_single.isChecked() and self.lineEdit_sy_single.text()):
#             sy = float(self.lineEdit_sy_single.text())
#             for f in feats:
#                 f['sy'] = sy
#                 self.layer.updateFeature(f)

#             self.layer.commitChanges()
#             time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
#             self.textEdit_mf_log.append(time+' -> ' + 'Specific Yield is entered ...')

#         else:
#             msgBox = QMessageBox()
#             msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#             msgBox.setWindowTitle("Oops!")
#             msgBox.setText("Please, provide a value of the Specific Yield!")
#             msgBox.exec_()

#     except:
#         msgBox = QMessageBox()
#         msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#         msgBox.setWindowTitle("Oops!")
#         msgBox.setText("ERROR: Specific Yield")
#         msgBox.exec_()


def cvtSYtoR(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("sy (MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

    extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
    
    # Get pixel size from top_elev raster
    delc = input2.rasterUnitsPerPixelX()
    delr = input2.rasterUnitsPerPixelY()
    
    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a = xmin, b = xmax, c = ymin, d = ymax)

    name = 'sy'
    name_ext = "sy.tif"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_raster = os.path.join(output_dir, name_ext)
    params = {
        'INPUT': input1,
        'FIELD': "sy_mean",
        'UNITS': 1,
        'WIDTH': delc,
        'HEIGHT': delr,
        'EXTENT': extent,
        'NODATA': -9999,
        'DATA_TYPE': 5,
        'OUTPUT': output_raster
    }
    processing.run("gdal:rasterize", params)
    layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("sy","MODFLOW"))
        
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")    
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Specific Yield is converted to Raster ...')


def loadSY(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Specific Yield Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = 'sy'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)                    
            shutil.copy(f, outfile)
    
        if os.name == 'nt':
            sy = ntpath.join(Out_folder, inName + ".tif")
        else:
            sy = posixpath.join(Out_folder, inName + ".tif")

        # Delete existing "bot_elev (MODFLOW)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("sy (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        layer = QgsRasterLayer(sy, '{0} ({1})'.format("sy", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_sy_raster.setText(sy)


def getSYfromR(self):
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("sy (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()

    if provider1.fields().indexFromName("sy_mean") != -1:
        attrIdx = provider1.fields().indexFromName("sy_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'sy_',
        'STATS':[2]            
    }      
    processing.run("qgis:zonalstatistics", params)
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Extrating Specific Yield from Raster has been finished...')


# ----------------------------------------------------------------------------------------------

def createInitialH(self):
    self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()

    try:
        if provider.fields().indexFromName("initialH") != -1:
            attrIdx = provider.fields().indexFromName( "initialH" )
            provider.deleteAttributes([attrIdx])
            field = QgsField("initialH", QVariant.Double,'double', 20, 5)

        elif provider.fields().indexFromName( "initialH" ) == -1:
            field = QgsField("initialH", QVariant.Double,'double', 20, 5)

        provider.addAttributes([field])
        self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()

        # Single value
        if (self.radioButton_initialH_single.isChecked() and self.lineEdit_initialH_single.text()):
            depth = float(self.lineEdit_initialH_single.text())
            for f in feats:
                f['initialH'] = - depth + f['elev_mf']
                self.layer.updateFeature(f)

            self.layer.commitChanges()
            self.time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(self.time+' -> ' + 'Initial Hydraulic Head is entered ...')

        # Uniform value
        elif (self.radioButton_initialH_uniform.isChecked() and self.lineEdit_initialH_uniform.text()):
            elev = float(self.lineEdit_initialH_uniform.text())
            for f in feats:
                f['initialH'] = elev
                self.layer.updateFeature(f)

            self.layer.commitChanges()
            self.time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(self.time+' -> ' + 'Initial Hydraulic Head is entered ...')

        else:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Oops!")
            msgBox.setText("Please, provide a value of the Initial Hydraulic Head!")
            msgBox.exec_()

    except:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("ERROR!!!")
        msgBox.exec_()


def cvtInitialHtoR(self):
    #extent = self.extentlayer()
    #layer_extent = extent
    QSWATMOD_path_dict = self.dirs_and_paths()

    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("initialH (MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

    extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
    
    # Get pixel size from top_elev raster
    delc = input2.rasterUnitsPerPixelX()
    delr = input2.rasterUnitsPerPixelY()
    
    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a = xmin, b = xmax, c = ymin, d = ymax)

    name = 'initialH'
    name_ext = "initialH.tif"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_raster = os.path.join(output_dir, name_ext)

    if (self.radioButton_initialH_raster.isChecked() and self.lineEdit_initialH_raster.text()):
        params = {
            'INPUT': input1,
            'FIELD': "ih_mean",
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': -9999,
            'DATA_TYPE': 5,
            'OUTPUT': output_raster
        }        
    else:
        params = {
            'INPUT': input1,
            'FIELD': "initialH",
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': -9999,
            'DATA_TYPE': 5,
            'OUTPUT': output_raster
        }

    processing.run("gdal:rasterize", params)
    layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("initialH", "MODFLOW"))

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Initial Hydraulic Head has been converted to Raster ...')


def loadInitialH(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Initial Head Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = 'initialH'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile)
        if os.name == 'nt':
            initialH = ntpath.join(Out_folder, inName + ".tif")
        else:
            initialH = posixpath.join(Out_folder, inName + ".tif")

        # Delete existing "bot_elev (MODFLOW)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("initialH (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        layer = QgsRasterLayer(initialH, '{0} ({1})'.format("initialH","DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_initialH_raster.setText(initialH)


def getIHfromR(self):
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("initialH (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()

    if provider1.fields().indexFromName("ih_mean") != -1:
        attrIdx = provider1.fields().indexFromName("ih_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'ih_',
        'STATS':[2]            
        }     
    processing.run("qgis:zonalstatistics", params)
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Extrating Initial Head from Raster has been finished...')

### ============================================================================================

def cvtEVTtoR(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("evt (MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

    extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
    
    # Get pixel size from top_elev raster
    delc = input2.rasterUnitsPerPixelX()
    delr = input2.rasterUnitsPerPixelY()
    
    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a = xmin, b = xmax, c = ymin, d = ymax)

    name = 'evt'
    name_ext = "evt.tif"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_raster = os.path.join(output_dir, name_ext)

    params = {
        'INPUT': input1,
        'FIELD': "elev_mean",
        'UNITS': 1,
        'WIDTH': delc,
        'HEIGHT': delr,
        'EXTENT': extent,
        'NODATA': -9999,
        'DATA_TYPE': 5,
        'OUTPUT': output_raster
    }
    processing.run("gdal:rasterize", params)
    layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("evt","MODFLOW"))
        
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")    
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Evapotranspiration has been converted to Raster ...')


def loadEVT(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Specific Yield Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = 'evt'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)                    
            shutil.copy(f, outfile)
    
        if os.name == 'nt':
            evt = ntpath.join(Out_folder, inName + ".tif")
        else:
            evt = posixpath.join(Out_folder, inName + ".tif")

        # Delete existing "bot_elev (MODFLOW)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("evt (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        layer = QgsRasterLayer(evt, '{0} ({1})'.format("evt", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_evt_raster.setText(evt)


def getEVTfromR(self):
    input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("evt (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()

    if provider1.fields().indexFromName("evt_mean") != -1:
        attrIdx = provider1.fields().indexFromName("evt_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'evt_',
        'STATS':[2]            
        }     
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Extrating Specific Yield from Raster has been finished...')


# ----------------------------------------------------------------------------------------------
def create_layer_inRiv(self):
    
    self.layer = QgsProject.instance().mapLayersByName("mf_riv2 (MODFLOW)")[0]
    provider = self.layer.dataProvider()

    if self.layer.dataProvider().fields().indexFromName( "layer" ) == -1:
        field = QgsField("layer", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
    feats = self.layer.getFeatures()
    self.layer.startEditing()
    for feat in feats:
        layer = 1
        feat['layer'] = layer
        self.layer.updateFeature(feat)
    self.layer.commitChanges()


# def extentlayer(self):
#   extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]

#   # get extent
#   ext = extlayer.extent()
#   xmin = ext.xMinimum()
#   xmax = ext.xMaximum()
#   ymin = ext.yMinimum()
#   ymax = ext.yMaximum()
#   extent = "{a},{b},{c},{d}".format(a = xmin, b = xmax, c = ymin, d = ymax)
#   return extent


# ----------------------------------------------------------------------------------------------
def createRch(self):
    if (self.radioButton_rch.isChecked() and self.lineEdit_rch.text()):
        rch = float(self.lineEdit_rch.text())

        self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
        provider = self.layer.dataProvider()
        if self.layer.dataProvider().fields().indexFromName("rch") == -1:
            field = QgsField("rch", QVariant.Double,'double', 20, 5)
            provider.addAttributes([field])
            self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for f in feats:
            f['rch'] = rch
            self.layer.updateFeature(f)
        self.layer.commitChanges()

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_mf_log.append(time+' -> ' + 'Specific Yield is entered ...')
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, provide a value of the recharge rate!")
        msgBox.exec_()

# def cvtRchtoR(self):
#     QSWATMOD_path_dict = self.dirs_and_paths()
#     extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
#     input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
#     input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
    
#     # Get pixel size from top_elev raster
#     delc = input2.rasterUnitsPerPixelX()
#     delr = input2.rasterUnitsPerPixelY()
    
#     # get extent
#     ext = extlayer.extent()
#     xmin = ext.xMinimum()
#     xmax = ext.xMaximum()
#     ymin = ext.yMinimum()
#     ymax = ext.yMaximum()
#     extent = "{a},{b},{c},{d}".format(a = xmin, b = xmax, c = ymin, d = ymax)

#     name = 'rch'
#     name_ext = "rch.tif"
#     output_dir = QSWATMOD_path_dict['org_shps']
#     output_raster = os.path.join(output_dir, name_ext)

#     processing.run(
#         "gdalogr:rasterize",
#         input1,
#         "rch",1, delc, delr,
#         extent,
#         False,5,"-9999",0,75,6,1,False,0,"",
#         output_raster)

#     layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("rch","MODFLOW"))
        
#     # Put in the group
#     root = QgsProject.instance().layerTreeRoot()
#     mf_group = root.findGroup("MODFLOW")    
#     QgsProject.instance().addMapLayer(layer, False)
#     mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))

#     time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
#     self.textEdit_mf_log.append(time+' -> ' + 'Specific Yield is converted to Raster ...')

# --------------------------------------------------------------------------------------------
def writeMFmodel(self):
    # import modules
    from QSWATMOD2.modules import flopy
    import os
    import numpy as np
    from osgeo import gdal
    from osgeo import osr
    import datetime

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))

    # set working directory and inputs -----------------------------------------------------
    # mffolder_path = self.createMFfolder()

    if not self.lineEdit_createMFfolder.text():
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, specify the path to your MODFLOW model working directory!")
        msgBox.exec_()
    elif not self.lineEdit_mname.text():
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, provide your MODFLOW model name!")
        msgBox.exec_()
    else:
        QSWATMOD_path_dict = self.dirs_and_paths()
        wd = QSWATMOD_path_dict['SMfolder']
        wd2 = QSWATMOD_path_dict['org_shps']
        mfwd = self.lineEdit_createMFfolder.text()
        mname = self.lineEdit_mname.text()

        ### =====================================================================
        cio = open(os.path.join(wd, "file.cio"), "r")
        lines = cio.readlines()
        skipyear = int(lines[59][12:16])
        iprint = int(lines[58][12:16]) #read iprint (month, day, year)
        styear = int(lines[8][12:16]) #begining year
        styear_warmup = int(lines[8][12:16]) + skipyear #begining year with warmup
        edyear = styear + int(lines[7][12:16])-1 # ending year
        edyear_warmup = styear_warmup + int(lines[7][12:16])-1 - int(lines[59][12:16])#ending year with warmup
        if skipyear == 0:
            FCbeginday = int(lines[9][12:16])  #begining julian day
        else:
            FCbeginday = 1  #begining julian day
        FCendday = int(lines[10][12:16])  #ending julian day
        cio.close()

        stdate = datetime.datetime(styear, 1, 1) + datetime.timedelta(FCbeginday - 1)
        eddate = datetime.datetime(edyear, 1, 1) + datetime.timedelta(FCendday - 1)

        startDate = stdate.strftime("%m/%d/%Y")
        endDate = eddate.strftime("%m/%d/%Y")
        duration = (eddate - stdate).days + 100 # add 100 days more ...considering leap years

        # ======================================================================
        mf = flopy.modflow.Modflow(
            mname, model_ws=mfwd,
            # exe_name = exe_name,
            version='mfnwt')

        # top_elev
        top_elev = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
        top_elev_Ds = gdal.Open(top_elev.source())
        top_elev_Data = top_elev_Ds.GetRasterBand(1).ReadAsArray()
        top_elev_nan = top_elev_Ds.GetRasterBand(1).GetNoDataValue()

        # bot_elev
        bot_elev = QgsProject.instance().mapLayersByName("bot_elev (MODFLOW)")[0]
        bot_elev_Ds = gdal.Open(bot_elev.source())
        bot_elev_Data = bot_elev_Ds.GetRasterBand(1).ReadAsArray()

        # Single HK
        if (self.radioButton_hk_single.isChecked() and self.lineEdit_hk_single.text()):
            hk_Data = float(self.lineEdit_hk_single.text())
            time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Single Hydraulic Conductivity is used...')
        elif (self.radioButton_hk_raster.isChecked() and self.lineEdit_hk_raster.text()):
            hk = QgsProject.instance().mapLayersByName("hk (MODFLOW)")[0]
            hk_Ds = gdal.Open(hk.source())
            hk_Data = hk_Ds.GetRasterBand(1).ReadAsArray()
        else:
            msgBox.setWindowTitle("Error!")
            msgBox.setText("Hydraulic Conductivity is NOT provided!")
            msgBox.exec_()

        # SS
        if (self.radioButton_ss_single.isChecked() and self.lineEdit_ss_single.text()):
            ss_Data = float(self.lineEdit_ss_single.text())
            time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Single Specific Storage is used...')
        elif (self.radioButton_ss_raster.isChecked() and self.lineEdit_ss_raster.text()):
            ss = QgsProject.instance().mapLayersByName("ss (MODFLOW)")[0]
            ss_Ds = gdal.Open(ss.source())
            ss_Data = ss_Ds.GetRasterBand(1).ReadAsArray()
        else:
            msgBox.setWindowTitle("Error!")
            msgBox.setText("Specific Storage is NOT provided!")
            msgBox.exec_()

        # SY
        if (self.radioButton_sy_single.isChecked() and self.lineEdit_sy_single.text()):
            sy_Data = float(self.lineEdit_sy_single.text())
            time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Single Specific Yield is used...')
        elif (self.radioButton_sy_raster.isChecked() and self.lineEdit_sy_raster.text()):
            sy = QgsProject.instance().mapLayersByName("sy (MODFLOW)")[0]
            sy_Ds = gdal.Open(sy.source())
            sy_Data = sy_Ds.GetRasterBand(1).ReadAsArray()
        else:
            msgBox.setWindowTitle("Error!")
            msgBox.setText("Specific Storage is NOT provided!")
            msgBox.exec_()

        # EVT
        if self.groupBox_evt.isChecked():
            if (self.radioButton_evt_single.isChecked() and self.lineEdit_evt_single.text()):
                evt_Data = float(self.lineEdit_evt_single.text())
                time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
                self.textEdit_mf_log.append(time+' -> ' + 'Single EVT value is used...')

            elif (self.radioButton_evt_raster.isChecked() and self.lineEdit_evt_raster.text()):
                evt = QgsProject.instance().mapLayersByName("evt (MODFLOW)")[0]
                evt_Ds = gdal.Open(evt.source())
                evt_Data = evt_Ds.GetRasterBand(1).ReadAsArray()
            else:
                msgBox.setWindowTitle("Error!")
                msgBox.setText("Evapotranspiration is NOT provided!")
                msgBox.exec_()

        # initialH
        initialH = QgsProject.instance().mapLayersByName("initialH (MODFLOW)")[0]
        initialH_Ds = gdal.Open(initialH.source())
        initialH_Data = initialH_Ds.GetRasterBand(1).ReadAsArray()

        # have geo transform to set things up to match later that puts our outputs
        geot = top_elev_Ds.GetGeoTransform()


        # The following method cause a problem (None Type has no SetProjection)
        # Get ibound -------------------------------------------------------------------------
        iboundDs = gdal.GetDriverByName('GTiff').Create(
                        os.path.join(wd2, 'ibound.tiff'), top_elev_Ds.RasterXSize,
                        top_elev_Ds.RasterYSize, 1, gdal.GDT_Int32)
        # iboundDs = gdal.Open(os.path.join(wd2, 'ibound.tiff'), 1)
        iboundDs.SetProjection(top_elev_Ds.GetProjection())
        iboundDs.SetGeoTransform(geot)

        iboundData = np.zeros(top_elev_Data.shape, dtype = np.int32)
        iboundData[top_elev_Data != top_elev_nan] = 1

        # negative on is the value in the i bound that represents there's a value for the initial hydraulic head condition
        iboundData[top_elev_Data == top_elev_nan] = 0
        iboundDs.GetRasterBand(1).WriteArray(iboundData)

        # New Method from Luke to create Bas input file 9/23/2018
        # mf_dem = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
        # mf_demDs = gdal.Open(sy.source())
        # gs = mf_demDs.GetRasterBand(1).ReadAsArray()
        # geot_gs = mf_demDs.GetGeoTransform()
        # # gsData = top_elev_Ds.GetRasterBand(1).ReadAsArray()
        # gs_demNd = mf_demDs.GetRasterBand(1).GetNoDataValue()
        # ibound = np.zeros(gs.shape, dtype=np.int32)
        # ibound[(gs[:, :] > 0)] = 1

        # Model domain and grid definition ------------------------------------------------------
        ztop = top_elev_Data
        zbot = bot_elev_Data
        nlay = 1
        nrow = top_elev_Ds.RasterYSize
        ncol = top_elev_Ds.RasterXSize
        delr = geot[1]
        delc = abs(geot[5])

        # Create dis file -------------------------------------------------------------------
        dis = flopy.modflow.ModflowDis(
            mf, nlay, nrow, ncol,
            delr=delr, delc=delc, top=ztop, botm=zbot, itmuni = 4,
            perlen=duration, nstp=duration, steady=False)

        # write bas -------------------------------------------------------------------
        bas = flopy.modflow.ModflowBas(mf, ibound=iboundData, strt=initialH_Data)

        # NWT solver -------------------------------------------------------------------
        nwt = flopy.modflow.ModflowNwt(
                    mf, headtol=0.1, fluxtol=500, maxiterout=1000,
                    Continue=False, iprnwt=1, linmeth=2
                    )

        # Create upw -------------------------------------------------------------------
        vka = float(self.lineEdit_vka.text())
        if self.comboBox_layerType.currentText() == " - Convertible - ":
            laytype = 1
        else:
            laytype = 0
        upw = flopy.modflow.ModflowUpw(mf, hk=hk_Data, ss=ss_Data, sy=sy_Data, vka=vka, laytyp=laytype)

        # Create EVT -------------------------------------------------------------------
        if self.groupBox_evt.isChecked():
            evt = flopy.modflow.ModflowEvt(mf, nevtop=3, evtr=evt_Data)


        ### Riv package =========================================================
        riv = QgsProject.instance().mapLayersByName("mf_riv2 (MODFLOW)")[0]
        provider = riv.dataProvider()

        # Get the index numbers of the fields
        grid_id_idx = provider.fields().indexFromName("grid_id")
        layer_idx = provider.fields().indexFromName("layer")
        row_idx = provider.fields().indexFromName("row")
        col_idx = provider.fields().indexFromName("col")
        riv_stage = provider.fields().indexFromName("riv_stage")
        riv_cond = provider.fields().indexFromName("riv_cond")
        riv_bot = provider.fields().indexFromName("riv_bot")

        # transfer the shapefile riv to a python list   
        l = []
        for i in riv.getFeatures():
            l.append(i.attributes())

        # then sort by grid_id
        import operator
        l_sorted = sorted(l, key=operator.itemgetter(grid_id_idx))

        # Extract grid_ids and layers as lists
        layers = [(ly[layer_idx]-1) for ly in l_sorted] 
        rows = [(r[row_idx]-1) for r in l_sorted]
        cols = [(c[col_idx]-1) for c in l_sorted]
        riv_stages = [float(rs[riv_stage]) for rs in l_sorted]
        riv_conds = [float(rc[riv_cond]) for rc in l_sorted]
        riv_bots = [float(rb[riv_bot]) for rb in l_sorted]
        riv_f = np.c_[layers, rows, cols, riv_stages, riv_conds, riv_bots]
        lrcd = {}
        lrcd[0] = riv_f # This river boundary will be applied to all stress periods
        riv_pac = flopy.modflow.ModflowRiv(mf, stress_period_data=lrcd)
        ###  ===========================================================================================

        ### Recharge Package (Recharge rate / Deep peroclation is passed from SWAT simulation!)
        rch = flopy.modflow.ModflowRch(mf, rech=0)
        ###  ===========================================================================================

        # oc package
        oc = flopy.modflow.ModflowOc(mf, ihedfm=1)

        # write input files
        mf.write_input()

        # run model
        # success, mfoutput = mf.run_model(silent = False, pause = False)
        time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_mf_log.append(time + ' -> ' + 'Your MODFLOW model has been created in the working directory ...')

        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Created!")
        msgBox.setText("MODFLOW model has been created!")
        msgBox.exec_()




