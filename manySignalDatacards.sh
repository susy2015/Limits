#!/bin/bash

while read p; do 

	xrdcp -f root://cmseos.fnal.gov//eos/uscms/store/user/lpcsusyhad/Stop_production/LimitInputs/26May2020_Run2Unblind_dev_v6/SMS_T2tt_fastsim/${p}.json Datacards/setup/SUSYNano19/SMS_T2tt_fastsim/.
	xrdcp -f root://cmseos.fnal.gov//eos/uscms/store/user/lpcsusyhad/Stop_production/LimitInputs/26May2020_Run2Unblind_dev_v6/SMS_T2tt_fastsim/${p}_syst.conf Datacards/setup/SUSYNano19/SMS_T2tt_fastsim/.
	python Datacards/python/writeDatacard_SUSYNano19.py -l SMS_T2tt_fastsim -s $p -m True

done < $1
