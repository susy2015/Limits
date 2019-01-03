#!/bin/bash

dphi=0
dphistring=""

for dphivalue in $(seq 0.0 0.1 2.0);
do
	echo "dphisrt12met > "$dphivalue
	dphistring=$( printf '%02d' $dphi)
	echo "dphitop"$dphistring
	cp dev_dphiOptimize_test_setup_T2bW.conf dev_dphiOptimize_test_T2bW_dphitop${dphistring}_setup.conf	
	perl -pi -e "s/dphisrt12met>0.0/dphisrt12met>$dphivalue/g" dev_dphiOptimize_test_T2bW_dphitop${dphistring}_setup.conf
	perl -pi -e "s/dphitop00/dphitop${dphistring}/g" dev_dphiOptimize_test_T2bW_dphitop${dphistring}_setup.conf

	#python Datacards/python/makeDatacards.py dev_dphiOptimize_test_T2bW_dphitop${dphistring}_setup.conf	
	python Datacards/python/runLimits.py -c dev_dphiOptimize_test_T2bW_dphitop${dphistring}_setup.conf
	
	let dphi+=1
done
