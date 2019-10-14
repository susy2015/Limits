#! /usr/bin/python
#
## Note on running:
## 
## In order to run this, you need to set up CMSSW_7_1_5 as follows
## (for more info see: https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit#How_to_prepare_the_datacard)
#
# export SCRAM_ARCH=slc6_amd64_gcc481 # for csh use: setenv SCRAM_ARCH slc6_amd64_gcc481
# cmsrel CMSSW_7_1_5                  # must be a 7_1_X release >= 7_1_5;  (7.0.X and 7.2.X are NOT supported either) 
# cd CMSSW_7_1_5/src
# cmsenv
# git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
#
## Updating to a tag (both the first time and whenever there are updates):
#
# cd HiggsAnalysis/CombinedLimit
# git fetch origin
# git checkout v5.0.1
# scramv1 b clean; scramv1 b # always make a clean build, as scram doesn't always see updates to src/LinkDef.h
# 

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
from ROOT import gROOT,TFile,TTree,TH1D,TH2D,TChain,TGraph2D
gROOT.SetBatch(True)

def main():
  parser = argparse.ArgumentParser(description='Produce or print limits based on existing datacards')
  parser.add_argument("-p", "--print", dest="printLimits", action='store_true', help="Print last set of limits/significances calculated. [Default: False]")
  parser.add_argument("-f", "--fill", dest="fillAsymptoticLimits", action='store_true', help="Fill root files with results of asymptotic limit calculations for all signal points. [Default: False]")
  parser.add_argument("-c", "--config", dest="configFile", default='dc_0l_setup.conf', help="Config file to be run with. [Default: dc_0l_setup.conf]")
  args = parser.parse_args()

  # to get the config file
  if os.path.exists(args.configFile):
    print 'running with config file', args.configFile
  else:
    print 'you are trying to use a config file ('+args.configFile+') that does not exist!'
    sys.exit(1)

  configparser = SafeConfigParser()
  configparser.optionxform = str
  
  limconfig = LimitConfig(args.configFile,configparser)

  if args.printLimits :
      limconfig.printLimits()
  elif args.fillAsymptoticLimits :
      if limconfig.limitmethod == 'Asymptotic' :
          print 'here'
          limconfig.fillSignificances()
      else :
          limconfig.fillAsymptoticLimits()
  else :
      limconfig.runLimits()
  
