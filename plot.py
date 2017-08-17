#!/bin/bash

#To do: set up some method to access already created plots

''':'
rm "treePlotter.pyc"
if [ -n "$ROOTSYS" ]; then
    exec python "$0" "$@"
else 
    exec root6 python "$0" "$@"
fi
exit 1
'''

import ROOT
import sys
#import tdrstyle
#import CMS_lumi
import math

from Datasets import DatasetDict

from treePlotter import histogram as h
from treePlotter import treePlotter

import filenames

import Plots.tdrstyle as tdrstyle

def pts(x,y,binNumber=40,mini=0,maxi=1000,flavor=lambda x:"Events per %s GeV" % x):
    binSize=(maxi-mini)/binNumber
    myList="{0},{0};{1};{2}".format(x,y,flavor(binSize)).split(',')
    myList.extend([binNumber,mini,maxi])
    return myList

def bookHistograms(plot,**kwargs):
    def deltaPhi(phi1,phi2):
        absDP=abs(phi1-phi2)
        return 2*math.pi-absDP if absDP>math.pi else absDP
    def MVAPass(event):
        retVal=0
        for n,MVA in enumerate((event.g1_mvaNonTrigValues,event.g2_mvaNonTrigValues,event.g3_mvaNonTrigValues)):
            retVal+=2**n if MVA > 0 else 0
        return retVal
    filters = { 'NoFilter' : [],
#                'tightMVAcut' : lambda event: max((event.g1_mvaNonTrigValues,event.g2_mvaNonTrigValues,event.g3_mvaNonTrigValues)) > .8,
#                'looseMVAcut' : lambda event: min((event.g1_mvaNonTrigValues,event.g2_mvaNonTrigValues,event.g3_mvaNonTrigValues)) > -.8,
                'g3_passPreselection' : [lambda event: event.g3_passPreselection == 1] }
    def stackPlotWithData(histogramDict,canvas,filterName):
        def COLOR(color):
            colorList=[ROOT.kRed, ROOT.kGreen, ROOT.kBlue, ROOT.kBlack, ROOT.kMagenta, ROOT.kCyan, ROOT.kOrange, ROOT.kGreen+2, ROOT.kRed-3, ROOT.kCyan+1, ROOT.kMagenta-3, ROOT.kViolet-1, ROOT.kSpring+10]
            return colorList[color % len(colorList)]
        canvas.cd()
        canvas.Clear()
        tdrstyle.setTDRStyle()
#        MCdatasets=('QCD','G+Jets','DiPhotonJetsBox_Sherpa')
        MCdatasets=[x for x in DatasetDict.keys() if ((not 'Data' in x) and (x in histogramDict.keys()))]
        ths=ROOT.THStack('fitstack','fitstack')
        ths.SetTitle(';;Whatever')
        binNames=['','FFF','PFF','FPF','PPF','FFP','PFP','FPP','PPP']
        for n,dataset in enumerate(MCdatasets):
            h=histogramDict[dataset]
            h.SetTitle(dataset)
            h.SetFillColorAlpha(COLOR(n),.5)
            for binNumber,binName in enumerate(binNames):
                if binNumber>0:
                    h.GetXaxis().SetBinLabel(binNumber,binName)
            ths.Add(h)  
        dataHist=histogramDict['Data']
        dataMax=dataHist.GetMaximum()
        thsMax=ths.GetMaximum()
        if dataMax > thsMax:
            dataHist.Draw('AXIS')
        else:
            ths.Draw('AXIS')
        ths.Draw('HIST SAME')
        dataHist.Draw('P SAME')
        for binNumber,binName in enumerate(binNames):
            if binNumber>0:
                dataHist.GetXaxis().SetBinLabel(binNumber,binName)
                ths.GetXaxis().SetBinLabel(binNumber,binName)
        canvas.BuildLegend()
        if(len(MCdatasets)==3):
            canvas.Print('TreePlots/Summary/Fit_%s.pdf' % filterName)
        else:
            canvas.Print('TreePlots/Summary/FitAllDatasets_%s.pdf' % filterName)
    plot.addHistogram(h(MVAPass,filters,'Fit','Fit',8,-.5,7.5,buildHistograms=lambda *args: None,buildSummary=stackPlotWithData))
