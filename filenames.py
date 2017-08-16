import glob

def _hadd(dataset):
    return 'ROOT_Files/ThreePhoton_%s.root' % dataset

def _notHadd(dataset):
    return glob.glob('crab_projects/*%s*/results/*.root' % dataset)

def getFilenamesFunction(hadd=True):
    if hadd:
        return _hadd
    else:
        return _notHadd
