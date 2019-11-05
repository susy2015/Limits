#! /usr/bin/python
import os
import sys
import re
import time
import ast
from shutil import copy
from ConfigParser import SafeConfigParser
from collections import OrderedDict
from ROOT import gROOT, TFile, TTree, TH1, TH1D, TH2D, Double
from math import sqrt
from array import array
gROOT.SetBatch(True)
TH1.SetDefaultSumw2(True)

def main():
    # to get the config file
    configFile = 'dc_0l_setup.conf'
    args = sys.argv[1:]
    if len(args) >= 1:
        configFile = args[0]
    if os.path.exists(configFile):
        print 'running with config file', configFile
    else:
        print 'you are trying to use a config file (' + configFile + ') that does not exist!'
        sys.exit(1)
    configparser = SafeConfigParser(dict_type=OrderedDict)
    configparser.optionxform = str

    config = DatacardConfig(configFile, configparser)
    dc = Datacard(config)
    dc.produceDatacards()

class DatacardConfig:
    # setup
    def __init__(self, conf_file, config_parser):
        self.conf_file = conf_file
        config_parser.read(self.conf_file)
        self.treebase = config_parser.get('config', 'treelocation')
        self.subdir = config_parser.get('config', 'subdir')
        self.datacarddir = os.path.join(config_parser.get('config', 'datacarddir'), self.subdir)
        self.setupbase = config_parser.get('config', 'setuplocation')
        self.xsecfile = config_parser.get('config', 'xsecfile')
        self.treename = config_parser.get('config', 'treename')
        self.weight = config_parser.get('config', 'weightname')
        self.signalweight = config_parser.get('config', 'signalweight')
        self.lumi = config_parser.get('config', 'lumiscale')
        self.filesuffix = config_parser.get('config', 'filesuffix')
        self.template = config_parser.get('config', 'template')
        self.uncdefinitions = config_parser.get('config', 'uncertainty_definitions')
        self.uncfileprefix = config_parser.get('config', 'uncertainty_fileprefix')
        self.binmapfile = config_parser.get('config', 'crtosr_bin_map')
        self.basesel = config_parser.get('config', 'basesel')
        self.usedummyuncs = config_parser.getboolean('config', 'dummyuncertainties')
        self.printuncs = config_parser.getboolean('config', 'printuncertainties')
        self.has_data = config_parser.getboolean('config', 'havedata')
        self.blind_sr = config_parser.getboolean('config', 'blindsr')
        self.scalesigtoacc = config_parser.getboolean('config', 'scalesigtoacc')
        self.saveoverwrites = config_parser.getboolean('config', 'saveoverwrites')
        self.signals = config_parser.get('signals', 'samples').replace(' ', '').split(',')
        self.backgrounds = config_parser.get('backgrounds', 'samples').replace(' ', '').split(',')
        self.yieldwidth = 20
        self.colwidth = 30
        self.evtwidth = 7
        self.uncwidth = 12

        self.bins = OrderedDict()
        for category_name in config_parser.options('bins'):
            self.bins[category_name] = ast.literal_eval(config_parser.get('bins', category_name))

        self.crconfigs = {cr : ast.literal_eval(config_parser.get('control_regions', cr)) for cr in config_parser.options('control_regions')}
        for cr in self.crconfigs:
            self.crconfigs[cr]['bins'] = OrderedDict()
            for category_name in config_parser.options(cr + '_bins'):
                self.crconfigs[cr]['bins'][category_name] = ast.literal_eval(config_parser.get(cr + '_bins', category_name))


