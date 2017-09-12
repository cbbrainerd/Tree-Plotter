import glob

def _hadd(dataset):
    return 'ROOT_Files/ThreePhoton_%s.root' % dataset

def _notHadd(dataset):
    return glob.glob('crab_projects/*%s*/results/*.root' % dataset)

def _run2(dataset):
    return glob.glob('Run2_FlatQCD_NoPreselection/*%s*/results/*.root' % dataset)

def _wgFakes(version='v6'):
    if version!='v6':
        raise ValueError(version)
    def _wgFakesH(dataset):  
        return glob.glob('WGFakeRate%s/*%s*/results/*.root' % (version,dataset))
    return _wgFakesH

def getFilenamesFunction(identifier=None,version='v6'):
    if not identifier:
        if hadd:
            return _hadd
        else:
            return _notHadd
    else:
        try:
            return { 'hadd' : _hadd , 'notHadd' : _notHadd , 'Run2' : _run2 , 'WGFakeRate' : _wgFakes, }[identifier](version)
        except KeyError:
            raise

fnf=getFilenamesFunction