#    def TwoDColorPlot(histogram):
    #plot.addHistogram(h(lambda event: (deltaPhi(event.g1_phi,event.met_phi),event.met_pt),None,'Leading photon: MET p_T vs #Delta#phi','Leading photon: MET p_T vs #Delta#phi;MET;Leading photon p_T',100,0,math.pi,1000,0,1000,histType=ROOT.TH2F))
    #plot.addHistogram(h(lambda event: (deltaPhi(event.g2_phi,event.met_phi),event.met_pt),None,'Subleading photon:MET p_T vs #Delta#phi','Subleading photon: MET p_T vs #Delta#phi;MET;Subleading photon p_T',100,0,math.pi,1000,0,1000,histType=ROOT.TH2F))
    #plot.addHistogram(h(lambda event: (deltaPhi(event.g3_phi,event.met_phi),event.met_pt),None,'Third photon: MET p_T vs #Delta#phi','Third photon: MET p_T vs #Delta#phi;MET;Third photon p_T',100,0,math.pi,1000,0,1000,histType=ROOT.TH2F))
#    plot.addHistogram(h(lambda event: max((event.g1_mvaNonTrigValues,event.g2_mvaNonTrigValues,event.g3_mvaNonTrigValues)),None,*pts('Max MVA','MVA',200,-1,1,lambda x:'')))
#    plot.addHistogram(h(lambda event: min((event.g1_mvaNonTrigValues,event.g2_mvaNonTrigValues,event.g3_mvaNonTrigValues)),None,*pts('Min MVA','MVA',200,-1,1,lambda x:'')))
#    plot.addHistogram(h(lambda event: sorted((event.g1_mvaNonTrigValues,event.g2_mvaNonTrigValues,event.g3_mvaNonTrigValues))[1],None,*pts('Middle MVA','MVA',200,-1,1,lambda x:'')))
    plot.addHistogram(h(lambda event: event.g1_pt,filters,*pts('Leading photon p_T','p_T')))
    plot.addHistogram(h(lambda event: event.g2_pt,filters,*pts('Subleading photon p_T','p_T')))
    plot.addHistogram(h(lambda event: event.g3_pt,filters,*pts('Third photon p_T','p_T')))
    passMVA1=lambda event: event.g1_mvaNonTrigValues > 0
    passMVA2=lambda event: event.g1_mvaNonTrigValues > 0
    passMVA3=lambda event: event.g1_mvaNonTrigValues > 0
    plot.addHistogram(h(lambda event: event.g1_pt,{x:list(y)+[passMVA1] for (x,y) in filters.iteritems()},*pts('Leading photon p_T: pass MVA','p_T')))
    plot.addHistogram(h(lambda event: event.g2_pt,{x:list(y)+[passMVA2] for (x,y) in filters.iteritems()},*pts('Subleading photon p_T: pass MVA','p_T')))
    plot.addHistogram(h(lambda event: event.g3_pt,{x:list(y)+[passMVA3] for (x,y) in filters.iteritems()},*pts('Third photon p_T: pass MVA','p_T')))
#    plot.addHistogram(h(lambda event: event.g1_eta,None,*pts('Leading photon #eta','#eta',100,0,5)))
#    plot.addHistogram(h(lambda event: event.g2_eta,None,*pts('Subleading photon #eta','#eta',100,0,5)))
#    plot.addHistogram(h(lambda event: event.g3_eta,None,*pts('Third photon photon #eta','#eta',100,0,5)))
#    plot.addHistogram(h(lambda event: event.g1_mvaNonTrigValues,None,*pts('Leading photon MVA','MVA',200,-1,1,lambda x:'')))
#    plot.addHistogram(h(lambda event: event.g2_mvaNonTrigValues,None,*pts('Subleading photon MVA','MVA',200,-1,1,lambda x:'')))
#    plot.addHistogram(h(lambda event: event.g3_mvaNonTrigValues,None,*pts('Third photon photon MVA','MVA',200,-1,1,lambda x:'')))
#    plot.addHistogram(h(lambda event: deltaPhi(event.g1_phi,event.met_phi),None,*pts('#Delta#phi between MET and leading photon','MVA',100,0,math.pi,lambda x:'')))
#    plot.addHistogram(h(lambda event: deltaPhi(event.g2_phi,event.met_phi),None,*pts('#Delta#phi between MET and subleading photon','MVA',100,0,math.pi,lambda x:'')))
#    plot.addHistogram(h(lambda event: deltaPhi(event.g3_phi,event.met_phi),None,*pts('#Delta#phi between MET and third photon','MVA',100,0,math.pi,lambda x:'')))
#    plot.addHistogram(h(lambda event: min([deltaPhi(x,event.met_phi) for x in (event.g1_phi,event.g2_phi,event.g3_phi)]),None,*pts('min(#Delta#phi) photon to MET','MVA',100,0,math.pi,lambda x:'')))
#    plot.addHistogram(h(lambda event: max([deltaPhi(x,event.met_phi) for x in (event.g1_phi,event.g2_phi,event.g3_phi)]),None,*pts('max(#Delta#phi) photon to MET','MVA',100,0,math.pi,lambda x:'')))
#    plot.addHistogram(h(lambda event: sorted([deltaPhi(x,event.met_phi) for x in (event.g1_phi,event.g2_phi,event.g3_phi)],key=lambda y:abs(math.pi/2-y))[0],None,*pts('#Delta#phi of least parallel photon to MET','MVA',100,0,math.pi,lambda x:'')))
#    plot.addHistogram(h(lambda event: sorted([deltaPhi(x,event.met_phi) for x in (event.g1_phi,event.g2_phi,event.g3_phi)],key=lambda y:abs(math.pi/2-y))[-1],None,*pts('#Delta#phi of most parallel photon to MET','MVA',100,0,math.pi,lambda x:'')))
    allHistograms=plot.histogramList
    def MVA_Filter(photon,cut,greaterThan=True):
        if photon in [1,2,3]:
            return eval ("lambda event:event.g%d_mvaNonTrigValues %s %s" % (photon,">" if greaterThan else "<=",cut))
    cuts= {
    'LooseMVA' : MVA_Filter(1,-.2),
    'TightMVA' : MVA_Filter(1,.8),
    'LooseInvertedMVA' : MVA_Filter(1,-.2,False),
    'TightInvertedMVA' : MVA_Filter(1,.8,False)
    }
