#!/usr/bin/env python
# encoding: utf-8

# File        : TestPerSB.py
# Author      : Ben Wu
# Contact     : benwu@fnal.gov
# Date        : 2020 Jul 30
#
# Description :


import json
import os 
import argparse
import subprocess
import multiprocessing

combineCards = os.environ["CMSSW_BASE"] + "/bin/" + os.environ["SCRAM_ARCH"] + "/combineCards.py"
combinejson = os.environ["CMSSW_BASE"] + "/src/Limits/Datacards/setup/SUSYNano19/combine_bkgPred.json"
NProcess = multiprocessing.cpu_count()

def GetAssociatedCRs(sb):
    crlist = []
    for CR in js["binMaps"].keys():
        mapstr = js["binMaps"][CR][sb]
        for sub in mapstr.split("+"):
            tempcr = sub.split("*")[-1].strip().strip('()')
            crlist.append(tempcr)
    return crlist

    
def CombineDatacard(loc, sb, crlist):
    cmd = "python %s "  %  combineCards
    sbfile = loc + "/" + sb +".txt"
    inputfiles = [sbfile]
    for cr in crlist:
        inputfiles.append(loc + "/" + cr +".txt")
    cmd  += " ".join(inputfiles)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = p.communicate()
    outname = sb[4:]
    with open("%s.txt" % outname, "w") as f:
        f.write(output[0])
    return "%s.txt" % outname

def RunLimit(DC):
    DCname = DC.split(".")[0]
    cmd = "combine -M AsymptoticLimits -d %s  --rMin 0 --rMax %d -n _%s " % (DC, int(args.rMax), DCname)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()
    with open("%s.log" % DCname, "w") as f:
        f.write(output[0])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("-l", "--location", dest="signalLocation", default='../T2tt_200_0/',
                             help="Signal point to use when running the maximum likelihood fit. [Default: T2tt_850_100]")
    parser.add_argument("-r", "--rMax", dest="rMax", default=20,
                             help="Signal strength upper bound. [Default: 20]")
    args = parser.parse_args()

    js = json.load(open(combinejson))


    DClist = []
    for srb in js["binNum"].keys():
        crlist = GetAssociatedCRs(srb)
        DC = CombineDatacard(args.signalLocation, srb, crlist)
        DClist.append(DC)

    r = None
    pool = multiprocessing.Pool(processes=NProcess)
    r = pool.map(RunLimit, DClist)
    pool.close()
