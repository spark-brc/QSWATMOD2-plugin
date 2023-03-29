# -*- coding: utf-8 -*-
from builtins import zip
from builtins import str
from builtins import range
from qgis.core import (
                        QgsProject, QgsLayerTreeLayer, QgsVectorFileWriter, QgsVectorLayer, QgsRasterLayer,
                        QgsField, QgsRasterBandStats, QgsColorRampShader, QgsRasterShader,
                        QgsSingleBandPseudoColorRenderer, QgsMapSettings, QgsMapRendererCustomPainterJob,
                        QgsRectangle)
from qgis.PyQt import QtCore, QtGui, QtSql
import datetime
import pandas as pd
import os
import glob
from PyQt5.QtGui import QIcon, QColor, QImage, QPainter, QPen, QFont
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant, QCoreApplication, QSize, Qt, QPoint, QRect
import calendar
import processing
from qgis.gui import QgsMapCanvas
import glob
from PIL import Image


def read_mf_recharge_dates(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m-%d-%Y")
    
    # Create swatmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("swatmf_results"):
        swatmf_results = root.findGroup("swatmf_results")
    else:
        swatmf_results = root.insertGroup(0, "swatmf_results")

    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = input1.dataProvider()

    if self.dlg.checkBox_recharge.isChecked() and self.dlg.radioButton_mf_results_d.isChecked():
        filename = "swatmf_out_MF_recharge"

        # Open "swatmf_out_MF_recharge" file
        y = ("MODFLOW", "--Calculated", "daily") # Remove unnecssary lines
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        # data1 = [x.split() for x in data] # make each line a list
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y")  # Change startDate format
        dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]
        self.dlg.comboBox_mf_results_sdate.clear()
        self.dlg.comboBox_mf_results_sdate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.clear()
        self.dlg.comboBox_mf_results_edate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.setCurrentIndex(len(dateList)-1)

        # Copy mf_grid shapefile to swatmf_results tree
        name_ext = "mf_rch_daily.gpkg"
        output_dir = QSWATMOD_path_dict['SMshps']

        # Check if there is an exsting mf_recharge shapefile
        if not any(lyr.name() == ("mf_rch_daily") for lyr in list(QgsProject.instance().mapLayers().values())):
            mf_rch_shapfile = os.path.join(output_dir, name_ext)
            # overwrite option
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            QgsVectorFileWriter.writeAsVectorFormat(input1, mf_rch_shapfile, options)
            layer = QgsVectorLayer(mf_rch_shapfile, '{0}'.format("mf_rch_daily"), 'ogr')
            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            swatmf_results = root.findGroup("swatmf_results")   
            QgsProject.instance().addMapLayer(layer, False)
            swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Created!")
            msgBox.setText("'mf_rch_daily.gpkg' file is created in 'swatmf_results' group!")
            msgBox.exec_()

    elif self.dlg.checkBox_recharge.isChecked() and self.dlg.radioButton_mf_results_m.isChecked():
        filename = "swatmf_out_MF_recharge_monthly"

        # Open "swatmf_out_MF_recharge" file
        y = ("Monthly") # Remove unnecssary lines
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        # data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()
        self.dlg.comboBox_mf_results_sdate.clear()
        self.dlg.comboBox_mf_results_sdate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.clear()
        self.dlg.comboBox_mf_results_edate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.setCurrentIndex(len(dateList)-1)

        # Copy mf_grid shapefile to swatmf_results tree
        name_ext = "mf_rch_monthly.gpkg"
        output_dir = QSWATMOD_path_dict['SMshps']

        # Check if there is an exsting mf_recharge shapefile
        if not any(lyr.name() == ("mf_rch_monthly") for lyr in list(QgsProject.instance().mapLayers().values())):
            mf_rch_shapfile = os.path.join(output_dir, name_ext)
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            QgsVectorFileWriter.writeAsVectorFormat(input1, mf_rch_shapfile, options)
            layer = QgsVectorLayer(mf_rch_shapfile, '{0}'.format("mf_rch_monthly"), 'ogr')

            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            swatmf_results = root.findGroup("swatmf_results")   
            QgsProject.instance().addMapLayer(layer, False)
            swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Created!")
            msgBox.setText("'mf_rch_monthly.gpkg' file is created in 'swatmf_results' group!")
            msgBox.exec_()      

    elif self.dlg.checkBox_recharge.isChecked() and self.dlg.radioButton_mf_results_y.isChecked():
        filename = "swatmf_out_MF_recharge_yearly"

        # Open "swatmf_out_MF_recharge" file
        y = ("Yearly") # Remove unnecssary lines
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("year:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        # data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'A').strftime("%Y").tolist()
        self.dlg.comboBox_mf_results_sdate.clear()
        self.dlg.comboBox_mf_results_sdate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.clear()
        self.dlg.comboBox_mf_results_edate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.setCurrentIndex(len(dateList)-1)

        # Copy mf_grid shapefile to swatmf_results tree
        name_ext = "mf_rch_yearly.gpkg"
        output_dir = QSWATMOD_path_dict['SMshps']

        # Check if there is an exsting mf_recharge shapefile
        if not any(lyr.name() == ("mf_rch_yearly") for lyr in list(QgsProject.instance().mapLayers().values())):
            mf_rch_shapfile = os.path.join(output_dir, name_ext)
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            QgsVectorFileWriter.writeAsVectorFormat(input1, mf_rch_shapfile, options)
            layer = QgsVectorLayer(mf_rch_shapfile, '{0}'.format("mf_rch_yearly"), 'ogr')

            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            swatmf_results = root.findGroup("swatmf_results")   
            QgsProject.instance().addMapLayer(layer, False)
            swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Created!")
            msgBox.setText("'mf_rch_yearly.gpkg' file is created in 'swatmf_results' group!")
            msgBox.exec_()      

    else:
        self.dlg.comboBox_mf_results_sdate.clear()


def export_mf_recharge (self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m-%d-%Y")

    # Open "swatmf_out_MF_recharge" file
    y = ("MODFLOW", "--Calculated", "daily", "Monthly", "Yearly") # Remove unnecssary lines

    if self.dlg.radioButton_mf_results_d.isChecked():
        filename = "swatmf_out_MF_recharge"
        self.layer = QgsProject.instance().mapLayersByName("mf_rch_daily")[0]
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
        dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]
    elif self.dlg.radioButton_mf_results_m.isChecked():
        filename = "swatmf_out_MF_recharge_monthly"
        self.layer = QgsProject.instance().mapLayersByName("mf_rch_monthly")[0]
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
        date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq ='M').strftime("%b-%Y").tolist()
    elif self.dlg.radioButton_mf_results_y.isChecked():
        filename = "swatmf_out_MF_recharge_yearly"
        self.layer = QgsProject.instance().mapLayersByName("mf_rch_yearly")[0]
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("year:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq='A').strftime("%Y").tolist()
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, select one of the time options!")
        msgBox.exec_()  

    selectedSdate = self.dlg.comboBox_mf_results_sdate.currentText()
    selectedEdate = self.dlg.comboBox_mf_results_edate.currentText()

    # Reverse step
    dateSidx = dateList.index(selectedSdate)
    dateEidx = dateList.index(selectedEdate)
    dateList_f = dateList[dateSidx:dateEidx+1]

    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0] # Put this here to know number of features

    per = 0
    self.dlg.progressBar_mf_results.setValue(0)    
    for selectedDate in dateList_f:

        # Reverse step
        dateIdx = dateList.index(selectedDate)

        #only
        onlyDate_lookup = onlyDate[dateIdx]
        if self.dlg.radioButton_mf_results_d.isChecked():       
            for num, line in enumerate(data1, 1):
                if line[0] == "Day:" in line and line[1] == onlyDate_lookup in line:
                    ii = num # Starting line
        elif self.dlg.radioButton_mf_results_m.isChecked():
            # Find year 
            dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
            year = dt.year
            for num, line in enumerate(data1, 1):
                if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                    ii = num # Starting line
        elif self.dlg.radioButton_mf_results_y.isChecked():     
            for num, line in enumerate(data1, 1):
                if line[0] == "year:" in line and line[1] == onlyDate_lookup in line:
                    ii = num # Starting line

        mf_rchs = []
        count = 0
        while count < input1.featureCount():
            for jj in range(len(data1[ii])):
                mf_rchs.append(float(data1[ii][jj]))
                count += 1
            ii += 1

        provider = self.layer.dataProvider()
        if self.layer.dataProvider().fields().indexFromName(selectedDate) == -1:
            field = QgsField(selectedDate, QVariant.Double, 'double', 20, 5)
            provider.addAttributes([field])
            self.layer.updateFields()

        mf_rchs_idx = provider.fields().indexFromName(selectedDate)

        tot_feats = self.layer.featureCount()
        count = 0
        # Get features (Find out a way to change attribute values using another field)
        feats = self.layer.getFeatures()
        self.layer.startEditing()

        # add row number
        for f, mf_rch in zip(feats, mf_rchs):
            self.layer.changeAttributeValue(f.id(), mf_rchs_idx, mf_rch)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_rch_head.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()

        # Update progress bar         
        per += 1
        progress = round((per / len(dateList_f)) *100)
        self.dlg.progressBar_mf_results.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("mf_recharge results were exported successfully!")
    msgBox.exec_()