class Datacard:
    def __init__(self, config):
        self.config = config
        # define signal region
        self.signalregion = FitRegion(config, type='signal')
        # define control regions
        self.extcontrolregions = {}
        self.fitcontrolregions = {}
        for cr, crconfig in config.crconfigs.iteritems():
            if crconfig['type'] == 'ext':
                self.extcontrolregions[cr] = FitRegion(config, crconfig=crconfig, type='external')
            else:
                self.fitcontrolregions[cr] = FitRegion(config, crconfig=crconfig, type='control')

        # fill mapping of signal region bins to control region bins
        self.srtocrbinmaps = {}
        self.fillBinMaps()

        # bkg process to control regions map
        self.bkgtocrmap = {bkg : cr for bkg in config.backgrounds for cr in self.extcontrolregions.values()+self.fitcontrolregions.values() if bkg==cr.srmcname}

        if not self.usedummyuncs:
            self.uncvalfiles = [f for f in os.listdir(self.setupbase) if self.uncfileprefix in f]
            self.uncnames = []
            self.uncertainties = {}
            self.compileUncertainties()
            self.fillUncertaintyValues()
            if self.printuncs :
                # printout for debugging
                print 'printing uncertanties by bin: uncName(' + 'type ::: ' + 'vals) [-1 means it will be calculated later]'
                for k in sorted(self.uncertainties.keys()):
                    print self.uncertainties[k]
                print 'printing cr yields by bin'
                for _, cr in self.extcontrolregions.iteritems():
                    for bin in cr.prediction:
                        print cr.prediction

    def __getattr__(self, name):
        # Look up attributes in self.config as well.
        return getattr(self.config, name)

    def fillBinMaps(self):
        """Fill maps from signal region to control region bins for transfer factors."""
        # use one-to-one mapping by default
        allcrs = self.extcontrolregions.values() + self.fitcontrolregions.values()
        for cr in allcrs:
            if cr.label not in self.srtocrbinmaps:
                self.srtocrbinmaps[cr.label] = {}
            for srbin in self.signalregion.binlist:
                self.srtocrbinmaps[cr.label][srbin] = srbin.replace('bin', 'bin_' + cr.label)
        # update the bin mapping from binmap.conf
        with open('%s/%s' % (self.setupbase, self.binmapfile), 'r') as f :
            for line in f :
                if line.startswith('#') or line.startswith('%') or line.strip() == '' :
                    continue;
                line = line.strip().rstrip('\n')
                entries = re.split('\s+:\s+', line)
                srbin = entries[0]
                crbin = entries[1]
                crlabel = crbin.split('_')[1]
                self.srtocrbinmaps[crlabel][srbin] = crbin

    def produceDatacards(self):
        '''Make datacards, one for every bin combination.
        First the template card is made with all backgrounds,
        then the signal points are looped to get the sig numbers.'''
        if os.path.exists(self.datacarddir) :
            print '\nWARNING!', self.datacarddir, 'already exists!'
            if self.saveoverwrites :
                t = time.localtime()
                moveStr = '_moveTime' + str(t.tm_year) + '-' + str(t.tm_mon) + '-' + str(t.tm_mday) + '-' + str(t.tm_hour * 10000 + t.tm_min * 100 + t.tm_sec)
                print 'renaming existing directory to', self.datacarddir + moveStr
                os.rename(self.datacarddir, self.datacarddir + moveStr)
                os.makedirs(self.datacarddir)
            else :
                print 'will be overwritten'
                os.popen('rm -rf ' + self.datacarddir)
        else :
            os.makedirs(self.datacarddir)
        copy(self.conf_file, self.datacarddir)
        # write datacards for control regions
        for _, cr in self.fitcontrolregions.iteritems():
            self.writeDatacards(cr)
        # write datacards for signal region
        self.writeDatacards(self.signalregion)

    def writeDatacards(self, fitregion):
        """Write out datacards for given fit region, one per for each defined bin and signal point
        """
        print '\n~~~Making datacards for ', fitregion.type, ' region ', fitregion.label, '~~~'
        # loop over all bins
        ibin = -1
        for binlabel in fitregion.binlist :
            ibin += 1
            binFileBaseName = '_%s.txt' % binlabel
            if fitregion.type == 'control' :
                binFileBaseName = '_' + fitregion.label + binFileBaseName
            templateFile = os.path.join(self.datacarddir, 'template' + binFileBaseName)

            # first create the template file for this combination of bins
            fdatacard = open(os.path.join(self.setupbase, self.template), 'r')
            templateDatacard = fdatacard.read()
            fdatacard.close()

            # lines to replace placeholders for current bin's template datacard
            # placeholders are left for signal numbers
            lineSBin = 'bin'.ljust(self.yieldwidth) + str(ibin)
            lineSBBin = 'bin'.ljust(self.yieldwidth) + str(ibin).ljust(self.yieldwidth)
            lineProcess1 = 'process'.ljust(self.yieldwidth) + 'signal'.ljust(self.yieldwidth)
            lineProcess2 = 'process'.ljust(self.yieldwidth) + '0'.ljust(self.yieldwidth)
            lineRate = 'rate'.ljust(self.yieldwidth) + 'SIGRATE'

            # loop through backgrounds to get yields
            ibkg = 0
            nBkgEvts = []
            bkgs_to_process = fitregion.backgrounds[-1:] if fitregion.type == 'control' else fitregion.backgrounds # for cr fit regions, bkg is the last element in 'backgrounds'

            for background in bkgs_to_process :
                nevts = None

                if fitregion.type == 'control':
                    nevts = self._get(fitregion.crmcname, binlabel)[0]
                else:
                    # fitregion.type == 'signal'
                    if background in self.bkgtocrmap:
                        cr = self.bkgtocrmap[background]
                        crbinlabel = self.srtocrbinmaps[cr.label][binlabel]
                        if cr.type == 'external':
                            # get prediction from cr
                            cr.prediction[binlabel]['srmc'] = max(cr.get(cr.srmcname, binlabel)[0], 1e-9)
                            nevts = float(cr.prediction[crbinlabel]['data']) / cr.prediction[crbinlabel]['mc'] * cr.prediction[binlabel]['srmc']
                            if cr.prediction[crbinlabel]['mcsub'] > 0.0 :
                                nevts *= cr.prediction[crbinlabel]['mcsub']
                            cr.prediction[binlabel]['pred'] = nevts
                    if nevts is None:
                        # if not from external cr, then take the raw mc
                        nevts = self._get(background, binlabel)[0]

                ibkg += 1
                nBkgEvts.append(nevts)
                lineSBBin += str(ibin).ljust(self.yieldwidth)
                lineProcess1 += background.ljust(self.yieldwidth)
                lineProcess2 += str(ibkg).ljust(self.yieldwidth)
                lineRate += str(nevts).ljust(self.yieldwidth)

            # compute data yield if applicable
            datayield = 0
            if self.has_data and not (self.blind_sr and fitregion.type == 'signal') :
                datayield = int(fitregion.get(fitregion.dataname, binlabel)[0])
            else :
                datayield = int(round(sum(nBkgEvts)))

            lineSObs = 'observation'.ljust(self.yieldwidth) + str(datayield)

            # fill uncertainties
            lineSys = ''
            nUncs = 0
            if self.usedummyuncs or not self.uncertainties :
            # flat uncertainties
                lineSysSig = 'sysSig\tlnN\t' + str(self.getDummyUncertainties('signal')) + '\t'
                nUncs += 1
                ibkg = -1
                lineSysBkg = ''
                for background in bkgs_to_process :
                    ibkg += 1
                    lineSysSig += '-\t'
                    lineSysBkg += 'sys' + background + 'bin' + str(ibin) + '\tlnN\t-\t'
                    if ibkg > 0 :
                        for ibef in range(ibkg) :
                            lineSysBkg += '-\t'
                    lineSysBkg += str(self.getDummyUncertainties('bkg')) + '\t'
                    if ibkg < len(fitregion.backgrounds) :
                        for iaft in range(len(fitregion.backgrounds) - ibkg - 1) :
                            lineSysBkg += '-\t'
                    lineSysBkg += '\n'
                    nUncs += 1
                lineSys += lineSysSig + '\n' + lineSysBkg
            else :
            # fill uncertainties according to values defined in uncertainty config files
                for uncname in sorted(self.uncertainties.keys()) :
                    uncline = self.getUncertaintyLine(uncname, binlabel, bkgs_to_process)
                    lineSys += uncline
                    if not uncline == '' :
                        nUncs += 1

            # put current lines into the placeholders in the template datacard
            templateDatacard = templateDatacard.replace('IMAX'    , '1')  # need to change if more bins are put into one datacard
            templateDatacard = templateDatacard.replace('JMAX'    , str(1 if fitregion.type == 'control' else len(fitregion.backgrounds)))
            templateDatacard = templateDatacard.replace('KMAX'    , str(nUncs))
            templateDatacard = templateDatacard.replace('BKGLIST' , ', '.join([fitregion.backgrounds[0].split('_')[0]] if fitregion.type == 'control' else [b for b in fitregion.backgrounds]))
            templateDatacard = templateDatacard.replace('SBIN'    , lineSBin)
            templateDatacard = templateDatacard.replace('SOBS'    , lineSObs)
            templateDatacard = templateDatacard.replace('SBBIN'   , lineSBBin)
            templateDatacard = templateDatacard.replace('PROCESS1', lineProcess1)
            templateDatacard = templateDatacard.replace('PROCESS2', lineProcess2)
            templateDatacard = templateDatacard.replace('RATE'    , lineRate)
            templateDatacard = templateDatacard.replace('SYS\n'   , lineSys)

            # save the template datacard
            f = open(templateFile, 'w')
            f.write(templateDatacard)
            f.close()

            # now loop through the signal files to get the actual datacards
            for signal in self.signals:
                nSig = fitregion.get(signal, binlabel)[0]
                if nSig == 0.0 :
                    nSig = 0.00000001

                # put signal numbers into the placeholders in the template datacard
                fdatacard = open(templateFile, 'r')
                datacard = fdatacard.read()
                fdatacard.close()
                datacard = datacard.replace('SIGRATE', str(nSig).ljust(self.yieldwidth))
                dclines = datacard.split('\n')
                sigunclines = []
                for iline in range(len(dclines)) :
                    line = dclines[iline]
                    if '$SIG' in line or 'SIGUNC' in line :
                        hasUncVal = False
                        uncname = line.split()[0]
                        # any of the following if cases are problematic!
                        if not self.uncertainties.has_key(uncname) :
                            print 'Didn\'t find uncertainty', uncname, 'in uncertainty list'
                        elif not self.uncertainties[uncname].vals.has_key(binlabel) :
                            print 'Uncertainty', uncname, 'not defined for bin', binlabel
                        elif not self.uncertainties[uncname].vals[binlabel].has_key(signal) :
                            print 'Uncertainty', uncname, 'not filled for', signal, 'in bin', binlabel
                        else :
                            hasUncVal = True
                        sigUncVal = self.uncertainties[uncname].vals[binlabel][signal] if hasUncVal else 1.0
                        newline = line.replace('$SIG', 'signal').replace('SIGUNC', '%4.3f' % sigUncVal)
                        dclines[iline] = newline
                datacard = '\n'.join(dclines)

                # save the current datacard
                datacardSaveLocation = os.path.join(self.datacarddir, signal)
                if not os.path.exists(datacardSaveLocation) :
                    os.makedirs(datacardSaveLocation)
                datacardName = os.path.join(datacardSaveLocation, signal + binFileBaseName)
                f = open(datacardName, 'w')
                f.write(datacard)
                f.close()

    def getDummyUncertainties(self, procname):
        """Function to get dummy uncertanties.
        """
        if procname == 'signal' :
            return 1.1
        else :
            return 1.3
        return '-'

    def _getBinList(self, uncname, sample=None):
        crname = uncname.split('_')[0]
        if crname in self.extcontrolregions:
            binlist = self.extcontrolregions[crname].binlist[:]
        else:
            binlist = self.signalregion.binlist[:]
            for cr in self.fitcontrolregions.values():
                # add cr bins of fit regions for singals and corresponding bkg
                if sample and (sample != cr.backgrounds[-1] or sample not in self.signals): continue
                binlist += cr.binlist
        return binlist

    def _get(self, sample, binlabel):
        val = None
        for cr in self.extcontrolregions.values()+self.fitcontrolregions.values():
            if cr.label == binlabel.lstrip('bin_').split('_')[0]:
                val = cr.get(sample, binlabel)
                break
        if not val:
            val = self.signalregion.get(sample, binlabel)
        return val

    def compileUncertainties(self):
        """Get list of all uncertainty names and values and samples to which they must be applied
        """
        print '\n~~~Compiling uncertainty list~~~'
        with open('%s/%s' % (self.setupbase, self.uncdefinitions), 'r') as f :
            for line in f :
                if line.startswith('#') or line.startswith('%') or line.strip() == '' :
                    continue
                line = line.strip().rstrip('\n')
                entries = re.split('\s+', line)
                name = entries[0]
                type = entries[1]
                if '$BIN' not in name:
                    if self.uncertainties.has_key(name) :
                        continue
                    self.uncertainties[name] = Uncertainty(name, type)
                    self.uncnames.append(name)
                else :
                    binlist = self._getBinList(name)
                    for binlabel in binlist :
                        uncname = name.replace('$BIN', binlabel)
                        if '$BKG' not in uncname:
                            # '$SIG' will be grouped together w/ the same uncname
                            if self.uncertainties.has_key(uncname) :
                                continue
                            self.uncertainties[uncname] = Uncertainty(uncname, type)
                            self.uncnames.append(uncname)
                        else:
                            for samp in self.backgrounds:
                                sampuncname = uncname.replace('$BKG', samp)
                                if self.uncertainties.has_key(sampuncname) :
                                    continue
                                self.uncertainties[sampuncname] = Uncertainty(sampuncname, type)
                                self.uncnames.append(sampuncname)

    def fillUncertaintyValues(self):
        """Get values of each designated uncertainty
        """
        # mcstatuncs = open('mcstatuncs.txt','w')
        print '\n~~~Filling uncertainty values~~~'
        for file in self.uncvalfiles :
            print 'Opening ', file
            with open(os.path.join(self.setupbase, file), 'r') as f :
                for line in f :
                    if line.startswith('#') or line.startswith('%') or line.strip() == '' :
                        continue
                    line = line.strip().rstrip('\n')
                    # example line: [all     lumi                signal,diboson              1.062]
                    entries = re.split('\s+', line)
                    _bin,_uncname,_samples = entries[:3]
                    samples = _samples.strip().split(',')
                    uncval = entries[3] if len(entries)>3 else None
                    for samp in samples:
                        if samp!='signal' and samp not in self.backgrounds and samp not in self.signals:
                            print '[Warning] Uncertainty %s is defined for an unknown sample %s and will be ignored!'%(_uncname, samp)
                            samples.remove(samp)
                    if 'signal' in samples:
                        samples.remove('signal')
                        samples += self.signals
                    if _bin != 'perbin':
                        # correlated unc
                        binlist = self._getBinList(_uncname) if _bin=='all' else _bin.strip().split(',')
                        uncname = _uncname

                        hasunc = uncname in self.uncertainties
                        if not hasunc:
                            # check if unc w/o suffix is defined
                            for name, unc in self.uncertainties.iteritems():
                                if uncname.startswith(name):
                                    self.uncertainties[uncname] = Uncertainty(uncname, unc.type)
                                    self.uncnames.append(uncname)
                                    hasunc = True
                                    break
                        if not hasunc :
                            print ' [Warning] Uncertainty', uncname, 'is not defined and will be ingored!'

                        if len(uncname) > self.colwidth:
                            self.colwidth = len(uncname) + 5
                        unc = self.uncertainties[uncname]
                        for binlabel in binlist:
                            for samp in samples:
                                unc.vals[binlabel][samp] = float(uncval)
                    else:
                        # uncorrelated 'perbin' unc
                        print 'Processing perbin unc', _uncname
                        for samp in samples:
                            binlist = self._getBinList(_uncname, samp)
                            for binlabel in binlist:
                                if '$BIN' in _uncname:
                                    uncname = _uncname.replace('$BIN', binlabel)
                                else:
                                    uncname = '_'.join([_uncname, binlabel])
                                
                                if len(uncname) > self.colwidth:
                                    self.colwidth = len(uncname) + 5
                                unc = self.uncertainties[uncname]
                                crname = uncname.split('_')[0]
                                if unc.type == 'gmN':
                                    # for, e.g., photoncr_stat
                                    cr = self.extcontrolregions[crname]
                                    crnevts = int(round(cr.get(cr.dataname, binlabel)[0]))
                                    cr.prediction[binlabel]['data'] = max(crnevts, 1)
                                    cr.prediction[binlabel]['mc'] = max(cr.get(cr.crmcname, binlabel)[0], 0.00000001)
                                    cr.prediction[binlabel]['mcsub'] = max(cr.get(cr.crsubname, binlabel)[0], 0.00000001) if cr.crsubname else 0.0
                                    if hasattr(cr, 'crnormsel'):
                                        cr.prediction[binlabel]['mcsub'] *= cr.get('crnorm', binlabel)[0]
                                    if hasattr(cr, 'crsubRawMC'):
                                        cr.prediction[binlabel]['mcsub'] += max(cr.get(cr.crsubRawMC, binlabel)[0], 0.00000001)
                                    # Get the subtraction correction
                                    if cr.prediction[binlabel]['mcsub'] > 0 :
                                        if cr.prediction[binlabel]['data'] < 10 :
                                            tempMC = cr.get(cr.crmcname + '_subsel', binlabel)[0]
                                            cr.prediction[binlabel]['mcsub'] = (1.0 - (cr.prediction[binlabel]['mcsub'] / (tempMC + cr.prediction[binlabel]['mcsub'])))
                                        else :
                                            cr.prediction[binlabel]['mcsub'] = (1.0 - (cr.prediction[binlabel]['mcsub'] / float(cr.prediction[binlabel]['data'])))
                                    unc.vals[binlabel][samp] = -1
                                elif unc.type == 'lnU':
                                    unc.vals[binlabel][samp] = float(uncval) if uncval else 2
                                    # to use lnN unc, comment the line above and uncomment the lines below
                                    # cr = self.fitcontrolregions[crname]
                                    # crnevts = int(cr.get(cr.dataname, binlabel)[0])
                                    # crnevts = max(crnevts, 1)
                                    # unc.vals[binlabel][samp] = 1 + sqrt(crnevts)/crnevts
                                    # unc.type = 'lnN'
                                elif unc.type == 'lnN':
                                    if crname in self.extcontrolregions:
                                        # mcstat unc for 'external' cr, e.g., photoncr_mcstat
                                        (crevts, crunc) = cr.get(cr.crmcname, binlabel)
                                        self.uncertainties[uncname].vals[binlabel][samp] = 1 + (crunc / crevts) if crevts > 0 else 2.00
                                    else :
                                        # mcstat unc for sr bkgs/signals
                                        # - bkgs from raw mc
                                        # - bkgs/signals in fit cr
                                        # - bkgs from ext cr [sr mcstats]
                                        def _fill(binlabel, value):
                                            (mcevts, mcunc) = value
                                            if not mcevts == 0 :
                                                if mcunc > mcevts :
                                                    print 'Warning! %s has %s uncertainty %4.2f in bin %s, setting to 100' % (samp, uncname, 100.0 * mcunc / mcevts, binlabel)
                                                    unc.vals[binlabel][samp] = 2.0
                                                else :
                                                    unc.vals[binlabel][samp] = 1 + (mcunc / mcevts)
                                            else :
                                                unc.vals[binlabel][samp] = 2.0

                                        cr=self.bkgtocrmap[samp] if samp in self.bkgtocrmap else None 
                                        if cr:
                                            # from ext/fit control region
                                            if cr.type=='control' and binlabel not in self.signalregion.binlist:
                                                _fill(binlabel, cr.get(cr.crmcname, binlabel))
                                            else:
                                                _fill(binlabel, cr.get(cr.srmcname, binlabel))
                                        else:
                                            # from raw MC and sr signals
                                            _fill(binlabel, self._get(samp, binlabel))
                                else:
                                    raise Exception('Type %s is not supported for perbin uncertainty!'%unc.type)
                                # mcstatuncs.write('%s\t%s\t%s\t%4.3f\n' % (binname,uncname,samp,unc.vals[binname][samp]))
        # mcstatuncs.close()

    def getUncertaintyLine(self, uncname, binlabel, backgrounds):
        """Get line with uncertainty name, type, and values correctly formatted
        """
        unc = self.uncertainties[uncname]
        crname = uncname.split('_')[0]
        if crname not in self.extcontrolregions.keys()+self.fitcontrolregions.keys():
            crname = None
        if crname:
            # unc related to cr: are we dealing w/ signal region or fit CR?
            if binlabel in self.signalregion.binlist:
                cr = self.extcontrolregions[crname] if crname in self.extcontrolregions else self.fitcontrolregions[crname]
                crbinlabel = self.srtocrbinmaps[cr.label][binlabel]
            else:
                #fit CR
                crbinlabel = binlabel
            if crbinlabel not in unc.vals: 
                return ''
        if '$SIG' in unc.label :
            # only for signal mc stats (?)
            uncline = unc.label.ljust(self.colwidth - 2)
        else :
            uncline = unc.label.ljust(self.colwidth)
        uncline += ' ' + unc.type + ' '
        # don't count uncertainties with no entries for any of the processes
        hasEntry = False
        if unc.type == 'gmN' :
            if crbinlabel not in cr.prediction:
                print 'Control region yields not loaded for ', uncname
                return ''
            uncline += str(cr.prediction[crbinlabel]['data']).ljust(self.evtwidth)
            hasEntry = True
        else:
            uncline += ' ' * self.evtwidth
        if self.signals[0] in unc.vals[binlabel]:
            # if this uncname is relevant for signal
            uncline += ('SIGUNC').ljust(self.uncwidth - 1)
            hasEntry = True
        else :
            uncline += '-'.ljust(self.uncwidth)
        # background uncerts
        for background in backgrounds:
            unc_binlabel = crbinlabel if crname else binlabel
            if background in unc.vals[unc_binlabel]:
                if unc.type == 'gmN':
                    uncline += ('%6.5f' % ( cr.prediction[binlabel]['pred'] / cr.prediction[crbinlabel]['data'])).ljust(self.uncwidth)
                else:
                    uncline += ('%4.3f' % unc.vals[unc_binlabel][background]).ljust(self.uncwidth)
                hasEntry = True
            else:
                uncline += '-'.ljust(self.uncwidth)
        uncline += '\n'
        if not hasEntry :
            return ''
        return uncline

