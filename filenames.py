import glob

def _hadd(dataset):
    return 'ROOT_Files/ThreePhoton_%s.root' % dataset

def _notHadd(dataset):
    return glob.glob('crab_projects/*%s*/results/*.root' % dataset)

def _run2(dataset):
    return glob.glob('Run2_FlatQCD_NoPreselection/*%s*/results/*.root' % dataset)

def _wgFakes(version='v5'):
    def _wgFakesH(dataset):  
        return glob.glob('WGFakeRate%s/*%s*/results/*.root' % (version,dataset))
    return _wgFakesH

def getFilenamesFunction(identifier=None):
    if not identifier:
        if hadd:
            return _hadd
        else:
            return _notHadd
    else:
        try:
            return { 'hadd' : _hadd , 'notHadd' : _notHadd , 'Run2' : _run2 , 'WGFakeRate' : _wgFakes() , 'WGFakeRateOld' : _wgFakes('') }[identifier]
        except KeyError:
            return _wgFakes(identifier.split('FakeRate',1)[1])

fnf=getFilenamesFunction
