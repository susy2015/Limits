#! /usr/bin/python
import os
import sys
import ROOT as rt

""" creates root files (one for each input directory) with the efficiency plots for
the baseline selection (relitive to full yield from the xsec) and for each bin
(relitive to the baseline selection)
"""

lumi = 12.9
xsecs = {}
binlist = []

sig = 'T2tt'

if sig == 'T2tt':
    xmin = 150.0
    xmax = 1200.0
    xbin = 1
    ymin = 0.0
    ymax = 700.0
    ybin = 1
elif sig == 'T2bW':
    xmin = 200.0
    xmax = 1000.0
    xbin = 25
    ymin = 0.0
    ymax = 500.0
    ybin = 25
elif sig == 'T2fbd':
    xmin = 250.0
    xmax = 600.0
    xbin = 25
    ymin = 100.0
    ymax = 700.0
    ybin = 5


def getXbin(mstop): return int((int(mstop) - xmin) / xbin) + 1
def getYbin(mlsp) : return int((int(mlsp) - ymin) / ybin) + 1


def makeEffMap(inDir):
  sigPts = {}
  for d in os.listdir(inDir):
    if '.' in d : continue
    sigPts[d] = 0
    updateXsecs(d)

  model = sigPts.keys()[0].split('_')[0]
  f = rt.TFile('effMap_' + model + '.root', 'RECREATE')
  sumAllBins(inDir, sigPts)

  print '\n' + '=' * 5, 'making eff map for', model, '=' * 5
  for bin in binlist:
    print bin
    savebin = bin.replace('bin_', 'bin_met').replace('mtb0', 'lowmtb').replace('mtb175', 'highmtb').replace('1t','geq1').replace('5t','geq5')
    h = rt.TH2F(savebin, '%s;m_{#tilde{t}} [GeV];m_{#tilde{#chi}_{1}^{0}} [GeV]'%savebin, int((xmax - xmin) / xbin), xmin, xmax, int((ymax - ymin) / ybin), ymin, ymax)
    for sigPt in sigPts:
      (mstop, mlsp) = sigPt.split('_')[1:]
      sigDir = os.path.join(inDir, sigPt)
      nevents = getYield(os.path.join(sigDir, sigPt + '_' + bin + '.txt'))
      eff = nevents / sigPts[sigPt]
      h.SetBinContent(getXbin(mstop), getYbin(mlsp), eff)
    h.Write(savebin, rt.TObject.kOverwrite)
  f.Close()


def sumAllBins(inDir, sigPts):
  h = rt.TH2F('baseline', 'baseline;m_{#tilde{t}} [GeV];m_{#tilde{#chi}_{1}^{0}} [GeV]', int((xmax - xmin) / xbin), xmin, xmax, int((ymax - ymin) / ybin), ymin, ymax)
  for sigPt in sigPts:
    (mstop, mlsp) = sigPt.split('_')[1:]
    sigDir = os.path.join(inDir, sigPt)
    nevents = 0
    print sigPt
    for bin in binlist:
      nevt = getYield(os.path.join(sigDir, sigPt + '_' + bin + '.txt'))
      print '...', bin, nevt
      nevents += nevt
    eff = nevents / (lumi * xsecs[int(mstop)] * 1000)
    h.SetBinContent(getXbin(mstop), getYbin(mlsp), eff)
    sigPts[sigPt] = nevents
  h.Write('baseline', rt.TObject.kOverwrite)


def getYield(datacard):
  if not os.path.exists(datacard):
    print '!!!', 'unknown datacard:', datacard
    return 0
  mstop = int(datacard.split('/')[-2].split('_')[1])
  f = open(datacard)
  n = ''
  for l in f:
    if len(l) < 1 : continue
    if not 'rate' in l : continue
    n = l.split()[1]
  f.close()
  n = float(n)
  return n


def compileBinList(dir):
    del binlist[:]
    for file in os.listdir(dir):
        if 'template_bin' in file:
            bin = file.replace('template_', '').replace('.txt', '')
            binlist.append(bin)

def updateXsecs(d):
  mstop = int(d.split('_')[1])
  if mstop not in xsecs.keys():
    xsecfile = rt.TFile('../data/xsecs/stop.root')
    xsechist = rt.TH1D()
    xsechist = xsecfile.Get('xsecs')
    xsec = xsechist.Interpolate(mstop)
    xsecs[mstop] = xsec


def main():
  args = sys.argv[1:]
  if not args:
    print('usage: makeYieldTables.py <directory[s] with template datacards>')
    sys.exit(1)
  inDirs = args[:]

  for inDir in inDirs:
    compileBinList(inDir)
    print binlist
    makeEffMap(inDir)


if __name__ == '__main__' : main()
