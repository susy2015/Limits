#!/bin/bash

declare -a StringArray=("T2tt" "T2bW" "T2tb" "T2fbd" "T2bWC" "T2cc" "t2fbd" "t2bWC" "t2cc" "T2All")
 
# Iterate the string array using for loop
for val in ${StringArray[@]}; do

	loc=""
        if [ "$val" = "t2fbd" ]; then
		loc="T2fbd"
	elif [ "$val" = "t2cc" ]; then
		loc="T2cc"
	elif [ "$val" = "t2bWC" ]; then
		loc="T2bWC"
	else
		loc="$val"
	fi
        
	if [ "$val" != "T2All" ]; then
		python Datacards/python/runLimits.py -c dc_SUSY19Nano_setup_Local.conf -f -e limits_multi_${loc}_081820_UnblindRun2 -a ${loc}_signals.conf -n ${val}
	fi
	python PlotsSMS/python/makeSMSplots.py PlotsSMS/config/${val}_SUS16005.cfg ${val}_v7smooth_

done
