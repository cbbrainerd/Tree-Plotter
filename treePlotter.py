#!/usr/bin/env python
import ROOT
import time
import abc
try:
    from DevTools.Plotter.xsec import getXsec
except ImportError:
    try:
        from DevTools.Plotter.python.xsec import getXsec
    except ImportError:
        print "getXsec could not be imported."
        print "Weighting cannot be done properly without getXsec."
        raise

class customHistogramBase:
    __metaclass__=abc.ABCMeta
    def __init__(self,*args):
        pass
    @abc.abstractmethod
    def finish(self):
        pass
    @abc.abstractmethod
    def Fill(self,*args):
        pass

class histogram:
    def __init__(self,fillFunction=None,eventFilters=None,*args,**kwargs):
        self.fillFunction=fillFunction
        self.style=None
        if args:
            self.args=args
        else:
            self.args=None
        self.histograms=[dict()]
        self.histType=kwargs.pop('histType',ROOT.TH1F)
        self.buildSummary=kwargs.pop('buildSummary',None)
        self.buildHistograms=kwargs.pop('buildHistograms',None)
        self.name=None
        self.title=None
        self.filterNames=['NoFilter']
        self.Fill=self._isMultidimensional
        try:
            self.name=args[0]
            self.title=args[1]
        except IndexError:
            pass
        if not eventFilters:
            self.eventFilters=[[]] #List of lists lambdas or functions that return True if the event should be accepted. Requires an AND of all such filters: one histogram produced for each such list with different filters
        else:
            print "Not yet implemented"
            raise TypeError
        #    try:
        #        self.eventFilters=list(eventFilters)
        #    except TypeError:
        #        self.eventFilters=[eventFilters]
    def addEventFilter(self,name,functions):
        try:
            self.eventFilters.append(list(functions))
        except TypeError:
            self.eventFilters.append([functions])
        self.histograms.append(dict())
        self.filterNames.append(name)
    def hist(self,*args):
        self.args=args
    def setType(self,rootType):
        self.histType=rootType
    def setTitle(self,title):
        self.title=title
    def setStyle(self,styleFunction):
        self.style=styleFunction
    def setName(self,name):
        self.name=name
    def setFillFunction(self,function): #Function that takes histogram as one argument, and returns the value (or list for multi-dim) that should be filled
        self.fillFunction=function
    def _isMultidimensional(self,tfile,dataset,event,weight=1): #Determine if plot is 1-D or not by checking the signature of the return value of the fill function
        #Sets to proper fill function for given type
        #Only runs once per histogram class instance, to avoid the expense of checking every time
        fv=self.fillFunction(event)
        try:
            (lambda *args: None)(*fv) #Can we expand? Then it's a list or a tuple or something similar, not a 1-D object (or even if it is 1-D, we want to expand every time)
            self.Fill=self._FillMD
            return self.Fill(tfile,dataset,event,weight)
        except TypeError:
            self.Fill=self._Fill1D
            return self.Fill(tfile,dataset,event,weight)
    def _FillMD(self,tfile,dataset,event,weight=1):
        fillValue=self.fillFunction(event)
        retVal=None
        for number,eventFilterSet in enumerate(self.eventFilters):
            failedFilter=False
            for eventFilter in eventFilterSet:
                if not eventFilter(event):
                    failedFilter=True
                    break
            if failedFilter:
                continue
            histogramDict=self.histograms[number]
            try:
                fillHist=histogramDict[dataset]
            except KeyError:
                myArgs=list(self.args)
                myArgs[0]=self.name+'_%s_%s' % (dataset,self.filterNames[number])
                myArgs[1].replace(';','_%s_%s;' % (dataset,self.filterNames[number]),1)
                tfile.cd()
                histogramDict[dataset]=self.histType(*myArgs)
                print '%s booked!' % histogramDict[dataset]
                fillHist=histogramDict[dataset]
            if fillHist.GetDimension==2:
                retVal=fillHist.Fill(fillValue[0],fillValue[1],weight)
            else:
                retVal=fillHist.Fill(fillValue[0],fillValue[1],fillValue[2],weight)
        return retVal
    def _Fill1D(self,tfile,dataset,event,weight=1):
#        if not self.isValid(): Don't bother checking anymore
#            return False
        fillValue=self.fillFunction(event)
        retVal=None
        for number,eventFilterSet in enumerate(self.eventFilters):
            failedFilter=False
            for eventFilter in eventFilterSet:
                if not eventFilter(event):
                    failedFilter=True
                    break
            if failedFilter:
                continue
            histogramDict=self.histograms[number]
            try:
                fillHist=histogramDict[dataset]
            except KeyError:
                myArgs=list(self.args)
                myArgs[0]=self.name+'_%s_%s' % (dataset,self.filterNames[number])
                myArgs[1].replace(';','_%s_%s;' % (dataset,self.filterNames[number]),1)
                tfile.cd()
                histogramDict[dataset]=self.histType(*myArgs)
                print '%s booked!' % histogramDict[dataset]
                fillHist=histogramDict[dataset]
            retVal=fillHist.Fill(fillValue,weight)
        return retVal
    def isValid(self):
        return self.args and self.histType and self.name and self.title and self.fillFunction

