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

import re,os,sys,csv,datetime,shutil,json,yaml,argparse,openpyxl,sqlite3#sys,string,
from math import *
from string import ascii_uppercase as abet
#import matplotlib as mpl
import numpy as np
#mpl.use('Qt5Agg')
#mpl.interactive(False)
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, WeekdayLocator,DateFormatter,SUNDAY
import pylab as pl
#from pylab import get_current_fig_manager as gcfm

dbg=False
dir=os.path.dirname(os.path.realpath(sys.argv[0]))+'/'

'version 0.0.0'


def main():
    global m
    parser=argparse.ArgumentParser(description='Analyze finances')
    parser.add_argument('--data',help='Name of transaction data file.',default='Debit')
    parser.add_argument('--config',help='Name of alternative configuration file.',default='Settings.json')
    parser.add_argument('--months',help='Number of months to go back.',default=3,type=int)
    parser.add_argument('--moyr',help='What month/year to look at [1/2016]',default='{}/{}'.format(datetime.date.today().month,datetime.date.today().year))
    parser.add_argument('--lists',help='List month[/year]:type[/subtype] transactions of type/subtype over given month/year.  Eg 9/2015:Supplies/Hobbies',default=None)
    parser.add_argument('--showUnsorted',help='Show unsorted items.',action='store_true')
    parser.add_argument('--createExcel',help='Create Excel file analyzing monthly spending by type for past 23 months.',action='store_true')
    parser.add_argument('--fourier',help='Fourier Analysis of costs by subtype.',action='store_true')
    args=parser.parse_args()

    dataFile,settingsFile,months,lists=args.data,args.config,args.months,args.lists
    month,year=[int(i) for i in args.moyr.split('/')]
    m=Account(dataFile+'.csv',settingsFile=settingsFile)
    
    print(spendingTablesSubtypesString(m,month,year,months,lists))
    if args.showUnsorted: print(m.showUnsorted())
    if args.createExcel: parseAnalyzeMonthlySpendingTypes(args)
    if args.fourier: fourierAnalyzeData(m)

    
def fourierAnalyzeData(acct):
    typess=[['Transportation','Flights'],['Food',None],['Utilities','Gas'],['Utilities','Rent'],['Utilities','Electric'],['Utilities','Groceries'],['Services','Haircut']]
    txt=''
    for q in typess:
        trans=m.getTransactions(daterange=[datetime.date(2015,9,15),datetime.date(2016,5,15)],ttype=q[0],stype=q[1])
        l=m.fourierAnalyze(trans,show=True)
        if l is not None:
            txt+=q,l
    # I don't understand why Utilities/Electric doesn't show a better trend.
    # I'd love to find the frequency and divide by period to get average spent
    #     then automate prediction algorithms, but fft disappoints, or I don't
    #     understand it fully.
    # Instead, for now it makes sense to temporarily provide manually the periodicities
    #     of the periodic expenditures; eg Utilities/Groceries=7 (every 7 days), Utili-
    #     ties/Rent=365.25/12 (every month), etc.
    #     As for the values, they should probably also be input manually, though they
    #     can be analyzed automatically.

    
def spendingTablesSubtypes(account,month,year,months,lists):
    """Output tables of montly expenditures by subtype.  To see how the output is parsed, visit pyFinance-qt.py::Form._popTree()."""
    #print(month,year,months)
    data=[]
    monthsn=('January','February','March','April','May','June','July',
             'August','September','October','November','December')
    for i in range(month-months+1,month+1): # TODO: fix for months>12
        if i<=0:      # last year
            data.append(dict(list(account.analyzeMonth(year-1,i+12).items())+list({'name':'%d %s'%(year,monthsn[i+11])}.items())))
        else:
            data.append(dict(list(account.analyzeMonth(year,i).items())+list({'name':'%d %s'%(year,monthsn[i-1])}.items())))

    if lists is not None and False:
        [moyri,tpstp]=lists.split(':')
        yr,stp=None,None
        if '/' in moyri:
            mo,yr=[int(q) for q in moyri.split('/')]
        else:
            mo=int(moyri)
        if '/' in tpstp:
            tp,stp=tpstp.split('/')
        else:
            tp=tpstp
        data.append(['%s %d---%s/%s'%(monthsn[mo-1],yr,tp.stp)],account.printTransactions(mo,yr,tp,stp))
    return data


