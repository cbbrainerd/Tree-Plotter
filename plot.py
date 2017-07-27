#!/usr/bin/env python
import ROOT
import sys
#import tdrstyle
#import CMS_lumi
import math

from Datasets import DatasetDict

from treePlotter import histogram as h
from treePlotter import treePlotter

def pts(x,y,binNumber=40,mini=0,maxi=1000,flavor=lambda x:"Events per %s GeV" % x):
    binSize=(maxi-mini)/binNumber
    myList="{0},{0};{1};{2}".format(x,y,flavor(binSize)).split(',')
    myList.extend([binNumber,mini,maxi])
    return myList

def bookHistograms(plot):
    def deltaPhi(phi1,phi2):
        absDP=abs(phi1-phi2)
        return 2*math.pi-absDP if absDP>math.pi else absDP
    plot.addHistogram(h(lambda event: event.g1_pt,None,*pts('Leading photon p_T','p_T')))
    plot.addHistogram(h(lambda event: event.g2_pt,None,*pts('Subleading photon p_T','p_T')))
    plot.addHistogram(h(lambda event: event.g3_pt,None,*pts('Third photon photon p_T','p_T')))
    plot.addHistogram(h(lambda event: event.g1_eta,None,*pts('Leading photon #eta','#eta')))
    plot.addHistogram(h(lambda event: event.g2_eta,None,*pts('Subleading photon #eta','#eta')))
    plot.addHistogram(h(lambda event: event.g3_eta,None,*pts('Third photon photon #eta','#eta')))
    plot.addHistogram(h(lambda event: event.g1_mvaNonTrigValues,None,*pts('Leading photon MVA','MVA',200,-1,1,lambda x:'')))
    plot.addHistogram(h(lambda event: event.g2_mvaNonTrigValues,None,*pts('Subleading photon MVA','MVA',200,-1,1,lambda x:'')))
    plot.addHistogram(h(lambda event: event.g3_mvaNonTrigValues,None,*pts('Third photon photon MVA','MVA',200,-1,1,lambda x:'')))
    plot.addHistogram(h(lambda event: deltaPhi(event.g1_phi,event.met_phi),None,*pts('#Delta#phi between MET and leading photon','MVA',100,0,math.pi,lambda x:'')))
    plot.addHistogram(h(lambda event: deltaPhi(event.g2_phi,event.met_phi),None,*pts('#Delta#phi between MET and subleading photon','MVA',100,0,math.pi,lambda x:'')))
    plot.addHistogram(h(lambda event: deltaPhi(event.g3_phi,event.met_phi),None,*pts('#Delta#phi between MET and third photon','MVA',100,0,math.pi,lambda x:'')))
    
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

datasets=('DiPhotonJetsBox_Sherpa','G+Jets','QCD')
tfile=ROOT.TFile('treePlotterOutput.root','RECREATE')
c1=ROOT.TCanvas()

plot=treePlotter(tfile,datasets)
bookHistograms(plot)

for dataset in datasets:
    files=['ROOT_Files/ThreePhoton_%s.root' % x for x in DatasetDict[dataset]]
    histogram=None
    for filename in files:
        plot.fileHandle(dataset,filename)
    plot.finish(c1)

tfile.Write()
tfile.Close()
