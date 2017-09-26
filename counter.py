import ROOT
from Datasets import DatasetDict
from filenames import getFilenamesFunction as filenames
from array import array

try:
    from DevTools.Plotter.xsec import getXsecRaise as getXsec
except ImportError:
    try:
        from DevTools.Plotter.python.xsec import getXsecRaise as getXsec
    except ImportError:
        print "getXsec could not be imported."
        print "Weighting cannot be done properly without getXsec."
        raise

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

class counter(object):
    def __enter__(self):
        pass
    def __exit__(self):
        self.__del__()
    def __init__(self,**kwargs):
        self.analysis=kwargs.pop('analysis')
        self.datasets=kwargs.pop('datasets')
        self.cutFilters=kwargs.pop('cutFilters')
        self.countFilters=kwargs.pop('countFilters')
        self.lumi=kwargs.pop('luminosity')
        self.info=kwargs.pop('info',None)
        self.eventWeight=kwargs.pop('weighting') #Lambda takes event
        self.fn=kwargs.pop('filename','%s_count' % self.analysis)
        countFilterFunctions=self.countFilters.keys()
        self.countFilters['All']=lambda event: True
        self.inputTreeName=kwargs.pop('inputTreeName','%sTree' % self.analysis)
        self.trees={}
        self.branches={}
        self.cutCounts={}
        self.countCounts={}
        self.datasetCutCounts={}
        self.datasetCountCounts={}
        for cut in self.countFilters:
            self.countCounts[cut]={}
            self.datasetCountCounts[cut]={}
        self.eventCounts={}
        self.fileOut=open('%s.txt' % self.fn,'wb')
        self.filenames=filenames(self.analysis)
        self.TFileOut=ROOT.TFile('%s.root' % self.fn,'RECREATE')
        self.addBranch(self.eventWeight,'eventWeight','F')
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
        for cut in self.countFilters:
            for subdataset in DatasetDict[dataset]:
                self.countCounts[cut][subdataset]=0
        for subdataset in DatasetDict[dataset]:
            self.cutCounts[subdataset]=0
        self.tree=ROOT.TTree(dataset,dataset)
        self.trees[dataset]=self.tree
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
            if len(funcVal)<strSize:
                self.branches[label]['var'][:strSize] = funcVal
            else:
                raise ValueError('Size mismatch function with label {0}.'.format(label))
        else:
            self.branches[label]['var'][0] = pyType(self.branches[label]['function'](event))
    def _evalCutFilters(self,event):
        for filt in self.cutFilters:
            if not filt(event): 
                return False
        return True
    def _evalCountFilters(self,event):
        retVal={ filt : cfilt(event) for filt,cfilt in self.countFilters.iteritems() }
        retVal['All']=all(retVal.values())
        return retVal
    def fill(self,event):
        for label in self.branches:
            self._evaluate(label,event)
        self.tree.Fill()
    def _genSubdatasetWeights(self):
        self.subdatasetWeight={}
        for dataset in self.datasets:
            for subDataset in DatasetDict[dataset]:
                if dataset=='Data':
                    self.subdatasetWeight[subDataset]=1
                else:        
                    fns=self.filenames(subDataset)
                    numberOfEvents=0
                    for fn in fns:
                        tmpTfile=ROOT.TFile(fn)
                        if not tmpTfile:
                            raise IOError(fn)
                        numberOfEvents+=tmpTfile.summedWeights.GetBinContent(1)
                        tmpTfile.Close()
                    xsec=getXsec(subDataset)
                    self.subdatasetWeight[subDataset]=xsec*self.lumi/float(numberOfEvents)
    def _handleFile(self,dataset,subdataset,fn,sdw,ew):
