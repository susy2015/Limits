#! /usr/bin/python
#
# # Note on running:
# #
# # In order to run this, you need to set up CMSSW_7_1_5 as follows
# # (for more info see: https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit#How_to_prepare_the_datacard)
#
# export SCRAM_ARCH=slc6_amd64_gcc481 # for csh use: setenv SCRAM_ARCH slc6_amd64_gcc481
# cmsrel CMSSW_7_1_5                  # must be a 7_1_X release >= 7_1_5;  (7.0.X and 7.2.X are NOT supported either)
# cd CMSSW_7_1_5/src
# cmsenv
# git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
#
# # Updating to a tag (both the first time and whenever there are updates):
#
# cd HiggsAnalysis/CombinedLimit
# git fetch origin
# git checkout v5.0.1
# scramv1 b clean; scramv1 b # always make a clean build, as scram doesn't always see updates to src/LinkDef.h
#
import multiprocessing

"""This takes all the per-bin datacards from makeDatacards.py, combines them into a single
datacard and then runs the limits. At the moment it assumes that the datacards for each
signal point are in their own folder and combines all files in each signal point's folder.

It currently runs HybridNew, ProfileLikelihood, and Asymptotic.
"""

import commands
import os
import sys
import time
import array
import argparse
from ConfigParser import SafeConfigParser
from ROOT import gROOT, TFile, TTree, TH1D, TH2D, TChain, TGraph2D
gROOT.SetBatch(True)

import functools
from multiprocessing import Pool, Lock
lock = Lock()  # global lock
def lprint(command, output):
    lock.acquire()
    print '>', command
    print output
    lock.release()

import string
import random
def rand_generator(size=10, chars=string.ascii_letters):
    return ''.join(random.choice(chars) for _ in range(size))


def main():
    parser = argparse.ArgumentParser(
        description='Produce or print limits based on existing datacards')
    parser.add_argument("-m", "--maxlikelihood", dest="maxLikelihoodFit", action='store_true',
                        help="Run the maximum likelihood fit using the signal point defined by the -s option. [Default: False]")
    parser.add_argument("-s", "--signal", dest="signalPoint", default='T2tt_850_100',
                        help="Signal point to use when running the maximum likelihood fit. [Default: T2tt_850_100]")
    parser.add_argument("-p", "--print", dest="printLimits", action='store_true',
                        help="Print last set of limits/significances calculated. [Default: False]")
    parser.add_argument("-f", "--fill", dest="fillAsymptoticLimits", action='store_true',
                        help="Fill root files with results of asymptotic limit calculations for all signal points. [Default: False]")
    parser.add_argument("-n", "--name", dest="name", default='T2tt',
                        help="Name of the signal, used as suffix of the file names. [Default: T2tt]")
#     parser.add_argument("-l", "--limfile", dest="limitFile", default='results_T2tt.root',
#                         help="Name of output file with upper limit histograms. [Default: results_T2tt.root]")
#     parser.add_argument("-e", "--excfile", dest="exclusionFile", default='limit_scan_T2tt.root',
#                         help="Name of output file with exclusion curves and interpolated cross section limits. [Default: results_T2tt.root]")
    parser.add_argument("-i", "--interpolate", dest="addInterpolation", type=int, default=0, choices=[
                        0, 1], help="Whether or not to run Chris West's interpolation. [Options: 0 (no), 1 (yes). Default: 0]")
    parser.add_argument("-c", "--config", dest="configFile", default='dc_0l_setup.conf',
                        help="Config file to be run with. [Default: dc_0l_setup.conf]")
    args = parser.parse_args()

    # to get the config file
    if os.path.exists(args.configFile):
        print 'running with config file', args.configFile
    else:
        print 'you are trying to use a config file (' + args.configFile + ') that does not exist!'
        sys.exit(1)

    configparser = SafeConfigParser()
    configparser.optionxform = str

    limconfig = LimitConfig(args.configFile, configparser)

    if args.printLimits:
        printLimits(limconfig)
    elif args.fillAsymptoticLimits:
        if limconfig.limitmethod == 'Asymptotic' or limconfig.limitmethod == 'AsymptoticObs':
            sigfile = 'significances_%s.root'%args.name
            fillSignificances(limconfig, sigfile, args.name)
        else:
            limitFile = 'results_%s.root'%args.name
            exclusionFile = 'limit_scan_%s.root'%args.name
            fillAsymptoticLimits(limconfig, limitFile, exclusionFile, args.addInterpolation)
    elif args.maxLikelihoodFit:
        runMaxLikelihoodFit(limconfig, args.signalPoint)
    else:
        runLimits(limconfig)


