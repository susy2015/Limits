#!/bin/bash

name=$1

CMSSW=${CMSSW_BASE##*/}
DIR=$(pwd)

cd $CMSSW_BASE
cd ..
eosrm /store/user/${USER}/${CMSSW}_${name}.tgz
tar --exclude-caches-all -zcf ${CMSSW}_${name}.tgz $CMSSW --exclude="$CMSSW/src/PhysicsTools/*" --exclude="$CMSSW/src/TopTagger*/*" --exclude="$CMSSW/src/.git/*" --exclude="*.pdf" --exclude="*.png" --exclude="*.log" --exclude="*.err" --exclude="*.out" --exclude="*.txt" --exclude="*.tex" --exclude="*.sh" --exclude="$CMSSW/src/SusyAnaTools/*" --exclude="$CMSSW/src/Datacards/results/*moveTime*" --exclude="$CMSSW/src/CombineHarvester/*" --exclude="$CMSSW/src/HiggsAnalysis/*"
xrdcp -f ${CMSSW}_${name}.tgz root://cmseos.fnal.gov//store/user/${USER}/${CMSSW}_${name}.tgz
rm -f ${CMSSW}_${name}.tgz
cd $DIR
