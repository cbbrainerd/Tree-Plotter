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

cutAndCount=counter(analysis='WGFakeRate',datasets=('WJetsToLNu','T+Jets','WZ+G+Jets','DYJetsToLL_amcatnlo','QCD','Data'),cutFilters=[lambda event:event.wm_mt > 80,lambda event:event.z_deltaR > 1,lambda event: event.minDeltaR_passCSVv2L > 1 or event.minDeltaR_passCSVv2L < 0],countFilters={'MVA' : lambda event:event.g_mvaNonTrigValues > 0, 'PreselectionNoElectronVeto' : lambda event: event.g_passPreselectionNoElectronVeto > .5 ,'Preselection' : lambda event: event.g_passPreselection > .5,'PhotonId' : lambda event: event.g_passId > .5},function=lambda event: event.g_pt,histogram=ROOT.TH1F('hist','hist',500,0,500))
cutAndCount.addBranch('g_mvaNonTrigValues','mva','F')
cutAndCount.analyze()