class LimitConfig:
  # setup
  def __init__(self, conf_file, config_parser):
    self.conf_file = conf_file
    config_parser.read(self.conf_file)
    self.limitmethod = config_parser.get('config', 'limitmethod')
    self.subdir = config_parser.get('config', 'subdir')
    self.datacarddir = os.path.join(config_parser.get('config', 'datacarddir'), self.subdir)
    self.limitdir = os.path.join(config_parser.get('config', 'limitdir'), self.subdir + '_' + self.limitmethod)
    self.signals = config_parser.get('signals', 'samples').replace(' ', '').split(',')
    self.scalesigtoacc = config_parser.getboolean('config', 'scalesigtoacc')
    self.expectedonly = config_parser.getboolean('config', 'expectedonly')


def getLimit(rootFile, getMean=False, limit={}):
    file = TFile(rootFile)
    output = ''
    if getMean:
        tree = file.Get('limit')
        htmp = TH1D('htmp', 'htmp', 1, 0, 10000)
        tree.Project('htmp', 'limit')
        mean = htmp.GetMean()
        # error = htmp.GetError()
        # output = 'mean=' + str(mean) + '\terror=' + str(error) + '\n'
        output = 'mean=' + str(mean) + '\n'
        limit = mean
    else:
        tree = TChain('limit')
        tree.Add(rootFile)
        for entry in tree:
            if entry.quantileExpected < 0:
                output += 'Observed : r < %4.2f \n' % (entry.limit)
            else:
                output += 'Expected %4.2f %% : r < %4.2f \n' % (
                    (100.0 * entry.quantileExpected), entry.limit)
            if entry.quantileExpected < 0:
                limit['obs'] = entry.limit
            if 0.1 < entry.quantileExpected < 0.2:
                limit['-1'] = entry.limit
            elif 0.4 < entry.quantileExpected < 0.6:
                limit['0'] = entry.limit
            elif 0.8 < entry.quantileExpected < 0.9:
                limit['+1'] = entry.limit
    return (output, limit)

def printLimits(config):
    limits = []
    currentDir = os.getcwd()
    for signal in config.signals:
        outputLocation = os.path.join(currentDir, config.limitdir, signal)
        rootFile = ''
        dummyFiles = os.listdir(outputLocation)
        for df in dummyFiles:
            if 'higgsCombine' in df: rootFile = os.path.join(
                currentDir, config.limitdir, signal, df)
        if rootFile == '':
            limits.append(signal + ': no limit found..')
        else:
            output = getLimit(
                rootFile, False) if config.limitmethod == 'AsymptoticLimits' else getLimit(rootFile, True)
            # print signal, ':\n', output
            tempLimit = ''
            if config.limitmethod == 'AsymptoticLimits':
                for line in output[0].split('\n'):
                    if 'Expected 50' in line:
                        tempLimit = line.replace('Expected', signal + ' expected')
            else:
                for line in output[0].split('\n'):
                    if 'mean' in line:
                        tempLimit = line.replace('mean=', signal + ': ')
            limits.append(tempLimit)

    # print the results
    print '=' * 5, 'RESULTS', '(' + config.limitmethod + ')', '=' * 5
    print '\n'.join(limits)
    print '\n'

