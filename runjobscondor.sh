#!/bin/bash

runmacro=$1
config=$2
pathtomacro=$3
outputdir=$4
scramdir=$5
outdir=${6}
scram=${7}
signal=${8}
signalDir=${9}
eosDir=${10}

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

xrdcp root://cmseos.fnal.gov//store/user/$(whoami)/${CMSSW}_${outdir}.tgz .
tar -xf ${CMSSW}_${outdir}.tgz
rm ${CMSSW}_${outdir}.tgz
scramv1 b ProjectRename
echo $pwd
ls
cd ${CMSSW}/src/HiggsAnalysis/CombinedLimit
scramv1 b ProjectRename
scramv1 b clean
scramv1 b
eval `scramv1 runtime -sh`

cd ${CMSSW}/src/
ls -a
scramv1 b ProjectRename
scramv1 b
eval `scramv1 runtime -sh`

cd ${_CONDOR_SCRATCH_DIR}
pwd
cd ${CMSSW}/src/Limits/
echo $outdir

ulimit -s unlimited

#Copy signal json/conf to setup dir
mkdir Datacards/setup/SUSYNano19/${signalDir}/
xrdcp -f root://cmseos.fnal.gov//eos/uscms/store/user/lpcsusyhad/Stop_production/LimitInputs/${eosDir}/${signalDir}/${signal}.json Datacards/setup/SUSYNano19/${signalDir}/.
xrdcp -f root://cmseos.fnal.gov//eos/uscms/store/user/lpcsusyhad/Stop_production/LimitInputs/${eosDir}/${signalDir}/${signal}_syst.conf Datacards/setup/SUSYNano19/${signalDir}/.

#Make new config with sample replaced
sed -i -e "s/T2tt_1000_0/$signal/g" ${config}

python $pathtomacro/writeDatacard_SUSYNano19.py -l $signalDir -s $signal
python $pathtomacro$runmacro -c $config
python $pathtomacro$runmacro -c $config -p
xrdcp -r -np Datacards/limits/SUSYNano19-20200403_AsymptoticLimits root://cmseos.fnal.gov//store/user/$(whoami)/13TeV/${outdir}/.
ls -a

status=`echo $?`
echo "Status = $status"

exit $status
