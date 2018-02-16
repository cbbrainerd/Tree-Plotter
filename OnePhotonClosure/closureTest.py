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
fakerateWeight=_closureTestWeight('../FR_3_NEW.root','Fake vs. p_{T} and #eta_Data_AllId','Fake vs. p_{T} and #eta_Data_AllId_ExtraFilter_preselection')

Dataset='ZeroBias'

tfileout=ROOT.TFile("closureTest.root","RECREATE")
filenames=filenames(Dataset)('ZeroBias')

bins= {
'pt'       : array('f',[0,20,40,60,80,100,125,150,175,200,500]) ,
'eta'      : array('f',[0,.5,1,1.479,2.0,2.5]) ,
}

histogram=(ROOT.TH1F('Fake vs. p_{T}','Fake;p_{T};Fake',len(bins['pt'])-1,bins['pt']),ROOT.TH1F('Fake vs. #eta','Fake;|#eta|;Fake',len(bins['eta'])-1,bins['eta']),ROOT.TH2F('Fake vs. p_{T} and #eta','Fake;p_{T};|#eta|',len(bins['pt'])-1,bins['pt'],len(bins['eta'])-1,bins['eta']))
function=(lambda event,w: (event.g_pt,w), lambda event,w: (abs(event.g_eta),w), lambda event,w: (event.g_pt,abs(event.g_eta),w))

for hist in histogram:
    print hist
    hist.SetDirectory(tfileout)

print tfileout

for num,fn in enumerate(filenames):
    print "Opening tfile %d/%d..." % (num+1,len(filenames))
    tmpTFile=ROOT.TFile(fn)
    ttree=tmpTFile.Get("OnePhotonTree")
    for event in ttree:
        if event.g_pt < 20: continue
        weight=fakerateWeight(event,'ZeroBias')
        for hist,func in itertools.izip(histogram,function):
                hist.Fill(*func(event,weight))

tfileout.cd()
for hist in histogram:
    hist.Write()
