import ROOT

import sys
from filenames import getFilenamesFunction as filenames
import re
import collections

def generateHeader(analysis,usedBranches=None):
    analysis=sys.argv[1]
    tfile=ROOT.TFile(filenames(analysis)('SingleMuon')[0])
    if not tfile:
        print tfile
        raise ValueError(analysis)
    tree=tfile.Get("%sTree" % analysis)
    if not tree:
        print tree
        raise ValueError(analysis)
    tlist=tree.GetListOfBranches()
    disallowedCharacters=re.compile('[^A-Za-z0-9_]')
    disallowedFirstCharacters=re.compile('^([^A-Za-z_])')
    allNames=set()
    #Currently only supports tree with only leaves in it
    with open('%s_Event.h'%analysis,'w') as f:
        f.write('#include "RtypesCore.h"\n#include "TTree.h"\n\nstruct Event {\n')
        names=collections.OrderedDict()
        for x in tlist:
            tleaves=x.GetListOfLeaves()
            for y in tleaves:
                trueName=y.GetName()
                if usedBranches and trueName not in usedBranches:
                    continue
                name=disallowedCharacters.sub('_',trueName)
                name=disallowedFirstCharacters.sub('_\g<1>',name)
                names[trueName]=name
                if name in allNames:
                    raise name
                allNames.add(name)
                f.write('\t%s %s;\n' % (y.GetTypeName(),name))
        f.write('\tbool setAddresses(TTree* tree) {');
        if usedBranches:
            f.write('\n\t\t')
            f.write('tree->SetBranchStatus("*",0);');
        for branchName,cName in names.iteritems():
            if usedBranches:
                f.write('\n\t\t')
                f.write('tree->SetBranchStatus("%s",1);' % branchName)
            f.write('\n\t\t');
            f.write('tree->SetBranchAddress("%s",&%s);' % (branchName,cName));
        f.write('\n\t}\n};');
    return '%s_Event.h' % analysis
