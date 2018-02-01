#!/bin/bash

''':'
if [ -n "$ROOTSYS" ]; then
    exec python "$0" "$@"
else 
    exec root6 python "$0" "$@"
fi
exit 1
'''

from filenames import fnf as filenames
import ROOT
from array import array
import itertools

def _closureTestWeight(filename,fakeratePFHist,fakerateTriggerHist):
    tmpTFile=ROOT.TFile(filename)
    tmpHist=tmpTFile.Get(fakeratePFHist)
    fakerateHistPF=tmpHist.Clone()
    fakerateHistPF.SetDirectory(0)
    tmpHist=tmpTFile.Get(fakerateTriggerHist)
    fakerateHistTrigger=tmpHist.Clone()
    fakerateHistTrigger.SetDirectory(0)
    def getFakeRatePF(pt,eta):
        return fakerateHistPF.GetBinContent(fakerateHistPF.FindBin(pt,eta))
    def getFakeRateTrigger(pt,eta):
        return fakerateHistTrigger.GetBinContent(fakerateHistTrigger.FindBin(pt,eta))
    def getEventWeight(event,dataset):
        return getFakeRatePF(event.g_pt,event.g_eta)
    return getEventWeight
fakerateWeight=_closureTestWeight('../COUNT_FAKE_RATE_19.root','Fake Rate vs. p_{T} and #eta_Data_AllId','Fake Rate vs. p_{T} and #eta_Data_AllId_ExtraFilter_preselection')

Dataset='ZeroBias'

tfileout=ROOT.TFile("closureTest.root","RECREATE")
filenames=filenames(Dataset)('ZeroBias')

bins= {
'pt'       : array('f',[0,25,50,75,100,125,150,175,200,500]) ,
'eta'      : array('f',[-2.5,-2.0,-1.479,-1,-.5,0,.5,1,1.479,2.0,2.5]) ,
}

histogram=(ROOT.TH1F('Fake Rate vs. p_{T}','Fake Rate;p_{T};Fake Rate',len(bins['pt'])-1,bins['pt']),ROOT.TH1F('Fake Rate vs. #eta','Fake Rate;#eta;Fake Rate',len(bins['eta'])-1,bins['eta']),ROOT.TH2F('Fake Rate vs. p_{T} and #eta','Fake Rate;p_{T};#eta',len(bins['pt'])-1,bins['pt'],len(bins['eta'])-1,bins['eta']))
function=(lambda event,w: (event.g_pt,w), lambda event,w: ((event.g_eta),w), lambda event,w: (event.g_pt,(event.g_eta),w))

for hist in histogram:
    print hist
    hist.SetDirectory(tfileout)

print tfileout

for fn in filenames:
    tmpTFile=ROOT.TFile(fn)
    ttree=tmpTFile.Get("OnePhotonTree")
    for event in ttree:
        weight=fakerateWeight(event,'ZeroBias')
        for hist,func in itertools.izip(histogram,function):
            hist.Fill(*func(event,weight))

tfileout.cd()
for hist in histogram:
    hist.Write()
