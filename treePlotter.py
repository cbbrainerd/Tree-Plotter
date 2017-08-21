#!/usr/bin/env python
import ROOT
import time
import abc
import itertools
import re
import os
import errno

from Datasets import DatasetDict

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
            self.eventFilters=[]
            self.filterNames=[]
            self.histograms=[]
            for name,filt in eventFilters.iteritems():
                try:
                    self.eventFilters.append(list(filt))
                except TypeError:   
                    self.eventFilters.append([filt])
                self.filterNames.append(name)
                self.histograms.append(dict())
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
    def __init__(self,tfile,datasets,luminosity,filenamesFunction,**kwargs):
        self.outputDirectory=kwargs.pop('outputDirectory','TreePlots')
        try:
            os.makedirs('%s/Summary' % self.outputDirectory)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir('%s/Summary' % self.outputDirectory):
                pass
            else:
                raise
        self.eventCount=0
        self.subDatasetFiles=dict()
        self.subDatasetWeights=dict()
        self.totalEvents=0
        self.lumi=luminosity
        for dataset in datasets:
            subDatasets=DatasetDict[dataset]
            for subDataset in subDatasets:
                self.subDatasetFiles[subDataset]=filenamesFunction(subDataset)
                assert self.subDatasetFiles[subDataset]
                numberOfEvents=0
                xsec=getXsec(subDataset)
                if xsec==0:
                    raise KeyError
                for fn in self.subDatasetFiles[subDataset]:
                    tmpTfile=ROOT.TFile(fn)
                    tree=tmpTfile.Get("ThreePhotonTree")
                    self.totalEvents+=tree.GetEntries()
                    if not dataset=='Data':
                        numberOfEvents+=tmpTfile.summedWeights.GetBinContent(1)
                    tmpTfile.Close()
                if not dataset=='Data':
                    self.subDatasetWeights[subDataset]=xsec*self.lumi/float(numberOfEvents)
                else:
                    self.subDatasetWeights[subDataset]=1
        tfile.cd()
        self.startTime=time.time()
#        numberOfEvents=tmpTfile.summedWeights.GetBinContent(1)
#        xsec=getXsec('_'.join([x for x in filename.split('/')[-1].replace("ThreePhoton_","",1).replace(".root","",1).split('_') if not x.isdigit()]))
#        if dataset!='Data':
#            fileWeight=xsec*self.lumi/float(numberOfEvents)
#            print "File weight:",fileWeight
#        else:
#            fileWeight=1
        self.histogramList=[]
        self.tfile=tfile
        self.datasets=datasets
        self.weighted=False
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
    def process(self):
        for dataset in self.datasets:
            for subDataset in DatasetDict[dataset]:
                for filename in self.subDatasetFiles[subDataset]:
                    self._fileHandle(dataset,subDataset,filename)
    def _fileHandle(self,dataset,subDataset,filename):
        print "Opening file %s" % filename
        tmpTfile=ROOT.TFile(filename)
        tree=tmpTfile.Get("ThreePhotonTree")
        assert(self.weighted) #Always want weighting, really
        fileWeight=self.subDatasetWeights[subDataset]
        for event in tree:
            eventWeight=self.weightingFunction(event) if dataset!='Data' else 1
            eventWeight*=fileWeight
            self.eventCount+=1
            if(self.eventCount%10000 == 0):
                if self.totalEvents:
                    elapsed=time.time()-self.startTime
                    timeLeft=(self.totalEvents-self.eventCount)*elapsed/float(self.eventCount)
                    #Naive time averaging, no window or anything.
                    m,s=divmod(timeLeft,60)
                    h,m=divmod(m,60)
                    em,es=divmod(elapsed,60)
                    eh,em=divmod(em,60)
                    print "%d:%02d:%02d elapsed. Estimated %d:%02d:%02d remaining..." % (eh,em,es,h,m,s)
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
                        canvas.Print('%s/%s.pdf' % (self.outputDirectory,hist.GetName()))
                if histogram.buildSummary:
                    histogram.buildSummary(histogramDict,canvas,histogram.filterNames[filterNumber])
#                    canvas.Print('%s/Summary/%s_%s.pdf' % (self.outputDirectory,histogram.name,histogram.filterNames[filterNumber]))
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
                        canvas.Print('%s/Summary/%s_%s.pdf' % (self.outputDirectory,histogram.name,histogram.filterNames[filterNumber]))
    def postProcess(self,processFunction,*args,**kwargs): #Make histograms from other histograms: takes a function to run, any number of arguments, and any number of keyword arguments. Keyword arguments beginning with /h[0-9]+/ (as a regex) should be histogram names, which will be replaced to a reference to the histogram instead. All other args and kwargs are just passed to the function wholesale
        histogramName=re.compile('^h[0-9]+')
        for x,y in vars(self).iteritems():
            kwargs['treePlotter_%s' % x]=y #Make variables in treePlotter class available to processFunction via "kwargs.pop('treePlotter_[varName]')"
        for y in [y for y in kwargs.keys() if histogramName.match(y)]:
            x=kwargs.pop(y)
            for hist in self.histogramList:
                if x==hist.name:
                    kwargs[y]=hist
                    break
            try:
                kwargs[y]
            except KeyError:
                print 'Failed to find histogram "%s"' % y
                print 'Giving up!'
                return None
        return processFunction(*args,**kwargs)