def fillSignificances(config, sigfile, name):
    limits = []
    currentDir = os.getcwd()
    outfile = TFile(sigfile, 'RECREATE')
    maxmstop = 0.0
    minmstop = 0.0
    maxmlsp = 0.0
    minmlsp = 0.0
    mstop_step = 1
    mlsp_step = 10 if 'fbd' in sigfile else 1
    for signal in config.signals:
        mstop = int(signal.split('_')[1])
        mlsp = int(signal.split('_')[2])
        if mstop > maxmstop: maxmstop = mstop
        if mlsp > maxmlsp: maxmlsp = mlsp
        if minmstop == 0.0 or mstop < minmstop: minmstop = mstop
        if minmlsp == 0.0 or mlsp < minmlsp: minmlsp = mlsp
    nbinsx = int((maxmstop - minmstop) / mstop_step)
    nbinsy = int((maxmlsp - minmlsp) / mlsp_step)
#     minmstop -= 0.5*mstop_step
#     maxmstop -= 0.5*mstop_step
#     minmlsp  -= 0.5*mlsp_step
#     maxmlsp  -= 0.5*mlsp_step
    print 'XMin: %4.2f, XMax: %4.2f, YMin: %4.2f, YMax: %4.2f, NXBins: %d, NYBins: %d' % (minmstop, maxmstop, minmlsp, maxmlsp, nbinsx, nbinsy)

    hsig = TH2D('hsig', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)
    for signal in config.signals:
        outputLocation = os.path.join(currentDir, config.limitdir, signal)
        rootFile = ''
        dummyFiles = os.listdir(outputLocation)
        for df in dummyFiles:
            if 'higgsCombine' in df: rootFile = os.path.join(
                currentDir, config.limitdir, signal, df)
        if rootFile == '':
            limits.append(signal + ': no limit found..')
        else:
            output = getLimit(rootFile, True)
            print signal, ':\n', output
            tempLimit = ''
            for line in output[0].split('\n'):
                if 'mean' in line:
                    tempLimit = line.replace('mean=', signal + ': ')
            limits.append(tempLimit)
            mstop = int(signal.split('_')[1])
            mlsp = int(signal.split('_')[2])
            limit = output[1]
            bin = hsig.FindBin(mstop, mlsp)
            hsig.SetBinContent(bin, limit)
#             hsig.Fill(mstop, mlsp, limit)

    outfile.cd()
    hsig.Write()
    outfile.Close()
    os.system('root -l -q -b makeSigScanPlots.C\\(\\"%s\\",\\"%s\\"\\)'%(sigfile, name))

    # print the results
    print '=' * 5, 'RESULTS', '(' + config.limitmethod + ')', '=' * 5
    print '\n'.join(limits)
    print '\n'

