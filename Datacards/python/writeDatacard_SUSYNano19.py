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
parser.add_argument("-o", "--output", dest="output", default='Datacards/results/SUSYNano19-20200403',
                         help="Output folder")
parser.add_argument("-b", "--bins", dest="binSelect", default="all",
                         help="which bins to use for the datacard. [Default: all]")
args = parser.parse_args()

syscap = 2   ## Cap at 200% systematics uncertainties
## Whether to apply reduced efficiency method or fitting method for signal contamination
## Fitting method: fit signal in both search region and LL control region
## reduced efficiency method: N_sig^SR(corrected) = N_sig^SR - LL_TF * N_sig_LLCR 
reduceEff = True ## SUSY-19-010 moving to reduced eff by default for now

# datacard output directory
outputdir = args.output
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
bkgprocesses = ['ttbarplusw', 'znunu', 'qcd', 'TTZ', 'Rare']
# background process name -> control region name
processMap = {'ttbarplusw':'lepcr', 'znunu':'phocr', 'qcd':'qcdcr'}
#blind data
CRprocMap  = {
    "qcdcr" : {
        'qcd'        : 'qcdcr_qcd',
        'ttbarplusw' : 'qcdcr_ttbarplusw',
        'znunu'      : 'qcdcr_znunu',
        'Rare'    : 'qcdcr_Rare',
    },
    "qcdcr2" : {
        'qcd'        : 'qcd',
        'ttbarplusw' : 'ttbarplusw',
        'znunu'      : 'znunu',
        'Rare'    : 'Rare',
    },
    "lepcr": {
        'ttbarplusw' : 'ttbarplusw',
    },
    "phocr" :{
        'gjets'   : 'phocr_gjets',
        'otherbkgs' : 'phocr_back',
        'phocr_gjets' : 'phocr_gjets',
        'phocr_back' : 'phocr_back',
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
    content = yields[0] if forceContent is None else forceContent
    statunc = (toUnc(yields) -1 ) 
    ## Cap on stat. uncertainty to 100%, in order to preserve the Poisson uncertainty
    if statunc > 1:
        statunc = 1
    llh.SetBinContent(1, content)
    llh.SetBinError(1, statunc * content)
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
    return 2.0 if q[0]<=0 else 1+q[1]/q[0]

def toUncSep(y, dy):
    return 2.0 if y<=0 else 1+dy/y

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

def parseSigBinMap(process, srbin, cr_description, sigyields_dict, lepyields_dict):
    '''reduced efficiency method '''

    lepcr_process = "lepcr_" + process
    results = sigyields_dict[process][srbin][0]
    #print("descritipn: ", cr_description, results)
    srs = []
    crs = []
    for entry in cr_description.replace(' ','').split('+'):
        print(entry)
        if "*" not in entry:
            srs.append(srbin)
            crs.append(entry)
            break
        sr, cr = entry.split('*')
        if '<' in cr: sr, cr = cr, sr
        cr = cr.strip('()')
        sr = sr.strip('<>')
        srs.append(sr)
        crs.append(cr)

    for cr, sr in  zip(crs, srs):
        llcr = lepyields_dict["lepcr_ttbarplusw"][cr][0] if cr in lepyields_dict["lepcr_ttbarplusw"] else 0
        llsr = lepyields_dict["ttbarplusw"][sr][0] if sr in lepyields_dict["ttbarplusw"] else 0
        sigcr = sigyields_dict[lepcr_process][cr][0] if cr in sigyields_dict[lepcr_process] else 0
        if llcr != 0:
            results -= sigcr * llsr/ llcr
    return results if results > 0 else 0

def parseUncUnitBinMap(process, srbin, cr_description):
    '''reduced efficiency method '''

    srs = []
    crs = []
    srYield = 0.
    srStat = 0.
    for entry in cr_description.replace(' ','').split('+'):
        if "*" not in entry:
            srs.append(srbin)
            crs.append(entry)
            break
        sr, cr = entry.split('*')
        if '<' in cr: sr, cr = cr, sr
        cr = cr.strip('()')
        sr = sr.strip('<>')
        srYield += yields[process][sr][0]
        srStat += yields[process][sr][1]*yields[process][sr][1]

    return srYield, math.sqrt(srStat)

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
    stat_crdata = 0
    stat_crunit = 0.
    stat_crother = 0.
    stat_srunit = 0.
    nunit=0
    for entry in cr_description.replace(' ','').split('+'):
        if '*' in entry: sr, cr = entry.split('*')
        else:
            sr = bin
            cr = entry
        if '<' in cr: sr, cr = cr, sr
        sr = sr.strip('<>')
        cr = cr.strip('()')
        #print(cr)
        nunit += 1
        crdata += yields[crproc + '_data'][cr][0]
        srunit += yields_dict[process][sr][0]
        stat_srunit += yields_dict[process][sr][1]**2
        stat_crdata += yields[crproc + '_data'][cr][1]**2

        if 'ttbar' in process: 
            crunit += yields_dict[crproc+'_'+process][cr][0]
            stat_crunit += yields_dict[crproc+'_'+process][cr][1]**2
        if 'qcd' in process: 
            crunit += yields_dict[crproc+'_'+process][cr][0]
            crother+=yields[crproc+'_ttbarplusw'][cr][0]
            crother+=yields[crproc+'_znunu'][cr][0]
            crother+=yields[crproc+'_Rare'][cr][0]
            stat_crunit += yields_dict[crproc+'_'+process][cr][1]**2
            stat_crother += yields_dict[crproc+'_ttbarplusw'][cr][1]**2
            stat_crother += yields_dict[crproc+'_znunu'][cr][1]**2
            stat_crother += yields_dict[crproc+'_Rare'][cr][1]**2
        if 'znunu' in process: 
            crunit += yields_dict[crproc+'_gjets'][cr][0] if yields_dict[crproc+'_gjets'][cr][0] > 0 else 0.000001
            crother+=yields[crproc+'_back'][cr][0]
            stat_crunit += yields_dict[crproc+'_gjets'][cr][1]**2
            stat_crother += yields_dict[crproc+'_back'][cr][1]**2

        if 'znunu' in process: total = (crdata/(crunit + crother))*srunit
        elif 'qcd' in process: total = np.clip(crdata - crother, 1, None)*srunit/crunit
        else:                  total = crdata*srunit/crunit

    if 'znunu' in process:
        sumE2 += (1 - toUncSep(srunit, math.sqrt(stat_srunit)))**2
        sumE2 += (1 - toUncSep(crdata, math.sqrt(stat_crdata)))**2
        sumE2 += (1 - toUncSep(crunit+crother, math.sqrt(stat_crunit)))**2
        sumE2 += (1 - toUncSep(crunit+crother, math.sqrt(stat_crother)))**2
    elif 'qcd' in process:
        sumE2 += (1 - toUncSep(srunit, math.sqrt(stat_srunit)))**2
        sumE2 += (1 - toUncSep(crunit, math.sqrt(stat_crunit)))**2
        if crdata == 0: stat_crdata =1 # incorporate the effect of clipping
        sumE2 += (1 - toUncSep(np.clip(crdata - crother, 1, None), math.sqrt(stat_crdata)))**2
        sumE2 += (1 - toUncSep(np.clip(crdata - crother, 1, None), math.sqrt(stat_crother)))**2
    else:
        sumE2 += (1 - toUncSep(srunit, math.sqrt(stat_srunit)))**2
        sumE2 += (1 - toUncSep(crunit, math.sqrt(stat_crunit)))**2
        sumE2 += (1 - toUncSep(crdata, math.sqrt(stat_crdata)))**2

    stat = math.sqrt(sumE2)*total

    #KH add garwood interval
    if crdata == 0:
        if 'znunu' in process:
            stat = 1.83 / (crunit + crother)*srunit
            print 'KH:', process, bin, total, stat
        if 'ttbarplusw' in process:
            stat = 1.83 / (crunit)*srunit
            print 'KH:', process, bin, total, stat

    #print "%11s %30s %10.4f stat: %8.4f" % (process, bin, total, stat)

    #KH Debugging starts
    debug = False
    if debug:
        if 'qcd' in process:
            print("KH: %8s %60s (nunit) %3d (pred) %12.8e (crdatstat) %12.8e (mcstat) %12.8e"% (process,bin,nunit,total, \
                                                                                                abs(1 - toUncSep(np.clip(crdata - crother, 1, None), math.sqrt(stat_crdata)) ) * total, \
                                                                                                math.sqrt( (1 - toUncSep(srunit, math.sqrt(stat_srunit)))**2 + (1 - toUncSep(crunit, math.sqrt(stat_crunit)))**2 + (1 - toUncSep(np.clip(crdata - crother, 1, None), math.sqrt(stat_crother)))**2 )*total ) )
        else:
            print "KH: %8s %60s pred: %12.8e stat: %12.8e" % (process, bin, total, stat)
    #KH Debugging ends

    return total, stat

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

def badSystematic(UpRatio, DownRatio):
    log_ratio_difference = abs(math.log(UpRatio)) - abs(math.log(DownRatio))
    bad_systematic = abs(log_ratio_difference) > 0.35
    if bad_systematic:
        if log_ratio_difference > 0:
            # UpRatio is larger, so use DownRatio
            UpRatio = 1/DownRatio
        else:
            # DownRatio is larger, so use UpRatio
            DownRatio = 1/UpRatio
    return (DownRatio, UpRatio)


def oneSidedSystematic(UpRatio, DownRatio):
    one_sided_systematic = ((UpRatio > 1) and (DownRatio > 1)) or ((UpRatio < 1) and (DownRatio < 1))
    if one_sided_systematic:
        geomean = math.sqrt(UpRatio * DownRatio)
        UpRatio /= geomean
        DownRatio /= geomean

    return (DownRatio, UpRatio)

def killSystematic(central_value, stat_uncertainty, UpRatio, DownRatio):
    kill_systematic = central_value < stat_uncertainty
    if kill_systematic:
        UpRatio = 1.0
        DownRatio = 1.0

    return (DownRatio, UpRatio)

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
    maxsyscap = 1+ syscap
    minsyscap = 1.0/(syscap*100)
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
                        if "nan" in uncval or float(uncval) > maxsyscap:
                            uncval = maxsyscap
                        elif float(uncval) <= minsyscap:
                            uncval = minsyscap
                        unc_up = Uncertainty(uncname.strip("_Up"), unctype, uncval)
                    elif "Down" in uncname: 
                        if "nan" in uncval or float(uncval) <= minsyscap:
                            uncval = minsyscap
                        elif float(uncval) > maxsyscap:
                            uncval = maxsyscap

                        #uncavg = oneSidedSystematic(unc_up.value, float(uncval))
                        uncavg = badSystematic(unc_up.value, float(uncval))
                        uncavg = oneSidedSystematic(uncavg[1], uncavg[0])

                        crproc = 'lepcr_' if 'lepcr' in bin_str else ('qcdcr_' if 'qcdcr' in bin_str else '')
                        
                        if 'lepcr' in bin_str and ('T2' in proc_str or 'T1' in proc_str or 'T5' in proc_str): 
                            proc_str = 'lepcr_' + proc_str
                        elif 'qcdcr' in bin_str and ('T2' in proc_str or 'T1' in proc_str or 'T5' in proc_str): 
                            proc_str = 'qcdcr_' + proc_str
                        elif proc_str not in ['TTZ', 'Rare'] and 'cr' not in bin_str and ('T2' not in proc_str and 'T1' not in proc_str and 'T5' not in proc_str):
                            srYield, srStat = parseUncUnitBinMap(proc_str, bin_str, binMaps[processMap[proc_str]][bin_str])

                        if 'cr' in bin_str: print("{0} {1}".format(proc_str, bin_str))

                        if 'T2' in proc_str or 'T1' in proc_str or 'T5' in proc_str:
                            uncavg = killSystematic(sigYields[proc_str][bin_str][0], sigYields[proc_str][bin_str][1], uncavg[1], uncavg[0])
                        elif 'lepcr' in bin_str or 'qcdcr' in bin_str or 'phocr' in bin_str:
                            uncavg = killSystematic(yields[crproc + proc_str][bin_str][0], yields[crproc + proc_str][bin_str][1], uncavg[1], uncavg[0])
                        elif proc_str == 'TTZ' or proc_str == 'Rare':
                            uncavg = killSystematic(yields[proc_str][bin_str][0], yields[proc_str][bin_str][1], uncavg[1], uncavg[0])
                        else:
                            uncavg = killSystematic(srYield, srStat, uncavg[1], uncavg[0])

                        unc = Uncertainty(uncname.strip("_Down"), unctype, uncavg[0], uncavg[1])
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
        if args.binSelect != "all" and args.binSelect not in crbin: continue
        cb = ch.CombineHarvester()
#         print 'Writing datacard for', crbin
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, crbin)])
        if not reduceEff:
            cb.AddProcesses(procs = ['signal'],     bin = [(0, crbin)], signal=True)
        cb.AddProcesses(procs = ['ttbarplusw'], bin = [(0, crbin)], signal=False)
        cb.ForEachObs(lambda obs : obs.set_rate(yields['lepcr_data'][crbin][0]))
        cb.cp().process(['ttbarplusw']).ForEachProc(lambda p : p.set_rate(yields['lepcr_ttbarplusw'][crbin][0]))
        if not reduceEff:
            cb.cp().process(['signal']).ForEachProc(lambda p : p.set_rate(sigYields['lepcr_'+signal][crbin][0]))
        # stat uncs
        cb.cp().process(['ttbarplusw']).AddSyst(cb, "R_$BIN", "rateParam", ch.SystMap()(1.0))
        proclist = [ 'ttbarplusw'] if reduceEff else ['signal', signal, 'ttbarplusw']
        # syst unc
        if crbin in unc_dict:
            for proc in proclist:
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
        if not reduceEff:
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
                dc.write("* autoMCStats 10 1 1") # background + signal 
        os.remove(tmpdc)
                

