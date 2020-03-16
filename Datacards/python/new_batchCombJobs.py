#!/usr/bin/python

import os
import time
import math
import ROOT
from optparse import OptionParser # Command line parsing

from rm_bins import rm_bins

import new_combCardPerChannel as combCard

def main():
   usage = "usage: %prog options"
   version = "%prog."
   parser = OptionParser(usage=usage,version=version)
   parser.add_option("-s", "--signal", action="store", dest="signaldir", type="string", default="", help="set signal card directory for batch processing")
   parser.add_option("-m", "--mu", action="store", dest="ttbarW_mu", type="string", default="comb_mu.txt", help="ttbarW muon channel")
   parser.add_option("-e", "--ele", action="store", dest="ttbarW_ele", type="string", default="comb_ele.txt", help="ttbarW electron channel")
   parser.add_option("-c", "--comb", action="store", dest="ttbarW_comb", type="string", default="comb_comb.txt", help="ttbarW average comb channel")
   parser.add_option("-l", "--lostle", action="store", dest="lostle", type="string", default="lostle.txt", help="set lostle data card name")
   parser.add_option("-t", "--hadtau", action="store", dest="hadtau", type="string", default="hadtau.txt", help="set hadtau data card name")
   parser.add_option("-z", "--zinv", action="store", dest="zinv", type="string", default="zinv.txt", help="set zinv data card name")
   parser.add_option("-q", "--qcd", action="store", dest="qcd", type="string", default="qcd.txt", help="set qcd data card name")
   parser.add_option("-r", "--ttz", action="store", dest="ttz", type="string", default="ttz.txt", help="set ttz data card name")
   parser.add_option("-b", "--rare", action="store", dest="rare", type="string", default="rare.txt", help="set rare data card name")
   parser.add_option("-d", "--data", action="store", dest="data", type="string", default="data.txt", help="set data data card name")
   parser.add_option("-o", "--outputdir", action="store", dest="outputdir", type="string", default="", help="set combined card output directory")
   parser.add_option("-n", "--runlimit", action="store", dest="runlimit", type="string", default="yes", help="set run limit or not")
#   parser.add_option("-m", "--model", action="store", dest="model", type="string", default="T2tt", help="set SMS model type")
   parser.add_option("--model", action="store", dest="model", type="string", default="T2tt", help="set SMS model type")

   (options, args) = parser.parse_args()

   print 'ttbarW_comb :', options.ttbarW_comb
   print 'ttbarW_mu :', options.ttbarW_mu
   print 'ttbarW_ele :', options.ttbarW_ele
   print 'zinv :', options.zinv
   print 'qcd :', options.qcd
   print 'ttz :', options.ttz
   print 'rare :', options.rare
   print 'data :', options.data
   print 'signaldir : ', options.signaldir
   print 'runlimit : ', options.runlimit

   if len(options.outputdir) !=0:
      if not os.path.exists(options.outputdir): os.mkdir(options.outputdir)
   else:
      print "output directory cannot be empty!"
      return

   tarfilename = options.outputdir + ".tgz"

   submitLine = """universe = vanilla
Executable = """ + os.getcwd() + """/goScan.sh
Requirements = OpSys == "LINUX"&& (Arch != "DUMMY" )
Should_Transfer_Files = YES
WhenToTransferOutput = ON_EXIT
Transfer_Input_Files = """ + os.getcwd() + """/""" + tarfilename + """
Output = logs/basicCheck_$(Process).stdout
Error = logs/basicCheck_$(Process).stderr
Log = logs/basicCheck_$(Process).log
notify_user = ${LOGNAME}@FNAL.GOV
request_memory = 8000
"""
   fileParts = [submitLine]

   signal_key_list = []

# Batch making the cards for individual channels and a combined one for the combination tool
   for signal_name in os.listdir(options.signaldir):
      if not ("signal" in signal_name): continue
      if not (".txt" in signal_name): continue
      if signal_name.startswith('.'): continue

      splitsignalinput = signal_name.split("/")
      stripDirSignalInput = splitsignalinput[-1]

      if "signal_" in stripDirSignalInput: tmp_signal_key = stripDirSignalInput.replace("signal_", "")
      elif "signal" in stripDirSignalInput: tmp_signal_key = stripDirSignalInput.replace("signal", "")
      tmp_signal_key = tmp_signal_key.replace(".txt", "")

      signal_key_list.append(tmp_signal_key)

      tmp_signal_name = signal_name
      full_signal_name = os.path.join(options.signaldir, signal_name)

      outputdir = options.outputdir + "/" + tmp_signal_name.replace(".txt", "")

      if options.runlimit == "yes":
         if len(outputdir) !=0:
            if not os.path.exists(outputdir): os.mkdir(outputdir)

         print "processing the signal file : %s in output dir : %s" % (signal_name, outputdir)

# Core function to produce the cards
         combCard.prodCardPerChn(tmp_signal_key, outputdir, options.ttbarW_comb, options.ttbarW_mu, options.ttbarW_ele, options.zinv, options.qcd, options.ttz, options.rare, options.data, full_signal_name)

# Making a combined card
         rm_comb_cards_command = "rm "
         make_allComb_command = "combineCards.py "
         for card_name in os.listdir(outputdir):
            if not ("comb" in card_name): continue
            rm_comb_cards_command += (outputdir + "/" + card_name + " ")
	    bin_number = int(card_name.split('_ch')[1].replace('.txt','')) - 1
	    #if (bin_number in rm_bins): continue
            make_allComb_command += (outputdir + "/" + card_name + " ")
         make_allComb_command += (" > " + outputdir + "/allComb_"+tmp_signal_name)
         os.system(make_allComb_command)
         os.system(rm_comb_cards_command)

      allComb_file_dir = outputdir + "/" + "allComb_" + tmp_signal_name
      allComb_run_output_filename = "log_allComb_" + tmp_signal_name + ".lg"
      fileParts.append("Arguments = %s $ENV(CMSSW_BASE) %s\nQueue\n\n"%(allComb_file_dir, allComb_run_output_filename))