def fillAsymptoticLimits(config, limfilename, excfilename, interpolate):
    limits = []
    currentDir = os.getcwd()
    xsecfilename = ('../data/xsecs/stop.root')
    xsecfile = TFile(xsecfilename)
    xsechist = TH1D()
    xsechist = xsecfile.Get('xsecs')
    xsecuphist = TH1D()
    xsecuphist = xsecfile.Get('xsecsup')
    xsecdownhist = TH1D()
    xsecdownhist = xsecfile.Get('xsecsdown')
    outfile = TFile(limfilename, 'RECREATE')
    maxmstop = 0.0
    minmstop = 0.0
    maxmlsp = 0.0
    minmlsp = 0.0
    mstop_step = 1
    mlsp_step = 10 if 'fbd' in limfilename else 1
    for signal in config.signals:
        mstop = int(signal.split('_')[1])
        mlsp = int(signal.split('_')[2])
        if mstop > maxmstop: maxmstop = mstop
        if mlsp > maxmlsp: maxmlsp = mlsp
        if minmstop == 0.0 or mstop < minmstop: minmstop = mstop
        if mlsp < minmlsp: minmlsp = mlsp
    nbinsx = int((maxmstop - minmstop) / mstop_step)
    nbinsy = int((maxmlsp - minmlsp) / mlsp_step)
    minmstop -= 0.5*mstop_step
    maxmstop -= 0.5*mstop_step
    print 'XMin: %4.2f, XMax: %4.2f, YMin: %4.2f, YMax: %4.2f, NXBins: %d, NYBins: %d' % (minmstop, maxmstop, minmlsp, maxmlsp, nbinsx, nbinsy)

    hexp = TH2D('hexp', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)
    hexpup = TH2D('hexpup', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)
    hexpdown = TH2D('hexpdown', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)
    hxsecexp = TH2D('hxsecexp', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)
    hxsecobs = TH2D('hxsecobs', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)
    hobs = TH2D('hobs', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)
    hobsup = TH2D('hobsup', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)
    hobsdown = TH2D('hobsdown', '', nbinsx, minmstop, maxmstop, nbinsy, minmlsp, maxmlsp)

    for signal in config.signals:
        outputLocation = os.path.join(currentDir, config.limitdir, signal)
        rootFile = ''
        dummyFiles = os.listdir(outputLocation)
        for df in dummyFiles:
            if 'higgsCombine' in df: rootFile = os.path.join(
                currentDir, config.limitdir, signal, df)
        if rootFile == '':
            limits.append(signal + ': no limit found..')
        else:
            output = getLimit(rootFile, False)
            print signal, ':\n', output
            tempLimit = ''
            for line in output[0].split('\n'):
                if 'Observed' in line:
                    tempLimit = line.replace('Observed\t', signal + ' observed')
                if 'Expected 50' in line:
                    tempLimit += line.replace('Expected\t', signal + ' expected')
            limits.append(tempLimit)
            mstop = int(signal.split('_')[1])
            mlsp = int(signal.split('_')[2])
            limit = output[1]
            xsec = xsechist.Interpolate(mstop)
            xsecup = xsecuphist.Interpolate(mstop)
            xsecdown = xsecdownhist.Interpolate(mstop)
            if config.scalesigtoacc:
                xseclimit = limit['0']
                xsecobslimit = 0.0
                hexp.Fill(mstop, mlsp, limit['0'] / xsec)
                hexpdown.Fill(mstop, mlsp, limit['-1'] / xsec)
                hexpup.Fill(mstop, mlsp, limit['+1'] / xsec)
                if limit.has_key('obs'):
                    xsecobslimit = limit['obs']
                    hobs.Fill(mstop, mlsp, limit['obs'] / xsec)
                    hobsdown.Fill(mstop, mlsp, limit['obs'] / xsecup)
                    hobsup.Fill(mstop, mlsp, limit['obs'] / xsecdown)
                    print 'MStop: %d, MLSP: %d, XS: %4.2f, Exp Limit: %4.2f (+1 expt: %4.2f, -1 expt: %4.2f), Obs Limit: %4.2f (+1 theory: %4.2f, -1 theory: %4.2f), XS Limit: %4.2f exp, %4.2f obs' % (mstop, mlsp, xsec, limit['0'] / xsec, limit['+1'] / xsec, limit['-1'] / xsec, limit['obs'] / xsec, limit['obs'] / xsecdown, limit['obs'] / xsecup, xseclimit, xsecobslimit)
                else:
                    print 'MStop: %d, MLSP: %d, XS: %4.2f, Limit: %4.2f (+1: %4.2f, -1: %4.2f), XS Limit: %4.2f' % (mstop, mlsp, xsec, limit['0'] / xsec, limit['+1'] / xsec, limit['-1'] / xsec, xseclimit)
            else:
                xseclimit = limit['0'] * xsec
                xsecobslimit = 0.0
                hexp.Fill(mstop, mlsp, limit['0'])
                hexpdown.Fill(mstop, mlsp, limit['-1'])
                hexpup.Fill(mstop, mlsp, limit['+1'])
                if limit.has_key('obs'):
                    xsecobslimit = limit['obs'] * xsec
                    hobs.Fill(mstop, mlsp, limit['obs'])
                    hobsdown.Fill(mstop, mlsp, limit['obs'] * xsec / xsecup)
                    hobsup.Fill(mstop, mlsp, limit['obs'] * xsec / xsecdown)
                    # print 'Can\'t fill obs +/- 1 sigma theory if you didn\'t
                    # scale the signals to acceptance!'
                    print 'MStop: %d, MLSP: %d, XS: %4.2f, Exp Limit: %4.2f (+1 expt: %4.2f, -1 expt: %4.2f), Obs Limit: %4.2f (+1 theory: %4.2f, -1 theory: %4.2f), XS Limit: %4.2f exp, %4.2f obs' % (mstop, mlsp, xsec, limit['0'], limit['+1'], limit['-1'], limit['obs'], limit['obs'] * xsec / xsecdown, limit['obs'] * xsec / xsecup, xseclimit, xsecobslimit)
                else:
                    print 'MStop: %d, MLSP: %d, XS: %4.2f, Limit: %4.2f (+1: %4.2f, -1: %4.2f), XS Limit: %4.2f' % (mstop, mlsp, xsec, limit['0'], limit['+1'], limit['-1'], xseclimit)
            hxsecexp.Fill(mstop, mlsp, xseclimit)
            hxsecobs.Fill(mstop, mlsp, xsecobslimit)

    outfile.cd()
    hexp.Write()
    hexpdown.Write()
    hexpup.Write()
    hobs.Write()
    hobsdown.Write()
    hobsup.Write()
    hxsecexp.Write()
    hxsecobs.Write()
    outfile.Close()
    os.system('root -l -q -b makeScanPlots.C\\(\\"%s\\",\\"%s\\",%d,%d\\)' %
              (limfilename, excfilename, config.expectedonly, interpolate))

    # print the results
    print '=' * 5, 'RESULTS', '(' + config.limitmethod + ')', '=' * 5
    print '\n'.join(limits)
    print '\n'


