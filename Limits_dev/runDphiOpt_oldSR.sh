#!/bin/bash

dphi=0
dphistring=""

for dphivalue in $(seq 0.0 0.1 2.0);
do
	echo "dphisrt12met > "$dphivalue
	dphistring=$( printf '%02d' $dphi)
	echo "dphitop"$dphistring
	cp dev_dphiOptimize_test_oldSR_setup.conf dev_dphiOptimize_test_oldSR_dphitop${dphistring}_setup.conf	
	perl -pi -e "s/dphisrt12met>0.0/dphisrt12met>$dphivalue/g" dev_dphiOptimize_test_oldSR_dphitop${dphistring}_setup.conf
	perl -pi -e "s/dphitop00/dphitop${dphistring}/g" dev_dphiOptimize_test_oldSR_dphitop${dphistring}_setup.conf

	#python Datacards/python/makeDatacards.py dev_dphiOptimize_test_oldSR_dphitop${dphistring}_setup.conf	
	python Datacards/python/runLimits.py -c dev_dphiOptimize_test_oldSR_dphitop${dphistring}_setup.conf
	
	let dphi+=1

        #/Datacards/limits/mc_dphiOpt_BDT_130ifb_T2tt_dphitop${dphistring}_Asymptotic
        #/Datacards/limits/mc_dphiOpt_BDT_130ifb_T2tt_dphitop${dphistring}_AsymptoticLimits
done