class treePlotter:
    def _defaultPalette(_,color):
        colorList=[ROOT.kRed, ROOT.kGreen, ROOT.kBlue, ROOT.kBlack, ROOT.kMagenta, ROOT.kCyan, ROOT.kOrange, ROOT.kGreen+2, ROOT.kRed-3, ROOT.kCyan+1, ROOT.kMagenta-3, ROOT.kViolet-1, ROOT.kSpring+10]
        return colorList[color % len(colorList)]
    def __init__(self,tfile,datasets,luminosity,fileList=None):
        self.eventCount=0
        if fileList: #If list of files is provided at the beginning, can read through them and estimate time remaining
            self.totalEvents=0
            self.startTime=time.time()
            for fn in fileList:
                tmpTfile=ROOT.TFile(fn)
                tree=tmpTfile.Get("ThreePhotonTree")
                self.totalEvents+=tree.GetEntries()
                tmpTfile.Close()
                tfile.cd()
        else:
            self.totalEvents=None
        self.histogramList=[]
        self.tfile=tfile
        self.datasets=datasets
        self.weighted=False
        self.lumi=luminosity
        self.numberOfEvents=dict()
        self.palette=self._defaultPalette
        for dataset in datasets:
            self.numberOfEvents[dataset]=0
    def setPalette(self,function):
        self.palette=function
    def color(self,number):
        return self.palette(number)
    def addHistogram(self,histogram):
        self.histogramList.append(histogram)
        return self.histogramList[-1]
    def setWeightingFunction(self,wf):
        self.weightingFunction=wf
        self.weighted=True
    def fileHandle(self,dataset,filename):
        print "Opening file %s" % filename
        tmpTfile=ROOT.TFile(filename)
        tree=tmpTfile.Get("ThreePhotonTree")
        print type(tree)
        numberOfEvents=tmpTfile.summedWeights.GetBinContent(1)
        xsec=getXsec(filename.split('/')[-1].replace("ThreePhoton_","",1).replace(".root","",1))
        if dataset!='Data':
            fileWeight=xsec*self.lumi/float(numberOfEvents)
            print "File weight:",fileWeight
        else:
            fileWeight=1
        for event in tree:
            eventWeight=self.weightingFunction(event) if (self.weighted and dataset!='Data') else 1
            eventWeight*=fileWeight
            self.eventCount+=1
            if(self.eventCount%10000 == 0):
                if self.totalEvents:
                    elapsed=time.time()-self.startTime
                    timeLeft=(self.totalEvents-self.eventCount)*elapsed/float(self.eventCount)
                    m,s=divmod(timeLeft,60)
                    h,m=divmod(m,60)
                    d,h=divmod(h,24)
                    print "Estimated %d:%d:%02d:%02d remaining..." % (d,h,m,s)
                else:
                    print self.eventCount
            for histogram in self.histogramList:
                histogram.Fill(self.tfile,dataset,event,eventWeight)
    def finish(self,canvas):
        for histogram in self.histogramList:
            if not isinstance(histogram,ROOT.TH1): #Not a ROOT.TH1, call custom "finish" method
                #Future: Force custom objects to inherit from base classes
                try:
                    histogram.finish()
                except AttributeError,NotImplementedError:
                    pass
            if histogram.style:
                try:
                    for d in histogram.histograms:
                        for h in d.itervalues():
                            histogram.style(h)
                except Exception: #If style fails for any reason, just keep chugging along: we really don't want to just drop everything at this point
                    pass 
            for filterNumber,histogramDict in enumerate(histogram.histograms):
                if histogram.buildHistograms:
                    histogram.buildHistograms(histogram,canvas)
                else:
                    canvas.cd()
                    options="HIST" if histogram.Fill==histogram._Fill1D else "COLZ"
                    ROOT.gStyle.SetOptStat(1)
                    ROOT.gROOT.ForceStyle()
                    for dataset,hist in histogramDict.iteritems():
                        hist.SetLineColor(self.color(0))
                        hist.Draw(options)
                        canvas.Print('TreePlots/%s.pdf' % (hist.GetName()))
                if histogram.buildSummary:
                    histogram.buildSummary(histogram,canvas)
                    canvas.Print('TreePlots/Summary/%s_%s.pdf' % (histogram.name,histogram.filterNames[filterNumber]))
                else:
                    if histogram.Fill==histogram._Fill1D: #Can't make summary plots for 2-D plots
                        ROOT.gStyle.SetOptStat(0)
                        ROOT.gROOT.ForceStyle()
                        for number,hist in enumerate(histogramDict.itervalues()):
                            hist.SetLineColor(self.color(number))
                            events=hist.Integral()
                            hist.Scale(1/float(events))
                        for number,hist in enumerate(sorted(histogramDict.itervalues(),key=lambda h: h.GetMaximum(),reverse=True)):
                            if number==0:
                                hist.Draw("HIST")
                            else:
                                hist.Draw("HIST SAME")
                        canvas.BuildLegend()
                        canvas.Print('TreePlots/Summary/%s_%s.pdf' % (histogram.name,histogram.filterNames[filterNumber]))