def runMaxLikelihoodFit(config, signal):
    # get all datacards for combining
    currentDir = os.getcwd()
    datacardSaveLocation = os.path.join(currentDir, config.datacarddir, signal)
    datacards = os.listdir(datacardSaveLocation)

    # create and move into a dummy directory (using the timestamp in the name for uniqueness). At the end of
    # each signal loop, all remaining files will be either deleted or moved to
    # the actual output directory.
    dummyRunDir = 'dummy_' + rand_generator()
    os.makedirs(dummyRunDir)
    os.chdir(dummyRunDir)

    combinedDatacard = 'combined_' + signal + '.txt'
    combineDatacardsCommand = 'combineCards.py'
    for datacard in datacards:
        combineDatacardsCommand += ' ' + os.path.join(datacardSaveLocation, datacard)
    combineDatacardsCommand += ' > ' + combinedDatacard
    output = commands.getoutput(combineDatacardsCommand)

    with open(combinedDatacard, 'r') as f :
        contents = f.readlines()

    contents.insert(4,'shapes * * FAKE\n')

    with open(combinedDatacard, 'w') as f :
        f.writelines(contents)

    #lprint(combineDatacardsCommand, output)

    # run the maximum likelihood fit
    runLimitsCommand = 'combine -M MaxLikelihoodFit --saveNormalizations --saveShapes --saveWithUncertainties ' + combinedDatacard
    output = commands.getoutput(runLimitsCommand)
    lprint(runLimitsCommand, output)

    # move any output files to the correct directory
    os.chdir(currentDir)
    dummyFiles = os.listdir(dummyRunDir)
    for f in dummyFiles:
        if 'roostats' in f or 'higgsCombineTest' in f:
            os.remove(os.path.join(dummyRunDir, f))
            continue
        os.rename(os.path.join(dummyRunDir, f), os.path.join(currentDir, f))
    os.removedirs(dummyRunDir)


