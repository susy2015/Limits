#!/usr/bin/env python
import re
from sys import argv, stdout, stderr, exit, modules
from optparse import OptionParser
import json

# import ROOT with a fix to get batch mode (http://root.cern.ch/phpBB3/viewtopic.php?t=3198)
argv.append( '-b-' )
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True
argv.remove( '-b-' )

from HiggsAnalysis.CombinedLimit.DatacardParser import *
from HiggsAnalysis.CombinedLimit.ModelTools import *
from HiggsAnalysis.CombinedLimit.ShapeTools import *
from HiggsAnalysis.CombinedLimit.PhysicsModel import *
from collections import defaultdict
import pickle

parser = OptionParser(usage="usage: %prog [options] datacard.txt -o output \nrun with --help to get list of options")
addDatacardParserOptions(parser)
parser.add_option("-P", "--physics-model", dest="physModel", default="HiggsAnalysis.CombinedLimit.PhysicsModel:defaultModel",  type="string", help="Physics model to use. It should be in the form (module name):(object name)")
parser.add_option("--PO", "--physics-option", dest="physOpt", default=[],  type="string", action="append", help="Pass a given option to the physics model (can specify multiple times)")
parser.add_option("", "--dump-datacard", dest="dumpCard", default=False, action='store_true',  help="Print to screen the DataCard as a python config and exit")
parser.add_option("-j", "--bin-json", dest="json",
                  default="../../../setup/SUSYNano19/dc_BkgPred_BinMaps_master.json",
                  help="Print to screen the DataCard as a python config and exit")
(options, args) = parser.parse_args()

if len(args) == 0:
    parser.print_usage()
    exit(1)

options.fileName = args[0]
if options.fileName.endswith(".gz"):
    import gzip
    file = gzip.open(options.fileName, "rb")
    options.fileName = options.fileName[:-3]
else:
    file = open(options.fileName, "r")

## Parse text file 
DC = parseCard(file, options)
# print(type(DC))
# print(DC.list_of_backgrounds())
keymap = defaultdict(list)
for bin, process, issignal in DC.keyline:
    keymap[bin].append(process)

# print(DC.keyline)
# print(keymap)
# print(DC.orgCards[0])
# print(DC.orgCards[-1])

# for i, (lsyst,nofloat,pdf,args,errline) in enumerate(DC.systs):
    # if lsyst != "PDF_Weight":
        # continue
    # newerr = errline
    # for b, m in errline.items():
        # print(b)
        # bnumber = int(b.replace("ch", "")) -1 
        # print(bnumber, len(DC.orgCards))
        # for p, sys in m.items():
            # # if isinstance(sys, list):
            # if "qcdcr" in DC.orgCards[bnumber] and isinstance(sys, list):
                # if sys[0] > sys[1]:
                    # # print(DC.orgCards[bnumber], p, sys)
                    # newerr[b][p] = [sys[1], sys[0]]

        # # print(lsyst,nofloat,pdf,args,errline )
    # DC.systs[i] = (lsyst,nofloat,pdf,args,newerr )
    # # break

# for i, (lsyst,nofloat,pdf,args,errline) in enumerate(DC.systs):
    # if lsyst != "PDF_Weight":
        # continue
    # # newerr = errline
    # for b, m in errline.items():
        # # print(m)
        # for p, sys in m.items():
            # if isinstance(sys, list):
                # if sys[0] > sys[1]:
                    # bnumber = int(b.replace("ch", "")) -1 
                    # print(DC.orgCards[bnumber], p, sys)
                    # # newerr[b][p] = [sys[1], sys[0]]

        # # print(lsyst,nofloat,pdf,args,errline )
    # # DC.systs[i] = (lsyst,nofloat,pdf,args,errline )

jsonfile = open(options.json)
jsontot = json.load(jsonfile)

shapefit = ROOT.TFile("./fitDiagnostics.root")
shapeb = shapefit.Get("shapes_prefit")
# shapeb = shapefit.Get("shapes_fit_b")
yieldmap = defaultdict(dict)
testbin = "bin_lepcr_hm_nb3_highmtb_htlt1000_MET_pt550toinf"
for b in DC.list_of_bins():
    bnumber = int(b.replace("ch", "")) -1 
    strbin = DC.orgCards[bnumber]
    jsonbin = None
    if "lepcr" in strbin:
        jsonbin = int(jsontot["unitCRNum"]["lepcr"][strbin]) + 1000
    elif "phocr" in strbin:
        jsonbin = int(jsontot["unitCRNum"]["phocr"][strbin]) + 2000
    elif "qcdcr" in strbin:
        jsonbin = int(jsontot["unitCRNum"]["qcdcr"][strbin]) + 3000
    else:
        jsonbin = int(jsontot["binNum"][strbin])
    for p in keymap[b]:
        print(b, p)
        h = shapeb.Get("%s/%s" % (b, p))
        if h == None:
            print("Expecting %s in %s, but it is not in current folder" % (p, strbin))
            yieldmap[jsonbin][p] = [0, 0, 0]
            continue
            # print("=========", strbin, b, p, h == None)
        yeild = h.GetBinContent(1)
        yeilderr = h.GetBinError(1)
        yieldmap[jsonbin][p] = [yeild, yeilderr, yeilderr]
        if strbin == testbin:
            print(jsonbin, p, yeild, yeilderr)

    datah = shapeb.Get("%s/data" % b)
    if datah == None:
        print("No data in %s?" % strbin)
    x=ROOT.Double(0)
    y=ROOT.Double(0)
    datah.GetPoint(0, x, y)
    if strbin == testbin:
        print(b, "Data! ", x, y, datah.GetErrorYlow(0),  datah.GetErrorYhigh(0), datah.GetErrorXlow(0),  datah.GetErrorXhigh(0))
    yieldmap[jsonbin]["data"] = [y, datah.GetErrorYlow(0), datah.GetErrorYhigh(0)]

pickle.dump(yieldmap, open("yeild.p", "wb"), protocol=pickle.HIGHEST_PROTOCOL)


# print(DC.list_of_bins())
# print(shapeb, dir(shapeb))
# d = shapeb.Get("ch1/data")
# print(shapeb.ls())
# print(d)


# print(jsontot.keys())
# print(DC.systs)
      # ["PDF_Weight"])
# for i in DC.list_of_bins():
    # print(DC.uncert(i, "pdf", "PDF_weight"))
    # def uncert(self, bin, proc, resolve) :



if options.dumpCard:
    ## Load tools to build workspace
    MB = None
    if DC.hasShapes:
        MB = ShapeBuilder(DC, options)
    else:
        MB = CountingModelBuilder(DC, options)

    ## Load physics model
    (physModMod, physModName) = options.physModel.split(":")
    __import__(physModMod)
    mod = modules[physModMod]
    physics = getattr(mod, physModName)
    if mod     == None: raise RuntimeError, "Physics model module %s not found" % physModMod
    if physics == None or not isinstance(physics, PhysicsModelBase): 
        raise RuntimeError, "Physics model %s in module %s not found, or not inheriting from PhysicsModelBase" % (physModName, physModMod)
    physics.setPhysicsOptions(options.physOpt)
    ## Attach to the tools, and run
    MB.setPhysics(physics)
    MB.doModel()
