import sys
import re
import ROOT as rt
rt.gROOT.SetBatch(True)    

class inputFile_Cut_v2():

    def __init__(self, fileName):
        self.HISTOGRAM = self.findHISTOGRAM(fileName)
        self.HISTOGRAM_CUT = self.findHISTOGRAM_CUT(fileName)
        self.HISTOGRAM_SIG = self.findHISTOGRAM_SIG(fileName)
        self.HISTOGRAM_SIG_CUT = self.findHISTOGRAM_SIG_CUT(fileName)
        self.EXPECTED = self.findEXPECTED(fileName)
        self.EXPECTED_CUT = self.findEXPECTED_CUT(fileName)
        self.OBSERVED = self.findOBSERVED(fileName)
        self.LUMI = self.findATTRIBUTE(fileName, "LUMI")
        self.ENERGY = self.findATTRIBUTE(fileName, "ENERGY")
        print self.ENERGY
        self.PRELIMINARY = self.findATTRIBUTE(fileName, "PRELIMINARY")

    def findATTRIBUTE(self, fileName, attribute):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != attribute: continue
            fileIN.close()
            return tmpLINE[1]

    def findHISTOGRAM(self, fileName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "HISTOGRAM": continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            x = rootFileIn.Get(tmpLINE[2])
            x.SetDirectory(0)
            return {'histogram': x}
            
    def findHISTOGRAM_CUT(self, fileName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "HISTOGRAM_CUT": continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            x = rootFileIn.Get(tmpLINE[2])
            x.SetDirectory(0)
            return {'histogram_cut': x}
            
    def findHISTOGRAM_SIG(self, fileName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "HISTOGRAM_SIG": continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            x = rootFileIn.Get(tmpLINE[2])
            x.SetDirectory(0)
            return {'histogram_sig': x}
            
    def findHISTOGRAM_SIG_CUT(self, fileName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "HISTOGRAM_SIG_CUT": continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            x = rootFileIn.Get(tmpLINE[2])
            x.SetDirectory(0)
            return {'histogram_sig_cut': x}
            
    def findEXPECTED(self, fileName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "EXPECTED": continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            return {'nominal': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[2],tmpLINE[2]), key.GetName())],
                    'plus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[3],tmpLINE[3]), key.GetName())],
                    'minus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[4],tmpLINE[4]), key.GetName())],
                    'colorLine': tmpLINE[5],
                    'colorArea': tmpLINE[6]}

    def findEXPECTED_CUT(self, fileName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "EXPECTED_CUT": continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            return {'nominal': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[2],tmpLINE[2]), key.GetName())],
                    'plus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[3],tmpLINE[3]), key.GetName())],
                    'minus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[4],tmpLINE[4]), key.GetName())],
                    'colorLine': tmpLINE[5],
                    'colorArea': tmpLINE[6]}

    def findOBSERVED(self, fileName):
        fileIN = open(fileName)        
        for line in fileIN:
            tmpLINE =  line[:-1].split(" ")
            if tmpLINE[0] != "OBSERVED": continue
            fileIN.close()
            rootFileIn = rt.TFile.Open(tmpLINE[1])
            return {'nominal': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[2],tmpLINE[2]), key.GetName())],
                    'plus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[3],tmpLINE[3]), key.GetName())],
                    'minus': [rootFileIn.Get(key.GetName()) for key in rt.gDirectory.GetListOfKeys() if re.match(r'(%s_[0-9]+|%s)$' % (tmpLINE[4],tmpLINE[4]), key.GetName())],
                    'colorLine': tmpLINE[5],
                    'colorArea': tmpLINE[6]}