def writePhocr(signal):
    for crbin in crbinlist['phocr']:
        if args.binSelect != "all" and args.binSelect not in crbin: continue
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
                dc.write("* autoMCStats 10 1 1") # background + signal 
        os.remove(tmpdc)

def writeQCDcr(signal):
    for crbin in crbinlist['qcdcr']:
        if args.binSelect != "all" and args.binSelect not in crbin: continue
        cb = ch.CombineHarvester()
        #print crbin
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, crbin)])
        cb.AddProcesses(procs = ['qcd', 'ttbarplusw', 'znunu', 'Rare'], bin = [(0, crbin)], signal=False)
        cb.ForEachObs(lambda obs : obs.set_rate(yields['qcdcr_data'][crbin][0]))
        for proc in ['qcd', 'ttbarplusw', 'znunu', 'Rare']:
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
            for proc in ['qcd', 'ttbarplusw', 'znunu', 'Rare']:
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
        MakeStatHist('Rare',    yields[CRprocMap['qcdcr']['Rare']][crbin])
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
                dc.write("* autoMCStats 10 1 1") # background + signal 
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
    hRare = TH1F('hRare', 'Rare yields', nbins, 0, nbins)
    hpred = TH1F('hpred', 'pred yields', nbins, 0, nbins)
    hsignal = TH1F(signal, 'signal yields', nbins, 0, nbins)
    if not blind: hdata = TH1F('hdata', 'data yields', nbins, 0, nbins)
    
    diff = 0.
    whichBin = ""
    for bin in binlist:
        sr = int(binnum[bin])+1
        httbar.SetBinContent(sr, float(j[bin]['ttbarplusw'][0]))
        hznunu.SetBinContent(sr, float(j[bin]['znunu'][0]))
        hqcd.SetBinContent(sr, float(j[bin]['qcd'][0]))
        httz.SetBinContent(sr, float(j[bin]['TTZ'][0]))
        hRare.SetBinContent(sr, float(j[bin]['Rare'][0]))
        hpred.SetBinContent(sr, float(j[bin]['ttbarplusw'][0]) + float(j[bin]['znunu'][0]) + float(j[bin]['qcd'][0]) + float(j[bin]['TTZ'][0]) + float(j[bin]['Rare'][0]))
	hsignal.SetBinContent(sr, float(j[bin][signal][0]))

        if hsignal.GetBinContent(sr)/math.sqrt(hpred.GetBinContent(sr)) >= diff:
            whichBin = bin

        if not blind:
            hdata.SetBinContent(sr, float(j[bin]['data'][0]))
            hdata.SetBinError(sr, float(j[bin]['data'][1]))

        httbar.SetBinError(sr, float(j[bin]['ttbarplusw'][1]))
        hznunu.SetBinError(sr, float(j[bin]['znunu'][1]))
        hqcd.SetBinError(sr, float(j[bin]['qcd'][1]))
        httz.SetBinError(sr, float(j[bin]['TTZ'][1]))
        hRare.SetBinError(sr, float(j[bin]['Rare'][1]))
        hpred.SetBinError(sr, np.sqrt(float(j[bin]['ttbarplusw'][1])**2 + float(j[bin]['znunu'][1])**2 + float(j[bin]['qcd'][1])**2 + float(j[bin]['TTZ'][1])**2 + float(j[bin]['Rare'][1])**2))
	hsignal.SetBinError(sr, float(j[bin][signal][1]))

    httbar.SetFillColor(866)
    hznunu.SetFillColor(623)
    hqcd.SetFillColor(811)
    httz.SetFillColor(797)
    hRare.SetFillColor(391)
    hpred.SetFillColor(2)
    hsignal.SetFillColor(2)

    for h in [httbar, hznunu, hqcd, httz, hRare, hpred, hsignal]:
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
	

    bkgstack.Add(hRare)	
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
    leg.AddEntry(httz,"TTZ","F")
    leg.AddEntry(hRare,"Rare","F")
    leg.Draw()
    c.SetTitle("Sum of Background in Search Regions")
    c.SetCanvasSize(800, 600)
    #c.Print(outputBase + ".pdf")
    #c.Print(outputBase + ".C")
    #c.Print(outputBase + "_canvas.root")
    #c.SaveAs(outputBase + ".pdf")

    output = TFile(outputBase +".root", "UPDATE")
    httbar.Write()
    hznunu.Write()
    hqcd.Write()
    httz.Write()
    hRare.Write()
    hpred.Write()
    if not blind: hdata.Write()
    hsignal.Write()
    output.Close()

