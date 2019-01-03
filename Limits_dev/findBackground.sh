#!/bin/bash

LL="ttbarplusw"
Z="znunu"
Rare="rare"
QCD="qcd_orig"
Signal="signal"
ttz="ttZ"

#the positions are 72 characters apart

strindex(){
	x="${1%%$2*}"
	[[ "$x" = "$1" ]] && echo -1 || echo "${#x}"
}

while read p; do

	strindex "$p" "$LL"

done < Datacards/limits/mc_Moriond17_BDT_40ifb_HMSig_wodphiCut_round_Asymptotic/T2tt_1100_1/combined_T2tt_1100_1.txt 
