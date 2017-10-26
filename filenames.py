import glob

g_dataset=None
g_version=None

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

def _ThreePhoton(version='v3'):
    def _ThreePhotonH(dataset):
        return glob.glob('ThreePhoton%s/*%s*/results/*.root' % (version,dataset))
    return _ThreePhotonH

def getFilenamesFunction(identifier=None,version='v6'):
    global g_dataset
    global g_version
    g_dataset=identifier
    g_version=version
    if not identifier:
        if hadd:
            return _hadd
        else:
            return _notHadd
    else:
        try:
            return { 'hadd' : _hadd , 'notHadd' : _notHadd , 'Run2' : _run2 , 'WGFakeRate' : _wgFakes, 'ThreePhoton' : _ThreePhoton }[identifier](version)
        except KeyError:
            raise

fnf=getFilenamesFunction
