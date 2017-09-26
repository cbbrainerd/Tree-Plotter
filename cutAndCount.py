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

parameters=lambda:{
'analysis'     : 'WGFakeRate',
'datasets'     : ('WJetsToLNu','T+Jets','WZ+G+Jets','DYJetsToLL_amcatnlo','QCD','Data'),
'cutFilters'   : [lambda event:event.wm_mt > 80,lambda event:event.z_deltaR > 1.2 ,lambda event: event.minDeltaR_passCSVv2L > 1],
'countFilters' : {'MVA' : lambda event:event.g_mvaNonTrigValues > 0, 'PreselectionNoElectronVeto' : lambda event: event.g_passPreselectionNoElectronVeto > .5 ,'Preselection' : lambda event: event.g_passPreselection > .5,'PhotonId' : lambda event: event.g_passId > .5, 'PassPreselectionFailPhotonId' : lambda event: event.g_passPreselection and not event.g_passId, 'AllId' : lambda event: event.g_passPreselection and event.g_passId},
'function'     : (lambda event: (event.g_pt,), lambda event: (event.g_eta,), lambda event: (event.g_pt,event.g_eta)),
'histogram'    : (ROOT.TH1F('Fake Rate (Data)','Fake Rate;p_{T};Fake Rate',50,0,500),ROOT.TH1F('Fake Rate (Data)','Fake Rate;#eta;Fake Rate',50,-10,10),ROOT.TH2F('Fake Rate (Data)','Fake Rate;p_{T};Fake Rate',50,0,500,50,-10,10)),
'filename'     : 'Count_WGFakeRate',
'weighting'    : lambda event: event.genWeight*event.pileupWeight,
'luminosity'   : 35867.060,
}

info=inspect.getsourcelines(parameters)[0]
parameters=parameters()
parameters['info']=info
cutAndCount=counter(**parameters)
cutAndCount.addBranch('g_mvaNonTrigValues','mva','F')
cutAndCount.addBranch('g_passId','passPhotonId','I')
cutAndCount.addBranch('g_passPreselection','passPreselection','I')
cutAndCount.analyze()