def spendingTablesSubtypesString(account,month,year,months,lists):
    data=spendingTablesSubtypes(account,month,year,months,lists)
    for month in data:
        print('{} (${:6.2f})'.format(month['name'],sum([s[0] for s in month['totals']])))
        for ntype in month['totals']:
            print('    {} (${:6.2f})'.format(ntype[1],ntype[0]))
            for nntype in ntype[2:]:
                print('        ${:6.2f} {:30s}'.format(nntype[0],nntype[1]))
        '%10s %6.2f %-25s %-30s'

        
def parseAnalyzeMonthlySpendingTypes(args):
    """Parse program arguments and call AnalyzeMonthlySpendingTypes to create excel sheet."""
    dataFile,settingsFile=args.data,args.config
    loadSettings(settingsFile)
    m=Account(dataFile+'.csv')
    AnalyzeMonthlySpendingTypes(m)
    

def AnalyzeMonthlySpendingTypes(data,monthsback=24,filename='MonthlyAnalysis.xslx'):
    """Create an excel sheet over last [monthsback] months with months in columns and types in rows, comprising of sums spent."""
    #cyr,cmo=datetime.date.today().year,datetime.date.today().month
    dt=datetime.date.today().replace(day=1)
    moSpending={t:[] for t in self.types if t not in 'Utilities'}
    for i in self.types['Utilities']:
        moSpending['Utilities/{}'.format(i[1])]=[]
    months=[]
    for i in range(monthsback,0,-1):
        dti=dt+relativedelta(months=-i)
        months.append(dti.strftime('%b %y'))
        sumS=0
        for s in moSpending:
            if '/' in s:        # subType (eg, rent--more meaningful than Utilities)
                datae=data.getTransactionsInMonth(dti.month,dti.year,s.split('/')[0],s.split('/')[1])
            else:
                datae=data.getTransactionsInMonth(dti.month,dti.year,s)
            moSpending[s].append(round(100*sum([q.amt for q in datae]))/100)

    wb=openpyxl.Workbook()
    ws=wb.active
    ws.title=str(datetime.date.today())
    moSpending=sorted([[m.split('/')[1] if '/' in m else m]+moSpending[m] for m in moSpending if m not in ['Income','Manual','Transfer'] and sum(moSpending[m])!=0],key=lambda t: sum(t[1:]),reverse=True)
    moSpending_small=[q for q in moSpending if sum(q[1:])<500]
    moSpending_large=[q for q in moSpending if sum(q[1:])>=500]

    def outputExcel(qq,row_offset=0):
        """Write to excel file data in [qq] at row offset [row_offset]."""
        for m in range(len(months)):
            ws['{}{}'.format(abet[m+1],1+row_offset)].value=months[m]
        for i in range(len(qq)):
            for j in range(len(qq[i])):
                ws['{}{}'.format(abet[j],i+2+row_offset)].value=qq[i][j]
    outputExcel(moSpending_small)
    outputExcel(moSpending_large,20)
    
    if False:
        for m,i in zip(moSpending,range(len(moSpending))):
            ws['A{}'.format(i+2)].value=m
            for j in range(len(moSpending[m])):
                ws['{}{}'.format(abet[j+1],i+2)].value=moSpending[m][j]    
    wb.save(filename=dir+'/output/{}'.format(filename))


