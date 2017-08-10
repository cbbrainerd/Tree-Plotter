Root_Files='''
ThreePhoton_DiPhotonJetsBox_M40_80-Sherpa.root
ThreePhoton_DiPhotonJetsBox_MGG-80toInf_13TeV-Sherpa.root
ThreePhoton_DiPhotonJets_MGG-80toInf_13TeV_amcatnloFXFX_pythia8.root
ThreePhoton_DoubleEG.root
ThreePhoton_DoubleMuon.root
ThreePhoton_DYJetsToLL_M-10to50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8.root
ThreePhoton_DYJetsToLL_M-10to50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8.root
ThreePhoton_DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_SingleElectron.root
ThreePhoton_SinglePhoton.root
ThreePhoton_TGJets_TuneCUETP8M1_13TeV_amcatnlo_madspin_pythia8.root
ThreePhoton_TTGG_0Jets_TuneCUETP8M1_13TeV_amcatnlo_madspin_pythia8.root
ThreePhoton_TTGJets_TuneCUETP8M1_13TeV-amcatnloFXFX-madspin-pythia8.root
ThreePhoton_TTJets_DiLept_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_TTJets_SingleLeptFromTbar_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_TTJets_SingleLeptFromT_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_W1JetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_W2JetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_W3JetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_W4JetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_WGG_5f_TuneCUETP8M1_13TeV-amcatnlo-pythia8.root
ThreePhoton_WGGJets_TuneCUETP8M1_13TeV_madgraphMLM_pythia8.root
ThreePhoton_WGToLNuG_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8.root
ThreePhoton_WGToLNuG_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_WJetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root
ThreePhoton_WWG_TuneCUETP8M1_13TeV-amcatnlo-pythia8.root
ThreePhoton_WZG_TuneCUETP8M1_13TeV-amcatnlo-pythia8.root
ThreePhoton_ZGGJetsToLLGG_5f_LO_amcatnloMLM_pythia8.root
ThreePhoton_ZGGJets_ZToHadOrNu_5f_LO_madgraph_pythia8.root
ThreePhoton_ZGGToLLGG_5f_TuneCUETP8M1_13TeV-amcatnlo-pythia8.root
ThreePhoton_ZGGToNuNuGG_5f_TuneCUETP8M1_13TeV-amcatnlo-pythia8.root
ThreePhoton_ZGTo2LG_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8.root'''.split('\n')

DatasetDict= {
    'DYJetsToLL_madgraphMLM' : [ 'DYJetsToLL_M-10to50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' ],
    'DYJetsToLL_amcatnlo' : [ 'DYJetsToLL_M-10to50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8' , 'DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8' ],
    'DiPhotonJetsBox_Sherpa' : [ 'DiPhotonJetsBox_M40_80-Sherpa' , 'DiPhotonJetsBox_MGG-80toInf_13TeV-Sherpa' ],
    'DiPhotonJets_amcatnlo' : [ 'DiPhotonJets_MGG-80toInf_13TeV_amcatnloFXFX_pythia8' ],
    'T+Jets' : [ 'TTJets_DiLept_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'TTJets_SingleLeptFromT_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'TTJets_SingleLeptFromTbar_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' ],
    'T+G+Jets' : [ 'TGJets_TuneCUETP8M1_13TeV_amcatnlo_madspin_pythia8' , 'TTGG_0Jets_TuneCUETP8M1_13TeV_amcatnlo_madspin_pythia8' , 'TTGJets_TuneCUETP8M1_13TeV-amcatnloFXFX-madspin-pythia8' ],
    'W+Jets' : [ 'W1JetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'W2JetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'W3JetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'W4JetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'WJetsToLNu_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' ],
    'W/Z+G+Jets' : [ 'WGGJets_TuneCUETP8M1_13TeV_madgraphMLM_pythia8' , 'WGG_5f_TuneCUETP8M1_13TeV-amcatnlo-pythia8' , 'WGToLNuG_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8' , 'WGToLNuG_TuneCUETP8M1_13TeV-madgraphMLM-pythia8' , 'WWG_TuneCUETP8M1_13TeV-amcatnlo-pythia8' ,'WZG_TuneCUETP8M1_13TeV-amcatnlo-pythia8' ,'ZGGJetsToLLGG_5f_LO_amcatnloMLM_pythia8' ,'ZGGJets_ZToHadOrNu_5f_LO_madgraph_pythia8' ,'ZGGToLLGG_5f_TuneCUETP8M1_13TeV-amcatnlo-pythia8' ,'ZGGToNuNuGG_5f_TuneCUETP8M1_13TeV-amcatnlo-pythia8' ,'ZGTo2LG_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8' ],
    'G+Jets' : [ 'GJet_Pt-20to40_DoubleEMEnriched_MGG-80toInf_TuneCUETP8M1_13TeV_Pythia8' , 'GJet_Pt-20toInf_DoubleEMEnriched_MGG-40to80_TuneCUETP8M1_13TeV_Pythia8' , 'GJet_Pt-40toInf_DoubleEMEnriched_MGG-80toInf_TuneCUETP8M1_13TeV_Pythia8' ],
    'QCD' : ['QCD_Pt-30to40_DoubleEMEnriched_MGG-80toInf_TuneCUETP8M1_13TeV_Pythia8' , 'QCD_Pt-30toInf_DoubleEMEnriched_MGG-40to80_TuneCUETP8M1_13TeV_Pythia8' , 'QCD_Pt-40toInf_DoubleEMEnriched_MGG-80toInf_TuneCUETP8M1_13TeV_Pythia8' ]
}
