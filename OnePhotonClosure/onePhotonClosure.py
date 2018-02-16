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

bins= {
'pt'       : array('f',[0,20,25,50,75,100,125,150,175,200,500]) ,
'eta'      : array('f',[0,.5,1,1.479,2.0,2.5]) ,
#'pt'       : array('f',[0,200,500]) ,
#'eta'      : array('f',[0,1.479,2.5]) ,
}

parameters=lambda:{
'analysis'     : 'OnePhotonClosure',
'inputTreeName': 'OnePhotonTree',
'datasets'     : ('ZeroBias',),
'cutFilters'   : [lambda event: not (event.g_pt < 20),lambda event: abs(event.g_eta) < 2.5],
'extraFilters' : {'preselection' : lambda event:event.g_passPreselection > .5,'barrel' : lambda event:abs(event.g_eta) < 1.479 , 'endcap' : lambda event:abs(event.g_eta) > 1.479},
'countFilters' : {'MVA' : lambda event:event.g_mvaNonTrigValues > 0, 'PreselectionNoElectronVeto' : lambda event: event.g_passPreselectionNoElectronVeto > .5, 'Preselection' : lambda event: event.g_passPreselection > .5,'PhotonId' : lambda event: event.g_passId > .5, 'PassPreselectionFailPhotonId' : lambda event: event.g_passPreselection and not event.g_passId, 'AllId' : lambda event: event.g_passPreselection and event.g_passId and event.g_mvaNonTrigValues > 0},
'function'     : (lambda event: (event.g_pt,), lambda event: (abs(event.g_eta),), lambda event: (event.g_pt,abs(event.g_eta))),
'histogram'    : (ROOT.TH1F('Fake Rate vs. p_{T}','Fake Rate;p_{T};Fake Rate',len(bins['pt'])-1,bins['pt']),ROOT.TH1F('Fake Rate vs. #eta','Fake Rate;#eta;Fake Rate',len(bins['eta'])-1,bins['eta']),ROOT.TH2F('Fake Rate vs. p_{T} and #eta','Fake Rate;p_{T};#eta',len(bins['pt'])-1,bins['pt'],len(bins['eta'])-1,bins['eta'])),
'filename'     : 'Count_OnePhotonClosure',
'weighting'    : lambda event: event.genWeight*event.pileupWeight,
'luminosity'   : 35867.060,
'coarseBinning'        : True
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
cutAndCount.analyze()
