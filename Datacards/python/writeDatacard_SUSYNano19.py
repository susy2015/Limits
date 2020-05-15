import os
import time
import math
import CombineHarvester.CombineTools.ch as ch
import argparse
import json
import numpy as np

# import ROOT with a fix to get batch mode (http://root.cern.ch/phpBB3/viewtopic.php?t=3198)
from sys import argv
argv.append( '-b-' )
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True
argv.remove( '-b-' )

from ROOT import TCanvas, TFile, TProfile, TNtuple, TH1F, TH2F, THStack, TLegend, TFile, TColor
from ROOT import gROOT, gBenchmark, gRandom, gSystem, Double

parser = argparse.ArgumentParser(
        description='Produce or print limits based on existing datacards')
parser.add_argument("-s", "--signal", dest="signalPoint", default='',
                         help="Signal point to use when running the maximum likelihood fit. [Default: T2tt_850_100]")
parser.add_argument("-l", "--location", dest="signalLocation", default='',
                         help="Signal point to use when running the maximum likelihood fit. [Default: T2tt_850_100]")
parser.add_argument("-m", "--manySignals", dest="manySignals", default=False,
                         help="Signal point to use when running the maximum likelihood fit. [Default: T2tt_850_100]")
args = parser.parse_args()

# datacard output directory
outputdir = 'Datacards/results/SUSYNano19-20200403'
# directory with uncertainties files
setuplocation = 'Datacards/setup/SUSYNano19'

# json file with bkg predictions and signal yields
json_bkgPred = '%s/combine_bkgPred.json' % setuplocation
if args.signalPoint == "": json_sigYields = '%s/dc_SigYields_single.json' % setuplocation
else:		           json_sigYields = setuplocation +"/" +  args.signalLocation + '/' + args.signalPoint + '.json' 
# file with names and types of uncertainties to apply
uncertainty_definitions = '%s/define_uncs.conf' % setuplocation
# files specifying uncertainty values by bin start with this string
uncertainty_fileprefix = 'values_unc'
uncertainty_filepostfix = '_syst.conf'
# backgroud processes
bkgprocesses = ['ttbarplusw', 'znunu', 'qcd', 'ttZ', 'diboson']
# background process name -> control region name
processMap = {'ttbarplusw':'lepcr', 'znunu':'phocr', 'qcd':'qcdcr'}
#blind data
CRprocMap  = {
    "qcdcr" : {
        'qcd'        : 'qcdcr_qcd',
        'ttbarplusw' : 'qcdcr_ttbarplusw',
        'znunu'      : 'qcdcr_znunu',
        'diboson'    : 'qcdcr_Rare',
    },
    "qcdcr2" : {
        'qcd'        : 'qcd',
        'ttbarplusw' : 'ttbarplusw',
        'znunu'      : 'znunu',
        'diboson'    : 'Rare',
    },
    "lepcr": {
        
    },
    "phocr" :{
        'gjets'   : 'phocr_gjets',
        'otherbkgs' : 'phocr_back',
    }

}

blind = False

if os.path.exists(outputdir + '/' + args.signalPoint):
    t = time.localtime()
    moveStr = '_moveTime' + str(t.tm_year) + '-' + str(t.tm_mon) + '-' + str(t.tm_mday) + '-' + str(t.tm_hour * 10000 + t.tm_min * 100 + t.tm_sec)
    print 'renaming existing directory to', outputdir + moveStr
    os.rename(outputdir, outputdir + moveStr)
if not os.path.exists(outputdir): 
    os.makedirs(outputdir)

# ------ process json file ------
def json_load_byteified(file_handle):
#     https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-ones-from-json-in-python/13105359#13105359
    import json
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )
def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data

def MakeStatHist(proc, yields, forceContent=None):
    llh = TH1F(proc, proc, 1, 0, 1)
    llh.SetBinContent(1, yields[0] if forceContent is None else forceContent)
    llh.SetBinError(1, (toUnc(yields) -1 ) * yields[0])
    llh.Write()