class FitRegion:
    def __init__(self, config, crconfig={}, type='signal'):
        ':type config: DatacardConfig'
        self.config = config
        self.signals = config.signals
        self.weight = config.weight
        self.signalweight = config.signalweight
        self.basesel = config.basesel
        self.bins = config.bins
        self.treesubdir = ''

        self.type = type
        if type == 'signal':
            self.label = ''
            self.dataname = 'data'
            self.backgrounds = config.backgrounds
        else:
            if 'treesubdir' in crconfig:
                self.treesubdir = crconfig['treesubdir']
            self.label = crconfig['label'] if 'label' in crconfig else crconfig['dataFile'].split('_')[-1]
            self.dataname = crconfig['dataFile']
            self.backgrounds = crconfig['mcFiles']
            self.srmcname = crconfig['mcFiles'][-1]
            self.crmcname = crconfig['mcFiles'][0]
            self.bins = crconfig['bins']
            self.crwgt = crconfig['crwgt']
            self.crsignalwgt = crconfig['crsigwgt'] if 'crsigwgt' in crconfig else '1.0'
            self.crsel = crconfig['crsel']
            self.srwgt = crconfig['srwgt'] if 'srwgt' in crconfig else config.weight
            self.srsel = crconfig['srsel'] if 'srsel' in crconfig else config.basesel
            # MC to be subtracted
            self.crsubname = crconfig['mcFiles'][1]
            if self.crsubname:
                self.crsubsel = crconfig['crsubsel']
            if 'crsubRawMC' in crconfig:
                self.crsubRawMC = crconfig['crsubRawMC']
            # norm correction for the subtraction
            if 'crnormsel' in crconfig:
                self.crnormsel = crconfig['crnormsel']
                self.crnormwgt = crconfig['crnormwgt']
            # dict to store prediction
            self.prediction = Vividict()

        # dict to store yields for all samples
        self.numEventsAndErrors = {}

        print '\n~~~Compiling bin list for %s region %s~~~' % (self.type, self.label)
        self.compileBinList()
        for binlabel in self.binlist:
            print binlabel

    def getBinLabels(self, region, catetory_name, category):
        '''Get bin name, e.g., 'bin_medboost_lowptb_250to350' for sr, and 'bin_photoncr_medboost_lowptb_250to350' for cr.
        Category format:
        catA: { 'cut': '(j1lpt>250 && j1lpt<500) && csvj1pt<40',
                'var': 'met',
                'bin': [250, 350, 450, 550, 1000] }'''
        region = '_' + region if region else ''
        bins = category['bin']
        var  = category['var']
        nbins = len(bins)-1
        return ['bin%s_%s_%s%sto%s' % (region, catetory_name, var, str(bins[i]), str(bins[i+1]) if i<nbins-1 else 'inf') for i in range(nbins)]
