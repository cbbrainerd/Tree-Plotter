#!/bin/bash

''':'
if [ -n "$ROOTSYS" ]; then
    exec python "$0" "$@"
else 
    exec root6 python "$0" "$@"
fi
exit 1
'''

from counter import counterFunction as counter
import ROOT
import inspect
from array import array

from Datasets import DatasetDict
from math import pi


def parameters():
    class edict(dict): #Wrapper around a dict to act more like a CMS event object
        def __getattr__(self,name):
            return self[name]
    def trueProduct(e,branch):
        return getattr(e,'%s_pt' % branch) != 0
    def DeltaPhi(p1,p2):
        dphi=p1-p2
        if dphi > pi:
            return dphi-2*pi
        elif dphi < -pi:
            return dphi+2*pi
        else:
            return dphi
    def deltaR2(a,b):
        deltaPhi=DeltaPhi(a['phi'],b['phi'])
        deltaEta=a['eta']-b['eta']
        return deltaPhi**2+deltaEta**2
    def deltaR2Event(event,a,b):
        deltaPhi=DeltaPhi(getattr(event,'%s_phi'%a),getattr(event,'%s_phi'%b))
        deltaEta=getattr(event,'%s_eta'%a)-getattr(event,'%s_eta'%b)
        return deltaPhi**2+deltaEta**2
    def getCandidates(jets,photons):
        candidateList=[]
        for p in photons:
            closestJet=min(jets,key=lambda j: deltaR2(j,p))
            if deltaR2(closestJet,p) < .04:
                aVal=edict()
                for b in closestJet:
                    aVal['j_%s' % b]=closestJet[b]
                for b in p:
                    aVal['g_%s' % b]=p[b]
                candidateList.append(aVal)
        return candidateList
    def processMultiFunction(events):
        numberOfProducts=len(events)
        multiProducts=('g','j')
        singleProducts=('mm','met','m1','m2')
        branches=[x.GetName() for x in events[0].GetListOfBranches()]
        singleProductBranches=[]
        for x in singleProducts:
            singleProductBranches.extend([y for y in branches if y.split('_')[0] == x])
        multiProductBranches = { x : filter(lambda y: y.split('_')[0] == x,branches) for x in multiProducts }
        listOfX={ x : [] for x in multiProducts }
        for mp in multiProducts:
            for e in events:
                if trueProduct(e,mp):
                    listOfX[mp].append({ b.split('_',1)[1] : getattr(e,b) for b in multiProductBranches[mp]})
        candidates=getCandidates(listOfX['j'],listOfX['g'])
        for c in candidates:
            for b in singleProductBranches:
                c[b]=getattr(events[0],b)
        return candidates
    bins={
        'pt'       : array('f',[0,20,21,22,23,24,25,50,75,100,125,150,175,200,500]) ,
        'eta'      : array('f',[0,.5,1,1.479,2.0,2.5]) ,
    }
    Zmass=91.1876
    return {
        'analysis'     : 'ZFakeRate',
        'inputTreeName': 'WGFakeRateTree', #Whoops!
        'datasets'     : ('Data',),
        'cutFilters'   : [ lambda event: deltaR2Event(event,'j','m1') > 1 , lambda event: deltaR2Event(event,'j','m2') > 1  ], #Isolation between jet and muons
        'extraFilters' : {'preselection' : lambda event:event.g_passPreselection > .5 },
        'countFilters' : {'MVA' : lambda event:event.g_mvaNonTrigValues > 0, 'PreselectionNoElectronVeto' : lambda event: event.g_passPreselectionNoElectronVeto > .5, 'Preselection' : lambda event: event.g_passPreselection > .5,'PhotonId' : lambda event: event.g_passId > .5, 'PassPreselectionFailPhotonId' : lambda event: event.g_passPreselection and not event.g_passId, 'AllId' : lambda event: event.g_passPreselection and event.g_passId and event.g_mvaNonTrigValues > 0, 'lowMET' : lambda event: event.met_pt < 40 , 'highMET' : lambda event: event.met_pt >= 40 , },
        'function'     : (lambda event: (event.g_pt,), lambda event: (abs(event.g_eta),), lambda event: (event.g_pt,abs(event.g_eta))),
        'histogram'    : (ROOT.TH1F('Fake Rate vs. p_{T}','Fake Rate;p_{T};Fake Rate',len(bins['pt'])-1,bins['pt']),ROOT.TH1F('Fake Rate vs. #eta','Fake Rate;#eta;Fake Rate',len(bins['eta'])-1,bins['eta']),ROOT.TH2F('Fake Rate vs. p_{T} and #eta','Fake Rate;p_{T};#eta',len(bins['pt'])-1,bins['pt'],len(bins['eta'])-1,bins['eta'])),
        'filename'     : 'Count_ZFakeRate',
        'weighting'    : lambda event: event.genWeight*event.pileupWeight,
        'luminosity'   : 35867.060,
        'multiEvent'   : True,
        'globalFilter' : lambda event: abs(event.mm_mass - Zmass) < 2,
        'multiFunction': processMultiFunction,
    }

info=inspect.getsourcelines(parameters)[0]
parameters=parameters()
parameters['info']=info
cutAndCount=counter(**parameters)
cutAndCount.addBranch('g_mvaNonTrigValues','mva','F')
cutAndCount.addBranch('g_passId','passPhotonId','I')
cutAndCount.addBranch('g_passPreselection','passPreselection','I')
cutAndCount.addBranch('g_passPreselectionNoElectronVeto','passPreselectionNoElectronVeto','I')
cutAndCount.addBranch('g_pt','pt','F')
cutAndCount.addBranch('g_eta','eta','F')
cutAndCount.addBranch('met_pt','met','F')
cutAndCount.addBranch('candsInEvent','candsInEvent','I')
cutAndCount.analyze()