def get_rech_avg_m_df(self):
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Reading ...")
    msgBox.setText("We are going to read the 'swatmf_out_MF_recharge_monthly file ...")
    msgBox.exec_()

    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    exported_folder = QSWATMOD_path_dict["exported_files"]
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines
    filename = "swatmf_out_MF_recharge_monthly"
    # self.layer = QgsProject.instance().mapLayersByName("mf_nitrate_monthly")[0]
    with open(os.path.join(wd, filename), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
    date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
    onlyDate = [x[1] for x in date] # Only date
    data1 = [x.split() for x in data] # make each line a list
    dateList = pd.date_range(startDate, periods=len(onlyDate), freq ='M').strftime("%b-%Y").tolist()

    selectedSdate = self.dlg.comboBox_mf_results_sdate.currentText()
    selectedEdate = self.dlg.comboBox_mf_results_edate.currentText()
    # Reverse step
    dateSidx = dateList.index(selectedSdate)
    dateEidx = dateList.index(selectedEdate)
    dateList_f = dateList[dateSidx:dateEidx+1]
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0] # Put this here to know number of features

    big_df = pd.DataFrame()
    datecount = 0
    for selectedDate in dateList_f:
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
        year = dt.year
        layerN = self.dlg.comboBox_rt_layer.currentText()
        for num, line in enumerate(data1, 1):
            if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                ii = num # Starting line
        mf_rchs = []
        hdcount = 0
        while hdcount < input1.featureCount():
            for kk in range(len(data1[ii])):
                mf_rchs.append(float(data1[ii][kk]))
                hdcount += 1
            ii += 1
        s = pd.Series(mf_rchs, name=datetime.datetime.strptime(selectedDate, "%b-%Y").strftime("%Y-%m-%d"))
        big_df = pd.concat([big_df, s], axis=1)
        datecount +=1
        provalue = round(datecount/len(dateList_f)*100)
        self.dlg.progressBar_rch_head.setValue(provalue)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    big_df = big_df.T
    big_df.index = pd.to_datetime(big_df.index)
    mbig_df = big_df.groupby(big_df.index.month).mean()
    mbig_df.to_csv(os.path.join(exported_folder, "mf_rch_avg_mon.csv"), index=False)


    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("'mf_rch_avg_mon.csv' was exported ...")
    msgBox.exec_()
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exporting ...")
    msgBox.setText("It will begin in exporting data to the shapefile.")
    msgBox.exec_()
    return mbig_df


