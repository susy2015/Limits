import os
import time
import math
import CombineHarvester.CombineTools.ch as ch
import argparse

parser = argparse.ArgumentParser(
        description='Produce or print limits based on existing datacards')
parser.add_argument("-s", "--signal", dest="signalPoint", default='',
                         help="Signal point to use when running the maximum likelihood fit. [Default: T2tt_850_100]")
parser.add_argument("-l", "--location", dest="signalLocation", default='',
                         help="Signal point to use when running the maximum likelihood fit. [Default: T2tt_850_100]")
args = parser.parse_args()

# json file with bkg predictions and signal yields
json_bkgPred = 'Datacards/setup/SUSYNano19/combine_bkgPred.json'
#json_sigYields = 'Datacards/setup/SUSYNano19/dc_SigYields_single.json'
if args.signalPoint == "": json_sigYields = 'Datacards/setup/SUSYNano19/dc_SigYields_single.json'
else:		           json_sigYields = 'Datacards/setup/SUSYNano19/' +  args.signalLocation + '/' + args.signalPoint + '.json'
# datacard output directory
outputdir = 'Datacards/results/SUSYNano19-20191010'
# directory with uncertainties files
setuplocation = 'Datacards/setup/SUSYNano19'
# file with names and types of uncertainties to apply
uncertainty_definitions = 'Datacards/setup/SUSYNano19/define_uncs.conf'
# files specifying uncertainty values by bin start with this string
uncertainty_fileprefix = 'values_unc'
uncertainty_filepostfix = '_syst.conf'
# backgroud processes
bkgprocesses = ['ttbarplusw', 'znunu', 'qcd', 'ttZ', 'diboson']
# background process name -> control region name
processMap = {'ttbarplusw':'lepcr', 'znunu':'phocr', 'qcd':'qcdcr'}
#blind data
blind = True

if os.path.exists(outputdir):
    t = time.localtime()
    moveStr = '_moveTime' + str(t.tm_year) + '-' + str(t.tm_mon) + '-' + str(t.tm_mday) + '-' + str(t.tm_hour * 10000 + t.tm_min * 100 + t.tm_sec)
    print 'renaming existing directory to', outputdir + moveStr
    os.rename(outputdir, outputdir + moveStr)
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