class transaction:
    """Every line of the csv is a transaction."""
    def __init__(self,date,amt,dscr,category,checkno=''):
        daten=[int(s) for s in date.split('/')]
        self.date=datetime.date(daten[-1],daten[0],daten[1])
        self.amt=-float(amt)
        self.descr=dscr
        if checkno: self.checkno=checkno
        self.cat=category

    def __str__(self):
        return '%10s %6.2f %-25s %-30s'%(self.date,self.amt,' / '.join(self.cat),self.descr)

    
class Account:
    def __init__(self,filename=None,settingsFile='Settings.json'):
        # self.advanced is advanced settings passed through settingsFile.
        self.filename,self.settingsFile=[filename,settingsFile]
        self.types,self.advanced=self.loadSettings(settingsFile)

        self.transactions=[]
        if filename is not None:
            self.transactions=self.__loadTransactions(filename)
            self.sql=self.__sqlize(self.transactions)

    def __loadTransactions(self,filename):
        transactions=[]
        with open(dir+'Data/Debit/'+filename) as f: # Debit
            fcsv=csv.reader(f)
            for row in fcsv:
                #print(row)
                if '#' in row[-1]:
                    pass
                elif 'Accounts' not in self.advanced or not any(re.search(q[0],row[2]) for q in self.advanced['Accounts']):
                    transactions.append(transaction(row[1],row[3],row[2],self.getType(row[2]),row[4]))
        if 'Accounts' in self.advanced:  # of the form '#Advanced':{"Accounts":[["regexp match for transfers","account name"],..]}
            for q in self.advanced['Accounts']:
                if not os.path.isfile(dir+'Data/%s/%s'%(q[1],filename)):
                    print('Warning: Account file "%s" does not exist.  Edit Settings/#Advanced/Accounts to fix or add file to directory.'%(dir+'Data/%s/%s'%(q[1],filename)))
                else:
                    with open(dir+'Data/%s/%s'%(q[1],filename)) as f: # Secondary account
                        fcsv=csv.reader(f)
                        for row in fcsv:
                            if '#' in row[-1] or not all([q.isnumeric() for q in row]):
                                pass
                            elif row[0]!='Payment':  # Ignore Paid Balances
                                transactions.append(transaction(row[1],row[4],row[3],self.getType(row[3])))
        
        return sorted(transactions,key=lambda t: t.date)

    def __sqlize(self,transactions):
        con=sqlite3.connect(":memory:")
        cur=con.cursor()
        cur.execute("CREATE TABLE t(date date,amt real,dscr text,type text,subtype text);")
        cur.executemany("INSERT INTO t VALUES (?,?,?,?,?);",[[s.date,s.amt,s.descr,s.cat[0],s.cat[1]] for s in transactions])
        return con

    def searchSQL(self,query):
        reply=''
        try:
            for s in self.sql.execute(query):
                reply+='\n%10s %7.2f %-25s %-30s'%(s[0],s[1],'/'.join([s[3],s[4]]),s[2])
        except sqlite3.OperationalError as err:
            reply+="\nError: {}\n".format(err)
            reply+="Table structure is t(date date,amt real,dscr text,type text,subtype text)\n"
        except:
            reply+=sys.exc_info()[0]
        return reply

    def reload(self):
        self.__init__(self.filename,self.settingsFile)

    def getType(self,dscr):
        for category in self.types:
            for subcat in self.types[category]:
                if re.search(subcat[0],dscr):
                    return [category,subcat[1]]
        return ['Unknown','Unknown']

    def loadSettings(self,filename='Settings.json'):
        """Parses Settings json/yaml file and separates advanced settings (in 'advanced' key of dictionary), returns (Types,Advanced)."""
        advanced={};types={}
        if not os.path.isfile(dir+'Settings/'+filename):
            print('No Settings file %s found.  Creating new Settings file.'%(dir+'Settings/'+filename))
            shutil.copy2('Settings_blank.json',dir+'Settings/'+filename)
        with open(dir+'Settings/'+filename,'r') as settings:
            if filename.split('.')[1]=='json':
                types=json.load(settings)
            elif filename.split('.')[1]=='yaml':
                types=yaml.load(settings.read())
            else:
                printError('Could not parse settings file "%s".  Ensure the file has a json or yaml extension.'%(dir+'Settings/'+filename))
        if '#Advanced' in types:
            # Eg, "#Advanced":{"Accounts":[["PPD ID: 123456789","Credit"],..]}
            for advancedOption in types['#Advanced']:
                advanced[advancedOption]=types['#Advanced'][advancedOption]
        types.pop("#Advanced",None) # advanced settings passed via json popped out of types.
        return types,advanced

    def showUnsorted(self):
        txt=""
        for t in self.transactions:
            if t.cat[0]=='Unknown':
                txt+='%10s %7.2f %-30s\n'%(t.date,t.amt,t.descr)
        return txt

    def getTransactions(self,daterange=None,ttype=None,stype=None):
        """Get transactions in date range, substituting for payments in other accounts.  daterange=[beginDate,endDate]."""
        if ttype!=None and ttype not in self.types:
            print('Unrecognized type %s.'%ttype)
            return
        if stype!=None and stype not in list(zip(*self.types[ttype]))[1]:
            print('Unrecognized subtype %s.'%stype)
            return
        
        datedTrans=[]        
        for i,t in enumerate(self.transactions):
            if daterange==None or (t.date>=daterange[0] and t.date<=daterange[1]):
                if ttype==None or t.cat[0]==ttype:
                    if stype==None or t.cat[1]==stype:
                        datedTrans.append(i)
        return datedTrans

    def analyzeMonth(self,year,month):
        """month starts at 1"""
        firstDay=datetime.date(year,month,1)
        #[month.replace(day=1),(date.today().replace(day=25)+timedelta(days=10)).month])
        return self.AnalyzeSpending([firstDay,(firstDay.replace(day=25)+datetime.timedelta(days=10)).replace(day=1)])

    def subTransactions(self,daterange=None,types=None):
        """return transactions within daterange matching types."""
        data=[]
        for t in self.transactions:
            if (daterange is None or (t.date>=daterange[0] and t.date<daterange[1])):
                if (types is None or (t.cat[0]==types[0] and (len(types)==2 and t.cat[1]==types[1]))):# and (t.cat[0] not in ['Transfer'])
                    data.append(t)
        return data

    def AnalyzeSpending(self,daterange,show=True,showSubtotals=True):
        """Bins transactions into subtypes within daterange=[beginDate,endDate].  
           Transactions must be sorted."""
        totes=[];txt=''#data=[];
        ntypes={}
        totals={}
        obj={}
        for s in self.types:
            ntypes[s]={}
            obj[s]={}
            totals[s]=0.
            for t in self.types[s]:
                obj[s][t[1]]=[]
                ntypes[s][t[1]]=0.
        ntypes['Unknown']={'Unknown':0.}
        obj['Unknown']={'Unknown':[]}
        totals['Unknown']=0.
        for t in self.transactions:
            if t.date>=daterange[0] and t.date<daterange[1]:
                #if t.cat[0] not in ['Transfer']:
                ntypes[t.cat[0]][t.cat[1]]+=t.amt
                obj[t.cat[0]][t.cat[1]].append(t)
                totals[t.cat[0]]+=t.amt
                    
        txt+='Amount spent: $%.2f\n'%(sum([totals[s] for s in totals]))
        for s in sorted(ntypes,key=lambda l:abs(totals[l]),reverse=True):
            if totals[s]!=0:
                txt+='%-22s ($%8.2f)\n'%(s,totals[s])
                totes.append([totals[s],s])
                if showSubtotals:
                    for t in ntypes[s]:
                        if ntypes[s][t]!=0:
                            txt+='\t%-15s $  %6.2f\n'%(t,ntypes[s][t])
                            totes[-1].append([ntypes[s][t],t])
        return {'data':obj,'totals':totes}
        
    def printTransactions(self,month=None,year=None,ttype=None,subType=None):
        """Prints specific transactions by month (1=Jan)."""
        title=False
        if year==None: year=datetime.date.today().year
        txt=''
        for s in self.getTransactionsInMonth(month,year,ttype,subType):
            if title is False:
                txt+='{:8}   {:10}   {:70}   {:30}\n'.format('Amount','Date','Description','Category')
                title=True
            txt+='{:8.2f}   {:10}   {:70}   {:30}\n'.format(s.amt,s.date.strftime('%d-%m-%y'),s.descr,'/'.join(s.cat))
        if txt=='':
            txt='No transactions in {} found in date range {}.\n'.format(ttype+('' if ttype==None else '/{}'.format(subType)),('' if month==None else ('January','February','March','April','May','June','July','August','September','October','November','December')[month-1]+' {}'.format(year)))
        return txt

    def getTransactionsInMonth(self,month=None,year=None,ttype=None,subType=None):
        """Return list of transactions over month in year matching ttype and subType.  Transactions must be ordered."""
        #title=False
        if year==None: year=datetime.date.today().year
        transactions=[]
        for s in self.transactions:
            theMonth=datetime.date(year,month,1)
            if ((month==None or s.date>=theMonth and s.date<=(theMonth.replace(day=25)+datetime.timedelta(days=10)).replace(day=1))) and ((ttype==None or s.cat[0]==ttype)) and ((subType==None or s.cat[1]==subType)):
                transactions.append(s)
        return transactions

    def fourierAnalyze(self,transactions,show=False):
        """Return ordered maxima of fourier transform of transactions.  Assumes sorted data."""
        transactions=[[self.transactions[q].date,self.transactions[q].amt] for q in transactions]
        # make array of uniformly spaced data
        dates=[q for q in list(zip(*transactions))[0]]
        sdate,edate=min(dates),max(dates)
        idate=sdate
        signal=[]
        dates=[]
        while idate<edate:
            isig=0
            while transactions[0][0]==idate:
                isig+=transactions[0][1]
                transactions.pop(0)
            signal.append(isig)
            dates.append(idate)
            idate=idate+datetime.timedelta(days=1)
            
        if show:
            plt.plot(dates,signal)
            plt.show()
        if len(signal)==0:
            return None
        fsig=abs(np.fft.rfft(signal,norm='ortho')[1:]) # ignore 'dc offset'
        ffreq=np.fft.rfftfreq(len(signal),d=1/len(signal))[1:]
        y=list(zip(*sorted(zip(fsig.real,ffreq),key=lambda t:abs(t[0].real),reverse=True)))[1]
        if show:
            plt.plot(ffreq,fsig.real)
            plt.show()
        return y[:min(5,len(y))]
        #print(sum(signal)/(edate-sdate).days*7)

        