#        return ['bin%s_%s_%d' % (region, catetory_name, lowedge) for lowedge in category['bin'][:-1]]

    def compileBinList(self):
        self.binlist = []
        for name, cat in self.bins.iteritems():
            self.binlist += self.getBinLabels(self.label, name, cat)

    def removeNegatives(self, hist):
        for ibin in range(hist.GetNbinsX() + 2):
            bincontent = hist.GetBinContent(ibin)
            binerror = hist.GetBinError(ibin)
            if hist.GetBinContent(ibin) < 0:
                hist.SetBinContent(ibin, 0)
                hist.SetBinError(ibin, binerror + abs(bincontent))

    def getCategoryYields(self, tree, wgtvar, basesel, category):
        '''Get a list of yields for the given category by projecting the tree.'''
        bins = category['bin']
        nbins = len(bins) - 1
        htmp = TH1D('htmp', 'htmp', nbins, array('d', bins))
        cutstr = wgtvar + "*(" + basesel + ' && ' + category['cut'] + ")"
        tree.Project('htmp', category['var'], cutstr, 'e')

        # add overflow
        e1 = htmp.GetBinError(nbins);
        e2 = htmp.GetBinError(nbins + 1);
        htmp.AddBinContent(nbins, htmp.GetBinContent(nbins + 1));
        htmp.SetBinError(nbins, sqrt(e1 * e1 + e2 * e2));
        htmp.SetBinContent(nbins + 1, 0);
        htmp.SetBinError(nbins + 1, 0);

        # remove negatives
        self.removeNegatives(htmp)

        yields = []
        for ib in range(nbins):
            yields.append((htmp.GetBinContent(ib + 1), htmp.GetBinError(ib + 1)))
        return yields

    def getYield(self, filename, wgtvar, basesel):
        '''Calculate the yield for the given selection.'''
        filepath = os.path.join(self.config.treebase, self.treesubdir, filename + self.config.filesuffix)
        print '[%s region %s] Reading file %s...' % (self.type, self.label, filename)
        file = TFile(filepath)
        tree = file.Get(self.config.treename)
        htmp = TH1D('htmp', 'htmp', 1, 0, 1e9)
        cutstr = wgtvar + "*(" + basesel + ")"
        tree.Project('htmp', wgtvar, cutstr, 'e')
        error = Double()
        value = htmp.IntegralAndError(0, 2, error)
        file.Close()
        # remove negatives
        if value < 0:
            error += abs(value)
            value = 0
        return value, error

    def getNormFactor(self, dataname, mcname, subname, wgtvar, selection):
        '''Calculate normalization factor.'''
        crnorm_wgtvar = self.config.lumi + '*' + wgtvar
        normdata = self.getYield(dataname, '1.0', selection)[0]
        normmc = self.getYield(mcname, crnorm_wgtvar, selection)[0]
        normsub = self.getYield(subname, crnorm_wgtvar, selection)[0]
        if normdata > 0 and normsub + normmc > 0:
            return normdata / (normmc + normsub)
        else:
            return 1.0

    def calcSampleYields(self, filename, wgtvar, basesel, bins, region=None, extra=''):
        '''Calculate the yields of a sample in all bins.
        The result is a dict {binlabel:(nevt, error)}, and is stored in self.numEventsAndErrors.
        Keyword parameters:
        region -- region name for binlabel. Set to empty string '' if calculating sr MC yields in a control region. Leave empty to use the default label of the region.
        extra -- extra string for indexing in self.numEventsAndErrors, used if multiple yields are calcuated from the same file with different selections.'''
        filepath = os.path.join(self.config.treebase, self.treesubdir, filename + self.config.filesuffix)
        print '[%s region %s] Reading file %s...' % (self.type, self.label, filename)
        file = TFile(filepath)
        tree = file.Get(self.config.treename)
        yields_dict = {}
        # need 'is None' because empty string '' (for sr) is also False
        region = self.label if region is None else region
        for name, cat in bins.iteritems():
            labels = self.getBinLabels(region, name, cat)
            yields = self.getCategoryYields(tree, wgtvar, basesel, cat)
            yields_dict.update(dict(zip(labels, yields)))
        self.numEventsAndErrors[filename + extra] = yields_dict
        file.Close()

    def calcNormFactorPerCategory(self, dataname, mcname, subname, wgtvar, basesel, bins, label='crnorm'):
        '''Calculate normalization factors per category and fill in self.numEventsAndErrors.'''
        norm_dict = {}
        for name, cat in bins.iteritems():
            labels = self.getBinLabels(self.label, name, cat)
            norm_factor = self.getNormFactor(dataname, mcname, subname, wgtvar, basesel + ' && ' + cat['cut'])
            norms = [(norm_factor, 0) for _ in range(len(labels))]
            norm_dict.update(dict(zip(labels, norms)))
        self.numEventsAndErrors[label] = norm_dict

    def calcYields(self, sample):
        '''Calculate the yields for a sample. Evaluate weight and selection based on sample name.'''

        # get signal xsec
        if sample in self.signals and self.config.scalesigtoacc:
            mstop = int(sample.split('_')[-2])
            if 'T2bW' in sample :
                mstop = int(sample.split('_')[-3])
            xsecfile = TFile(self.config.xsecfile)
            xsechist = xsecfile.Get('xsecs')
            xsec = xsechist.Interpolate(mstop)

        if self.type == 'signal':
            # signal region
            wgtvar = self.config.lumi + '*' + self.weight
            if sample == self.dataname:
                if self.config.has_data and not self.config.blind_sr:
                    self.calcSampleYields(sample, '1.0', self.basesel, self.bins)
            elif sample in self.signals:
                sigwgt = self.config.lumi + '*' + self.signalweight
                sig_wgtvar = sigwgt + '/' + str(xsec) if self.config.scalesigtoacc else sigwgt
                self.calcSampleYields(sample, sig_wgtvar, self.basesel, self.bins)
            else:
                # backgrounds
                self.calcSampleYields(sample, wgtvar, self.basesel, self.bins)
        else:
            # control regions
            crwgtvar = self.config.lumi + '*' + self.crwgt
            srwgtvar = self.config.lumi + '*' + self.srwgt
            if sample == self.dataname:
                if self.config.has_data:
                    self.calcSampleYields(sample, '1.0', self.crsel, self.bins)
                else:
                    self.calcSampleYields(sample, crwgtvar, self.crsel, self.bins)
            elif sample == self.crmcname:
                self.calcSampleYields(sample, crwgtvar, self.crsel, self.bins)
            elif sample == self.crmcname + '_subsel':
                self.calcSampleYields(self.crmcname, crwgtvar, self.crsubsel, self.bins, extra='_subsel')
            elif sample == self.crsubname or (hasattr(self, 'crsubRawMC') and sample == self.crsubRawMC):
                # cr subtraction sample
                self.calcSampleYields(sample, crwgtvar, self.crsel, self.bins)
            elif sample == 'crnorm':
                self.calcNormFactorPerCategory(self.dataname, self.crmcname, self.crsubname, self.crnormwgt, self.crnormsel, self.bins, label='crnorm')
            elif sample == self.srmcname:
                self.calcSampleYields(sample, srwgtvar, self.srsel, self.config.bins, region='')
            elif sample in self.signals:
                crsigwgt = self.config.lumi + '*' + self.crsignalwgt
                sig_crwgtvar = crsigwgt + '/' + str(xsec) if self.config.scalesigtoacc else crsigwgt
                self.calcSampleYields(sample, sig_crwgtvar, self.crsel, self.bins)

    def get(self, sample, binlabel):
        ''' Get the yield of a specific sample in a given bin. Returns a tuple (value, error).
        Perform the actual calculation at the first time when a sample is requested.'''
        try:
            return self.numEventsAndErrors[sample][binlabel]
        except KeyError:
            self.calcYields(sample)
            return self.numEventsAndErrors[sample][binlabel]

class Vividict(dict):
    '''https://stackoverflow.com/questions/635483/what-is-the-best-way-to-implement-nested-dictionaries'''
    def __missing__(self, key):
        value = self[key] = type(self)() # retain local pointer to value
        return value                     # faster to return than dict lookup

class Uncertainty:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.label = name
        self.vals = Vividict()
    def __str__(self):
        printStr = self.name + '(' + self.type + ' ::: '
        printStr += ' ::: '
        for k in self.vals.keys():
            printStr += str(k) + ':' + str(self.vals[k]) + ','
        printStr += ')'
        return printStr


if __name__ == '__main__': main()
