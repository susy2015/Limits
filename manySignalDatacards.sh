#!/bin/bash

while read p; do 

	python Datacards/python/writeDatacard_SUSYNano19.py -l SMS_T1tttt_fastsim -s $p -m True

done < $1
