#!/usr/bin/python3
# encoding:utf-8

# pyFinance: Analyze bank histories
# Copyright (C) 2017 Maziar Saleh Ziabari

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys,os,datetime,re,shutil#,time,subprocess
from dateutil import relativedelta
from PyQt5 import QtWidgets,QtGui,QtCore
import pyFinance as pyfin

#from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
#from PyQt5.QtGui import QIcon

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.dates import MonthLocator,WeekdayLocator,DateFormatter,SUNDAY
from matplotlib.figure import Figure
import pylab as pl
from pylab import get_current_fig_manager as gcfm
#import matplotlib.pyplot as plt

# event signals http://zetcode.com/gui/pyqt5/eventssignals/
# layout http://zetcode.com/gui/pyqt5/layout/
# treeviews https://joekuan.wordpress.com/2016/02/11/pyqt-how-to-hide-top-level-nodes-in-tree-view/

dir=os.path.dirname(os.path.realpath(__file__))+'/'
global globdata
version='0.0.0'


def main():
    global m,globdata
    m=pyfin.Account()
    globdata={}
    globdata['settingsFile']='Settings.json'
    app=QtWidgets.QApplication([])
    screen=Form()
    screen.show()

    sys.exit(app.exec_())

    
class Form(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)

        self.data=[]
        self.mbar=self._initMenu()
        self._initLayout()
        self.OpenFileprompt=openDialog()

    def _initLayout(self):
        VB0=QtWidgets.QVBoxLayout()
        HB1=QtWidgets.QVBoxLayout()
        VB2=QtWidgets.QVBoxLayout()
        
        VB0.addWidget(self.mbar)
        
        self.tree=QtWidgets.QTreeView()
        # This part took a while:
        # http://stackoverflow.com/questions/23993895/python-pyqt-qtreeview-example-selection
        #self.tree.clicked.connect(self._upd)
        self.tree.clicked.connect(self._upd)
        HB1.addWidget(self.tree)
        HB1.addLayout(VB2)

        self.lblMain=QtWidgets.QTextEdit('Open a file to begin.')
        self.lblMain.setLineWrapMode(self.lblMain.NoWrap)
        f=QtGui.QFont('Monospace',8)
        f.setStyleHint(QtGui.QFont.TypeWriter)
        self.lblMain.setCurrentFont(f)
        self.lblMain.setTabStopWidth(40)
        self.lblMain.setReadOnly(True)
        
        HB1.addWidget(self.lblMain)

        self.tabs=QtWidgets.QTabWidget()
        self.tab1=QtWidgets.QWidget()
        self.tab2=QtWidgets.QWidget()
        self.tab3=QtWidgets.QWidget()
        self.tabs.addTab(self.tab1,"Data")
        self.tabs.addTab(self.tab2,"Graph")
        self.tabs.addTab(self.tab3,"Search")
        #self.tab1.addLayout(VB0)
        self.tab1.setLayout(HB1)
 
        self.graph=PlotCanvas(parent=self)
        VB1=QtWidgets.QVBoxLayout()
        VB1.addWidget(self.graph)
        self.tab2.setLayout(VB1)

        HB3=QtWidgets.QHBoxLayout()
        self.searchbar=QtWidgets.QLineEdit("SELECT * FROM t WHERE type='Utilities'")
        btnSearch=QtWidgets.QPushButton('&Search')
        btnSearch.clicked.connect(self._searchSQL)
        HB3.addWidget(self.searchbar)
        HB3.addWidget(btnSearch)
        self.searchResults=QtWidgets.QTextEdit("Press enter to run SQL query.")
        self.searchResults.setReadOnly(True)
        self.searchResults.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.searchResults.setCurrentFont(f)
        VB3=QtWidgets.QVBoxLayout()
        VB3.addLayout(HB3)
        VB3.addWidget(self.searchResults)
        self.tab3.setLayout(VB3)
        
        #HB1.addLayout(self._mainMenu())
        VB0.addWidget(self.tabs)

        self.setLayout(VB0)
        #self.addWidget(self.tabs)
        self.setWindowTitle('pyFinance')

        self.show()

    def _searchSQL(self):
        query=self.searchbar.text()
        print(query)
        reply=''
        for s in m.sql.execute(query):
            reply+='\n%10s %7.2f %-25s %-30s'%(s[0],s[1],'/'.join([s[3],s[4]]),s[2])
        self.searchResults.setText(query+'\n'+reply)

    def _upd(self,s):
        """Find out what was selected in the tree and update label accordingly with selected transactions."""
        #i=self.tree.selectedIndexes()[1] # 0 for first col
        #print(i)
        #c=i.model().itemFromIndex(i)
        #c=i.model().index(
        #print(c.text())
        #print(c)
        #i=self.tree.selectedIndexes()[1] # 0 for col 1
        path=[];npath=[]
        #c=i.model().itemFromIndex(i)

        curdir=s
        while curdir.row()!=-1: # not root node
            f=curdir.sibling(curdir.row(),1)
            npath.append(f.model().itemFromIndex(f).text())
            path.append(curdir.row())
            curdir=curdir.parent()
        path=path[::-1]
        npath=npath[::-1]

        txt='';delim='\n'
        if len(path)==3:
            for q in self.d[path[0]]['data'][npath[1]][npath[2]]:
                txt+=str(q)+delim
        elif len(path)==2:
            for a in self.d[path[0]]['data'][npath[1]]:
                for b in self.d[path[0]]['data'][npath[1]][a]:
                    txt+=str(b)+delim
        elif len(path)==1:
            for q in self.d[path[0]]['data']:
                for a in self.d[path[0]]['data'][q]:
                    for b in self.d[path[0]]['data'][q][a]:
                        txt+=str(b)+delim
        else:
            return
        
        self.lblMain.setText(txt)
        #print(self.d[path[0]][npath[1]][npath[2]])
        #print(self.d[])

    def _show(self,d):
        #self.lblMain.setText(d)
        self._popTree(d)
                            
    def _popTree(self,data):
        """Populate treeview with monthly data."""
        model=QtGui.QStandardItemModel()
        model.setColumnCount(2)
        model.setHorizontalHeaderLabels(['Spent','Category'])
        #model.setData(0,QtCore.QVariant(QtCore.Qt.AlignRight),QtCore.Qt.TextAlignmentRole)
        self.tree
        #model.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        root=model.invisibleRootItem()
        #print(data)
        
        for month in data:
            monthn=month['name']
            mtotes=month['totals']
            #mdata=month['data']
            #ral=QtCore.QVariant(QtCore.Qt.AlignRight)
            a=QtGui.QStandardItem(str(round(sum([s[0] for s in mtotes])*100)/100))
            #a.setTextAlignment(ral)
            b=QtGui.QStandardItem(monthn)
            root.appendRow([a,b])
            for ntype in mtotes:
                an=QtGui.QStandardItem(str(round(ntype[0]*100)/100))
                bn=QtGui.QStandardItem(ntype[1])
                #an.setTextAlignment(ral)
                a.appendRow([an,bn])
                #rooti.appendRow([cb])
                for nntype in ntype[2:]:
                    ann=QtGui.QStandardItem(str(round(nntype[0]*100)/100))
                    #ann.setTextAlignment(ral)
                    bnn=QtGui.QStandardItem(nntype[1])
                    
                    an.appendRow([ann,bnn])

        self.tree.setModel(model)
        #self.tree.setEditTriggers(self.tree.SelectedClicked)
        #def edit(self,index,trigger):
        #    print('Edit index')
        #self.tree.edit=edit
        self.tree.expandToDepth(2)
        self.tree.resizeColumnToContents(0)
        self.tree.expandToDepth(0)
        
