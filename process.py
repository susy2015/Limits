#!/usr/bin/env python
import os
import sys
import argparse

parser = argparse.ArgumentParser(description='Process config file')
parser.add_argument("-c", "--conf", dest="conf", default="dc_LL_test_setup.conf", help="Input configuration file. [Default: dc_LL_test_setup.conf]")
parser.add_argument("-s", "--submit", dest="submit", default="submitall", help="Name of shell script to run for job submission. [Default: submitall]")
parser.add_argument("-p", "--pathtomacro", dest="path", default="..", help="Path to directory with run macro and configuration file. [Default: \"../\"]")
parser.add_argument("-m", "--runmacro", dest="macro", default="runLimits.py", help="Python macro to run. [Default: runLimits.py]")
parser.add_argument("-n", "--sysname", dest="sysname", default="limits", help="type of uncertainty calc")
parser.add_argument("-o", "--outdir", dest="outdir", default="${PWD}/plots", help="Output directory for plots, [Default: \"${PWD}/plots\"]")
parser.add_argument("-r", "--runscript", dest="script", default="runjobs", help="Shell script to be run by the jobs, [Default: runjobs]")
parser.add_argument("-t", "--submittype", dest="submittype", default="condor", choices=["interactive","lsf","condor"], help="Method of job submission. [Options: interactive, lsf, condor. Default: condor]")
parser.add_argument("-q", "--queue", dest="queue", default="1nh", help="LSF submission queue. [Default: 1nh]")
parser.add_argument("--jobdir", dest="jobdir", default="jobs", help="Job dir. [Default: %(default)s]")
#parser.print_help()
args = parser.parse_args()

types = []
state = 0
snum = 0

os.system("mkdir -p %s" % args.jobdir)

print "Creating submission file: ",args.submit+".sh"
script = open(args.submit+".sh","w")
script.write("""#!/bin/bash
outputdir={outdir}
runmacro={macro}
sysname={sysname}
config={conf}
""".format(outdir=args.outdir, pathtomacro=args.path, macro=args.macro, sysname=args.sysname, conf=args.conf))

if args.submittype == "lsf" or args.submittype == "condor" :
    script.write("""
workdir=$CMSSW_BASE
scram=$SCRAM_ARCH
runscript={runscript}{stype}.sh

if [ ! "$CMSSW_BASE" ]; then
  echo "-------> error: define cms environment."
  exit 1
fi

cp $config $workdir
cp {pathtomacro}$runmacro $workdir
""".format(pathtomacro=args.path,runscript=args.script,stype=args.submittype))
    script.write("""
    
source tarCMSSW.sh

echo "$runscript $runmacro $workdir $outputdir $config"    
""")

if args.submittype == "interactive" :
    script.write("""python {pathtomacro}$runmacro $config\n""".format(
    pathtomacro=args.path, 
    ))
elif args.submittype == "condor" :
    os.system("mkdir -p %s/logs" % args.outdir)
    jobscript = open(os.path.join(args.jobdir,"submit_{}.sh".format(args.sysname)),"w")
    outputname = ''
    jobscript.write("""
cat > submit.cmd << EOF
universe                = vanilla
Executable              = {runscript}{stype}.sh
Arguments               = {macro} {config} {pathtomacro} . {workdir} {outdir} {scram}
Output                  = logs/{sysname}.out
Error                   = logs/{sysname}.err
Log                     = logs/{sysname}.log
x509userproxy           = 
request_memory 		= 6000
initialdir              = {outdir}
Should_Transfer_Files   = YES
transfer_input_files    = 
transfer_output_files   = {outname}
WhenToTransferOutput    = ON_EXIT
Queue
EOF

  condor_submit submit.cmd;
  rm submit.cmd""".format(
    runscript=args.script, stype=args.submittype, macro=args.macro, config=args.conf, pathtomacro=args.path, sysname=args.sysname, workdir="${CMSSW_BASE}", outdir=args.outdir, outname=outputname, scram="${SCRAM_ARCH}"
    ))
    jobscript.close()
    script.write("./{jobdir}/submit_{name}.sh\n".format(jobdir=args.jobdir, name=args.sysname))
    os.system("chmod +x %s/submit_%s.sh" %(args.jobdir, args.sysname))

script.close()
os.system("chmod +x %s.sh" % args.submit)
#transfer_input_files    = {workdir}/{macro} {workdir}/{config}

print "Done!"