with open(json_bkgPred) as jf:
    j_bkg = json_load_byteified(jf)
    binMaps = j_bkg['binMaps']
    yields  = j_bkg['yieldsMap']
    binlist = j_bkg['binlist']
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
        values.append(yields_dict[process][sr][0])
        sumE2 += yields_dict[process][sr][1]*yields_dict[process][sr][1]
        cr = 'R_'+cr.strip('()')
	#print cr
        params.append(cr)
    results = {}
    results['yield'] = (sum(values), math.sqrt(sumE2))
    parts = ['@%d*%f'%(i, values[i]) for i in range(len(values))]
    results['rateParam'] = ('(%s)'%('+'.join(parts)), ','.join(params))
    return results
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
    sign = 1 if up >= 1 else -1
    val = 0.5 * (abs(up - 1) + abs(1 - down))
    return (sign * val)

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
                    if "up" in uncname: 
			if "nan" in uncval:
				uncval = 2
			elif float(uncval) <= 0:
				uncval = 0.001
			unc_up = Uncertainty(uncname.strip("up"), unctype, uncval)
                    elif "down" in uncname: 
			if uncval == "2" or "nan" in uncval or float(uncval) <= 0:
				uncval = 0.001
			if (unc_up.value > 1 and float(uncval) > 1) or (unc_up.value < 1 and float(uncval) < 1):
				uncavg = averageUnc(unc_up.value, float(uncval))			
		    		unc = Uncertainty(uncname.strip("_down"), unctype, (1 - uncavg), (1 + uncavg))
			else:	
		    		unc = Uncertainty(uncname.strip("_down"), unctype, uncval, unc_up.value)	
                    else: 
			unc = Uncertainty(uncname, unctype, uncval)
                except ValueError as e:
                    print line
                    raise e
                processes = proc_str.replace(' ','').split(',')
                bins = [bin_str]
                if bin_str=='all': bins = binlist
                elif bin_str in crbinlist: bins = crbinlist[bin_str]
		if "up" not in uncname:
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
        cb.AddSyst(cb, "mcstats_$PROCESS_$BIN", "lnN", ch.SystMap('process')
                   (['ttbarplusw'], toUnc(yields['lepcr_ttbarplusw'][crbin]))
                   (['signal'],     toUnc(sigYields['lepcr_'+signal][crbin]))
                   )
        # syst unc
        if crbin in unc_dict:
            for proc in ['signal', signal, 'ttbarplusw']:
                if proc in unc_dict[crbin]:
                    for unc in unc_dict[crbin][proc].values():
                        procname_in_dc = 'ttbarplusw' if proc=='ttbarplusw' else 'signal'
                        cb.cp().process([procname_in_dc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()(unc.value))
        tmpdc = os.path.join(outputdir, signal, '%s.tmp'%crbin)
        cb.WriteDatacard(tmpdc)
        with open(tmpdc) as tmpfile:
            with open(tmpdc.replace('.tmp', '.txt'), 'w') as dc:
                for line in tmpfile:
                    if 'rateParam' in line:
                        line = line.replace('\n', '  [0.01,5]\n') # set range of rateParam by hand
                    dc.write(line)
        os.remove(tmpdc)
                

def writePhocr(signal):
    for crbin in crbinlist['phocr']:
        cb = ch.CombineHarvester()
#         print crbin
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, crbin)])
        cb.AddProcesses(procs = ['gjets', 'otherbkgs'], bin = [(0, crbin)], signal=False)
        cb.ForEachObs(lambda obs : obs.set_rate(yields['phocr_data'][crbin][0]))
        cb.cp().process(['gjets']).ForEachProc(lambda p : p.set_rate(yields['phocr_gjets'][crbin][0]))
	cb.cp().process(['otherbkgs']).ForEachProc(lambda p : p.set_rate(yields['phocr_back'][crbin][0]))
	#if yields['phocr_back'][crbin][0] > 0: cb.cp().process(['otherbkgs']).ForEachProc(lambda p : p.set_rate(yields['phocr_back'][crbin][0]))
	#else:				       cb.cp().process(['otherbkgs']).ForEachProc(lambda p : p.set_rate(1e-06))
        # stat uncs
        cb.cp().process(['gjets']).AddSyst(cb, "R_$BIN", "rateParam", ch.SystMap()(1.0))
        cb.AddSyst(cb, "mcstats_$PROCESS_$BIN", "lnN", ch.SystMap('process')
                   (['gjets'],        toUnc(yields['phocr_gjets'][crbin]))
                   (['otherbkgs'],    toUnc(yields['phocr_back'][crbin]))
                   )
        # syst uncs
        if crbin in unc_dict:
            for proc in ['gjets', 'otherbkgs']:
                if proc in unc_dict[crbin]:
                    for unc in unc_dict[crbin][proc].values():
                        cb.cp().process([proc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()(unc.value))
        tmpdc = os.path.join(outputdir, signal, '%s.tmp'%crbin)
        cb.WriteDatacard(tmpdc)
        with open(tmpdc) as tmpfile:
            with open(tmpdc.replace('.tmp', '.txt'), 'w') as dc:
                for line in tmpfile:
                    if 'rateParam' in line:
                        line = line.replace('\n', '  [0.01,5]\n') # set range of rateParam by hand
                    dc.write(line)
        os.remove(tmpdc)

def writeQCDcr(signal):
    for crbin in crbinlist['qcdcr']:
        cb = ch.CombineHarvester()
	#cb.SetVerbosity(3) ## Boolean to enable debug printout
        #print crbin
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, crbin)])
        cb.AddProcesses(procs = ['qcd', 'otherbkgs'], bin = [(0, crbin)], signal=False)
        cb.ForEachObs(lambda obs : obs.set_rate(yields['qcdcr_data'][crbin][0]))
        cb.cp().process(['qcd']).ForEachProc(lambda p : p.set_rate(yields['qcdcr_qcd'][crbin][0]))
        cb.cp().process(['otherbkgs']).ForEachProc(lambda p : p.set_rate(yields['qcdcr_otherbkgs'][crbin][0]))
        # stat uncs
        cb.cp().process(['qcd']).AddSyst(cb, "R_$BIN", "rateParam", ch.SystMap()(1.0))
        cb.AddSyst(cb, "mcstats_$PROCESS_$BIN", "lnN", ch.SystMap('process')
                   (['qcd'],        toUnc(yields['qcdcr_qcd'][crbin]))
                   (['otherbkgs'],  2.0)
                   )
        # syst uncs
        if crbin in unc_dict:
            for proc in ['qcd', 'otherbkgs']:
                if proc in unc_dict[crbin]:
                    for unc in unc_dict[crbin][proc].values():
                        cb.cp().process([proc]).AddSyst(cb, unc.name, unc.type, ch.SystMap()(unc.value))
        tmpdc = os.path.join(outputdir, signal, '%s.tmp'%crbin)
        cb.WriteDatacard(tmpdc)
        with open(tmpdc) as tmpfile:
            with open(tmpdc.replace('.tmp', '.txt'), 'w') as dc:
                for line in tmpfile:
                    if 'rateParam' in line:
                        line = line.replace('\n', '  [0.01,5]\n') # set range of rateParam by hand
                    dc.write(line)
        os.remove(tmpdc)