class LimitConfig:
  # setup
  def __init__(self,conf_file,config_parser):
    self.conf_file      = conf_file
    config_parser.read(self.conf_file)
    self.limitmethod    = config_parser.get('config','limitmethod')
    self.subdir         = config_parser.get('config','subdir')
    self.datacarddir    = os.path.join( config_parser.get('config','datacarddir'), self.subdir                      )
    self.limitdir       = os.path.join( config_parser.get('config','limitdir'   ), self.subdir+'_'+self.limitmethod )
    self.signals        = config_parser.get('signals','samples').replace(' ','').split(',') 
    self.scalesigtoacc  = config_parser.getboolean('config','scalesigtoacc')
  
  
  def getLimit(self,rootFile,getMean=False,limit={}):
    file = TFile(rootFile)
    output = ''
    if getMean :
      tree = file.Get('limit')
      htmp = TH1D('htmp','htmp',1,0,10000)
      tree.Project('htmp','limit')
      mean = htmp.GetMean()
      #error = htmp.GetError()
      #output = 'mean=' + str(mean) + '\terror=' + str(error) + '\n'
      output = 'mean=' + str(mean) + '\n'
      limit = mean
    else :
      tree = TChain('limit')
      tree.Add(rootFile)
      for entry in tree :
        if entry.quantileExpected < 0 :
            output += 'Observed : r < %4.2f \n' % (entry.limit)
        else :
            output += 'Expected %4.2f %% : r < %4.2f \n' % ((100.0*entry.quantileExpected) , entry.limit)
        if entry.quantileExpected < 0 :
          limit['obs'] = entry.limit
        if 0.1 < entry.quantileExpected < 0.2 :
          limit['-1'] = entry.limit
        elif 0.4 < entry.quantileExpected < 0.6 :
          limit['0'] = entry.limit
        elif 0.8 < entry.quantileExpected < 0.9 :
          limit['+1'] = entry.limit
    return (output,limit)

  def printLimits(self):
    limits = []
    currentDir = os.getcwd()
    for signal in self.signals :
      outputLocation = os.path.join(currentDir,self.limitdir,signal)
      rootFile = ''
      dummyFiles = os.listdir(outputLocation)
      for df in dummyFiles:
        if 'higgsCombine' in df: rootFile = os.path.join(currentDir,self.limitdir,signal,df)
      if rootFile=='':
        limits.append(signal+': no limit found..')
      else:
        output = self.getLimit(rootFile,False) if self.limitmethod == 'AsymptoticLimits' else self.getLimit(rootFile,True)
        #print signal, ':\n', output
        tempLimit = ''
        if self.limitmethod == 'AsymptoticLimits' :
            for line in output[0].split('\n'): 
                if 'Expected 50' in line: 
                    tempLimit = line.replace('Expected',signal+' expected') 
        else :
            for line in output[0].split('\n'): 
                if 'mean' in line: 
                    tempLimit = line.replace('mean=',signal+': ') 
        limits.append( tempLimit )

    # print the results
    print '='*5, 'RESULTS', '('+self.limitmethod+')', '='*5
    print '\n'.join(limits)
    print '\n'

  def fillSignificances(self):
    limits = []
    currentDir = os.getcwd()
    outfile = TFile('significances_T2tt.root','RECREATE')
    maxmstop = 0.0
    minmstop = 0.0
    maxmlsp  = 0.0
    minmlsp  = 0.0
    for signal in self.signals :
      mstop = int(signal.split('_')[1])
      mlsp = int(signal.split('_')[2])
      if mstop > maxmstop : maxmstop = mstop
      if mstop > maxmstop : maxmstop = mstop
      if minmlsp == 0.0 or mlsp < minmlsp : minmlsp = mlsp
      if minmlsp == 0.0 or mlsp < minmlsp : minmlsp = mlsp
    nbinsx = int((maxmstop - minmstop)/12.5)
    nbinsy = int((maxmlsp - minmlsp)/12.5)

    hsig = TH2D('hsig','',36,100,1000,20,0,500)
    for signal in self.signals :
      outputLocation = os.path.join(currentDir,self.limitdir,signal)
      rootFile = ''
      dummyFiles = os.listdir(outputLocation)
      for df in dummyFiles:
        if 'higgsCombine' in df: rootFile = os.path.join(currentDir,self.limitdir,signal,df)
      if rootFile=='':
        limits.append(signal+': no limit found..')
      else:
        output = self.getLimit(rootFile,True)
        print signal, ':\n', output
        tempLimit = ''
        for line in output[0].split('\n'): 
            if 'mean' in line: 
                tempLimit = line.replace('mean=',signal+': ') 
        limits.append( tempLimit )
        mstop = int(signal.split('_')[1])
        mlsp = int(signal.split('_')[2])
        limit = output[1]
        hsig.Fill(mstop,mlsp,limit)

    outfile.cd()
    hsig.Write()
    outfile.Close()
    os.system('root -l -q -b makeSigScanPlots.C')
       
    # print the results
    print '='*5, 'RESULTS', '('+self.limitmethod+')', '='*5
    print '\n'.join(limits)
    print '\n'

  def fillAsymptoticLimits(self):
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
    outfile = TFile('results_T2tt.root','RECREATE')
    maxmstop = 0.0
    minmstop = 0.0
    maxmlsp  = 0.0
    minmlsp  = 0.0
    for signal in self.signals :
      mstop = int(signal.split('_')[1])
      mlsp = int(signal.split('_')[2])
      if mstop > maxmstop : maxmstop = mstop
      if mstop > maxmstop : maxmstop = mstop
      if minmlsp == 0.0 or mlsp < minmlsp : minmlsp = mlsp
      if minmlsp == 0.0 or mlsp < minmlsp : minmlsp = mlsp
    nbinsx = int((maxmstop - minmstop)/12.5)
    nbinsy = int((maxmlsp - minmlsp)/12.5)

    hexp = TH2D('hexp','',36,100,1000,20,0,500)
    hexpup = TH2D('hexpup','',36,100,1000,20,0,500)
    hexpdown = TH2D('hexpdown','',36,100,1000,20,0,500)
    hxsecexp = TH2D('hxsecexp','',36,100,1000,20,0,500)
    hobs = TH2D('hobs','',36,100,1000,20,0,500)
    hobsup = TH2D('hobsup','',36,100,1000,20,0,500)
    hobsdown = TH2D('hobsdown','',36,100,1000,20,0,500)
    for signal in self.signals :
      outputLocation = os.path.join(currentDir,self.limitdir,signal)
      rootFile = ''
      dummyFiles = os.listdir(outputLocation)
      for df in dummyFiles:
        if 'higgsCombine' in df: rootFile = os.path.join(currentDir,self.limitdir,signal,df)
      if rootFile=='':
        limits.append(signal+': no limit found..')
      else:
        output = self.getLimit(rootFile,False)
        print signal, ':\n', output
        tempLimit = ''
        for line in output[0].split('\n'): 
          if 'Observed' in line: 
            tempLimit = line.replace('Observed\t',signal+' observed') 
          if 'Expected 50' in line: 
            tempLimit += line.replace('Expected\t',signal+' expected') 
        limits.append( tempLimit )
        mstop = int(signal.split('_')[1])
        mlsp = int(signal.split('_')[2])
        limit = output[1]
        xsec = xsechist.Interpolate(mstop)
        xsecup = xsecuphist.Interpolate(mstop)
        xsecdown = xsecdownhist.Interpolate(mstop)
        if self.scalesigtoacc :
            xseclimit = limit['0']
            hexp.Fill(mstop,mlsp,limit['0']/xsec)
            hexpdown.Fill(mstop,mlsp,limit['-1']/xsec)
            hexpup.Fill(mstop,mlsp,limit['+1']/xsec)
            if limit.has_key('obs') :
                hobs.Fill(mstop,mlsp,limit['obs']/xsec)
                hobsdown.Fill(mstop,mlsp,limit['obs']/xsecup)
                hobsup.Fill(mstop,mlsp,limit['obs']/xsecdown)
                print 'MStop: %d, MLSP: %d, XS: %4.2f, Exp Limit: %4.2f (+1 expt: %4.2f, -1 expt: %4.2f), Obs Limit: %4.2f (+1 theory: %4.2f, -1 theory: %4.2f), XS Limit: %4.2f' % (mstop,mlsp,xsec,limit['0']/xsec,limit['+1']/xsec,limit['-1']/xsec,limit['obs']/xsec,limit['obs']/xsecdown,limit['obs']/xsecup,xseclimit)
            else :
                print 'MStop: %d, MLSP: %d, XS: %4.2f, Limit: %4.2f (+1: %4.2f, -1: %4.2f), XS Limit: %4.2f' % (mstop,mlsp,xsec,limit['0']/xsec,limit['+1']/xsec,limit['-1']/xsec,xseclimit)
        else :
            xseclimit = limit['0']*xsec
            hexp.Fill(mstop,mlsp,limit['0'])
            hexpdown.Fill(mstop,mlsp,limit['-1'])
            hexpup.Fill(mstop,mlsp,limit['+1'])
            if limit.has_key('obs') :
                hobs.Fill(mstop,mlsp,limit['obs'])
                print 'Can\'t fill obs +/- 1 sigma theory if you didn\'t scale the signals to acceptance!'
                print 'MStop: %d, MLSP: %d, XS: %4.2f, Exp Limit: %4.2f (+1: %4.2f, -1: %4.2f), Obs Limit: %4.2f, XS Limit: %4.2f' % (mstop,mlsp,xsec,limit['0'],limit['+1'],limit['-1'],limit['obs'],xseclimit)
            else :
                print 'MStop: %d, MLSP: %d, XS: %4.2f, Limit: %4.2f (+1: %4.2f, -1: %4.2f), XS Limit: %4.2f' % (mstop,mlsp,xsec,limit['0'],limit['+1'],limit['-1'],xseclimit)
        hxsecexp.Fill(mstop,mlsp,xseclimit)

    outfile.cd()
    hexp.Write()
    hexpdown.Write()
    hexpup.Write()
    hobs.Write()
    hobsdown.Write()
    hobsup.Write()
    hxsecexp.Write()
    outfile.Close()
    os.system('root -l -q -b makeScanPlots.C')
       
    # print the results
    print '='*5, 'RESULTS', '('+self.limitmethod+')', '='*5
    print '\n'.join(limits)
    print '\n'

  # for each signal, combine the datacards for it, run the
  # chosen limit method, then print the significances for
  # eachpoint at the end. 
  def runLimits(self):
    if not os.path.exists(self.datacarddir):
      print self.datacarddir, 'does not exist!' 
      print 'Are you sure you already ran makeDatacards.py?'
      sys.exit(1)
    
    currentDir = os.getcwd()
    significances = [] # store the Significance from each sig point to print at the end
    observeds = [] # store the Significance from each sig point to print at the end
    
    for signal in self.signals: 
      # create and move into a dummy directory (using the timestamp in the name for uniqueness). At the end of 
      # each signal loop, all remaining files will be either deleted or moved to the actual output directory. 
      dummyRunDir = 'dummy_' + str(int(time.time()*1e8))
      print 'creating a dummy directory to run in:', dummyRunDir 
      os.makedirs(dummyRunDir)
      os.chdir(dummyRunDir)
        
      datacardSaveLocation = os.path.join(currentDir,self.datacarddir,signal)
      datacards = os.listdir(datacardSaveLocation)
      combinedDatacard = 'combined_'+signal+'.txt'
      
      #combineDatacardsCommand = 'combineCards.py'
      #for datacard in datacards:
      #  combineDatacardsCommand += ' ' + os.path.join(datacardSaveLocation,datacard)
      #combineDatacardsCommand += ' > ' + combinedDatacard
      
      #print 'now running:' #DEBUGGING ONLY
      #print combineDatacardsCommand, '\n' #DEBUGGING ONLY
      #output = commands.getoutput(combineDatacardsCommand)
      #print output # probably keep this in case of datacard syntax problems

      sigSignificances = []
      sigObserveds = []

      # ===== run the limits ===== 
      #
      ### notes from previous versions:
      # runLimitsCommand =  'combine -M ProfileLikelihood '+combinedDatacard+' --significance -t 500 --expectSignal=1 -n '+limitsOutputFile
      # for now, remove '--pvalue' (between --significance and -t 500)
      # note: the default for -t is -1 (Asimov dataset) see https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit
      #####
      
      # === Asymptotic
      if self.limitmethod=='AsymptoticLimits':
        for datacard in datacards:
          if 'onelepcr' in datacard : continue

          crcard = datacard.replace('_met','_onelepcr_met').replace('nbjets2','nbjets1')
          if 'ncttstd1' in crcard:
            crcard = crcard.split('_')
            crcard[4] = 'met250'
            crcard = '_'.join(crcard)
          combineDatacardsCommand = 'combineCards.py'
          combineDatacardsCommand += ' ' + os.path.join(datacardSaveLocation,datacard) + ' ' + os.path.join(datacardSaveLocation,crcard)
          combineDatacardsCommand += ' > ' + combinedDatacard

          print 'now running:' #DEBUGGING ONLY
          print combineDatacardsCommand, '\n' #DEBUGGING ONLY
          output = commands.getoutput(combineDatacardsCommand)
          print output # probably keep this in case of datacard syntax problems

          #runLimitsCommand =  'combine -M Asymptotic '+combinedDatacard+' --run expected -t -1 --rMin 0 --rMax 10 -n '+signal
          mstop = int(signal.split('_')[1])
          runLimitsCommand =  'combine -M Asymptotic '+combinedDatacard+' --rMin 0 --rMax 10 -n '+datacard.replace('.txt','')
          if mstop < 400 :
              #runLimitsCommand =  'combine -M Asymptotic '+combinedDatacard+' -n '+signal
              runLimitsCommand =  'combine -M Asymptotic '+combinedDatacard+' -n '+datacard.replace('.txt','')
          # run the limit command and figure out what the output root file is
          print 'now running:' #DEUBGGING ONLY
          print runLimitsCommand, '\n' # keep this in some kind of log file?
          output = commands.getoutput(runLimitsCommand)
          print output # maybe redirect this to some kind of log file?

          # pull the expected limit out and store
          tempLimit = ''
          tempObsLimit = ''
          for line in output.split('\n'):
            if 'Expected 50' in line:
              tempLimit = (float(line.split()[-1]), datacard.replace('.txt',''))
            elif 'Observed' in line:
              tempObsLimit = (float(line.split()[-1]), datacard.replace('.txt',''))
          if tempLimit=='':
            sigSignificances.append((9999999.0, datacard.replace('.txt','')))
          else:
            sigSignificances.append(tempLimit)
            sigObserveds.append(tempObsLimit)

      elif self.limitmethod=='Asymptotic':
        #runLimitsCommand =  'combine -M ProfileLikelihood '+combinedDatacard+' --significance -t -1 --toysFreq --expectSignal=1 -n '+signal
        #runLimitsCommand =  'combine -M ProfileLikelihood '+combinedDatacard+' --significance -t -1 --expectSignal=1 -n '+signal
        runLimitsCommand =  'combine -M ProfileLikelihood --significance '+combinedDatacard+' -n '+signal
        # run the limit command and figure out what the output root file is
        print 'now running:' #DEUBGGING ONLY 
        print runLimitsCommand, '\n' # keep this in some kind of log file?
        output = commands.getoutput(runLimitsCommand)
        print output # maybe redirect this to some kind of log file?
        
        # pull the Significance out and store
        tempSig = ''
        for line in output.split('\n'): 
          if 'Significance' in line: 
            tempSig = line.replace('Significance',signal) 
        if tempSig=='': 
          significances.append(signal+': no significance found..')
        else:
          significances.append(tempSig)  
      
      # === ProfileLikelihood
      elif self.limitmethod=='ProfileLikelihood':
        runLimitsCommand =  'combine -M ProfileLikelihood '+combinedDatacard+' --significance -t 500 --expectSignal=1 -n '+signal
        # run the limit command and figure out what the output root file is
        print 'now running:' #DEUBGGING ONLY 
        print runLimitsCommand, '\n' # keep this in some kind of log file?
        output = commands.getoutput(runLimitsCommand)
        print output # maybe redirect this to some kind of log file?
        
        # get the significance and store
        rootFile = ''
        dummyFiles = os.listdir('./')
        for df in dummyFiles:
          if 'higgsCombine' in df: rootFile = df
        if rootFile=='':
          significances.append(signal+': no significance found..')
        else:
          significances.append( signal + ': ' + self.getLimit(rootFile,True)[0] )
      
      # === HybridNew method
      elif self.limitmethod=='HybridNew':
        # run the first limit command and figure out what the output root file is
        runLimitsCommand =  'combine -M HybridNew --frequentist '+combinedDatacard+' --significance --saveToys --fullBToys --saveHybridResult -T 500 -i 10 -n '+signal
        print 'now running:' #DEUBGGING ONLY 
        print runLimitsCommand, '\n' # keep this in some kind of log file?
        output = commands.getoutput(runLimitsCommand)
        print output # maybe redirect this to some kind of log file?
        # now need to figure out what the root output of the previous file is
        dummyFiles = os.listdir('./')
        outputRootFile = ''
        for f in dummyFiles:
          if 'higgsCombine' in f:
            outputRootFile = f
        # now run the second limit command with the above root file 
        runLimitsCommand =  'combine -M HybridNew --frequentist '+combinedDatacard+' --significance --readHybridResult --toysFile='+outputRootFile+' --expectedFromGrid=0.5 -n '+signal
        print 'now running:' #DEUBGGING ONLY 
        print runLimitsCommand, '\n' # keep this in some kind of log file?
        output = commands.getoutput(runLimitsCommand)
        print output # maybe also redirect this to some kind of log file?
        
        # pull the Significance out and store
        tempSig = ''
        for line in output.split('\n'): 
          if 'Significance' in line: 
            tempSig = line.replace('Significance',signal) 
        if tempSig=='': 
          significances.append(signal+': no significance found..')
        else:
          significances.append(tempSig)  
      
      # === non-existant choice of limit method
      else:
        print self.limitmethod, 'is not one of the currently implemented methods! You need to pick one of the allowed ones!'
        sys.exit(1)

      # sort by append significances for current signal point to full list of lists
      sigSignificances = sorted( sigSignificances, reverse=False, key=lambda s: s[0])
      sigObserveds     = sorted( sigObserveds    , reverse=False, key=lambda s: s[0])
      significances.append(sigSignificances)
      observeds.append(sigObserveds)
        
      # move any output files to the correct directory
      os.chdir(currentDir)
      dummyFiles = os.listdir(dummyRunDir)
      outputLocation = os.path.join(currentDir,self.limitdir,signal)
      if not os.path.exists(outputLocation): os.makedirs(outputLocation)
      print '\n'
      print 'moving files to:', outputLocation
      for f in dummyFiles:
        print ' '*3, f
        if 'roostats' in f:
          os.remove(os.path.join(dummyRunDir,f))
          continue
        os.rename(os.path.join(dummyRunDir,f),os.path.join(outputLocation,f)) 
      os.removedirs(dummyRunDir)
      print '\n', '='*60, '\n'
    
    # print the significances
    #print '='*5, 'RESULTS', '('+self.limitmethod+')', '='*5
    #print '\n'.join(significances)
    #print '\n'
    #print '\n'.join(observeds)
    #print '\n'

    print '='*5, 'SIGNIFICANCES', '('+self.limitmethod+')', '='*5
    for pointSigs in significances:
      print '\n'
      for bin in pointSigs:
        print str(round(bin[0],2)) + ' \t' + bin[1]
      print '\n'

    print '='*5, 'OBSERVATIONS', '('+self.limitmethod+')', '='*5
    for pointObs in observeds:
      print '\n'
      for bin in pointObs:
        print str(round(bin[0],2)) + ' \t' + bin[1]
      print '\n'


    # rearrange significances to be more eaisly put in a table
    if self.limitmethod=='Asymptotic':
      sigsamps = []
      siglims  = []
      for s in significances:
        s = s.split()
        sigsamps.append(s[0][:-1])
        siglims.append(s[1])
      print '\t'.join(sigsamps)
      print '\t'.join(siglims)
      print '\n'
      

if __name__=='__main__': main()