def AnalyzeSpending(transactions,daterange,show=True,showSubtotals=True):
    """Bins transactions into subtypes within daterange=[beginDate,endDate].  
       Transactions must be sorted."""
    ntypes={}
    totals={}
    obj={}
    for s in self.types:
        ntypes[s]={}
        obj[s]={}
        totals[s]=0.
        for t in self.types[s]:
            obj[s][t[1]]=[]
            ntypes[s][t[1]]=0.
    ntypes['Unknown']={'Unknown':0.}
    obj['Unknown']={'Unknown':[]}
    totals['Unknown']=0.
    for t in transactions:
        if t.date>=daterange[0] and t.date<=daterange[1]:
            #if t.cat[0] not in ['Transfer']:
            ntypes[t.cat[0]][t.cat[1]]+=t.amt
            obj[t.cat[0]][t.cat[1]].append(t)
            totals[t.cat[0]]+=t.amt
    if show:
        print('Amount spent: $%.2f'%(sum([totals[s] for s in totals])))
        for s in ntypes:
            if totals[s]!=0:
                print('%-22s ($%8.2f)'%(s,totals[s]))
                if showSubtotals:
                    for t in ntypes[s]:
                        if ntypes[s][t]!=0:
                            print('\t%-15s $  %6.2f'%(t,ntypes[s][t]))
    return obj


