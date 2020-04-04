#!/bin/bash

while read p; do 

	python Datacards/python/writeDatacard_SUSYNano19.py -l SMS_T2tt_fastsim_2016 -s $p -m True

done < $1
