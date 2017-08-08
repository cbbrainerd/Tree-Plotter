#!/usr/bin/env python
import ROOT
import time
try:
    from DevTools.Plotter.xsec import getXsec
except ImportError:
    try:
        from DevTools.Plotter.python.xsec import getXsec
    except ImportError:
        print "getXsec could not be imported."
        print "Weighting cannot be done properly without getXsec."
        raise

class histogram:
    def __init__(self,fillFunction=None,eventFilters=None,*args):
        self.fillFunction=fillFunction
        if args:
            self.args=args
        else:
            self.args=None
        self.histograms=[dict()]
        self.histType=ROOT.TH1F
        self.name=None
        self.title=None
        self.filterNames=['NoFilter']
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
    def setName(self,name):
        self.name=name
    def setFillFunction(self,function): #Function that takes histogram as one argument, 
        self.fillFunction=function
    def Fill(self,tfile,dataset,event,weight=1):
#        if not self.isValid(): Don't bother checking anymore
#            return False
        fillValue=self.fillFunction(event)
        retVal=None
        for number,eventFilterSet in enumerate(self.eventFilters):
            for eventFilter in eventFilterSet:
                if not eventFilter(event):
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
    def setWeightingFunction(self,wf):
        self.weightingFunction=wf
        self.weighted=True
    def fileHandle(self,dataset,filename):
        print "Opening file %s" % filename
        tmpTfile=ROOT.TFile(filename)
        tree=tmpTfile.Get("ThreePhotonTree")
        numberOfEvents=tmpTfile.summedWeights.GetBinContent(1)
        xsec=getXsec(filename.split('/')[-1].replace("ThreePhoton_","",1).replace(".root","",1))
        fileWeight=xsec*self.lumi/float(numberOfEvents)
        print "File weight:",fileWeight
        for event in tree:
            eventWeight=self.weightingFunction(event) if self.weighted else 1
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
            canvas.cd()
            for dataset,hist in histogram.histograms.iteritems():
                hist.SetLineColor(self.color(0))
                hist.Draw("HIST")
                canvas.Print('TreePlots/%s_%s.pdf' % (histogram.title,dataset))
            if True:
                ROOT.gStyle.SetOptStat(0)
                ROOT.gROOT.ForceStyle()
                for number,hist in enumerate(histogram.histograms.itervalues()):
                    hist.SetLineColor(self.color(number))
                    events=hist.Integral()
                    hist.Scale(1/float(events))
                for number,hists in enumerate(sorted(histogram.histograms.itervalues(),key=lambda h: h.GetMaximum(),reverse=True)):
                    if number==0:
                        hist.Draw("HIST")
                    else:
                        hist.Draw("HIST SAME")
                canvas.BuildLegend()
                canvas.Print('TreePlots/Summary/%s.pdf' % (histogram.title))
