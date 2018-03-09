import glob

g_dataset=None
g_version=None

def _hadd(dataset):
    return 'ROOT_Files/ThreePhoton_%s.root' % dataset

def _notHadd(dataset):
    return glob.glob('crab_projects/*%s*/results/*.root' % dataset)

def _run2(dataset):
    return glob.glob('Run2_FlatQCD_NoPreselection/*%s*/results/*.root' % dataset)

def _wgFakes(version='v9'):
    if version!='v9':
        raise ValueError(version)
    def _wgFakesH(dataset):  
        return glob.glob('InclusiveWGFakeRate/*%s*/results/*.root' % (dataset))
    return _wgFakesH

def _ThreePhoton(version='v9'):
    def _ThreePhotonH(dataset):
        return glob.glob('ThreePhoton%s/*%s*/results/*.root' % (version,dataset))
    return _ThreePhotonH

def _Directory(directory):
    def _DirectoryH(dataset):
        return glob.glob('%s/*%s*/results/*.root' % (directory,dataset))
    return _DirectoryH

def getFilenamesFunction(identifier=None,version='v9'):
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
            try:
                return _Directory(identifier)
            except:
                raise

fnf=getFilenamesFunction
