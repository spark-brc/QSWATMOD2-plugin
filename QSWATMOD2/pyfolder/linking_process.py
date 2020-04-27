from builtins import str
import os
import os.path
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.PyQt.QtCore import QVariant, QCoreApplication
import processing
from processing.tools import dataobjects
from qgis.core import (
                    QgsVectorLayer, QgsField, QgsProject, QgsFeatureIterator,
                    QgsFeatureRequest, QgsLayerTreeLayer, QgsExpression, QgsFeature,
                    QgsProcessingFeedback)
import glob
import subprocess
import shutil
from datetime import datetime
import csv


def calculate_hru_area(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating 'HRU areas' ... processing")
    self.dlg.label_StepStatus.setText("Calculating 'HRU areas' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("hru_area") == -1:
        # field = QgsField("hru_area", QVariant.Int)
        field = QgsField("hru_area", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        tot_feats = self.layer.featureCount()
        count = 0
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for feat in feats:
            area = feat.geometry().area()
            feat['hru_area'] = round(area)
            self.layer.updateFeature(feat)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'hru_area' already exists ...")        
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating 'HRU areas' ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


def multipart_to_singlepart(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Disaggregating HRUs ... processing")
    self.dlg.label_StepStatus.setText("Disaggregating HRUs ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()


    QSWATMOD_path_dict = self.dirs_and_paths()
    layer = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]
    name = "dhru"
    name_ext = "dhru.gpkg"
    output_dir = QSWATMOD_path_dict['SMshps']    
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))
    # runinng the actual routine:
    params = {
        'INPUT': layer,
        'OUTPUT': output_file
    }
    processing.run("qgis:multiparttosingleparts", params)
    # defining the outputfile to be loaded into the canvas        
    dhru_shapefile = os.path.join(output_dir, name_ext)
    layer = QgsVectorLayer(dhru_shapefile, '{0} ({1})'.format("dhru", "SWAT-MODFLOW"), 'ogr')
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")
    QgsProject.instance().addMapLayer(layer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Disaggregating HRUs ... passed")
    self.dlg.label_StepStatus.setText("Step Status: ")
    self.dlg.progressBar_step.setValue(100)
    QCoreApplication.processEvents()


def create_dhru_id(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating DHRU ids ... processing")
    self.dlg.label_StepStatus.setText("Creating 'dhru_id' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("dhru (SWAT-MODFLOW)")[0]  # get active layer
    # create list of tupels of area and feature-id
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("dhru_id") == -1:
        field = QgsField("dhru_id", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()

        # BUG: featur count not working with geopackage
        tot_feats = self.layer.featureCount()
        count = 0
        #field1Id = provider.fields().indexFromName( "hru_id" ) # for SWAT+
        field1Id = provider.fields().indexFromName("HRU_ID") # for origin SWAT
        attrIdx = provider.fields().indexFromName("dhru_id")

        # aList = list( aLayer.getFeatures() )
        aList = self.layer.getFeatures()
        featureList = sorted(aList, key=lambda f: f[field1Id])
        self.layer.startEditing()
        for i, f in enumerate(featureList):
            self.layer.changeAttributeValue(f.id(), attrIdx, i+1)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'dhru_id' already exists ...")        
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating DHRU ids ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


# calculate the dhru area
def calculate_dhru_area(self): 
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating 'DHRU areas' ... processing")
    self.dlg.label_StepStatus.setText("Calculating 'DHRU areas' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("dhru (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("dhru_area") == -1:
        field = QgsField("dhru_area", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        tot_feats = self.layer.featureCount()
        count = 0
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for feat in feats:
            area = feat.geometry().area()
            feat['dhru_area'] = round(area)
            self.layer.updateFeature(feat)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'dhru_area' already exists ...")        
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating 'DHRU areas' ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


def hru_dhru(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Intersecting DHRUs by SUBs ... processing")
    self.dlg.label_StepStatus.setText("Intersecting DHRUs by SUBs ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    QSWATMOD_path_dict = self.dirs_and_paths()
    input1 = QgsProject.instance().mapLayersByName("dhru (SWAT-MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]    
    name = "hru_dhru_"
    name_ext = "hru_dhru_.gpkg"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))

    # runinng the actual routine:
    params = {
        'INPUT': input1,
        'OVERLAY': input2,
        'OUTPUT': output_file
    }
    processing.run("native:intersection", params)
    # processing.run("saga:intersect", params)
    # defining the outputfile to be loaded into the canvas        
    hru_dhru_shapefile = os.path.join(output_dir, name_ext)
    # layer = QgsVectorLayer(hru_dhru_shapefile, '{0} ({1})'.format("hru_dhru","--"), 'ogr')  # if it needs additional processing
    layer = QgsVectorLayer(hru_dhru_shapefile, '{0} ({1})'.format("hru_dhru", "SWAT-MODFLOW"), 'ogr')

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")   
    QgsProject.instance().addMapLayer(layer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Intersecting DHRUs by SUBs ... passed")
    self.dlg.label_StepStatus.setText("Step Status: ")
    self.dlg.progressBar_step.setValue(100)
    QCoreApplication.processEvents()


def hru_dhru_dissolve(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    input1 = QgsProject.instance().mapLayersByName("hru_dhru (--)")[0]
    name = "hru_dhru"
    name_ext = "hru_dhru.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))
    fieldName = "dhru_id"

    # runinng the actual routine: 
    processing.run('qgis:dissolve', input1, False, fieldName, output_file)

    # defining the outputfile to be loaded into the canvas        
    hru_dhru_shapefile = os.path.join(output_dir, name_ext)
    layer = QgsVectorLayer(hru_dhru_shapefile, '{0} ({1})'.format("hru_dhru","SWAT-MODFLOW"), 'ogr')

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")   
    QgsProject.instance().addMapLayer(layer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(layer))


# Create a field for filtering rows on area
def create_hru_dhru_filter(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Checking nulls ... processing")
    self.dlg.label_StepStatus.setText("Checking nulls ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("area_f") == -1:
        # field = QgsField("area_f", QVariant.Int)
        field = QgsField("area_f", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        # 
        tot_feats = self.layer.featureCount()
        count = 0

        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for feat in feats:
            area = feat.geometry().area()
            #score = scores[i]
            feat['area_f'] = round(area) # abs function for negative area a bug produces same dhru_id
            self.layer.updateFeature(feat)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Checking nulls ... passed")
        self.dlg.label_StepStatus.setText('Step Status: ')
        QCoreApplication.processEvents()


def delete_hru_dhru_with_zero(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Deleting nulls ... processing")
    self.dlg.label_StepStatus.setText("Deleting nulls ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression('"area_f" < 900')
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    tot_feats = self.layer.featureCount()
    count = 0
    feats = self.layer.getFeatures()
    self.layer.startEditing()
    for f in self.layer.getFeatures(request):
        self.layer.deleteFeature(f.id())
        count += 1
        provalue = round(count/tot_feats*100)
        self.dlg.progressBar_step.setValue(provalue)
        QCoreApplication.processEvents()
    self.layer.commitChanges()
    QCoreApplication.processEvents()
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Deleting nulls ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


def dhru_grid(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Intersecting DHRUs by GRIDs ... processing")
    self.dlg.label_StepStatus.setText("Intersecting DHRUs by GRIDs ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    QSWATMOD_path_dict = self.dirs_and_paths()
    input1 = QgsProject.instance().mapLayersByName("dhru (SWAT-MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    name = "dhru_grid"
    name_ext = "dhru_grid.gpkg"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))

    params = {
        'INPUT': input1,
        'OVERLAY': input2,
        'OUTPUT': output_file
    }
    processing.run("native:intersection", params)

    # defining the outputfile to be loaded into the canvas        
    dhru_grid_shapefile = os.path.join(output_dir, name_ext)
    layer = QgsVectorLayer(dhru_grid_shapefile, '{0} ({1})'.format("dhru_grid","SWAT-MODFLOW"), 'ogr')

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")   
    QgsProject.instance().addMapLayer(layer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Intersecting DHRUs by GRIDs ... passed")
    self.dlg.label_StepStatus.setText("Step Status: ")
    self.dlg.progressBar_step.setValue(100)
    QCoreApplication.processEvents()


# Create a field for filtering rows on area
def create_dhru_grid_filter(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating overlapping sizes ... processing")
    self.dlg.textEdit_sm_link_log.append('              ⮡     *** BE PATIENT!!! This step takes the most time! ***    ')

    self.dlg.label_StepStatus.setText("Calculating overlapping sizes than the setting ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("ol_area") == -1:
        field = QgsField("ol_area", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        # 
        tot_feats = self.layer.featureCount()
        count = 0

        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for feat in feats:
            area = feat.geometry().area()
            #score = scores[i]
            feat['ol_area'] = round(area)
            self.layer.updateFeature(feat)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating overlapping sizes... processing")
        self.dlg.textEdit_sm_link_log.append('              ⮡     *** HOORAY!!! Almost there! ***    ')      
        self.dlg.label_StepStatus.setText('Step Status: ')
        QCoreApplication.processEvents()


def delete_dhru_grid_with_zero(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Deleting small DHRUs ... processing")
    self.dlg.label_StepStatus.setText("Deleting small DHRUs ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    if self.dlg.groupBox_threshold.isChecked():
        threshold = self.dlg.horizontalSlider_ol_area.value()
        request = QgsFeatureRequest().setFilterExpression('"ol_area" < {}'.format(threshold))
    else:
        request = QgsFeatureRequest().setFilterExpression('"ol_area" < 900')
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    tot_feats = self.layer.featureCount()
    count = 0
    self.layer.startEditing()
    for f in self.layer.getFeatures(request):
        self.layer.deleteFeature(f.id())
        count += 1
        provalue = round(count/tot_feats*100)
        self.dlg.progressBar_step.setValue(provalue)
        QCoreApplication.processEvents()
    self.layer.commitChanges()
    QCoreApplication.processEvents()
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Deleting small DHRUs ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


# deleting existing river_grid
def deleting_river_grid(self):
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("river_grid (SWAT-MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

# Used for both SWAT and SWAT+
def river_grid(self): #step 1
    QSWATMOD_path_dict = self.dirs_and_paths()

    # Initiate rive_grid shapefile
    # if there is an existing river_grid shapefile, it will be removed
    for self.lyr in list(QgsProject.instance().mapLayers().values()):
        if self.lyr.name() == ("river_grid (SWAT-MODFLOW)"):
            QgsProject.instance().removeMapLayers([self.lyr.id()])
    if self.dlg.radioButton_mf_riv1.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (SWAT)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv1 (MODFLOW)")[0]
    elif self.dlg.radioButton_mf_riv2.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (SWAT)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv2 (MODFLOW)")[0]
    elif self.dlg.radioButton_mf_riv3.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (SWAT)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv3 (MODFLOW)")[0]
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setMaximumSize(1000, 200) # resize not working
        msgBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred) # resize not working
        msgBox.setWindowTitle("Hello?")
        msgBox.setText("Please, select one of the river options!")
        msgBox.exec_()

    name = "river_grid"
    name_ext = "river_grid.gpkg"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))

    # runinng the actual routine:
    params = { 
        'INPUT' : input1,
        'OVERLAY' : input2, 
        'OUTPUT' : output_file,
        'OVERWRITE': True
    }
    processing.run('qgis:intersection', params)
    
    # defining the outputfile to be loaded into the canvas        
    river_grid_shapefile = os.path.join(output_dir, name_ext)
    self.layer = QgsVectorLayer(river_grid_shapefile, '{0} ({1})'.format("river_grid","SWAT-MODFLOW"), 'ogr')    
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")   
    QgsProject.instance().addMapLayer(self.layer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(self.layer))

# 
def river_grid_delete_NULL(self):
    layer = QgsProject.instance().mapLayersByName("river_grid (SWAT-MODFLOW)")[0]
    provider = layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression("grid_id IS NULL" )
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    request2 = QgsFeatureRequest().setFilterExpression("subbasin IS NULL" )
    request2.setSubsetOfAttributes([])
    request2.setFlags(QgsFeatureRequest.NoGeometry)

    layer.startEditing()
    for f in layer.getFeatures(request):
        layer.deleteFeature(f.id())
    for f in layer.getFeatures(request2):
        layer.deleteFeature(f.id())
    layer.commitChanges()


# SWAT+
# Create a field for filtering rows on area
def create_river_grid_filter(self):
    self.layer = QgsProject.instance().mapLayersByName("river_grid (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    field = QgsField("ol_length", QVariant.Int)
    #field = QgsField("ol_area", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()

    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
        length = feat.geometry().length()
        #score = scores[i]
        feat['ol_length'] = length
        self.layer.updateFeature(feat)
    self.layer.commitChanges()


def delete_river_grid_with_threshold(self):
    self.layer = QgsProject.instance().mapLayersByName("river_grid (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression('"rgrid_len" < 0.5')
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    self.layer.startEditing()
    for f in self.layer.getFeatures(request):
        self.layer.deleteFeature(f.id())
    self.layer.commitChanges()


def rgrid_len(self):

    self.layer = QgsProject.instance().mapLayersByName("river_grid (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    field = QgsField("rgrid_len", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()
    
    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
        length = feat.geometry().length()
        #score = scores[i]
        feat['rgrid_len'] = length
        self.layer.updateFeature(feat)
    self.layer.commitChanges()


# SWAT+
def river_sub(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    input1 = QgsProject.instance().mapLayersByName("river_grid (SWAT-MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
    name = "river_sub_union"
    name_ext = "river_sub_union.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))

    processing.run('qgis:union', input1, input2, output_file)

    # defining the outputfile to be loaded into the canvas        
    river_sub_union_shapefile = os.path.join(output_dir, name_ext)
    layer = QgsVectorLayer(river_sub_union_shapefile, '{0} ({1})'.format("river_sub","SWAT-MODFLOW"), 'ogr')
    layer = QgsProject.instance().addMapLayer(layer)   

# SWAT+
def river_sub_delete_NULL(self):
    layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    provider = layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression("grid_id IS NULL" )
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    request2 = QgsFeatureRequest().setFilterExpression("subbasin IS NULL" )
    request2.setSubsetOfAttributes([])
    request2.setFlags(QgsFeatureRequest.NoGeometry)

    layer.startEditing()
    for f in layer.getFeatures(request):
        layer.deleteFeature(f.id())
    for f in layer.getFeatures(request2):
        layer.deleteFeature(f.id())

    layer.commitChanges()

# SWAT+
def _create_river_sub_filter(self):
    self.layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    field = QgsField("ol_length", QVariant.Int)
    #field = QgsField("ol_area", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()

    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
        length = feat.geometry().length()
        #score = scores[i]
        feat['ol_length'] = length
        self.layer.updateFeature(feat)
    self.layer.commitChanges()

def _delete_river_sub_with_threshold(self):
    self.layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression('"ol_length" < 1.0')
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    self.layer.startEditing()
    for f in self.layer.getFeatures(request):
        self.layer.deleteFeature(f.id())
    self.layer.commitChanges()


def _rgrid_len(self):

    self.layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsField, QgsExpression, QgsFeature

    field = QgsField("rgrid_len", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()
    
    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
       length = feat.geometry().length()
       #score = scores[i]
       feat['rgrid_len'] = length
       self.layer.updateFeature(feat)
    self.layer.commitChanges()

""" 
/********************************************************************************************
 *                                                                                          *
 *                              Export GIS Table for original SWAT                          *
 *                                                                                          *
 *******************************************************************************************/
"""

def export_hru_dhru(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    #sort by hru_id and then by dhru_id and save down 
    #read in the hru_dhru shapefile
    layer = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]

    # Get the index numbers of the fields
    dhru_id_index = layer.dataProvider().fields().indexFromName("dhru_id")
    dhru_area_index = layer.dataProvider().fields().indexFromName("dhru_area")
    hru_id_index = layer.dataProvider().fields().indexFromName("HRU_ID")
    hru_area_index = layer.dataProvider().fields().indexFromName("hru_area")
    subbasin_index = layer.dataProvider().fields().indexFromName("Subbasin")

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())

    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(hru_id_index, dhru_id_index))
    dhru_number = len(l_sorted) # number of lines


    # Get hru number
    hru =[]
    # slice the column of interest in order to count the number of hrus
    for h in l:
        hru.append(h[hru_id_index])

    # Wow nice!!!
    hru_unique = []        
    for h in hru:
        if h not in hru_unique:
            hru_unique.append(h)
    hru_number = max(hru_unique)

    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "hru_dhru"
    output_dir = QSWATMOD_path_dict['Table']
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        first_row = [str(dhru_number)]  # prints the dhru number to the first row
        second_row = [str(hru_number)]  # prints the hru number to the second row
        third_row = ["dhru_id dhru_area hru_id subbasin hru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        
        for item in l_sorted:
        
        # Write item to outcsv. the order represents the output order
            writer.writerow([item[dhru_id_index], item[dhru_area_index], item[hru_id_index],
                item[subbasin_index], item[hru_area_index]])


def export_dhru_grid(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]

    # Get the index numbers of the fields
    dhru_id_index = layer.dataProvider().fields().indexFromName("dhru_id")
    dhru_area_index = layer.dataProvider().fields().indexFromName("dhru_area")
    grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
    overlap_area_index = layer.dataProvider().fields().indexFromName("ol_area")

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(grid_id_index, dhru_id_index))

    #l.sort(key=itemgetter(6))
    #add a counter as index for the dhru id
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).

    cell_size = delr * delc
    number_of_grids = nrow * ncol

    for i in l_sorted:     
        i.append(str(int(cell_size))) # area of the grid
        
    ''' I don't know what this is for
    gridcell =[]
    # slice the column of interest in order to count the number of grid cells
    for h in l_sorted:
        gridcell.append(h[6])

    gridcell_unique = []    
        
    for h in gridcell:
        if h not in gridcell_unique:
            gridcell_unique.append(h)

    gridcell_number = len(gridcell_unique) # number of hrus
    '''

    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "dhru_grid"
    output_dir = QSWATMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dhru number to the file
        second_row = [str(number_of_grids)] # prints the total number of grid cells
        third_row = ["grid_id grid_area dhru_id overlap_area dhru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([
                item[grid_id_index], item[overlap_area_index + 1],
                item[dhru_id_index], item[overlap_area_index], item[dhru_area_index]])


def export_grid_dhru(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]
    layer2 = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]

    # Get max number of dhru id
    dhrus2 = [f.attribute("dhru_id") for f in layer2.getFeatures()]

    # Get the index numbers of the fields
    dhru_id_index = layer.dataProvider().fields().indexFromName("dhru_id")
    dhru_area_index = layer.dataProvider().fields().indexFromName("dhru_area")
    grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
    overlap_area_index = layer.dataProvider().fields().indexFromName("ol_area")

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(dhru_id_index, grid_id_index))

    #l.sort(key=itemgetter(6))
    #add a counter as index for the dhru id
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).

    cell_size = delr * delc
    number_of_grids = nrow * ncol

    for i in l_sorted:
        i.append(str(int(cell_size))) # area of the grid
        
    # # It
    # dhru_id =[]
    # # slice the column of interest in order to count the number of grid cells
    # for h in l_sorted:
    #   dhru_id.append(h[dhru_id_index])

    # dhru_id_unique = []    
        
    # for h in dhru_id:
    #   if h not in dhru_id_unique:
    #     dhru_id_unique.append(h)


    # It seems we need just total number of DHRUs not the one used in study area
    # dhru_number = len(dhru_id_unique) # number of dhrus
    dhru_number = max(dhrus2) # number of dhrus
    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "grid_dhru"
    output_dir = QSWATMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dnumber of lines with information
        second_row = [str(dhru_number)] # prints the total number of dhru
        third_row = [str(nrow)] # prints the row number to the file
        fourth_row = [str(ncol)] # prints the column number to the file     
        fifth_row = ["grid_id grid_area dhru_id overlap_area dhru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        writer.writerow(fourth_row)
        writer.writerow(fifth_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[grid_id_index], item[overlap_area_index + 1],
                item[dhru_id_index], item[overlap_area_index], item[dhru_area_index]])


def export_rgrid_len(self):
    QSWATMOD_path_dict = self.dirs_and_paths()  
    ### sort by dhru_id and then by grid and save down ### 
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("river_grid (SWAT-MODFLOW)")[0]

    # Get the index numbers of the fields
    grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
    subbasin_index = layer.dataProvider().fields().indexFromName("Subbasin")
    ol_length_index = layer.dataProvider().fields().indexFromName("ol_length")
    
    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(grid_id_index))
    
    info_number = len(l_sorted) # number of lines
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "river_grid"
    output_dir = QSWATMOD_path_dict['Table']   
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dhru number to the file
        second_row = ["grid_id subbasin rgrid_len"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        for item in l_sorted:
            # Write item to outcsv. the order represents the output order
            writer.writerow([item[grid_id_index], item[subbasin_index], item[ol_length_index]])



def run_CreateSWATMF(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    output_dir = QSWATMOD_path_dict['Table']
    #Out_folder_temp = self.dlg.lineEdit_output_folder.text()
    #swatmf = os.path.normpath(output_dir + "/" + "SWATMF_files")
    name = "CreateSWATMF.exe"
    exe_file = os.path.normpath(os.path.join(output_dir, name))
    #os.startfile(File_Physical)    
    p = subprocess.Popen(exe_file , cwd = output_dir) # cwd -> current working directory    
    p.wait()

def copylinkagefiles(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    source_dir = QSWATMOD_path_dict['Table']
    dest_dir = QSWATMOD_path_dict['SMfolder']
    for filename in glob.glob(os.path.join(source_dir, '*.txt')):
        shutil.copy(filename, dest_dir)




'''
grid_id = []
for feat in features:
    attrs = feat.attributes()
    grid_id.append(attrs[grid_id_index])

info_number = len(l) # Number of observation cells



# ------------ Export Data to file -------------- #
name = "modflow.obs"
output_dir = SMfolder
output_file = os.path.normpath(os.path.join(output_dir, name)
with open(output_file, "w", newline='') as f:
    writer = csv.writer(f, delimiter = '\t')
    first_row = ["test"]
    second_row = [str(info_number)]
    for item in grid_id:
        writer.writerow([item])
'''

    
#*******************************************************************************************                                                                                        *
#                                                                                           *
#                               Export GIS Table for SWAT+ MODFLOW
#                          
#*******************************************************************************************/


def _export_hru_dhru(self): 
    #sort by hru_id and then by dhru_id and save down 
    #read in the hru_dhru shapefile
    layer = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]
    
    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(2, 0))
    dhru_number = len(l_sorted) # number of lines


    # Get hru number
    hru =[]
    # slice the column of interest in order to count the number of hrus
    for h in l:
        hru.append(h[0])
 
    # Wow nice!!!
    hru_unique = []    
        
    for h in hru:
        if h not in hru_unique:
          hru_unique.append(h)
    hru_number =  max(hru_unique)


#-----------------------------------------------------------------------#
    # exporting the file 
    name = "hru_dhru"
    output_dir = QSWATMOD_path_dict['Table']
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(dhru_number)] # prints the dhru number to the first row
        second_row = [str(hru_number)] # prints the hru number to the second row
        
        third_row = ["dhru_id dhru_area hru_id subbasin hru_area"]
        
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        
        for item in l_sorted:
        
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[2], item[3], item[0], item[4], item[1]])


def _export_dhru_grid(self):
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(9, 2))
    
    #l.sort(key=itemgetter(6))
    #add a counter as index for the dhru id
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).

    cell_size = delr * delc
    number_of_grids = nrow * ncol

    for i in l_sorted:     
        i.append(str(int(cell_size))) # area of the grid
        
    ''' I don't know what this is for
    gridcell =[]
    # slice the column of interest in order to count the number of grid cells
    for h in l_sorted:
        gridcell.append(h[6])
  
    gridcell_unique = []    
        
    for h in gridcell:
        if h not in gridcell_unique:
          gridcell_unique.append(h)
    
    gridcell_number = len(gridcell_unique) # number of hrus
    '''

    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "dhru_grid"
    output_dir = QSWATMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dhru number to the file
        second_row = [str(number_of_grids)] # prints the total number of grid cells
        third_row = ["grid_id grid_area dhru_id overlap_area dhru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[9], item[11], item[2], item[10], item[3]])



def _export_grid_dhru(self):    
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(2, 9))
    
    #l.sort(key=itemgetter(6))
    #add a counter as index for the dhru id
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).

    cell_size = delr * delc
    number_of_grids = nrow * ncol

    for i in l_sorted:     
        i.append(str(int(cell_size))) # area of the grid
        

    dhru_id =[]
    # slice the column of interest in order to count the number of grid cells
    for h in l_sorted:
        dhru_id.append(h[2])
  
    dhru_id_unique = []    
        
    for h in dhru_id:
        if h not in dhru_id_unique:
          dhru_id_unique.append(h)
    
    dhru_number = len(dhru_id_unique) # number of dhrus
    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "grid_dhru"
    output_dir = QSWATMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dnumber of lines with information
        second_row = [str(dhru_number)] # prints the total number of dhru
        third_row = [str(nrow)] # prints the row number to the file
        fourth_row = [str(ncol)] # prints the column number to the file     
        fifth_row = ["grid_id grid_area dhru_id overlap_area dhru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        writer.writerow(fourth_row)
        writer.writerow(fifth_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[9], item[11], item[2], item[10], item[3]])


def _export_rgrid_len(self): 

    """
    sort by dhru_id and then by grid and save down 
    """
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    
    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(22))
    
    info_number = len(l_sorted) # number of lines
            
    #-----------------------------------------------------------------------#
    # exporting the file 
    
    name = "river_grid"
    output_dir = QSWATMOD_path_dict['Table']   
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dhru number to the file
        
        second_row = ["grid_id subbasin rgrid_len"]
        
        writer.writerow(first_row)
        writer.writerow(second_row)
        
        for item in l_sorted:
        
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[22], item[23], item[25]])



'''
grid_id = []
for feat in features:
    attrs = feat.attributes()
    grid_id.append(attrs[grid_id_index])

info_number = len(l) # Number of observation cells



# ------------ Export Data to file -------------- #
name = "modflow.obs"
output_dir = QSWATMOD_path_dict['SMfolder']
output_file = os.path.normpath(os.path.join(output_dir, name_ext))
with open(output_file, "w", newline='') as f:
    writer = csv.writer(f, delimiter = '\t')
    first_row = ["test"]
    second_row = [str(info_number)]
    for item in grid_id:
        writer.writerow([item])
'''


def convert_r_v(self):
    input1 = QgsProject.instance().mapLayersByName("HRU_swat")[0]
    fieldName = "hru_id"
            
    name1 = "hru_S"
    name_ext1 = "hru_S.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file1 = os.path.normpath(os.path.join(output_dir, name_ext1))

    # runinng the actual routine: 
    processing.run('gdalogr:polygonize', input1, fieldName, output_file1)

    # defining the outputfile to be loaded into the canvas        
    hru_shapefile = os.path.join(output_dir, name_ext1)
    layer = QgsVectorLayer(hru_shapefile, '{0} ({1})'.format("hru","--"), 'ogr')
    layer = QgsProject.instance().addMapLayer(layer)

def dissolve_hru(self):
    import ntpath
    import posixpath

    input2 = QgsProject.instance().mapLayersByName("hru (--)")[0]
    fieldName = "hru_id"
            
    name2 = "hru_SM"
    name_ext2 = "hru_SM.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file2 = os.path.normpath(os.path.join(output_dir, name_ext2))

    # runinng the actual routine: 

    processing.run('qgis:dissolve', input2,False, fieldName, output_file2)
    # defining the outputfile to be loaded into the canvas        
    hru_shapefile = os.path.join(output_dir, name_ext2)
    layer = QgsVectorLayer(hru_shapefile, '{0} ({1})'.format("hru","SWAT"), 'ogr')
    layer = QgsProject.instance().addMapLayer(layer)

    if os.name == 'nt':
        hru_shp = ntpath.join(output_dir, name2 + ".shp")
    else:
        hru_shp = posixpath.join(output_dir, name2 + ".shp")
    self.dlg.lineEdit_hru_rasterfile.setText(hru_shp)  