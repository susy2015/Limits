#!/bin/bash

runmacro=$1
config=$2
pathtomacro=$3
outputdir=$4
scramdir=$5
outdir=${6}
scram=${7}

workdir=`pwd`
cmssw=${scramdir##*/}

echo $(whoami)
echo `hostname`
echo "${_CONDOR_SCRATCH_DIR}"
echo "scramdir: $scramdir"
echo "workdir: $workdir"
echo "args: $*"
echo $cmssw
echo $scram
ls -l

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=$scram
eval `scramv1 project CMSSW $cmssw`
cd ${cmssw}/src/
eval `scramv1 runtime -sh`
scramv1 b ProjectRename
echo "CMSSW: "$CMSSW_BASE
cd ../../
CMSSW=${CMSSW_BASE##*/}

xrdcp root://cmseos.fnal.gov//store/user/$(whoami)/${CMSSW}.tgz .
tar -xf ${CMSSW}.tgz
rm ${CMSSW}.tgz
scramv1 b ProjectRename
echo $pwd
ls
cd ${CMSSW}/src/HiggsAnalysis/CombinedLimit
scramv1 b ProjectRename
scramv1 b clean
scramv1 b
eval `scramv1 runtime -sh`

cd ${_CONDOR_SCRATCH_DIR}
pwd
cd ${CMSSW}/src/Limits/
echo $outdir

python $pathtomacro$runmacro -c $config
xrdcp -np results*.root root://cmseos.fnal.gov//store/user/$(whoami)/13TeV/${outdir}/.
xrdcp -r -np Datacards/limits/SUSYNano19-*_AsymptoticLimits/* root://cmseos.fnal.gov//store/user/$(whoami)/14TeV/${outdir}/.
ls -a

status=`echo $?`
echo "Status = $status"

exit $status