def create_rech_avg_mon_shp(self):
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    QSWATMOD_path_dict = self.dirs_and_paths()

    # Copy mf_grid shapefile to swatmf_results tree
    name = "mf_rch_avg_mon"
    name_ext = "mf_rch_avg_mon.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    # Check if there is an exsting mf_head shapefile
    if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
        mf_rch_shp = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, mf_rch_shp,
            "utf-8", input1.crs(), "ESRI Shapefile")
        layer = QgsVectorLayer(mf_rch_shp, '{0}'.format(name), 'ogr')
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        swatmf_results = root.findGroup("swatmf_results")
        QgsProject.instance().addMapLayer(layer, False)
        swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Created!")
        msgBox.setText("'mf_rch_avg_mon.shp' file has been created in 'swatmf_results' group!")
        msgBox.exec_()
        msgBox = QMessageBox()

def selected_mf_mon(self):
    selected_months = []
    if self.dlg.checkBox_hr_jan.isChecked():
        selected_months.append(1)
    if self.dlg.checkBox_hr_feb.isChecked():
        selected_months.append(2)
    if self.dlg.checkBox_hr_mar.isChecked():
        selected_months.append(3)
    if self.dlg.checkBox_hr_apr.isChecked():
        selected_months.append(4)
    if self.dlg.checkBox_hr_may.isChecked():
        selected_months.append(5)
    if self.dlg.checkBox_hr_jun.isChecked():
        selected_months.append(6)
    if self.dlg.checkBox_hr_jul.isChecked():
        selected_months.append(7)
    if self.dlg.checkBox_hr_aug.isChecked():
        selected_months.append(8)
    if self.dlg.checkBox_hr_sep.isChecked():
        selected_months.append(9)
    if self.dlg.checkBox_hr_oct.isChecked():
        selected_months.append(10)
    if self.dlg.checkBox_hr_nov.isChecked():
        selected_months.append(11)    
    if self.dlg.checkBox_hr_dec.isChecked():
        selected_months.append(12)
    return selected_months