def MakeObsHist(obsRate):
    datah = TH1F("data_obs", "data_obs", 1, 0, 1)
    datah.SetBinContent(1, obsRate )
    datah.Write()

with open(json_bkgPred) as jf:
    j_bkg = json_load_byteified(jf)
    binMaps = j_bkg['binMaps']
    yields  = j_bkg['yieldsMap']
    binlist = j_bkg['binlist']
    binnum  = j_bkg['binNum']
    crbinlist = {
        'lepcr': yields['lepcr_data'].keys(),
        'phocr': yields['phocr_data'].keys(),
        'qcdcr': yields['qcdcr_data'].keys(),
    }

with open(json_sigYields) as jf:
    j_sig = json_load_byteified(jf)
    signals   = j_sig['signals']
    sigYields = j_sig['yieldsMap']
# ------ process json file ------

# ------ helper functions ------
def toUnc(q):
    return 2.0 if q[0]<=0 else min([1+q[1]/q[0], 2.0])

def parseBinMap(process, cr_description, yields_dict):
    values = []
    params = []
    sumE2 = 0
    for entry in cr_description.replace(' ','').split('+'):
        sr, cr = entry.split('*')
        if '<' in cr: sr, cr = cr, sr
        sr = sr.strip('<>')
        values.append(yields_dict[process][sr][0] if yields_dict[process][sr][0] > 0 else 0.000001)
        sumE2 += yields_dict[process][sr][1]*yields_dict[process][sr][1]
        cr = 'R_'+cr.strip('()')
        #print cr
        params.append(cr)
    results = {}
    results['yield'] = (sum(values), math.sqrt(sumE2))
    parts = ['@%d*%f'%(i, values[i]) for i in range(len(values))]
    results['rateParam'] = ('(%s)'%('+'.join(parts)), ','.join(params))
    return results

def sumBkgYields(process, signal, bin, cr_description, yields_dict):
    values = []
    params = []
    total = 0.
    crproc = 'lepcr' if 'ttbar' in process else ('qcdcr' if 'qcd' in process else 'phocr')
    sumE2 = 0.
    crdata = 0
    crunit = 0.
    srunit = 0.
    crother = 0
    stat_crunit = 0.
    stat_crdata = 0.
    for entry in cr_description.replace(' ','').split('+'):
        if '*' in entry: sr, cr = entry.split('*')
        else:
            sr = bin
            cr = entry
        if '<' in cr: sr, cr = cr, sr
        sr = sr.strip('<>')
        cr = cr.strip('()')
        #print(cr)
        if 'znunu' in process:
            crdata += yields[crproc + '_data'][cr][0]
            srunit += yields_dict[process][sr][0]
        else:
            crdata = yields[crproc + '_data'][cr][0]
            srunit = yields_dict[process][sr][0]

        sumE2 += yields_dict[process][sr][1]**2
        stat_crunit += yields_dict[crproc+'_'+process][cr][1] if not "znunu" in process else yields_dict[crproc+'_gjets'][cr][1]
        stat_crdata += yields[crproc + '_data'][cr][1] if crdata != 0 else 1.84105
        if 'ttbar' in process: 
            crunit = yields_dict[crproc+'_'+process][cr][0]
            crother= sigYields[crproc+'_'+signal][cr][0]
        if 'qcd' in process: 
            crunit = yields_dict[crproc+'_'+process][cr][0]
            crother =yields[crproc+'_ttbarplusw'][cr][0]
            crother+=yields[crproc+'_znunu'][cr][0]
            crother+=yields[crproc+'_Rare'][cr][0]
        if 'znunu' in process: 
            crunit += yields_dict[crproc+'_gjets'][cr][0] if yields_dict[crproc+'_gjets'][cr][0] > 0 else 0.000001
            crother+=yields[crproc+'_back'][cr][0]

        if 'znunu' in process: total = (crdata/(crunit + crother))*srunit
        elif 'qcd' in process: total += np.clip(crdata - crother, 1, None)*srunit/crunit
        else:                  total += crdata*srunit/crunit

    return total, math.sqrt(sumE2)*stat_crdata/stat_crunit

