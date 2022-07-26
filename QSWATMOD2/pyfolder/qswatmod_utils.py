import numpy as np
import datetime
import os

class ObjFns:
    def __init__(self) -> None:
        pass
        
    # def obj_fns(obj_fn, sims, obds):
    #     return obj_fn(sims, obds)
    @staticmethod
    def nse(sims, obds):
        """Nash-Sutcliffe Efficiency (NSE) as per `Nash and Sutcliffe, 1970
        <https://doi.org/10.1016/0022-1694(70)90255-6>`_.

        :Calculation Details:
            .. math::
            E_{\\text{NSE}} = 1 - \\frac{\\sum_{i=1}^{N}[e_{i}-s_{i}]^2}
            {\\sum_{i=1}^{N}[e_{i}-\\mu(e)]^2}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, *s* is (one of) the
            *sims* series, and *μ* is the arithmetic mean.

        """
        nse_ = 1 - (
                np.sum((obds - sims) ** 2, axis=0, dtype=np.float64)
                / np.sum((obds - np.mean(obds)) ** 2, dtype=np.float64)
        )
        return nse_

    @staticmethod
    def rmse(sims, obds):
        """Root Mean Square Error (RMSE).

        :Calculation Details:
            .. math::
            E_{\\text{RMSE}} = \\sqrt{\\frac{1}{N}\\sum_{i=1}^{N}[e_i-s_i]^2}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, *s* is (one of) the
            *sims* series.

        """
        rmse_ = np.sqrt(np.mean((obds - sims) ** 2,
                                axis=0, dtype=np.float64))

        return rmse_

    @staticmethod
    def pbias(sims, obds):
        """Percent Bias (PBias).

        :Calculation Details:
            .. math::
            E_{\\text{PBias}} = 100 × \\frac{\\sum_{i=1}^{N}(e_{i}-s_{i})}{\\sum_{i=1}^{N}e_{i}}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, and *s* is (one of)
            the *sims* series.

        """
        pbias_ = (100 * np.sum(obds - sims, axis=0, dtype=np.float64)
                / np.sum(obds))

        return pbias_

    @staticmethod
    def rsq(sims, obds):
        ## R-squared
        rsq_ = (
            (
                (sum((obds - obds.mean())*(sims-sims.mean())))**2
            ) 
            /
            (
                (sum((obds - obds.mean())**2)* (sum((sims-sims.mean())**2))
            ))
        )
        return rsq_


class DefineTime:

    def __init__(self) -> None:
        pass

    def define_sim_period(self):
        import datetime
        QSWATMOD_path_dict = self.dirs_and_paths()
        wd = QSWATMOD_path_dict['SMfolder']
        if os.path.isfile(os.path.join(wd, "file.cio")):
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
            stdate_warmup = datetime.datetime(styear_warmup, 1, 1) + datetime.timedelta(FCbeginday - 1)
            eddate_warmup = datetime.datetime(edyear_warmup, 1, 1) + datetime.timedelta(FCendday - 1)
            startDate_warmup = stdate_warmup.strftime("%m/%d/%Y")
            endDate_warmup = eddate_warmup.strftime("%m/%d/%Y")
            startDate = stdate.strftime("%m/%d/%Y")
            endDate = eddate.strftime("%m/%d/%Y")
            duration_ = (eddate - stdate).days

            # ##### 
            # start_month = stdate.strftime("%b")
            # start_day = stdate.strftime("%d")
            # start_year = stdate.strftime("%Y")
            # end_month = eddate.strftime("%b")
            # end_day = eddate.strftime("%d")
            # end_year = eddate.strftime("%Y")

            # # Put dates into the gui
            # self.dlg.lineEdit_start_m.setText(start_month)
            # self.dlg.lineEdit_start_d.setText(start_day)
            # self.dlg.lineEdit_start_y.setText(start_year)
            # self.dlg.lineEdit_end_m.setText(end_month)
            # self.dlg.lineEdit_end_d.setText(end_day)
            # self.dlg.lineEdit_end_y.setText(end_year)
            # self.dlg.lineEdit_duration.setText(str(duration))

            # self.dlg.lineEdit_nyskip.setText(str(skipyear))

            # # Check IPRINT option
            # if iprint == 0:  # month
            #     self.dlg.comboBox_SD_timeStep.clear()
            #     self.dlg.comboBox_SD_timeStep.addItems(['Monthly', 'Annual'])
            #     self.dlg.radioButton_month.setChecked(1)
            #     self.dlg.radioButton_month.setEnabled(True)
            #     self.dlg.radioButton_day.setEnabled(False)
            #     self.dlg.radioButton_year.setEnabled(False)
            # elif iprint == 1:
            #     self.dlg.comboBox_SD_timeStep.clear()
            #     self.dlg.comboBox_SD_timeStep.addItems(['Daily', 'Monthly', 'Annual'])
            #     self.dlg.radioButton_day.setChecked(1)
            #     self.dlg.radioButton_day.setEnabled(True)
            #     self.dlg.radioButton_month.setEnabled(False)
            #     self.dlg.radioButton_year.setEnabled(False)
            # else:
            #     self.dlg.comboBox_SD_timeStep.clear()
            #     self.dlg.comboBox_SD_timeStep.addItems(['Annual'])
            #     self.dlg.radioButton_year.setChecked(1)
            #     self.dlg.radioButton_year.setEnabled(True)
            #     self.dlg.radioButton_day.setEnabled(False)
            #     self.dlg.radioButton_month.setEnabled(False)
            return duration_