#        for q in s:
#            item=QtWidgets.QTreeWidgetItem(self.tree,q)

    def _mainMenu(self):
        VB0=QtWidgets.QVBoxLayout()

        btnMoYr=QtWidgets.QPushButton('Choose &Month')
        btnMoYr.clicked.connect(self._askDialog)

        VB0.addWidget(btnMoYr)
        return VB0

    def _askDialog(self):
        global globdata
        globdata=self.OpenFileprompt.getData()

        self._updateData(globdata)
        
    def _updateData(self,data=None):
        """Get requested data (see _askDialog) and display it."""
        global m,globdata
        if data is None:
            data=globdata

        m=pyfin.Account(data['dataFile']+'.csv',settingsFile=data['settingsFile'])
        month,year=[int(i) for i in data['moyr'].split('/')]
        self.d=pyfin.spendingTablesSubtypes(m,month,year,data['months'],lists=None)
        self._show(self.d)
        d2=datetime.date.today()
        d1=d2-relativedelta.relativedelta(months=data['months'])
        self.graph.plot(m.subTransactions([d1,d2]))
        
    def _initMenu(self):
        mbar=QtWidgets.QMenuBar()
        mFile=mbar.addMenu('&File')

        mOpen=QtWidgets.QAction('&Open',mbar)
        mOpen.setShortcut('Ctrl+O')
        mOpen.triggered.connect(self._askDialog)
        #mOpen.triggered.connect(self.openFile)
        mFile.addAction(mOpen)

        mQuit=QtWidgets.QAction('&Quit',mbar)
        mQuit.setShortcut('Ctrl+Q')
        mQuit.triggered.connect(self.close)
        mFile.addAction(mQuit)

        mEdit=mbar.addMenu('&Edit')
        
        mReload=QtWidgets.QAction('&Reload',mbar)
        mReload.setShortcut('Ctrl+R')
        mReload.triggered.connect(self._reload)
        mEdit.addAction(mReload)
        
        mSettings=QtWidgets.QAction('&Settings',mbar)
        mSettings.setShortcut('Ctrl+S')
        mSettings.triggered.connect(self._editSettings)
        mEdit.addAction(mSettings)

        mHelp=mbar.addMenu('&Help')

        mAbout=QtWidgets.QAction('&About',mbar)
        mAbout.setShortcut('ctrl+V')
        mAbout.triggered.connect(self._about)
        mHelp.addAction(mAbout)

        return mbar

    def _about(self):
        """display version number."""
        global version
        QtWidgets.QMessageBox.information(self,'pyFinance v. %s'%version,'pyFinance v. %s (c) 2017 Maziar Saleh Ziabari.'%version)
    
    def _editSettings(self):
        'Edit Settings file.'
        self.settEdit=QtCore.QProcess()
        self.settEdit.finished.connect(self._reload)
        filename=dir+'Settings/'+globdata['settingsFile']
        if not os.path.isfile(filename):
            print('No Settings file %s found.  Creating new Settings file.'%(dir+'Settings/'+filename))
            shutil.copy2('Settings_blank.json',filename)
        self.settEdit.start('%s %s'%(m.advanced['Editor'],filename))

    def _reload(self):
        if m.filename!=None:
            m.reload()              # re-bin data in pyfin
            self._updateData()          # update our view
        
    def close(self):
        QtWidgets.qApp.quit()

        