#    for name,cut in cuts.iteritems(): #Do some MVA cuts
#        for histogram in allHistograms:
#            histogram.addEventFilter(name,cut)
    print "%d histograms booked!" % len(plot.histogramList)
    
def sortHistograms(histogramList):
    histogramList.sort(key=lambda hist:hist.Integral())
    return histogramList

def getHistograms(tfile):
    return [x.ReadObj() for x in tfile.GetListOfKeys() if 'ROOT.TH1' in str(x.ReadObj())]

def getUsedMCHistograms(histogramList):
    return [x for x in histogramList if x.GetName() not in ['mc','data'] and 'unused' not in x.GetName()]

def myPalette(color):
#    return ROOT.gROOT.GetColor(color+2)
#    return color+2
    colorList=[ROOT.kRed, ROOT.kGreen, ROOT.kBlue, ROOT.kBlack, ROOT.kMagenta, ROOT.kCyan, ROOT.kOrange, ROOT.kGreen+2, ROOT.kRed-3, ROOT.kCyan+1, ROOT.kMagenta-3, ROOT.kViolet-1, ROOT.kSpring+10]
    return colorList[color % len(colorList)]

tfile=ROOT.TFile('treePlotterOutput.root','UPDATE')
c1=ROOT.TCanvas()

ff=filenames.getFilenamesFunction(False)
datasets=('DiPhotonJetsBox_Sherpa','G+Jets','QCD','Data')
plot=treePlotter(tfile,datasets,35867.060,ff)
plot.setWeightingFunction(lambda event: event.genWeight*event.pileupWeight)
bookHistograms(plot)
plot.process()
plot.finish(c1)

c1=ROOT.TCanvas()

ff=filenames.getFilenamesFunction(False)
datasets=DatasetDict.keys()
plot=treePlotter(tfile,datasets,35867.060,ff)
plot.setWeightingFunction(lambda event: event.genWeight*event.pileupWeight)
bookHistograms(plot)
plot.process()
plot.finish(c1)
def ratioPlot(*args,**kwargs):
    plotName=kwargs.pop('name')
    h1=kwargs.pop('h1')
    h2=kwargs.pop('h2')
    canvas=kwargs.pop('canvas')
    tfile=kwargs.pop('tfile')
    tfile.cd()
    canvas.cd()
    whichPhoton=h1.name.split('p_T')[0]
    filters=h1.filterNames
    for number,filt in enumerate(h1.filterNames):
        histogramDict1=h1.histograms[number]
        histogramDict2=h2.histograms[number]
        for dataset in histogramDict1.iterkeys():
            h=histogramDict1[dataset].Clone()
            h.Divide(histogramDict2[dataset])
            h.Draw()
            canvas.Print('TreePlots/%s_%s_%s.pdf' % (plotName,dataset,filt))

for photon in ('Leading photon','Subleading photon','Third photon'):
    try:
        plot.postProcess(ratioPlot,plotName='FakeRate',h1='%s p_T' % photon,h2='%s p_T: pass MVA' % photon,canvas=c1,tfile=tfile)
    except Exception:
        pass

#plot.addHistogram(h(lambda event: event.g1_pt,filters,*pts('Leading photon p_T','p_T')))
#plot.addHistogram(h(lambda event: event.g2_pt,filters,*pts('Subleading photon p_T','p_T')))
#plot.addHistogram(h(lambda event: event.g3_pt,filters,*pts('Third photon photon p_T','p_T')))
tfile.Write()
tfile.Close()