def calcLimit(config, signal):
    # for each signal, combine the datacards for it, run the
    # chosen limit method, then print the significances for
    # eachpoint at the end.

    # get all datacards for combining
    currentDir = os.getcwd()
    datacardSaveLocation = os.path.join(currentDir, config.datacarddir, signal)
    datacards = os.listdir(datacardSaveLocation)

    # create and move into a dummy directory (using the timestamp in the name for uniqueness). At the end of
    # each signal loop, all remaining files will be either deleted or moved to
    # the actual output directory.
    dummyRunDir = 'dummy_' + rand_generator()
    os.makedirs(dummyRunDir)
    os.chdir(dummyRunDir)

    combinedDatacard = 'combined_' + signal + '.txt'
    combineDatacardsCommand = 'combineCards.py'
    for datacard in datacards:
        combineDatacardsCommand += ' ' + os.path.join(datacardSaveLocation, datacard)
    combineDatacardsCommand += ' > ' + combinedDatacard
    output = commands.getoutput(combineDatacardsCommand)

    #lprint(combineDatacardsCommand, output)

    # ===== run the limits =====
    #
    # ## notes from previous versions:
    # runLimitsCommand =  'combine -M ProfileLikelihood '+combinedDatacard+' --significance -t 500 --expectSignal=1 -n '+limitsOutputFile
    # for now, remove '--pvalue' (between --significance and -t 500)
    # note: the default for -t is -1 (Asimov dataset) see https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit
    #####

    result = {}
    # === Asymptotic
    if config.limitmethod == 'AsymptoticLimits':
        # runLimitsCommand =  'combine -M Asymptotic '+combinedDatacard+' --run
        # expected -t -1 --rMin 0 --rMax 10 -n '+signal
        mstop = int(signal.split('_')[1])
        mlsp = int(signal.split('_')[2])
        sigtype = signal.split('_')[0]
        runLimitsCommand = 'combine -M Asymptotic ' + combinedDatacard + ' -n ' + signal
        if (mstop<450 and 'fbd' not in sigtype) or (mstop >= 350 and mlsp < 350 and 'T2tt' in sigtype) :
            runLimitsCommand = 'combine -M Asymptotic ' + combinedDatacard + ' --rMin 0 --rMax 10 -n ' + signal
        if ('fbd' in sigtype or '4bd' in sigtype) and (mstop<=250):
            runLimitsCommand = 'combine -M Asymptotic ' + combinedDatacard + ' --rMin 0 --rMax 1 -n ' + signal
        if config.expectedonly :
            runLimitsCommand += ' --run expected'
        output = commands.getoutput(runLimitsCommand)
        lprint(runLimitsCommand, output)

        # pull the expected limit out and store
        tempLimit = ''
        tempObsLimit = ''
        for line in output.split('\n'):
            if 'Expected 50' in line:
                tempLimit = line.replace('Expected', signal + ' expected')
            elif 'Observed' in line:
                tempObsLimit = line.replace('Observed', signal + ' obs')
        result = (tempLimit, tempObsLimit, '')

    elif config.limitmethod == 'Asymptotic':
        runLimitsCommand = 'combine -M ProfileLikelihood ' + combinedDatacard + ' --significance -t -1 --toysFreq --expectSignal=1 -n ' + signal
        # runLimitsCommand =  'combine -M ProfileLikelihood '+combinedDatacard+' --significance -t -1 --expectSignal=1 -n '+signal
        # runLimitsCommand =  'combine -M ProfileLikelihood --significance '+combinedDatacard+' -n '+signal
        # run the limit command and figure out what the output root file is
        output = commands.getoutput(runLimitsCommand)
        lprint(runLimitsCommand, output)

        # pull the Significance out and store
        tempSig = ''
        for line in output.split('\n'):
            if 'Significance' in line:
                tempSig = line.replace('Significance', signal)
        result = ('', '', tempSig)

    elif config.limitmethod == 'AsymptoticObs':
        runLimitsCommand = 'combine -M ProfileLikelihood ' + combinedDatacard + ' --uncapped 1 --significance --rMin -5 -n ' + signal
        # run the limit command and figure out what the output root file is
        output = commands.getoutput(runLimitsCommand)
        lprint(runLimitsCommand, output)

        # pull the Significance out and store
        tempSig = ''
        for line in output.split('\n'):
            if 'Significance' in line:
                tempSig = line.replace('Significance', signal)
        result = ('', '', tempSig)

    # === ProfileLikelihood
    elif config.limitmethod == 'ProfileLikelihood':
        runLimitsCommand = 'combine -M ProfileLikelihood ' + combinedDatacard + ' --significance -t 500 --expectSignal=1 -n ' + signal
        # run the limit command and figure out what the output root file is
        output = commands.getoutput(runLimitsCommand)
        lprint(runLimitsCommand, output)

        # get the significance and store
        rootFile = ''
        dummyFiles = os.listdir('./')
        for df in dummyFiles:
            if 'higgsCombine' in df: rootFile = df
        if rootFile == '':
            tempSig = signal + ':'
        else:
            tempSig = signal + ':' + getLimit(rootFile, True)[0]
        result = ('', '', tempSig)

    # === HybridNew method
    elif config.limitmethod == 'HybridNew':
        # run the first limit command and figure out what the output root file is
        runLimitsCommand = 'combine -M HybridNew --frequentist ' + combinedDatacard + ' --significance --saveToys --fullBToys --saveHybridResult -T 500 -i 10 -n ' + signal
        output = commands.getoutput(runLimitsCommand)
        lprint(runLimitsCommand, output)

        # now need to figure out what the root output of the previous file is
        dummyFiles = os.listdir('./')
        outputRootFile = ''
        for f in dummyFiles:
            if 'higgsCombine' in f:
                outputRootFile = f
        # now run the second limit command with the above root file
        runLimitsCommand = 'combine -M HybridNew --frequentist ' + combinedDatacard + \
             ' --significance --readHybridResult --toysFile=' + \
             outputRootFile + ' --expectedFromGrid=0.5 -n ' + signal
        output = commands.getoutput(runLimitsCommand)
        lprint(runLimitsCommand, output)

        # pull the Significance out and store
        tempSig = ''
        for line in output.split('\n'):
            if 'Significance' in line:
                tempSig = line.replace('Significance', signal)
        result = ('', '', tempSig)

    # === non-existant choice of limit method
    else:
        print config.limitmethod, 'is not one of the currently implemented methods! You need to pick one of the allowed ones!'
        sys.exit(1)

    # move any output files to the correct directory
    os.chdir(currentDir)
    dummyFiles = os.listdir(dummyRunDir)
    outputLocation = os.path.join(currentDir, config.limitdir, signal)
    if not os.path.exists(outputLocation): os.makedirs(outputLocation)
    for f in dummyFiles:
        if 'roostats' in f:
            os.remove(os.path.join(dummyRunDir, f))
            continue
        os.rename(os.path.join(dummyRunDir, f), os.path.join(outputLocation, f))
    os.removedirs(dummyRunDir)

    return result