def export_mf_rch_avg_m(self):
    mbig_df = get_rech_avg_m_df(self)
    selected_months = selected_mf_mon(self)
    self.layer = QgsProject.instance().mapLayersByName("mf_rch_avg_mon")[0]
    per = 0
    self.dlg.progressBar_mf_results.setValue(0)
    for m in selected_months:
        m_vals = mbig_df.loc[m, :]
        QCoreApplication.processEvents()
        mon_nam = calendar.month_abbr[m]

        provider = self.layer.dataProvider()
        if self.layer.dataProvider().fields().indexFromName(mon_nam) == -1:
            field = QgsField(mon_nam, QVariant.Double, 'double', 20, 5)
            provider.addAttributes([field])
            self.layer.updateFields()
        mf_hds_idx = provider.fields().indexFromName(mon_nam)
        
        tot_feats = self.layer.featureCount()
        count = 0        
        # Get features (Find out a way to change attribute values using another field)
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        for f, mf_hd in zip(feats, m_vals):
            self.layer.changeAttributeValue(f.id(), mf_hds_idx, mf_hd)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_rch_head.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()

        # Update progress bar 
        per += 1
        progress = round((per / len(selected_months)) *100)
        self.dlg.progressBar_mf_results.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("mf_rch_avg_mon results were exported successfully!")
    msgBox.exec_()


def read_vector_maps_hydrology(self):
    layers = [lyr.name() for lyr in list(QgsProject.instance().mapLayers().values())]
    available_layers = [
                'mf_hd_monthly',
                'mf_hd_yearly',
                'mf_rch_monthly',
                'mf_rch_yearly',
                'mf_rech_avg_mon',
                'base_rd_avg_mon_rech_f'
                ]
    self.dlg.comboBox_vector_lyrs_mf.clear()
    self.dlg.comboBox_vector_lyrs_mf.addItems(available_layers)
    for i in range(len(available_layers)):
        self.dlg.comboBox_vector_lyrs_mf.model().item(i).setEnabled(False)
    for i in available_layers:
        for j in layers:
            if i == j:
                idx = available_layers.index(i)
                self.dlg.comboBox_vector_lyrs_mf.model().item(idx).setEnabled(True)
    self.dlg.mColorButton_min_rmap.defaultColor()
    self.dlg.mColorButton_max_rmap.defaultColor()


