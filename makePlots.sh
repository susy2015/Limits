#!/bin/bash

#declare -a StringArray=("T2tt" "T2bW" "T2tb" "T2fbd" "T2bWC" "T2cc" "t2fbd" "t2bWC" "t2cc" "T2All")
declare -a StringArray=("T2bW" "T2All")
 
# Iterate the string array using for loop
for val in ${StringArray[@]}; do

	loc="$val"
        conf=""
        suffix=""
        if [ "$val" = "t2fbd" ]; then
		loc="T2fbd"
		suffix="replot_"
	elif [ "$val" = "t2cc" ]; then
		loc="T2cc"
		conf="_local"
		suffix="replot_"
        elif [ "$val" = "T2cc" ]; then
		conf="_local"
	elif [ "$val" = "t2bWC" ]; then
		loc="T2bWC"
		suffix="replot_"
	fi
        
	if [ "$val" != "T2All" ]; then
		echo python Datacards/python/runLimits.py -c dc_SUSY19Nano_setup_Local.conf -f -e limits_multi_${loc}_081820_UnblindRun2 -a ${loc}_signals${conf}.conf -n ${val}
		python Datacards/python/runLimits.py -c dc_SUSY19Nano_setup_Local.conf -f -e limits_multi_${loc}_081820_UnblindRun2 -a ${loc}_signals${conf}.conf -n ${val}
	fi

	echo python PlotsSMS/python/makeSMSplots.py PlotsSMS/config/${val}_SUS16005.cfg ${val}_v7smooth_${suffix}
	python PlotsSMS/python/makeSMSplots.py PlotsSMS/config/${val}_SUS16005.cfg ${val}_v7smooth_${suffix}

done