#        print 'Opening file %s.' % fn
        tmpTFile=ROOT.TFile.Open(fn)
        tree=tmpTFile.Get(self.inputTreeName)
        for event in tree:
            self.eventCounts[dataset]+=1
            if not (self.eventCounts[dataset] % 100000):
                print '%d events analyzed.' % self.eventCounts[dataset] 
            if self._evalCutFilters(event):
                weight=sdw*ew(event)
                self.fill(event)
                self.cutCounts[subdataset]+=weight #Do weighting later
                for cut,retval in self._evalCountFilters(event).items():
                    if retval:
                        self.countCounts[cut][subdataset]+=weight
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
                self._handleFile(dataset,subDataset,fn,self.subdatasetWeight[subDataset],self.eventWeight if dataset!='Data' else lambda event:1)
        self.tree.Write()
        for subdataset in DatasetDict[dataset]:
            self.fileOut.write('%s:' % subdataset)
            if not self.cutCounts[subdataset]:
                self.fileOut.write('No events passing selection cut.\n')
            else:
                self.fileOut.write('\n');
            for cut in self.countFilters:
                self.fileOut.write('%s: %s %f/%f: %f\n' % (subdataset,cut,float(self.countCounts[cut][subdataset]),float(self.cutCounts[subdataset]),self.countCounts[cut][subdataset]/float(self.cutCounts[subdataset]) if self.cutCounts[subdataset]>0 else -1))
    def analyze(self):
        if self.info:
            for line in self.info:
                self.fileOut.write(line)
        self._genSubdatasetWeights()
        for dataset in self.datasets:
            self._handleDataset(dataset)
            self.datasetCutCounts[dataset]=0
            for cut in self.countFilters:
                self.datasetCountCounts[cut][dataset]=0
            for subDataset in DatasetDict[dataset]:
                self.datasetCutCounts[dataset]+=self.cutCounts[subDataset]
                for cut in self.countFilters:
                    self.datasetCountCounts[cut][dataset]+=self.countCounts[cut][subDataset]
        self.datasetCutCounts['MC']=0
        for cut in self.countFilters:
            self.datasetCountCounts[cut]['MC']=0
        for dataset in self.datasets:
            if dataset=='Data':
                continue
            self.datasetCutCounts['MC']+=self.datasetCutCounts[dataset]
            for cut in self.countFilters:
                self.datasetCountCounts[cut]['MC']+=self.datasetCountCounts[cut][dataset]
        self.fileOut.write('Datasets:\n')
        for dataset in self.datasetCutCounts.iterkeys():
            self.fileOut.write('%s:\n' % dataset)
            for cut in self.countFilters:
                self.fileOut.write('%s: %s %f/%f: %f\n' % (dataset,cut,float(self.datasetCountCounts[cut][dataset]),float(self.datasetCutCounts[dataset]),self.datasetCountCounts[cut][dataset]/float(self.datasetCutCounts[dataset])))
    def __del__(self):
        self.TFileOut.Close()
        self.fileOut.close()

class counterFunction(counter): #Cut and count as a function
    def __init__(self,**kwargs):
        super(counterFunction,self).__init__(**kwargs)
        self.functionals=kwargs.pop('function') #Lambda takes event
        self.histTemplates=kwargs.pop('histogram')
    def analyze(self):
        self.cutHists=[ht.Clone() for ht in self.histTemplates]
        [ht.SetDirectory(self.TFileOut) for ht in self.cutHists]
        self.countHists=[{ filt : ht.Clone() for filt in self.countFilters } for ht in self.histTemplates]
 #       [x.SetDirectory(self.TFileOut) for x in [y.values() for y in self.countHists]]
        super(counterFunction,self).analyze()
        canvas=ROOT.TCanvas()
        for hl in self.countHists:
            for name,hist in hl.iteritems():
                hname=hist.GetTitle()
                hist.SetStats(0)
                hist.Divide(self.cutHist)
                hist.GetYaxis().SetRangeUser(0,1)
                hist.Draw()
                canvas.Print('COUNT_%s_%s_%s.pdf' % (self.analysis,hname,name))
                for y in xrange(1,10):
                    hist.GetYaxis().SetRangeUser(0,y/float(10))
                    hist.Draw()
                    canvas.Print('COUNT_%s_%s_%s_y%d.pdf' % (self.analysis,hname,name,y))
    def _handleFile(self,dataset,subdataset,fn,sdw,ew):
        tmpTFile=ROOT.TFile.Open(fn)
        tree=tmpTFile.Get(self.inputTreeName)
        for event in tree:
            self.eventCounts[dataset]+=1
            if not (self.eventCounts[dataset] % 100000):
                print '%d events analyzed.' % self.eventCounts[dataset] 
            if self._evalCutFilters(event):
                weight=sdw*ew(event)
                fillVals=[list(fun(event)) for fun in self.functionals]
                [fillVal.append(weight) for fillVal in fillVals]
                self.fill(event)
                [ch.Fill(*fillVal) for (ch,fillVal) in itertools.izip(self.cutHists,fillVals)]
                self.cutCounts[subdataset]+=weight #Do weighting later
                for cut,retval in self._evalCountFilters(event).items():
                    if retval:
                        self.countCounts[cut][subdataset]+=weight
                        [ch[cut].Fill(*fillVal) for (ch,fillVal) in itertools.izip(self.countHists,fillVals)]
        tmpTFile.Close()
        self.TFileOut.cd()

#class combinatorics(counterFunction):
#    def __init__(self,**kwargs):
#        super(combinatorics,self).__init__(**kwargs)
#        self.countFilters.remove('All')
#        self.originalCountFilters=dict(self.countFilters)
#        for cut in self.countFilters:
#            for x in ['e','t','f']:
                
