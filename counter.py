import ROOT
from Datasets import DatasetDict
from filenames import getFilenamesFunction as filenames
import filenames as fnm
from array import array
import itertools
import datetime
import os

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
        self.directory=kwargs.pop('outputDirectory','COUNT_Output/%s' % datetime.datetime.now().isoformat())
        self.extraFilters=kwargs.pop('extraFilters',{})
        os.makedirs(self.directory)
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
        self.fileOut=open('%s/%s.txt' % (self.directory,self.fn),'w',1)
        self.filenames=filenames(self.analysis)
        with open('%s/FILES' % self.directory,'w') as f: f.write('%s_%s' % (fnm.g_dataset,fnm.g_version))
        self.TFileOut=ROOT.TFile('%s/%s.root' % (self.directory,self.fn),'RECREATE')
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
        print "Tree %s initialized..." % self.tree.GetName()
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
                    try:
                        self.subdatasetWeight[subDataset]=xsec*self.lumi/float(numberOfEvents)
                    except ZeroDivisionError:
                        print subDataset
                        raise
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
        print "Writing tree %s..." % self.tree.GetName()
        self.tree.Write(str(),ROOT.TObject.kOverwrite)
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
        self.cutHists={dataset:[ht.Clone() for ht in self.histTemplates] for dataset in self.datasets}
        self.extraHists={}
        for extraFilter in self.extraFilters:
            self.extraHists[extraFilter]={dataset:[ht.Clone() for ht in self.histTemplates] for dataset in self.datasets}
        for dataset in self.datasets:
            [ht.SetDirectory(self.TFileOut) for ht in self.cutHists[dataset]]
            for extraHist in self.extraHists.itervalues():
                [ht.SetDirectory(self.TFileOut) for ht in extraHist[dataset]]
        self.countHists={dataset:[{ filt : ht.Clone() for filt in self.countFilters } for ht in self.histTemplates] for dataset in self.datasets}
        for dataset,datasetHist in self.cutHists.iteritems():
            for hist in datasetHist:
                hist.SetName("%s_%s_cutHist" % (hist.GetName(),dataset))
        for extraFilter in self.extraFilters:
            for dataset,datasetHist in self.extraHists[extraFilter].iteritems():
                for hist in datasetHist:
                    hist.SetName("%s_%s_ExtraFilter_%s" % (hist.GetName(),dataset,extraFilter))
        for dataset,datasetHist in self.countHists.iteritems():
            for hdict in datasetHist:
                for filt,hist in hdict.items():
                    hist.SetDirectory(self.TFileOut)
                    hist.SetName('%s_%s_%s' % (hist.GetName(),dataset,filt))
        try:
            super(counterFunction,self).analyze()
        except KeyboardInterrupt: raise
        canvas=ROOT.TCanvas()
        for datasetHist in self.cutHists.itervalues():
            for hist in datasetHist:
                hist.Write()
        for dataset,datasetHist in self.countHists.iteritems():
            for num,hl in enumerate(datasetHist):
                for name,hist in hl.iteritems():
                    hname=hist.GetName()+hist.GetTitle()
                    hist.SetStats(0)
                    fullHist=hist.Clone()
                    extraHists={extraFilter : hist.Clone() for extraFilter in self.extraFilters}
                    [extraHists[extraFilter].SetName('%s_ExtraFilter_%s'%(hist.GetName(),extraFilter)) for extraFilter in self.extraFilters]
                    fullHist.SetName('%s_Full' % fullHist.GetName())
                    fullHist.Write()
                    hist.Divide(self.cutHists[dataset][num])
                    for extraFilter in self.extraFilters:
                        extraHists[extraFilter].Divide(self.extraHists[extraFilter][dataset][num])
                    for histogram in itertools.chain((hist,),extraHists.itervalues()):
                        print type(histogram)
                        if isinstance(histogram,ROOT.TH2):
                            histogram.Draw('colz')
                        else:
                            histogram.GetYaxis().SetRangeUser(0,1)
                            histogram.Draw()
                        histogram.Write()
                        canvas.Print('%s/COUNT_%s_%s.pdf' % (self.directory,self.analysis,histogram.GetName()))
#                    if not isinstance(hist,ROOT.TH2):
#                        for y in xrange(1,10):
#                            hist.GetYaxis().SetRangeUser(0,y/float(10))
#                            hist.Draw()
#                            canvas.Print('%s/COUNT_%s_%s_%s_%s_y%d.pdf' % (self.directory,self.analysis,dataset,hname,name,y))
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
                [ch.Fill(*fillVal) for (ch,fillVal) in itertools.izip(self.cutHists[dataset],fillVals)]
                for extraFilter in self.extraFilters:
                    [ch.Fill(*fillVal) for (ch,fillVal) in itertools.izip(self.extraHists[extraFilter][dataset],fillVals)]
                self.cutCounts[subdataset]+=weight #Do weighting later
                for cut,retval in self._evalCountFilters(event).items():
                    if retval:
                        self.countCounts[cut][subdataset]+=weight
                        [ch[cut].Fill(*fillVal) for (ch,fillVal) in itertools.izip(self.countHists[dataset],fillVals)]
        tmpTFile.Close()
        self.TFileOut.cd()

#class combinatorics(counterFunction):
#    def __init__(self,**kwargs):
#        super(combinatorics,self).__init__(**kwargs)
#        self.countFilters.remove('All')
#        self.originalCountFilters=dict(self.countFilters)
#        for cut in self.countFilters:
#            for x in ['e','t','f']:
                
