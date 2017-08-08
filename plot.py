#!/bin/bash

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
    plot.addHistogram(h(lambda event: event.g1_eta,None,*pts('Leading photon #eta','#eta',100,0,5)))
    plot.addHistogram(h(lambda event: event.g2_eta,None,*pts('Subleading photon #eta','#eta',100,0,5)))
    plot.addHistogram(h(lambda event: event.g3_eta,None,*pts('Third photon photon #eta','#eta',100,0,5)))
    plot.addHistogram(h(lambda event: event.g1_mvaNonTrigValues,None,*pts('Leading photon MVA','MVA',200,-1,1,lambda x:'')))
    plot.addHistogram(h(lambda event: event.g2_mvaNonTrigValues,None,*pts('Subleading photon MVA','MVA',200,-1,1,lambda x:'')))
    plot.addHistogram(h(lambda event: event.g3_mvaNonTrigValues,None,*pts('Third photon photon MVA','MVA',200,-1,1,lambda x:'')))
    plot.addHistogram(h(lambda event: deltaPhi(event.g1_phi,event.met_phi),None,*pts('#Delta#phi between MET and leading photon','MVA',100,0,math.pi,lambda x:'')))
    plot.addHistogram(h(lambda event: deltaPhi(event.g2_phi,event.met_phi),None,*pts('#Delta#phi between MET and subleading photon','MVA',100,0,math.pi,lambda x:'')))
    plot.addHistogram(h(lambda event: deltaPhi(event.g3_phi,event.met_phi),None,*pts('#Delta#phi between MET and third photon','MVA',100,0,math.pi,lambda x:'')))
    plot.addHistogram(h(lambda event: min([deltaPhi(x,event.met_phi) for x in (event.g1_phi,event.g2_phi,event.g3_phi)]),None,*pts('min(#Delta#phi) photon to MET','MVA',100,0,math.pi,lambda x:'')))
    plot.addHistogram(h(lambda event: max([deltaPhi(x,event.met_phi) for x in (event.g1_phi,event.g2_phi,event.g3_phi)]),None,*pts('max(#Delta#phi) photon to MET','MVA',100,0,math.pi,lambda x:'')))
    plot.addHistogram(h(lambda event: sorted([deltaPhi(x,event.met_phi) for x in (event.g1_phi,event.g2_phi,event.g3_phi)],key=lambda y:abs(math.pi/2-y))[0],None,*pts('#Delta#phi of least parallel photon to MET','MVA',100,0,math.pi,lambda x:'')))
    plot.addHistogram(h(lambda event: sorted([deltaPhi(x,event.met_phi) for x in (event.g1_phi,event.g2_phi,event.g3_phi)],key=lambda y:abs(math.pi/2-y))[-1],None,*pts('#Delta#phi of most parallel photon to MET','MVA',100,0,math.pi,lambda x:'')))
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
    for name,cut in cuts.iteritems(): #Do some MVA cuts
        for histogram in allHistograms:
            histogram.addEventFilter(name,cut)
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

datasets=('DiPhotonJetsBox_Sherpa','G+Jets','QCD')
tfile=ROOT.TFile('treePlotterOutput.root','RECREATE')
c1=ROOT.TCanvas()

fl=[]
for dataset in datasets:
    fl.extend(['ROOT_Files/ThreePhoton_%s.root' % x for x in DatasetDict[dataset]])
plot=treePlotter(tfile,datasets,35867.060,fl)
plot.setWeightingFunction(lambda event: event.genWeight*event.pileupWeight)
bookHistograms(plot)

for dataset in datasets:
    files=['ROOT_Files/ThreePhoton_%s.root' % x for x in DatasetDict[dataset]]
    histogram=None
    for filename in files:
        plot.fileHandle(dataset,filename)
plot.finish(c1)

tfile.Write()
tfile.Close()