def listTransactions(transactions,filename='Transactions'):
    total=0.
    with open(dir+filename+'.dmp','w') as f:
        for s in transactions:
            total=total-s.amt
            f.write('%8.2f\t%8.2f\t%10s\t%s\n'%(1,s.amt,s.date,s.descr))

            
def getTotalSpendOn(transactions,ntype,nsubtype=None):
    totalSpent=0
    for t in transactions:
        if t.cat[0]==ntype:
            if nsubtype==None or t.cat[1]==nsubtype:
                totalSpent-=t.amt
    return totalSpent


def getTransactions(transactions,daterange):
    """Get transactions in date range, substituting for account transfers payments.  daterange=[beginDate,endDate]."""
    datedTrans=[]
    for t in transactions:
        if t.date>=daterange[0] and t.date<=daterange[1]:
            #if t.cat[0] not in ['Transfer']:
            datedTrans.append(t)
    return datedTrans


def linePlot(transactions):
    """Plot balance v. time"""
    lineplot=[]
    for q in transactions:
        lineplot.append([q.date,-q.amt,q.descr,q.cat])
    #print('\n'.join(['%s\t%.2f\t%s\t%s'%(q[0],q[1],q[2],q[3][0]) for q in lineplot]))
    lineplot=[list(q) for q in zip(*lineplot[::])]
    lsum=[0]
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

    fig,ax=plt.subplots()
    ax.plot_date(lineplot[0],lsum,'ko')
    #print(len(dates),len(tda))
    ax.plot_date(dates,tda,'c--')
    ax.plot_date(dates,currbal,'r-')
    
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(monthsFmt)
    ax.xaxis.set_minor_locator(sundays)
    ax.autoscale_view()
    ax.grid(True)
    fig.autofmt_xdate()
    plt.show()
    return ax

    #def _onMotion(event):
    #    collisionFound=False
    #    tooltip.Enable(False)
    #    if event.xdata!=None and event.ydata!=None:   # within plot range
    #        #print(event.xdata,event.ydata)
    #        for i in range(len(lineplot[0])):
    #            if abs(event.xdata-xdata[i])<5 and abs(event.ydata-lsum[i])<1:
    #                tip=str(lineplot[0][i])[-5:]+': '+'/'.join(lineplot[3][i])+' ($%5.2f)\n'%lineplot[1][i]+lineplot[2][i]
    #                tooltip.SetTip(tip)
    #                tooltip.Enable(True)
    #                collisionFound=True
    #                break
    #        if not collisionFound:
    #            tooltip.Enable(False)

#    tooltip=wx.ToolTip(tip='')
#    gcfm().canvas.SetToolTip(tooltip)
#    tooltip.Enable(False)
#    tooltip.SetDelay(0)
#    fig.canvas.mpl_connect('motion_notify_event',_onMotion)


def piePlot(transactions):
    """Plot data in pie chart."""
    piechart={}
    for q in transactions:
        #if q.cat[0] in ['Travel','Misc']:
        #    continue
        if q.cat[0] in piechart:
            piechart[q.cat[0]]+=max(0,q.amt)
        else:
            piechart[q.cat[0]]=max(0,q.amt)
    piechart=list(zip(*piechart.items()))
    cols=['red','green','brown','cyan','orange','yellow','pink','violet','gray']
    #piechart[1]=[q/sum(piechart[1]) for q in piechart[1]]
    pl.pie(piechart[1],labels=piechart[0],colors=cols*3,autopct='%1.1f%%')
    pl.show()

    
def subPiePlot(subtrans):
    """Plot one subcategory's pie chart"""
    piechart={}
    for q in subtrans:
        pass

    
def printError(txt):
    print(txt)

    
def printDBG(txt):
    pass


if __name__=='__main__':
    main()