def cvt_vtr_hydrology(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    selectedVector = self.dlg.comboBox_vector_lyrs_mf.currentText()
    layer = QgsProject.instance().mapLayersByName(str(selectedVector))[0]

    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (y spacing)
        delc = float(data[3][1]) # is the cell width along columns (x spacing).

    # get extent
    ext = layer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)

    fdnames = [
                field.name() for field in layer.dataProvider().fields() if not (
                field.name() == 'fid' or
                field.name() == 'id' or
                field.name() == 'xmin' or
                field.name() == 'xmax' or
                field.name() == 'ymin' or
                field.name() == 'ymax' or
                field.name() == 'grid_id' or
                field.name() == 'row' or
                field.name() == 'col' or
                field.name() == 'elev_mf'
                )
                    ]

    # Create swatmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("swatmf_results"):
        swatmf_results = root.findGroup("swatmf_results")
    else:
        swatmf_results = root.insertGroup(0, "swatmf_results")
    
    if root.findGroup(selectedVector):
        rastergroup = root.findGroup(selectedVector)
    else:
        rastergroup = swatmf_results.insertGroup(0, selectedVector)
    per = 0
    self.dlg.progressBar_cvt_vtr_mf.setValue(0)
    for fdnam in fdnames:
        QCoreApplication.processEvents()
        nodata = float(self.dlg.lineEdit_nodata_mf.text())
        mincolor = self.dlg.mColorButton_min_map_mf.color().name()
        maxcolor = self.dlg.mColorButton_max_map_mf.color().name()
        name = fdnam
        name_ext = "{}.tif".format(name)
        output_dir = QSWATMOD_path_dict['SMshps']
        # create folder for each layer output
        rasterpath = os.path.join(output_dir, selectedVector)
        if not os.path.exists(rasterpath):
            os.makedirs(rasterpath)
        output_raster = os.path.join(rasterpath, name_ext)
        params = {
            'INPUT': layer,
            'FIELD': fdnam,
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': nodata,
            'DATA_TYPE': 5, #Float32
            'OUTPUT': output_raster
        }
        processing.run("gdal:rasterize", params)
        rasterlayer = QgsRasterLayer(output_raster, '{0} ({1})'.format(fdnam, selectedVector))
        QgsProject.instance().addMapLayer(rasterlayer, False)
        rastergroup.insertChildNode(0, QgsLayerTreeLayer(rasterlayer))
        stats = rasterlayer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
        rmin = stats.minimumValue
        rmax = stats.maximumValue
        fnc = QgsColorRampShader()
        lst = [QgsColorRampShader.ColorRampItem(rmin, QColor(mincolor)), QgsColorRampShader.ColorRampItem(rmax, QColor(maxcolor))]
        fnc.setColorRampItemList(lst)
        fnc.setColorRampType(QgsColorRampShader.Interpolated)
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)
        renderer = QgsSingleBandPseudoColorRenderer(rasterlayer.dataProvider(), 1, shader)
        rasterlayer.setRenderer(renderer)
        rasterlayer.triggerRepaint()

        # create image
        img = QImage(QSize(800, 800), QImage.Format_ARGB32_Premultiplied)
        # set background color
        # bcolor = QColor(255, 255, 255, 255)
        bcolor = QColor(255, 255, 255, 0)
        img.fill(bcolor.rgba())
        # create painter
        p = QPainter()
        p.begin(img)
        p.setRenderHint(QPainter.Antialiasing)
        # create map settings
        ms = QgsMapSettings()
        ms.setBackgroundColor(bcolor)
        # set layers to render
        flayer = QgsProject.instance().mapLayersByName(rasterlayer.name())
        ms.setLayers([flayer[0]])
        # set extent
        rect = QgsRectangle(ms.fullExtent())
        rect.scale(1.1)
        ms.setExtent(rect)
        # set ouptut size
        ms.setOutputSize(img.size())
        # setup qgis map renderer
        render = QgsMapRendererCustomPainterJob(ms, p)
        render.start()
        render.waitForFinished()
        # get timestamp
        p.drawImage(QPoint(), img)
        pen = QPen(Qt.red)
        pen.setWidth(2)
        p.setPen(pen)

        font = QFont()
        font.setFamily('Times')
        # font.setBold(True)
        font.setPointSize(18)
        p.setFont(font)
        # p.setBackground(QColor('sea green')) doesn't work    
        p.drawText(QRect(0, 0, 800, 800), Qt.AlignRight | Qt.AlignBottom, fdnam)
        p.end()

        # save the image
        img.save(os.path.join(rasterpath, '{:03d}_{}.jpg'.format(per, fdnam)))
        
        # Update progress bar         
        per += 1
        progress = round((per / len(fdnames)) *100)
        self.dlg.progressBar_cvt_vtr_mf.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    duration = self.dlg.doubleSpinBox_ani_mf_time.value()
    # filepaths
    fp_in = os.path.join(rasterpath, '*.jpg')
    fp_out = os.path.join(rasterpath, '{}.gif'.format(selectedVector))
    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
    fimg, *fimgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
    fimg.save(fp=fp_out, format='GIF', append_images=fimgs,
            save_all=True, duration=duration*1000, loop=0, transparency=0)
    
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Coverted!")
    msgBox.setText("Fields from {} were converted successfully!".format(selectedVector))
    msgBox.exec_()

    questionBox = QMessageBox()
    questionBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    reply = QMessageBox.question(
                    questionBox, 'Open?', 
                    'Do you want to open the animated gif file?', QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        os.startfile(os.path.join(rasterpath, '{}.gif'.format(selectedVector)))