# ------ helper functions ------

# ------ process uncertainties ------ 
class Vividict(dict):
    '''https://stackoverflow.com/questions/635483/what-is-the-best-way-to-implement-nested-dictionaries'''
    def __missing__(self, key):
        value = self[key] = type(self)() # retain local pointer to value
        return value                     # faster to return than dict lookup

class Uncertainty:
    def __init__(self, name, type, value, value2 = -999.):
        self.name = name
        self.type = type
        self.value = float(value)
        self.value2 = float(value2)
        #if self.value > 2 or self.value < 0.5:
        #if self.value > 2:
        #    raise ValueError('Invalid unc value %f for %s!'%(self.value, self.name))

def averageUnc(up, down):
    #sign = 1 if up >= 1 else -1
    up_ = math.exp(math.log(up/math.sqrt(up*down)))
    down_ = math.exp(math.log(down/math.sqrt(up*down)))
    #val = 0.5 * (abs(up - 1) + abs(1 - down))
    #if abs(val) >= 1: val = 0.999
    return (down_, up_)

unc_def = {}
unc_dict = Vividict() # bin -> { proc -> { uncname -> Uncertainty } } , proc can be 'signal'
def readUncs():
    unc_processed = set()
    with open(uncertainty_definitions) as f:
        for line in f:
            line = line.strip()   # remove whitespace at the beginning/end
            if not line: continue # ignore empty line
            if line[0]=='#' or line[0]=='%': continue
            uncname, unctype = line.split()
            if unctype not in ['lnN','lnU','gmN']: 
                print line
                raise ValueError('Uncertainty type "%s" is not recognized!'%unctype)
            unc_def[uncname] = unctype
    
#     filelist = [os.path.join(setuplocation, f) for f in os.listdir(setuplocation) if f.startswith(uncertainty_fileprefix)]
    filelist = [os.path.join(dp, f) for dp, dn, filenames in os.walk(setuplocation) for f in filenames if f.startswith(uncertainty_fileprefix)]
    if args.signalPoint != "": filelist.append(str(setuplocation + '/' + args.signalLocation + '/' + args.signalPoint + uncertainty_filepostfix))
    for uncfile in filelist:
        with open(uncfile) as f:
            print 'Reading unc from', uncfile
            for line in f:
                line = line.strip()   # remove whitespace at the beginning/end
                if not line: continue # ignore empty line
                if line[0]=='#' or line[0]=='%': continue
                bin_str, uncname, proc_str, uncval = line.split()
                unctype = None
                for u_name,u_type in unc_def.iteritems():
                    if uncname.startswith(u_name):
                        unctype = u_type
                        unc_processed.add(u_name)
                        break
                if not unctype:
                    print line 
                    raise ValueError('Uncertainty "%s" is not defined!'%uncname)
                try:
                    if "Up" in uncname: 
                        if "nan" in uncval or float(uncval) > 10000000:
                            uncval = 2
                        elif float(uncval) <= 0:
                            uncval = 0.001
                        unc_up = Uncertainty(uncname.strip("_Up"), unctype, uncval)
                    elif "Down" in uncname: 
                        if "nan" in uncval or float(uncval) <= 0 or float(uncval) > 10000000:
                            uncval = 0.001
                        if (unc_up.value > 1 and float(uncval) > 1) or (unc_up.value < 1 and float(uncval) < 1):
                            uncavg = averageUnc(unc_up.value, float(uncval))			
                            unc = Uncertainty(uncname.strip("_Down"), unctype, uncavg[0], uncavg[1])
                        else:	
                            unc = Uncertainty(uncname.strip("_Down"), unctype, uncval, unc_up.value)	
                    else: 
                        unc = Uncertainty(uncname, unctype, uncval)
                except ValueError as e:
                    print line
                    raise e
                processes = proc_str.replace(' ','').split(',')
                bins = [bin_str]
                if bin_str=='all': bins = binlist
                elif bin_str in crbinlist: bins = crbinlist[bin_str]
                if "Up" not in uncname:
                    for bin in bins:
                        for proc in processes:
                            unc_dict[bin][proc][uncname] = unc
    
    unc_defined = set(unc_def.keys())
    if unc_defined!=unc_processed:
        print "Declared but not defined: ", unc_defined - unc_processed
        raise ValueError('Inconsistent uncertainty definition!')
