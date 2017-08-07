#!/usr/bin/env python
import ROOT
try:
    from DevTools.Plotter.xsec import getXsec
except ImportError:
    try:
        from DevTools.Plotter.python.xsec import getXsec
    except ImportError:
        getXsec=None
        print "getXsec could not be imported."
        raise

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
    def _defaultPalette(_,color):
        colorList=[ROOT.kRed, ROOT.kGreen, ROOT.kBlue, ROOT.kBlack, ROOT.kMagenta, ROOT.kCyan, ROOT.kOrange, ROOT.kGreen+2, ROOT.kRed-3, ROOT.kCyan+1, ROOT.kMagenta-3, ROOT.kViolet-1, ROOT.kSpring+10]
        return colorList[color % len(colorList)]
    def __init__(self,tfile,datasets,luminosity):
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
    def setWeightingFunction(self,wf):
        self.weightingFunction=wf
        self.weighted=True
    def fileHandle(self,dataset,filename):
        print "Opening file %s" % filename
        tmpTfile=ROOT.TFile(filename)
        tree=tmpTfile.Get("ThreePhotonTree")
        eventCount=0
        numberOfEvents=tmpTfile.summedWeights.GetBinContent(1)
        xsec=getXsec(filename.split('/')[-1].replace("ThreePhoton_","",1).replace(".root","",1))
        fileWeight=xsec*self.lumi/float(numberOfEvents)
        print "File weight:",fileWeight
        for event in tree:
            eventWeight=self.weightingFunction(event) if self.weighted else 1
            eventWeight*=fileWeight
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
                hist.SetLineColor(self.color(0))
                hist.Draw("HIST")
                canvas.Print('TreePlots/%s_%s.pdf' % (histogram.title,dataset))
            if self.lumi:
                for number,hist in enumerate(histogram.histograms.itervalues()):
                    hist.SetLineColor(self.color(number))
                    if number==0:
                        hist.Draw("HIST")
                    else:
                        hist.Draw("HIST SAME")
                canvas.BuildLegend()
                canvas.Print('TreePlots/Summary/%s.pdf' % (histogram.title))