def writeSR(signal):
    mergedbins = [bin for bin in binlist if '*' in binMaps['lepcr'][bin]]
    sepYields = {}
    for bin in binlist:
        if args.binSelect != "all" and args.binSelect not in bin: continue
        rateParamFixes = {}
        cb = ch.CombineHarvester()
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, bin)])
        cb.AddProcesses(procs = ['signal'],     bin = [(0, bin)], signal=True)
        cb.AddProcesses(procs = ['ttbarplusw', 'znunu', 'qcd', 'TTZ', 'Rare'], bin = [(0, bin)], signal=False)
        expected = 0.
        sepBins = {}
        for proc in ['TTZ', 'Rare']:
            expected += yields[proc][bin][0]
            sepBins[proc] = (yields[proc][bin][0], yields[proc][bin][1])
        for proc in ['ttbarplusw', 'znunu', 'qcd']:
            sepExpected, sepStat = sumBkgYields(proc, signal, bin, binMaps[processMap[proc]][bin], yields)
            expected += sepExpected
            sepBins[proc] = (sepExpected, sepStat)

        if reduceEff:
            sigyield = parseSigBinMap(signal, bin, binMaps[processMap["ttbarplusw"]][bin], sigYields, yields)
        else:
            sigyield = sigYields[signal][bin][0]
        sepBins[signal] = (sigyield, sigYields[signal][bin][1])
        if not blind: 
            cb.ForEachObs(lambda obs : obs.set_rate(yields['data'][bin][0]))
            sepBins["data"] = (yields['data'][bin][0], yields['data'][bin][1])
        else:         
            cb.ForEachObs(lambda obs : obs.set_rate(expected))
        sepYields[bin] = sepBins
        cb.cp().process(['signal']).ForEachProc(lambda p : p.set_rate(sigyield))
        cb.cp().process(['TTZ','Rare']).ForEachProc(lambda p : p.set_rate(yields[p.process()][bin][0]))

        trootout = os.path.join(outputdir, signal, '%s.root'%bin)
        tmproot = TFile(trootout, "Recreate")
        tmproot.cd()
        MakeStatHist("signal", sigYields[signal][bin], forceContent=sigyield )
        MakeStatHist("TTZ", yields['TTZ'][bin])
        MakeStatHist("Rare", yields['Rare'][bin])
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
                dc.write("* autoMCStats 10 1 1") # background + signal
        os.remove(tmpdc)
    # with open('BkgExpected.json', 'w') as outfile:
        # json.dump(sepYields, outfile)

readUncs()
for sig in signals:
    dest = os.path.join(outputdir, sig)
    if not os.path.exists(dest):
        os.makedirs(dest)
    writeLepcr(sig)
    writePhocr(sig)
    writeQCDcr(sig)
    writeSR(sig)
    # if not args.manySignals and args.binSelect == "all": BkgPlotter('BkgExpected.json', 'SumOfBkg', sig)