def runLimits(config):
    if not os.path.exists(config.datacarddir):
        print config.datacarddir, 'does not exist!'
        print 'Are you sure you already ran makeDatacards.py?'
        sys.exit(1)

    currentDir = os.getcwd()
    significances = []  # store the Significance from each sig point to print at the end
    observeds = []  # store the Significance from each sig point to print at the end

    # run limits in parallel
    print 'Running limits for %d signal points. Please wait...'%len(config.signals)
    signals = config.signals[:]
    pool = Pool(multiprocessing.cpu_count()-2)
    results = pool.map(functools.partial(calcLimit, config), signals)

    # print the significances
    print '=' * 5, 'RESULTS', '(' + config.limitmethod + ')', '=' * 5
    for rlt in results:
        if config.limitmethod == 'AsymptoticLimits':
            # print exp limit
            print rlt[0]
        else:
            # print significance
            print rlt[-1]
    print '\n'

    for rlt in results:
        if config.limitmethod == 'AsymptoticLimits':
            # print obs limit
            print rlt[1]

    # rearrange significances to be more easily put in a table
    if config.limitmethod == 'Asymptotic' or config.limitmethod == 'AsymptoticObs':
        sigsamps = []
        siglims = []
        for s in results:
            s = s[-1].split()
            sigsamps.append(s[0][:-1])
            siglims.append(s[1])
        print '\t'.join(sigsamps)
        print '\t'.join(siglims)
        print '\n'


if __name__ == '__main__': main()
