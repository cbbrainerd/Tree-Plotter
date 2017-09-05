import ROOT
from Datasets import DatasetDict
from filenames import getFilenamesFunction as filenames
from array import array

typeMap = {
    'I': int,
    'l': long,
    'F': float,
    'C': str,
}
arrayMap = {
    'I': 'i',
    'l': 'L',
    'F': 'f',
}

class counter:
    def __enter__(self):
        pass
    def __exit__(self):
        self.__del__()
    def __init__(self,**kwargs):
        self.analysis=kwargs.pop('analysis')
        self.datasets=kwargs.pop('datasets')
        self.cutFilters=kwargs.pop('cutFilters')
        self.countFilters=kwargs.pop('countFilters')
        self.inputTreeName=kwargs.pop('inputTreeName','%sTree' % self.analysis)
        self.trees={}
        self.branches={}
        self.cutCounts={}
        self.countCounts={}
        for cut in self.countFilters:
            self.countCounts[cut]={}
        self.eventCounts={}
        self.fileOut=open('%s_count.txt' % self.analysis,'wb')
        self.filenames=filenames(self.analysis)
        self.TFileOut=ROOT.TFile('%s_count.root' % self.analysis,'RECREATE')
    def addBranch(self,function,label,rootType):
        if label not in self.branches:
            if rootType[0]=='C': # special handling of string
                self.branches[label] = {'var': bytearray(rootType[1]), 'rootType': rootType[0], 'function': function, 'branchName': '{0}[{1}]'.format(label,rootType[1]), 'size': rootType[1]}
            else:
                self.branches[label] = {'var': array(arrayMap[rootType],[0]), 'rootType': rootType, 'function': function, 'branchName': label}
        else:
            logging.error("{0} already in AnalysisTree.".format(label))
            raise ValueError("{0} already in AnalysisTree.".format(label))
    def _initTreeBranch(self,label):
        self.tree.Branch(label,self.branches[label]['var'],'{0}/{1}'.format(self.branches[label]['branchName'],self.branches[label]['rootType']))
    def _initTree(self,dataset):
        self.TFileOut.cd()
        print ROOT.gDirectory
        for cut in self.countFilters:
            for subdataset in DatasetDict[dataset]:
                self.countCounts[cut][subdataset]=0
        for subdataset in DatasetDict[dataset]:
            self.cutCounts[subdataset]=0
        self.tree=ROOT.TTree(dataset,dataset)
        self.trees[dataset]=self.tree
        print self.tree.GetDirectory()
        for label in self.branches:
            self._initTreeBranch(label)
    def _evalFunction(self,event,function,pyType):
        if isinstance(function,basestring):
            return pyType(getattr(event,function))
        else:
            return function(event)
    def _evaluate(self,label,event):
        pyType=typeMap[self.branches[label]['rootType']]
        if isinstance(self.branches[label]['function'], basestring): # its just a branch in the tree
            self.branches[label]['var'][0]=pyType(getattr(event,self.branches[label]['function']))
        elif self.branches[label]['rootType']=='C': # special handling of string
            strSize = self.branches[label]['size']
            funcVal = pyType(self.branches[label]['function'](event))
            #if len(funcVal)==strSize-1:
            if len(funcVal)<strSize:
                self.branches[label]['var'][:strSize] = funcVal
            else:
                logging.error('Size mismatch function with label {0}.'.format(label))
        else:
            self.branches[label]['var'][0] = pyType(self.branches[label]['function'](event))
    def _evalCutFilters(self,event):
        for filt in self.cutFilters:
            if not filt(event): 
                return False
        return True
    def _evalCountFilters(self,event):
        return { filt : cfilt(event) for filt,cfilt in self.countFilters.iteritems() }
    def fill(self,event):
        for label in self.branches:
            self._evaluate(label,event)
        self.tree.Fill()
    def _handleFile(self,dataset,subdataset,fn):
#        print 'Opening file %s.' % fn
        tmpTFile=ROOT.TFile.Open(fn)
        tree=tmpTFile.Get(self.inputTreeName)
        for event in tree:
            self.eventCounts[dataset]+=1
            if not (self.eventCounts[dataset] % 100000):
                print '%d events analyzed.' % self.eventCounts[dataset] 
            if self._evalCutFilters(event):
                self.fill(event)
                self.cutCounts[subdataset]+=1 #Do weighting later
                for cut,retval in self._evalCountFilters(event).items():
                    if retval:
                        self.countCounts[cut][subdataset]+=1 
        tmpTFile.Close()
        self.TFileOut.cd()
    def _handleDataset(self,dataset):
        print 'Processing dataset %s.' % dataset
        self.TFileOut.cd()
        self._initTree(dataset)
        self.eventCounts[dataset]=0
        for subDataset in DatasetDict[dataset]:
            fns=self.filenames(subDataset)
            for fn in fns:
                self._handleFile(dataset,subDataset,fn)
        self.tree.Write()
        for subdataset in DatasetDict[dataset]:
            self.fileOut.write('%s:\n' % subdataset)
            for cut in self.countFilters:
                self.fileOut.write('%s: %s %d/%d: %f\n' % (subdataset,cut,self.countCounts[cut][subdataset],self.cutCounts[subdataset],self.countCounts[cut][subdataset]/float(self.cutCounts[subdataset]) if self.cutCounts[subdataset]>0 else -1))
    def analyze(self):
        for dataset in self.datasets:
            self._handleDataset(dataset)
    def __del__(self):
        self.TFileOut.Close()
        self.fileOut.close()
