import glob

def _hadd(dataset):
    return 'ROOT_Files/ThreePhoton_%s.root' % dataset

def _notHadd(dataset):
    return glob.glob('crab_projects/*%s*/results/*.root' % dataset)

def _run2(dataset):
    return glob.glob('Run2_FlatQCD_NoPreselection/*%s*/results/*.root' % dataset)

def _wgFakes(dataset):  
    return glob.glob('WGFakeRate/*%s*/results/*.root' % dataset)

def getFilenamesFunction(identifier=None):
    if not identifier:
        if hadd:
            return _hadd
        else:
            return _notHadd
    else:
        return { 'hadd' : _hadd , 'notHadd' : _notHadd , 'Run2' : _run2 , 'WGFakeRate' : _wgFakes }[identifier]
