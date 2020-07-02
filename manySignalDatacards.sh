#!/bin/bash

while read p; do 

	xrdcp -f root://cmseos.fnal.gov//eos/uscms/store/user/lpcsusyhad/Stop_production/LimitInputs/15Jun2020_Run2_dev_v6/SMS_T2tt_fastsim/${p}.json Datacards/setup/SUSYNano19/SMS_T2tt_fastsim/.
	xrdcp -f root://cmseos.fnal.gov//eos/uscms/store/user/lpcsusyhad/Stop_production/LimitInputs/15Jun2020_Run2_dev_v6/SMS_T2tt_fastsim/${p}_syst.conf Datacards/setup/SUSYNano19/SMS_T2tt_fastsim/.
	cat list | xargs -P 4 -L 1 -I {} python Datacards/python/writeDatacard_SUSYNano19.py -l SMS_T2tt_fastsim -s {} -m True
	#python Datacards/python/writeDatacard_SUSYNano19.py -l SMS_T2tt_fastsim -s $p -m True

done < $1