# Preparing tarred cards, executable and condor configuration files for limit jobs
   if options.runlimit == "yes":
      os.system("tar -czvf "+tarfilename+" "+options.outputdir + "/*/allComb_*.txt")
      os.system("rm -fr "+options.outputdir)

   exeLine = """#!/bin/bash
export PATH=${PATH}:/cvmfs/cms.cern.ch/common
export CMS_PATH=/cvmfs/cms.cern.ch
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc6_amd64_gcc530
export CMSSW_Version=`echo $2 | awk -F / '{for (i=1;i<=NF;i++) if ($i ~ /^CMSSW_.*$/) print $i}'`
#cmsrel $CMSSW_Version
scramv1 project CMSSW $CMSSW_Version
cd ${CMSSW_Version}/src
eval `scramv1 runtime -sh`
git clone --branch 81x-root606 https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v7.0.9
scramv1 b clean
scramv1 b
eval `scramv1 runtime -sh`
cd ${_CONDOR_SCRATCH_DIR}
tar -zxvf """ + tarfilename + """
ulimit -s unlimited
combine -M Asymptotic $1 > $3
"""
   exeFile = open("goScan.sh", "w")
   exeFile.write(exeLine)
   exeFile.close()

   condorFile = open("condor_submit.txt", "w")
   condorFile.write(''.join(fileParts))
   condorFile.close()

# Submit the jobs
   if not os.path.exists("logs"): os.mkdir("logs")
   if options.runlimit == "yes":
      os.system("echo 'condor_submit condor_submit.txt'")
      os.system('condor_submit condor_submit.txt')

# Checking if the jobs are done
   while True:
      condor_check_command = "condor_q -submitter " + os.environ["USER"] + " -wide > tmp_condor_check_output.txt"
      os.system(condor_check_command)
      tmp_condor_file = open("tmp_condor_check_output.txt")
      cnt_runjobs =0
      for condor_line in tmp_condor_file:
         if "goScan.sh" in condor_line and "allComb" in condor_line : cnt_runjobs += 1
      print "current jobs in queue: %d" % (cnt_runjobs)
      if cnt_runjobs ==0: break;
      time.sleep(60)

# Removing intermediate files
   os.system("rm tmp_condor_check_output.txt")
   os.system("rm higgsCombineTest.Asymptotic.mH120.root")
   os.system("rm roostats*.root")

# Parsing the output files to make new files with correct format for drawing steps
   cards_for_plotting_dir_name = "cards_for_plotting"
   if not os.path.exists(cards_for_plotting_dir_name): os.mkdir(cards_for_plotting_dir_name)

   print "\nsignal_key_list : ", signal_key_list
   filelist_for_plotting = open(cards_for_plotting_dir_name+"/filelist.txt", "w")

   xSec_root_file = ROOT.TFile("xSec.root")
   if "T2tt" in options.model or "T2bb" in options.model or "T2tb" in options.model or "T6tt" in options.model:
      h1_xSec = xSec_root_file.Get("stop_xsection")
   elif "T1tt" in options.model or "T5tt" in options.model:
      h1_xSec = xSec_root_file.Get("gluino_xsection")

   for log_file_name in os.listdir(os.getcwd()):
      if not ("log_allComb" in log_file_name) and not (".lg" in log_file_name) : continue
      picked_key_name = ''
      for key_name in signal_key_list:
         more_key_name = "signal_"+key_name+".txt"
         if more_key_name in log_file_name:
            picked_key_name = key_name
            break

      if len(picked_key_name) ==0: continue

      split_key = picked_key_name.split("_")
      momMass = split_key[0]
      dauMass = split_key[1]

      binIdx = h1_xSec.FindBin(float(momMass))
      xSec = h1_xSec.GetBinContent(binIdx)

      log_file = open(log_file_name)
      for log_line in log_file:
         log_line_split = log_line.split()
         if "Observed Limit:" in log_line: obsLimit = float(log_line_split[-1])*xSec
         if "Expected 16.0%:" in log_line: expLimit_m1sigma = float(log_line_split[-1])*xSec
         if "Expected 50.0%:" in log_line: expLimit = float(log_line_split[-1])*xSec
         if "Expected 84.0%:" in log_line: expLimit_p1sigma = float(log_line_split[-1])*xSec

      format_file_name = "mSUGRA_" + picked_key_name + "_10_0_1.dat"
      format_file = open(cards_for_plotting_dir_name+"/"+format_file_name, "w")

      formatLine = """Azero = 0
Mu = 1
Mzero = """ + momMass + """
Mhalf = """ + dauMass + """
Xsection = """ + str(xSec) + """
limit.cls.observed = """ + str(obsLimit) + """
limit.cls.observed.error = 0
limit.cls.expected.m1sigma = """ + str(expLimit_m1sigma) + """
limit.cls.expected = """ + str(expLimit) + """
limit.cls.expected.p1sigma = """ + str(expLimit_p1sigma) + """
limit.cls.expected.1sigmaCoverage = -1
limit.cls.expected.2sigmaCoverage = -1
limit.cls.expected.m2sigma = -1
limit.cls.expected.p2sigma = -1
"""

      format_file.write(formatLine)
      format_file.close()

      filelist_for_plotting.write(format_file_name + "\n")

   filelist_for_plotting.close()

if __name__ == "__main__":
   main()
