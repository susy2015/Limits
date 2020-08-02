#!/bin/bash

name=$1

CMSSW=${CMSSW_BASE##*/}
DIR=$(pwd)

cd $CMSSW_BASE
cd ..
eos root://cmseos.fnal.gov rm /store/user/${USER}/${CMSSW}_${name}.tgz
tar --exclude-caches-all -zcf ${CMSSW}_${name}.tgz $CMSSW --exclude="$CMSSW/src/PhysicsTools/*" --exclude="$CMSSW/src/TopTagger*/*" --exclude="$CMSSW/src/.git/*" --exclude="*.pdf" --exclude="*.png" --exclude="*.log" --exclude="*.err" --exclude="*.out" --exclude="*.txt" --exclude="*.tex" --exclude="*.sh" --exclude="$CMSSW/src/Stop0l/*" --exclude="$CMSSW/src/SusyAnaTools/*" --exclude="$CMSSW/src/Limits/Datacards/results/*" --exclude="$CMSSW/src/Limits/dummy_*" --exclude="$CMSSW/src/Limits/limits*" 
xrdcp -f ${CMSSW}_${name}.tgz root://cmseos.fnal.gov//store/user/${USER}/${CMSSW}_${name}.tgz
rm -f ${CMSSW}_${name}.tgz
cd $DIR