# ------ process uncertainties ------

def writeLepcr(signal):
    for crbin in crbinlist['lepcr']:
        cb = ch.CombineHarvester()
#         print 'Writing datacard for', crbin
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, crbin)])
        cb.AddProcesses(procs = ['signal'],     bin = [(0, crbin)], signal=True)
        cb.AddProcesses(procs = ['ttbarplusw'], bin = [(0, crbin)], signal=False)
        cb.ForEachObs(lambda obs : obs.set_rate(yields['lepcr_data'][crbin][0]))
        cb.cp().process(['ttbarplusw']).ForEachProc(lambda p : p.set_rate(yields['lepcr_ttbarplusw'][crbin][0]))
        cb.cp().process(['signal']).ForEachProc(lambda p : p.set_rate(sigYields['lepcr_'+signal][crbin][0]))
        # stat uncs
        cb.cp().process(['ttbarplusw']).AddSyst(cb, "R_$BIN", "rateParam", ch.SystMap()(1.0))
        # syst unc
        if crbin in unc_dict:
            for proc in ['signal', signal, 'ttbarplusw']:
                if proc in unc_dict[crbin]:
                    for unc in unc_dict[crbin][proc].values():
                        procname_in_dc = 'ttbarplusw' if proc=='ttbarplusw' else 'signal'
                        if unc.value2 > -100.:
                            cb.cp().process([procname_in_dc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()((unc.value,unc.value2)))
                        else:
                            cb.cp().process([procname_in_dc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()(unc.value))
        tmpdc = os.path.join(outputdir, signal, '%s.tmp'%crbin)
        cb.WriteDatacard(tmpdc)
        trootout = os.path.join(outputdir, signal, '%s.root'%crbin)
        tmproot = TFile(trootout, "Recreate")
        tmproot.cd()
        MakeStatHist("ttbarplusw", yields['lepcr_ttbarplusw'][crbin])
        MakeStatHist("signal", sigYields['lepcr_'+signal][crbin])
        MakeObsHist(cb.GetObservedRate())
        tmproot.Close()

        with open(tmpdc) as tmpfile:
            with open(tmpdc.replace('.tmp', '.txt'), 'w') as dc:
                for line in tmpfile:
                    if 'rateParam' in line:
                        line = line.replace('\n', '  [0.01,5]\n') # set range of rateParam by hand
                    if 'shapes' in line:
                        line = line.replace('FAKE', '%s  $PROCESS' % ('%s.root'%crbin)) # set range of rateParam by hand
                    dc.write(line)
                dc.write("* autoMCStats 0")
        os.remove(tmpdc)
                

def writePhocr(signal):
    for crbin in crbinlist['phocr']:
        cb = ch.CombineHarvester()
#         print crbin
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, crbin)])
        cb.AddProcesses(procs = ['gjets', 'otherbkgs'], bin = [(0, crbin)], signal=False)
        cb.ForEachObs(lambda obs : obs.set_rate(yields['phocr_data'][crbin][0]))
        for proc in ['gjets', 'otherbkgs']:
            cb.cp().process([proc]).ForEachProc(lambda p : 
                                                 p.set_rate(
                                                     yields[CRprocMap['phocr'][proc]][crbin][0]
                                                     # if yields[CRprocMap['phocr'][proc]][crbin][0] > 0 else 0.000001
                                                 )
                                                )
        # stat uncs
        cb.cp().process(['gjets']).AddSyst(cb, "R_$BIN", "rateParam", ch.SystMap()(1.0))
        # syst uncs
        if crbin in unc_dict:
            for proc in ['gjets', 'otherbkgs']:
                if CRprocMap['phocr'][proc] in unc_dict[crbin]:
                    for unc in unc_dict[crbin][CRprocMap['phocr'][proc]].values():
                        if unc.value2 > -100.:
                            cb.cp().process([proc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()((unc.value,unc.value2)))
                        else:
                            cb.cp().process([proc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()(unc.value))
        trootout = os.path.join(outputdir, signal, '%s.root'%crbin)
        tmproot = TFile(trootout, "Recreate")
        tmproot.cd()
        MakeStatHist("gjets", yields[CRprocMap['phocr']['gjets']][crbin])
        MakeStatHist("otherbkgs", yields[CRprocMap['phocr']['otherbkgs']][crbin])
        MakeObsHist(cb.GetObservedRate())
        tmproot.Close()

        tmpdc = os.path.join(outputdir, signal, '%s.tmp'%crbin)
        cb.WriteDatacard(tmpdc)
        with open(tmpdc) as tmpfile:
            with open(tmpdc.replace('.tmp', '.txt'), 'w') as dc:
                for line in tmpfile:
                    if 'rateParam' in line:
                        line = line.replace('\n', '  [0.01,5]\n') # set range of rateParam by hand
                    if 'shapes' in line:
                        line = line.replace('FAKE', '%s  $PROCESS' % ('%s.root'%crbin)) # set range of rateParam by hand
                    dc.write(line)
                dc.write("* autoMCStats 0")
        os.remove(tmpdc)

def writeQCDcr(signal):
    for crbin in crbinlist['qcdcr']:
        cb = ch.CombineHarvester()
        #print crbin
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, crbin)])
        cb.AddProcesses(procs = ['qcd', 'ttbarplusw', 'znunu', 'diboson'], bin = [(0, crbin)], signal=False)
        cb.ForEachObs(lambda obs : obs.set_rate(yields['qcdcr_data'][crbin][0]))
        for proc in ['qcd', 'ttbarplusw', 'znunu', 'diboson']:
            cb.cp().process([proc]).ForEachProc(lambda p : 
                                                 p.set_rate(
                                                     yields[CRprocMap['qcdcr'][proc]][crbin][0]
                                                     # if yields[CRprocMap['qcdcr'][proc]][crbin][0] >= 0 else 0.000001
                                                 )
                                                )
        # stat uncs
        cb.cp().process(['qcd']).AddSyst(cb, "R_$BIN", "rateParam", ch.SystMap()(1.0))
        # syst uncs
        if crbin in unc_dict:
            #for proc in ['qcd', 'otherbkgs']:
            for proc in ['qcd', 'ttbarplusw', 'znunu', 'diboson']:
                if CRprocMap['qcdcr2'][proc] in unc_dict[crbin]:
                    for unc in unc_dict[crbin][CRprocMap['qcdcr2'][proc]].values():
                        if unc.value2 > -100.:
                            cb.cp().process([proc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()((unc.value,unc.value2)))
                        else:
                            cb.cp().process([proc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()(unc.value))

        trootout = os.path.join(outputdir, signal, '%s.root'%crbin)
        tmproot = TFile(trootout, "Recreate")
        tmproot.cd()
        MakeStatHist('qcd',        yields[CRprocMap['qcdcr']['qcd']][crbin])
        MakeStatHist('ttbarplusw', yields[CRprocMap['qcdcr']['ttbarplusw']][crbin])
        MakeStatHist('znunu',      yields[CRprocMap['qcdcr']['znunu']][crbin])
        MakeStatHist('diboson',    yields[CRprocMap['qcdcr']['diboson']][crbin])
        MakeObsHist(cb.GetObservedRate())
        tmproot.Close()

        tmpdc = os.path.join(outputdir, signal, '%s.tmp'%crbin)
        cb.WriteDatacard(tmpdc)
        with open(tmpdc) as tmpfile:
            with open(tmpdc.replace('.tmp', '.txt'), 'w') as dc:
                for line in tmpfile:
                    if 'rateParam' in line:
                        line = line.replace('\n', '  [0.01,5]\n') # set range of rateParam by hand
                    if 'shapes' in line:
                        line = line.replace('FAKE', '%s  $PROCESS' % ('%s.root'%crbin)) # set range of rateParam by hand
                    dc.write(line)
                dc.write("* autoMCStats 0")
        os.remove(tmpdc)

def BkgPlotter(json, outputBase, signal):
    gROOT.SetBatch(1)
    with open(json) as jf:
        j = json_load_byteified(jf)
    nbins = 183
    bkgstack = THStack("bkg", "Sum of Background in Search Region")
    c = TCanvas('c1', 'Sum of Background in Search Region', 200, 10, 700, 500)
    httbar = TH1F('httbar', 'ttbar yields', nbins, 0, nbins)
    hznunu = TH1F('hznunu', 'znunu yields', nbins, 0, nbins)
    hqcd = TH1F('hqcd', 'qcd yields', nbins, 0, nbins)
    httz = TH1F('httz', 'ttz yields', nbins, 0, nbins)
    hdiboson = TH1F('hdiboson', 'diboson yields', nbins, 0, nbins)
    hpred = TH1F('hpred', 'pred yields', nbins, 0, nbins)
    hsignal = TH1F(signal, 'signal yields', nbins, 0, nbins)
    if not blind: hdata = TH1F('hdata', 'data yields', nbins, 0, nbins)

    for bin in binlist:
        sr = int(binnum[bin])+1
        httbar.SetBinContent(sr, float(j[bin]['ttbarplusw'][0]))
        hznunu.SetBinContent(sr, float(j[bin]['znunu'][0]))
        hqcd.SetBinContent(sr, float(j[bin]['qcd'][0]))
        httz.SetBinContent(sr, float(j[bin]['ttZ'][0]))
        hdiboson.SetBinContent(sr, float(j[bin]['diboson'][0]))
        hpred.SetBinContent(sr, float(j[bin]['ttbarplusw'][0]) + float(j[bin]['znunu'][0]) + float(j[bin]['qcd'][0]) + float(j[bin]['ttZ'][0]) + float(j[bin]['diboson'][0]))
	hsignal.SetBinContent(sr, float(j[bin][signal][0]))

        if not blind:
            hdata.SetBinContent(sr, float(j[bin]['data'][0]))
            hdata.SetBinError(sr, float(j[bin]['data'][1]))

        httbar.SetBinError(sr, float(j[bin]['ttbarplusw'][1]))
        hznunu.SetBinError(sr, float(j[bin]['znunu'][1]))
        hqcd.SetBinError(sr, float(j[bin]['qcd'][1]))
        httz.SetBinError(sr, float(j[bin]['ttZ'][1]))
        hdiboson.SetBinError(sr, float(j[bin]['diboson'][1]))
        hpred.SetBinError(sr, float(j[bin]['ttbarplusw'][1]) + float(j[bin]['znunu'][1]) + float(j[bin]['qcd'][1]) + float(j[bin]['ttZ'][1]) + float(j[bin]['diboson'][1]))
	hsignal.SetBinError(sr, float(j[bin][signal][1]))

    httbar.SetFillColor(866)
    hznunu.SetFillColor(623)
    hqcd.SetFillColor(811)
    httz.SetFillColor(797)
    hdiboson.SetFillColor(391)
    hpred.SetFillColor(2)
    hsignal.SetFillColor(2)

    for h in [httbar, hznunu, hqcd, httz, hdiboson, hpred, hsignal]:
        h.SetXTitle("Search Region")
        h.SetYTitle("Events")
        h.SetTitleSize  (0.055,"Y")
        h.SetTitleOffset(1.600,"Y")
        h.SetLabelOffset(0.014,"Y")
        h.SetLabelSize  (0.040,"Y")
        h.SetLabelFont  (62   ,"Y")
        h.SetTitleSize  (0.055,"X")
        h.SetTitleOffset(1.300,"X")
        h.SetLabelOffset(0.014,"X")
        h.SetLabelSize  (0.040,"X")
        h.SetLabelFont  (62   ,"X")
        h.GetYaxis().SetTitleFont(62)
        h.GetXaxis().SetTitleFont(62)
        h.SetTitle("")
	

    bkgstack.Add(hdiboson)	
    bkgstack.Add(httz)	
    bkgstack.Add(hqcd)	
    bkgstack.Add(hznunu)	
    bkgstack.Add(httbar)	

    c.cd()
    c.SetLogy()
    bkgstack.Draw()
    bkgstack.GetYaxis().SetTitle("Events")
    bkgstack.GetXaxis().SetTitle("Search Region")
    leg = TLegend(.73,.65,.97,.90)
    leg.SetBorderSize(0)
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(42)
    leg.SetTextSize(0.035)
    leg.AddEntry(httbar,"ttbarplusw","F")
    leg.AddEntry(hznunu,"Znunu","F")
    leg.AddEntry(hqcd,"QCD","F")
    leg.AddEntry(httz,"ttZ","F")
    leg.AddEntry(hdiboson,"Rare","F")
    leg.Draw()
    c.SetTitle("Sum of Background in Search Regions")
    c.SetCanvasSize(800, 600)
    c.Print(outputBase + ".pdf")
    c.Print(outputBase + ".C")
    c.Print(outputBase + "_canvas.root")
    c.SaveAs(outputBase + ".pdf")

    output = TFile(outputBase +".root", "RECREATE")
    httbar.Write()
    hznunu.Write()
    hqcd.Write()
    httz.Write()
    hdiboson.Write()
    hpred.Write()
    if not blind: hdata.Write()
    hsignal.Write()
    output.Close()

def writeSR(signal):
    mergedbins = [bin for bin in binlist if '*' in binMaps['lepcr'][bin]]
    #mergedbins = [bin for bin in binlist if '+' in binMaps['lepcr'][bin]]
    sepYields = {}
    for bin in binlist:
        rateParamFixes = {}
        cb = ch.CombineHarvester()
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, bin)])
        cb.AddProcesses(procs = ['signal'],     bin = [(0, bin)], signal=True)
        cb.AddProcesses(procs = ['ttbarplusw', 'znunu', 'qcd', 'ttZ', 'diboson'], bin = [(0, bin)], signal=False)
        expected = 0.
        sepBins = {}
        for proc in ['ttZ', 'diboson']:
            expected += yields[proc][bin][0]
            sepBins[proc] = (yields[proc][bin][0], yields[proc][bin][1])
        for proc in ['ttbarplusw', 'znunu', 'qcd']:
            sepExpected, sepStat = sumBkgYields(proc, signal, bin, binMaps[processMap[proc]][bin], yields)
            expected += sepExpected
            sepBins[proc] = (sepExpected, sepStat)
        sepBins[signal] = (sigYields[signal][bin][0], sigYields[signal][bin][1])
        if not blind: 
            cb.ForEachObs(lambda obs : obs.set_rate(yields['data'][bin][0]))
            sepBins["data"] = (yields['data'][bin][0], yields['data'][bin][1])
        else:         
            cb.ForEachObs(lambda obs : obs.set_rate(expected))
        sepYields[bin] = sepBins
        cb.cp().process(['signal']).ForEachProc(lambda p : p.set_rate(sigYields[signal][bin][0]))
        cb.cp().process(['ttZ','diboson']).ForEachProc(lambda p : p.set_rate(yields[p.process()][bin][0]))

        trootout = os.path.join(outputdir, signal, '%s.root'%bin)
        tmproot = TFile(trootout, "Recreate")
        tmproot.cd()
        MakeStatHist("signal", sigYields[signal][bin])
        MakeStatHist("ttZ", yields['ttZ'][bin])
        MakeStatHist("diboson", yields['diboson'][bin])
        MakeObsHist(cb.GetObservedRate())
        if bin not in mergedbins:
            # one to one CR
            cb.cp().process(['ttbarplusw','znunu','qcd']).ForEachProc(lambda p : p.set_rate(yields[p.process()][bin][0]))
            cb.cp().process(['ttbarplusw']).AddSyst(cb, "R_%s"%binMaps['lepcr'][bin], "rateParam", ch.SystMap()(1.0))
            cb.cp().process(['znunu'     ]).AddSyst(cb, "R_%s"%binMaps['phocr'][bin], "rateParam", ch.SystMap()(1.0))
            cb.cp().process(['qcd'       ]).AddSyst(cb, "R_%s"%binMaps['qcdcr'][bin], "rateParam", ch.SystMap()(1.0))
            MakeStatHist("ttbarplusw", yields['ttbarplusw'][bin])
            MakeStatHist("znunu", yields['znunu'][bin])
            MakeStatHist("qcd", yields['qcd'][bin])
        else:
            cb.cp().process(['ttbarplusw','znunu','qcd']).ForEachProc(lambda p : p.set_rate(1))
            for proc in ['ttbarplusw','znunu','qcd']:
                rlt = parseBinMap(proc, binMaps[processMap[proc]][bin], yields)
                rName = "R_%s_%s"%(proc, bin)
                cb.cp().process([proc]).AddSyst(cb, rName, "rateParam", ch.SystMap()(999999.0)) # error if put formula here: need a workaround
                rateParamFixes[rName] = rlt['rateParam']
                MakeStatHist(proc, rlt['yield'], forceContent=1)
        # syst unc
        if bin in unc_dict:
            for proc in ['signal', signal]+bkgprocesses:
                if proc in unc_dict[bin]:
                    for unc in unc_dict[bin][proc].values():
                        procname_in_dc = proc if proc in bkgprocesses else 'signal'
                        if unc.value2 > -100.:
                            cb.cp().process([procname_in_dc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()((unc.value,unc.value2)))
                        else:
                            cb.cp().process([procname_in_dc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()(unc.value))
        # fix rateParams
        tmproot.Close()
        tmpdc = os.path.join(outputdir, signal, '%s.tmp'%bin)
        cb.WriteDatacard(tmpdc)
        with open(tmpdc) as tmpfile:
            with open(tmpdc.replace('.tmp', '.txt'), 'w') as dc:
                for line in tmpfile:
                    if 'rateParam' in line and '999999' not in line:
                        line = line.replace('\n', '  [0.01,5]\n') # set range of rateParam by hand
                    if 'shapes' in line:
                        line = line.replace('FAKE', '%s  $PROCESS' % ('%s.root'%bin)) # set range of rateParam by hand
                    for rName in rateParamFixes:
                        if rName not in line: continue
                        line = line.replace('999999', ' '.join(rateParamFixes[rName]))
                        break # fixed this rName
                    dc.write(line)
                dc.write("* autoMCStats 0\n")
        os.remove(tmpdc)
    with open('BkgExpected.json', 'w') as outfile:
        json.dump(sepYields, outfile)

readUncs()
for sig in signals:
    dest = os.path.join(outputdir, sig)
    if not os.path.exists(dest):
        os.makedirs(dest)
    writeLepcr(sig)
    writePhocr(sig)
    writeQCDcr(sig)
    writeSR(sig)
    if not args.manySignals: BkgPlotter('BkgExpected.json', 'SumOfBkg', sig)