def writeSR(signal):
    mergedbins = [bin for bin in binlist if '*' in binMaps['lepcr'][bin]]
    #mergedbins = [bin for bin in binlist if '+' in binMaps['lepcr'][bin]]
    for bin in binlist:
        rateParamFixes = {}
        cb = ch.CombineHarvester()
	#cb.SetVerbosity(3)
#         print bin
        cb.AddObservations(['*'], ['stop'], ['13TeV'], ['0l'], [(0, bin)])
        cb.AddProcesses(procs = ['signal'],     bin = [(0, bin)], signal=True)
        cb.AddProcesses(procs = ['ttbarplusw', 'znunu', 'qcd', 'ttZ', 'diboson'], bin = [(0, bin)], signal=False)
        if not blind: cb.ForEachObs(lambda obs : obs.set_rate(yields['data'][bin][0]))
        else:         cb.ForEachObs(lambda obs : obs.set_rate(1))
        cb.cp().process(['signal']).ForEachProc(lambda p : p.set_rate(sigYields[signal][bin][0]))
        cb.cp().process(['ttZ','diboson']).ForEachProc(lambda p : p.set_rate(yields[p.process()][bin][0]))
        cb.cp().process(['signal','ttZ','diboson']).AddSyst(cb, "mcstats_$PROCESS_$BIN", "lnN", ch.SystMap('process')
                   (['signal'],         toUnc(sigYields[signal][bin]))
                   (['ttZ'],            toUnc(yields['ttZ'][bin]))
                   (['diboson'],        toUnc(yields['diboson'][bin]))
                   )
        if bin not in mergedbins:
            # one to one CR
            cb.cp().process(['ttbarplusw','znunu','qcd']).ForEachProc(lambda p : p.set_rate(yields[p.process()][bin][0]))
            cb.cp().process(['ttbarplusw']).AddSyst(cb, "R_%s"%binMaps['lepcr'][bin], "rateParam", ch.SystMap()(1.0))
            cb.cp().process(['znunu'     ]).AddSyst(cb, "R_%s"%binMaps['phocr'][bin], "rateParam", ch.SystMap()(1.0))
            cb.cp().process(['qcd'       ]).AddSyst(cb, "R_%s"%binMaps['qcdcr'][bin], "rateParam", ch.SystMap()(1.0))
            cb.cp().process(['ttbarplusw','znunu','qcd']).AddSyst(cb, "mcstats_$PROCESS_$BIN", "lnN", ch.SystMap('process')
                       (['ttbarplusw'],     toUnc(yields['ttbarplusw'][bin]))
                       (['znunu'],          toUnc(yields['znunu'][bin]))
                       (['qcd'],            toUnc(yields['qcd'][bin]))
                       )
        else:
            cb.cp().process(['ttbarplusw','znunu','qcd']).ForEachProc(lambda p : p.set_rate(1))
            for proc in ['ttbarplusw','znunu','qcd']:
                rlt = parseBinMap(proc, binMaps[processMap[proc]][bin], yields)
                rName = "R_%s_%s"%(proc, bin)
                cb.cp().process([proc]).AddSyst(cb, rName, "rateParam", ch.SystMap()(999999.0)) # error if put formula here: need a workaround
                rateParamFixes[rName] = rlt['rateParam']
                cb.cp().process([proc]).AddSyst(cb, "mcstats_$PROCESS_$BIN", "lnN", ch.SystMap('process')
                        ([proc],            toUnc(rlt['yield']))
                        )
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
        tmpdc = os.path.join(outputdir, signal, '%s.tmp'%bin)
        cb.WriteDatacard(tmpdc)
        with open(tmpdc) as tmpfile:
            with open(tmpdc.replace('.tmp', '.txt'), 'w') as dc:
                for line in tmpfile:
                    if 'rateParam' in line and '999999' not in line:
                        line = line.replace('\n', '  [0.01,5]\n') # set range of rateParam by hand
                    for rName in rateParamFixes:
                        if rName not in line: continue
                        line = line.replace('999999', ' '.join(rateParamFixes[rName]))
                        break # fixed this rName
                    dc.write(line)
        os.remove(tmpdc)
        
readUncs()
for sig in signals:
    dest = os.path.join(outputdir, sig)
    if not os.path.exists(dest):
        os.makedirs(dest)
    writeLepcr(sig)
    writePhocr(sig)
    writeQCDcr(sig)
    writeSR(sig)
