import sys
import re
import ROOT as rt
rt.gROOT.SetBatch(True)    

class inputFile_all():

    def __init__(self, fileName):
        self.HISTOGRAM_T2tt = self.findHISTOGRAM(fileName, "T2tt")
        self.EXPECTED_T2tt = self.findEXPECTED(fileName, "T2tt")
        self.OBSERVED_T2tt = self.findOBSERVED(fileName, "T2tt")
        self.HISTOGRAM_T2bW = self.findHISTOGRAM(fileName, "T2bW")
        self.EXPECTED_T2bW = self.findEXPECTED(fileName, "T2bW")
        self.OBSERVED_T2bW = self.findOBSERVED(fileName, "T2bW")
        self.HISTOGRAM_T2cc = self.findHISTOGRAM(fileName, "T2cc")
        self.EXPECTED_T2cc = self.findEXPECTED(fileName, "T2cc")
        self.OBSERVED_T2cc = self.findOBSERVED(fileName, "T2cc")
        self.HISTOGRAM_T2fbd = self.findHISTOGRAM(fileName, "T2fbd")
        self.EXPECTED_T2fbd = self.findEXPECTED(fileName, "T2fbd")
        self.OBSERVED_T2fbd = self.findOBSERVED(fileName, "T2fbd")
        self.HISTOGRAM_T2tb = self.findHISTOGRAM(fileName, "T2tb")
        self.EXPECTED_T2tb = self.findEXPECTED(fileName, "T2tb")
        self.OBSERVED_T2tb = self.findOBSERVED(fileName, "T2tb")
        self.HISTOGRAM_T2bWC = self.findHISTOGRAM(fileName, "T2bWC")
        self.EXPECTED_T2bWC = self.findEXPECTED(fileName, "T2bWC")
        self.OBSERVED_T2bWC = self.findOBSERVED(fileName, "T2bWC")
        self.LUMI = self.findATTRIBUTE(fileName, "LUMI")
        self.ENERGY = self.findATTRIBUTE(fileName, "ENERGY")
        print self.ENERGY
        self.PRELIMINARY = self.findATTRIBUTE(fileName, "Supplementary")

    def findATTRIBUTE(self, fileName, attribute):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != attribute: continue
            fileIN.close()
            return tmpLINE[1]

    def findHISTOGRAM(self, fileName, sigName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "HISTOGRAM_" + sigName: continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            x = rootFileIn.Get(tmpLINE[2])
            x.SetDirectory(0)
            return {'histogram': x}
            
    def findEXPECTED(self, fileName, sigName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "EXPECTED_" + sigName: continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            return {'nominal': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[2],tmpLINE[2]), key.GetName())],
                    'plus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[3],tmpLINE[3]), key.GetName())],
                    'minus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[4],tmpLINE[4]), key.GetName())],
                    'plus2': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s2_[0-9]+|%s2)$' % (tmpLINE[3],tmpLINE[3]), key.GetName())],
                    'minus2': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s2_[0-9]+|%s2)$' % (tmpLINE[4],tmpLINE[4]), key.GetName())],
                    'colorLine': tmpLINE[5],
                    'colorArea': tmpLINE[6]}

    def findOBSERVED(self, fileName, sigName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "OBSERVED_" + sigName: continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            return {'nominal': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[2],tmpLINE[2]), key.GetName())],
                    'plus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[3],tmpLINE[3]), key.GetName())],
                    'minus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[4],tmpLINE[4]), key.GetName())],
                    'colorLine': tmpLINE[5],
                    'colorArea': tmpLINE[6]}

