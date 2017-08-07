#!/usr/bin/env python
import ROOT
try:
    from DevTools-Plotting.python.xsec import getXsec
except ImportError:
    try:
        from DevTools.Plotter.xsec import getXsec
    except ImportError:
        getXsec=None

class histogram:
    def __init__(self,fillFunction=None,eventFilter=None,*args):
        self.fillFunction=fillFunction
        if args:
            self.args=args
        else:
            self.args=None
        self.histograms=dict()
        self.histType=ROOT.TH1F
        self.name=None
        self.title=None
        try:
            self.name=args[0]
            self.title=args[1]
        except IndexError:
            pass
        if not eventFilter:
            self.eventFilters=[] #List of lambdas or functions that return True if the event should be accepted. Requires an AND of all such filters
    def addEventFilter(self,function):
        self.eventFilters.append(function)
    def hist(self,*args):
        self.args=args
    def setType(self,rootType):
        self.histType=rootType
    def setTitle(self,title):
        self.title=title
    def setName(self,name):
        self.name=name
    def setFillFunction(self,function): #Function that takes histogram as one argument, 
        self.fillFunction=function
    def Fill(self,tfile,dataset,event,weight=1):
        if not self.isValid():
            return False
        for eventFilter in self.eventFilters:
            if not eventFilter(event):
                continue
        try:
            fillHist=self.histograms[dataset]
        except KeyError:
            myArgs=list(self.args)
            myArgs[0]=self.name+'_'+dataset
            titleList=self.title.split(';')
            titleList[0]+='_'+dataset
            myArgs[1]=';'.join(titleList)
            tfile.cd()
            self.histograms[dataset]=self.histType(*myArgs)
            print '%s booked!' % self.histograms[dataset]
            fillHist=self.histograms[dataset]
        return self.histograms[dataset].Fill(self.fillFunction(event),weight)
    def isValid(self):
        return self.args and self.histType and self.name and self.title and self.fillFunction

class treePlotter:
    def __init__(self,tfile,datasets):
        self.histogramList=[]
        self.tfile=tfile
        self.datasets=datasets
        self.weighted=False
        self.lumi=None
        self.numberOfEvents=dict()
        for dataset in datasets
            self.numberOfEvents[dataset]=0
    def addHistogram(self,histogram):
        self.histogramList.append(histogram)       
    def setWeightingFunction(self,wf):
        self.weightingFunction=wf
        self.weighted=True
    def setLuminosity(self,lumi)
        self.lumi=lumi
    def fileHandle(self,dataset,filename):
        print "Opening file %s" % filename
        tmpTfile=ROOT.TFile(filename)
        tree=tmpTfile.Get("ThreePhotonTree")
        eventCount=0
        self.numberOfEvents[dataset]+=tmpTfile.summedWeights.GetBinContent(1)
        for event in tree:
            eventWeight=self.weightingFunction(event) if self.weighted else 1
            eventCount+=1
            if(eventCount%10000 == 0):
                print eventCount
            for histogram in self.histogramList:
                histogram.Fill(self.tfile,dataset,event,eventWeight)
    def finish(self,canvas):
        for histogram in self.histogramList:
            canvas.cd()
            constant=ROOT.TF1('tmp','1')
            for dataset,hist in histogram.histograms.iteritems():
                hist.Draw()
                canvas.Print('TreePlots/%s_%s.pdf' % (histogram.title,dataset))
                if self.lumi:
                    datasetWeight=getXsec(dataset)*self.lumi/float(self.numberOfEvents[dataset])
                    hist.Multiply(constant,datasetWeight)
            if self.lumi:
                canvas.Clear()
                for dataset,hist in histogram.histograms.iteritems():
                    hist.Draw("SAME")
                canvas.BuildLegend()
                canvas.Print('TreePlots/Summary/%s.pdf' % (histogram.title))
