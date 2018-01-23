#!/usr/bin/env python
import ROOT
import time
import abc
import itertools
import re
import os
import errno
import collections
import Plots.tdrstyle as tdrstyle

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
    def finish(self,canvas,outputDir,options='',style=None):
        canvas.cd()
        for histograms in self.histograms.itervalues():
            for histogram in histograms:
                name=histogram.GetName()
                histogram.Draw(options)
                if style:
                    style.cd()
                else:
                    tdrstyle.setTDRStyle()
                canvas.Print('%s/%s.pdf' % (outputDir,name))
            if self.buildSummary:
                self.buildSummary(self,outputDirectory=outputDir,canvas=canvas)
    def __init__(self,fillFunction=None,_=None,*args,**kwargs):
        self.fillFunction=fillFunction
        self.style=None
        if args:
            self.args=args
        else:
            self.args=None
        self.histType=kwargs.pop('histType',ROOT.TH1F)
        self.buildSummary=kwargs.pop('buildSummary',None)
        self.buildHistograms=kwargs.pop('buildHistograms',None)
        self.name=None
        self.title=None
        self.filterNames=None
        self.Fill=self._isMultidimensional
        try:
            self.name=args[0]
            self.title=args[1]
        except IndexError:
            pass
        self.histograms=dict()
        self.histogramFills=None
        assert(not kwargs)
    def switchDataset(self,tfile,dataset):
        if not dataset in self.histograms:
            tfile.cd()
            self.histograms[dataset]=[]
            for filterName in self.filterNames:
                myArgs=list(self.args)
                myArgs[0]=self.name+'_%s_%s' % (dataset,filterName)
                myArgs[1].replace(';','_%s_%s;' % (dataset,filterName),1)
                self.histograms[dataset].append(self.histType(*myArgs))
                print '%s booked!' % self.histograms[dataset]
        self.histogramFills=[hf.Fill for hf in self.histograms[dataset]]
    def setFilterNames(self,filterNames):
        self.filterNames=filterNames
        self.number=len(filterNames)
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
    def _isMultidimensional(self,*args): #Determine if plot is 1-D or not by checking the signature of the return value of the fill function
        #Sets to proper fill function for given type
        #Only runs once per histogram class instance, to avoid the expense of checking every time
        event=args[0]
        fv=self.fillFunction(event)
        try:
            (lambda *args: None)(*fv) #Can we expand? Then it's a list or a tuple or something similar, not a 1-D object (or even if it is 1-D, we want to expand every time)
            if not isinstance(fv,tuple): #Needs to be a python tuple
                off=self.fillFunction
                self.fillFunction=lambda event: tuple(off(event))
            self.Fill=self._FillMD
            return self.Fill(*args)
        except TypeError:
            self.Fill=self._Fill1D
            return self.Fill(*args)
    def _FillMD(self,event,filters,weight=1):
        fillValue=self.fillFunction(event)+(weight,)
        [self.histogramFills[n](*fillValue) for n in xrange(self.number) if filters[n]]
    def _Fill1D(self,event,filters,weight=1):
        fillValue=self.fillFunction(event)
        [self.histogramFills[n](fillValue,weight) for n in xrange(self.number) if filters[n]]
    def isValid(self):
        return self.args and self.histType and self.name and self.title and self.fillFunction

class treePlotter:
    def _defaultPalette(_,color):
        colorList=[ROOT.kRed, ROOT.kGreen, ROOT.kBlue, ROOT.kBlack, ROOT.kMagenta, ROOT.kCyan, ROOT.kOrange, ROOT.kGreen+2, ROOT.kRed-3, ROOT.kCyan+1, ROOT.kMagenta-3, ROOT.kViolet-1, ROOT.kSpring+10]
        return colorList[color % len(colorList)]
    def __init__(self,tfile,datasets,luminosity,filenamesFunction,**kwargs):
        self.treeName=kwargs.pop('treeName','ThreePhotonTree')
        self.DatasetDict=kwargs.pop('DatasetDict',DatasetDict)
        self.outputDirectory=kwargs.pop('outputDirectory','TreePlots')
        self.datasetWeights=kwargs.pop('additionalDatasetWeights',{})
        self.currentDataset=None
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
        totalEventsForSubDataset=dict()
        for dataset in datasets:
            subDatasets=self.DatasetDict[dataset]
            for subDataset in subDatasets:
                self.subDatasetFiles[subDataset]=filenamesFunction(subDataset)
                if not self.subDatasetFiles[subDataset]:
                    print 'Filenames not found for dataset %s' % subDataset
                    print filenamesFunction(subDataset)
                    raise KeyError(subDataset)
                numberOfEvents=0
                xsec=getXsec(subDataset)
                if xsec==0:
                    raise KeyError
                totalEventsForSubDataset[subDataset]=0
                for fn in self.subDatasetFiles[subDataset]:
                    tmpTfile=ROOT.TFile(fn)
                    tree=tmpTfile.Get(self.treeName)
                    if not tree:
                        print fn,self.treeName
                    tmp=tree.GetEntries()
                    self.totalEvents+=tmp
                    totalEventsForSubDataset[subDataset]+=tmp
                    if not dataset=='Data':
                        numberOfEvents+=tmpTfile.summedWeights.GetBinContent(1)
                    tmpTfile.Close()
                if not dataset=='Data':
                    self.subDatasetWeights[subDataset]=xsec*self.lumi/float(numberOfEvents)
                else:
                    self.subDatasetWeights[subDataset]=1
                if dataset in self.datasetWeights:
                    self.subDatasetWeights[subDataset]*=self.datasetWeights[dataset]
        with open('subDatasetWeights.log','wb') as f:
            f.write('Weights with luminosity: %f\n' % self.lumi)
            for x,y in self.subDatasetWeights.iteritems():
                f.write('%s: %i events, weight: %f\n' % (x,totalEventsForSubDataset[x],y))
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
        self.filters=collections.OrderedDict([('NoFilter',lambda event: True)])
        self.datasets=datasets
        self.weighted=False
        self.numberOfEvents=dict()
        self.palette=self._defaultPalette
        for dataset in datasets:
            self.numberOfEvents[dataset]=0
    def addFilter(self,name,function):
        self.filters.append((name,function))
    def setFilters(self,filters):
        self.filters=collections.OrderedDict(filters)
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
        for histogram in self.histogramList:
            histogram.setFilterNames(self.filters.keys())
        for dataset in self.datasets:
            for subDataset in self.DatasetDict[dataset]:
                for filename in self.subDatasetFiles[subDataset]:
                    self._fileHandle(dataset,subDataset,filename)
    def _fileHandle(self,dataset,subDataset,filename):
        if dataset!=self.currentDataset:
            for histogram in self.histogramList:
                histogram.switchDataset(self.tfile,dataset)
            self.currentDataset=dataset
        print "Opening file %s" % filename
        tmpTfile=ROOT.TFile(filename)
        tree=tmpTfile.Get(self.treeName)
        assert(self.weighted) #Always want weighting, really
        fileWeight=self.subDatasetWeights[subDataset]
        for event in tree:
            eventWeight=self.weightingFunction(event,dataset) if dataset!='Data' else 1
            eventWeight*=fileWeight
            filters=[x(event) for x in self.filters.itervalues()]
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
                histogram.Fill(event,filters,eventWeight)
    def finish(self,canvas):
        for histogram in self.histogramList:
            histogram.finish(canvas,self.outputDirectory)
        return
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
                    histogram.buildSummary(histogramDict,canvas,histogram.filterNames[filterNumber],vars(self),vars(histogram))
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