class PlotCanvas(FigureCanvas):
    def __init__(self, transactions=None, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.transactions=transactions
 
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
 
        #FigureCanvas.setSizePolicy(self,
        #QtWidgets.QSizePolicy.Expanding,
        #QtWidgets.QSizePolicy.Expanding)
        #FigureCanvas.updateGeometry(self)
        if self.transactions is not None:
            #print(self.transactions)
            self.plot()
        
    def plot(self,transactions=None):
        """Plot balance v. time"""
        self.figure.clf()
        if transactions is None:
            transactions=self.transactions
        #ax=pyfin.linePlot(transactions)
        ax=self.figure.add_subplot(111)
        #self.figure.axes.append(ax)

        lineplot=[]
        for q in transactions:
            lineplot.append([q.date,-q.amt,q.descr,q.cat])
        #print('\n'.join(['%s\t%.2f\t%s\t%s'%(q[0],q[1],q[2],q[3][0]) for q in lineplot]))
        lineplot=[list(q) for q in zip(*lineplot[::])]
        lsum=[0]
        #print(len(lineplot))
        for i in range(len(lineplot[1])):
            lsum.append(lsum[-1]+lineplot[1][i])   # Array of running balance
        lsum=lsum[1:]                              # Delete [0] entry
        #print('***'*10,lsum[-1]);sys.exit()

        #xdata=[q.toordinal() for q in lineplot[0]] # Dates
        # Fill array with dates every day since oldest
        dates=[lineplot[0][0]]
        #print(dates)
        while dates[-1]<datetime.date.today():
            dates.append(dates[-1]+datetime.timedelta(days=1))

        currbal=[0]                                # Get current balance
        for date in dates:
            adding=0
            for i in range(len(lineplot[0])):
                if date==lineplot[0][i]:
                    adding+=lineplot[1][i]         # Add all current date transactions to balance
            currbal.append(currbal[-1]+adding)     # Keep daily array of running balance
        currbal=currbal[1:]                        # Delete [0] element

        ndayrunningavg=21                          # Smoothing function
        ndaypad=int((ndayrunningavg-1)/2)
        tda=currbal[:ndaypad]                      # Fill first 20 days without smoothing, then smooth rest
        for i in range(ndaypad,len(currbal)-ndaypad):
            tda.append(sum(currbal[i-ndaypad:i+ndaypad+1])/float(ndayrunningavg))
        for s in currbal[-ndaypad:]:               # Append last 20 days without smoothing
            tda.append(s)

        sundays=WeekdayLocator(SUNDAY)
        months=MonthLocator(range(1,13),bymonthday=1,interval=1)
        monthsFmt=DateFormatter('%b %y')

        #fig,ax=plt.subplots()
        ax.plot_date(lineplot[0],lsum,'ko')
        #print(len(dates),len(tda))
        ax.plot_date(dates,tda,'c--')
        ax.plot_date(dates,currbal,'r-')

        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_major_formatter(monthsFmt)
        ax.xaxis.set_minor_locator(sundays)
        ax.autoscale_view()
        ax.grid(True)
        self.figure.autofmt_xdate()
        #plt.show()

        self.draw()
        return
        
        #data = [random() for i in range(25)]
        #ax = self.figure.add_subplot(111)
        #ax.plot(data, 'r-')
        #ax.set_title('PyQt Matplotlib Example')
        #self.draw()
        
        
class openDialog(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        gr0=self._initUI()

        self.setLayout(gr0)

    def _initUI(self):
        gr0=QtWidgets.QGridLayout()
        gr0.setSpacing(10)

        lblmoyr=QtWidgets.QLabel('Month/Year: ')
        lblnum=QtWidgets.QLabel('Months:')
        lblData=QtWidgets.QLabel('Data file:')
        lblSett=QtWidgets.QLabel('Settings File:')

        self.moyr=QtWidgets.QLineEdit('{}/{}'.format(datetime.date.today().month,datetime.date.today().year))
        self.sbmos=QtWidgets.QSpinBox()
        self.sbmos.setValue(3)
        
        ladate='000000'
        for filename in os.listdir(dir+'Data/Debit/'):
            s=re.match('([0-9]{6})\.csv',filename)
            if s!=None:
                if s.group(1)>ladate:
                    ladate=s.group(1)
        #ladate=time.strftime('%y%m%d') # TODO: update to latest file in dir
        
        self.dataf=QtWidgets.QLineEdit(ladate)
        self.settf=QtWidgets.QLineEdit('Settings.json')

        ok=QtWidgets.QPushButton('&Ok')
        ok.clicked.connect(self.close)
        cancel=QtWidgets.QPushButton('&Cancel')
        cancel.clicked.connect(self.close)

        gr0.addWidget(lblData,0,0)
        gr0.addWidget(self.dataf,0,1,1,9)
        gr0.addWidget(lblmoyr,1,0)
        gr0.addWidget(self.moyr,1,1,1,9)
        gr0.addWidget(lblnum,2,0)
        gr0.addWidget(self.sbmos,2,1)
        gr0.addWidget(lblSett,3,0)
        gr0.addWidget(self.settf,3,1,1,9)
        gr0.addWidget(ok,10,0,1,5)
        gr0.addWidget(cancel,10,6,1,5)

        return gr0

    def getData(self,parent=None):
        askData=openDialog(parent)
        askData.exec_()#result=
        data={'moyr':askData.moyr.text(),
              'dataFile':askData.dataf.text(),
              'settingsFile':askData.settf.text(),
              'months':askData.sbmos.value()}
        return data

    
if __name__=='__main__':
    main()
