#!/bin/bash

CMSSW=${CMSSW_BASE##*/}
DIR=$(pwd)

cd $CMSSW_BASE
cd ..
eosrm /store/user/${USER}/${CMSSW}.tgz
tar --exclude-caches-all -zcf ${CMSSW}.tgz $CMSSW --exclude="$CMSSW/src/PhysicsTools/*" --exclude="$CMSSW/src/TopTagger*/*" --exclude="$CMSSW/src/.git/*" --exclude="*.pdf" --exclude="*.png" --exclude="*.log" --exclude="*.err" --exclude="*.out" --exclude="*.txt" --exclude="*.tex" --exclude="*.sh" --exclude="$CMSSW/src/SusyAnaTools/*" --exclude="$CMSSW/src/Datacards/results/*moveTime*"
xrdcp -f ${CMSSW}.tgz root://cmseos.fnal.gov//store/user/${USER}/${CMSSW}.tgz
rm -f ${CMSSW}.tgz
cd $DIR
