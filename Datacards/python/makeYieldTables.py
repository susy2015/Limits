#! /usr/bin/python
import os
import sys
from math import sqrt
from ROOT import TFile,TH1D
from makeUncTables import getDataYield, getRawUnc, getFileName, chunkHeaderNoB, chunkHeader
#from makeUncTables import signals

"""Makes the yield tables for the AN for the various backgrounds and signal points using the datacards.
If the uncertanty names change, the "sources" dictornary will need to be updated apropriately. Other 
backgrounds can be added as new lists, just make sure that the numbers assigned to each bkg in the "ps" 
dictionary is correct. 
"""

binsB   = (1,2)
binsMet = ((250,'250-300'),(300,'300-400'),(400,'400-500'),(500,'500-600'),(600,'$>$600'))
ps = {'ttbarplusw':3, 'znunu':4, 'ttz':5, 'qcd':6, 'onelepcr':3, 'T2tt_700_1':2, 'T2tt_600_200':2, 'T2tt_300_200':2, 'signal':2}
#signals = ('T2tt_700_1','T2tt_600_200','T2tt_300_200')
signals = ('T2tb_550_1','T2tb_650_150','T2tb_500_200')
totalYields = {}
xsec = {}
sources = {
  'ttbarplusw' : [('corr_l'               , 'Lepton veto'                , 'syst'),
                  ('corr_tau'             , 'Tau veto'                   , 'syst'),
                  ('eff_b_heavy'          , '\\bq-tagging: heavy flavor' , 'syst'),
                  ('eff_b_light'          , '\\bq-tagging: light flavor' , 'syst'),
                  ('fake_t'               ,  'Top-taging'                , 'syst'),
                  ('pu'                   , 'Pileup reweighting'         , 'syst'),
                  ('lostlep_nt1metintunc' , '\\met integration'          , 'syst'),
                  ('scale_j'              , 'Jet energy scale'           , 'syst'),
                  ('ttbarNorm'            , '\\ttbar~normalization'      , 'syst'),
                  ('wjetsNorm'            , '\\W+jets normalization'     , 'syst'),
                  ('mcstat_ttbarplusw_bin', 'Monte Carlo statistics (SR)', 'stat'),
                  ('lostlep_bin_onelepcr' , 'Data statistics (CR)'       , 'stat'),# NEEDS TO COME FROM CR DATACARD
  ],
  'onelepcr' : [('corr_l'                        , 'Lepton veto'           , 'syst'),
                ('mcstat_ttbarplusw_bin_onelepcr', 'Monte Carlo statistics', 'stat'),
                #('lostlep_bin_onelepcr'          , 'Data statistics'       , 'stat'),# WILL BE INCLUDED IN SR UNCS
  ],
  'znunu' : [('corr_l'                        , 'Lepton veto'                , 'syst'),
             ('eff_b_heavy'                   , '\\bq-tagging: heavy flavor' , 'syst'),
             ('eff_b_light'                   , '\\bq-tagging: light flavor' , 'syst'),
             ('fake_t'                        ,  'Top-taging'                , 'syst'),
             ('pu'                            , 'Pileup reweighting'         , 'syst'),
             ('scale_j'                       , 'Jet energy scale'           , 'syst'),
             ('znunu_rzunc'                   , '$R_{\\cPZ}$'                , 'syst'),
             ('zfromgamma_mcstat_bin'         , 'Monte Carlo statistics (SR)', 'stat'),
             ('zfromgamma_mcstat_bin_photoncr', 'Monte Carlo statistics (CR)', 'stat'),
             ('zfromgamma_stat_bin_photoncr'  , 'Data statistics (CR)'       , 'stat'),
  ],
  'ttz' : [('corr_l'        , 'Lepton veto'               , 'syst'),
           ('eff_b_heavy'   , '\\bq-tagging: heavy flavor', 'syst'),
           ('eff_b_light'   , '\\bq-tagging: light flavor', 'syst'),
           ('lumi'          , 'Luminosity'                , 'syst'),
           ('pu'            , 'Pileup reweighting'        , 'syst'),
           ('scale_j'       , 'Jet energy scale'          , 'syst'),
           ('ttZNorm'       , 'Cross section'             , 'syst'),
           ('ttZ_pdfunc'    , 'pdf/$\\alpha_S$ variation' , 'syst'),
           ('ttZ_scaleunc'  , '$\\mu_R/\\mu_F$ variation' , 'syst'),
           ('mcstat_ttZ_bin', 'Monte Carlo statistics'    , 'stat'),
  ],
  'qcd' : [('corr_tau'          , 'Tau veto'                  , 'syst'),
           ('eff_b_heavy'       , '\\bq-tagging: heavy flavor', 'syst'),
           ('eff_b_light'       , '\\bq-tagging: light flavor', 'syst'),
           ('fake_t'            ,  'Top-taging'               , 'syst'),
           ('pu'                , 'Pileup reweighting'        , 'syst'),
           ('scale_j'           , 'Jet energy scale'          , 'syst'),
           ('qcd_bkgsubunc_'    , 'Background subtraction'    , 'syst'),
           ('qcd_jetresptailunc', 'Jet response tail'         , 'syst'),
           ('qcd_tfstatunc'     , 'Transfer factor'           , 'stat'),
           ('qcd_stat_bin_qcdcr', 'Data statistics (SR)'      , 'stat'),
  ]
} # sources

def main() :
  args = sys.argv[1:]
  if not args:
    print('usage: makeYieldTables.py <directory with template datacards>')
    sys.exit(1)
  inDir = args[0]
  
  # fill xsec dict here so we don't need to acces the root file a gazillin times
  for sig in signals :
    if not sig in xsec.keys() : 
      xsec[sig] = getXsec(sig)*1000 # pb->fb (lumi is in 1/fb)
  #print '\n', 'using xsecs:', xsec
  
  ### # MC predicted yields plus total uncertainties for all 4 bkgs from the datacards
  ### # currently used as a cross-check of the table made with getZeroLeptonUncertainty.py
  ### print '\n\n\n', '='*5, 'Making yield plus unc table...', '\n\n'
  ### print makeTable(inDir)
  
  ### # observed data and predicted MC (with stat/syst) yields for the LLB 1LCR
  ### print '\n\n\n', '='*5, 'Making yield plus unc table for onelepcr...', '\n\n'
  ### print makeCrTable(inDir,'onelepcr')
  
  # expected signal yields and efficiencies for the baseline selection and per bin for 2 example points
  # baseline effs are total and per bin effs are wrt the baseline selection
  print '\n\n\n', '='*5, 'Making signal yield plus acceptance*eff table...', '\n\n'
  print makeEffTable(inDir,2.263)
  print '\n\n\n'

# piece together chunks for the SR yields
def makeTable(inDir) : 
  s  = '\\hline\n'
  s += '\\met [GeV]  &  \\ttbar, \\W+jets  &  \\znunu  &  QCD  &  \\ttZ  &  total SM  &  $N_{\\rm data}$  \\\\ \n'
  s += '\\hline\n'
  s += makeCwhunk(inDir,5,1,  0,0)
  s += makeChunk(inDir,5,2,  0,0)
  s += makeChunk(inDir,7,1,  0,0)
  s += makeChunk(inDir,7,2,  0,0)
  s += makeChunk(inDir,5,1,175,0)
  s += makeChunk(inDir,5,2,175,0)
  s += makeChunk(inDir,7,1,175,0)
  s += makeChunk(inDir,7,2,175,0)
  s += makeChunk(inDir,5,1,175,1)
  s += makeChunk(inDir,5,2,175,1)
  s += '\\hline\n'
  return s

# piece together chunks for the CR yields
def makeCrTable(inDir,cr='') : 
  s  = '\\hline\n'
  s += '\\met [GeV]   & $N_{\\rm data}$ & \\ttbar, \\W+jets \\\\ \n'
  s += '\\hline\n'
  s += makeCrChunk(inDir,5,1,  0,0,cr)
  s += makeCrChunk(inDir,7,1,  0,0,cr)
  s += makeCrChunk(inDir,5,1,175,0,cr)
  s += makeCrChunk(inDir,7,1,175,0,cr)
  s += makeCrChunk(inDir,5,1,175,1,cr)
  s += '\\hline\n'
  return s.replace(', $\\nb = 1$','')

# piece together chunks for the signal yields
def makeEffTable(inDir,lumi) :
  for sig in signals :
    if not sig in totalYields.keys() : 
      totalYields[sig] = getTotalEvents(inDir,sig)*xsec[sig]/1000.
  s  = '\\hline\n'
  s += ' &  \\multicolumn{2}{c||}{T2tt(700,1)} & \multicolumn{2}{c||}{T2tt(600,200)} & \multicolumn{2}{c|}{T2tt(300,200)}  \\\\ \n'
  s += '\\hline\n'
  s += '\\met [GeV]' + '& $\\nb=1$ & $\\nb \\geq 2$'*len(signals) + ' \\\\ \n'
  s += '\\hline\n'
  s += '\\multicolumn{'+str(2*len(signals)+1)+'}{c}{Baseline selection}  \\\\ \n'
  s += '\\hline\n'
  for sig in signals :
    n = totalYields[sig]
    x = xsec[sig]
    eff = n/(x*lumi)
    s += ' & \\multicolumn{2}{c||}{' + str(round(n,1)) + ' (' + str(round(eff*100,1)) + '\\%)}'
  s += '\\\\ \n'
  s += makeEffChunk(inDir,lumi,5,  0,0)
  s += makeEffChunk(inDir,lumi,7,  0,0)
  s += makeEffChunk(inDir,lumi,5,175,0)
  s += makeEffChunk(inDir,lumi,7,175,0)
  s += makeEffChunk(inDir,lumi,5,175,1)
  s += '\\hline\n'
  return s

# signal yield/eff table chunk for a given bin in (njets, mtb, ntops)
def makeEffChunk(inDir,lumi,nj,mtb,nt,cr='') :
  s = chunkHeaderNoB(nj, mtb, nt, 2*len(signals)+1)
  for binMet in binsMet :
    s += binMet[1]
    for sig in signals :
      for nb in (1,2) :
        (n,eff) = getEff(inDir,lumi,sig,binMet[0],nj,nb,nt,mtb,cr)
        # this eff is relitive to ALL expected events for
        # now we're going to only consider it relitive
        # to the baseline selection, so need to calc that
        n = n*xsec[sig]/1000.
        effbase = n / totalYields[sig]
        s += ' & ' + str(round(n,2)) + ' (' + str(round(effbase*100,1)) +'\\%)'
    s += ' \\\\ \n'
  return s

# CR yield/unc table chunk for a given bin in (njets, mtb, ntops)
def makeCrChunk(inDir,nj,nb,mtb,nt,cr) :
  s = chunkHeader(nj,nb,mtb,nt,3)
  for binMet in binsMet :
    if nt==1 :
      if binMet[0] != 250 : continue
      s += '$>$250'
    else : s += binMet[1]
    s += ' & ' + str(getDataYield(inDir,'ttbarplusw',binMet[0],nj,nb,nt,mtb,cr))
    s += ' & ' + getBinYieldUncs(inDir,'ttbarplusw',binMet[0],nj,nb,nt,mtb,cr)[0]
    s += ' \\\\ \n'
  return s

# SR yield/unc table chunk for a given bin in (njets, mtb, ntops)
def makeChunk(inDir,nj,nb,mtb,nt) :
  s = chunkHeader(nj,nb,mtb,nt,7)
  for binMet in binsMet : 
    s += binMet[1] 
    #for sigpoint in signals :
    #  s += ' & ' + str(round(getYield(inDir,sigpoint,binMet[0],nj,nb,nt,mtb,'',sigpoint),2))
    n = 0
    e = 0
    for bkg in ('ttbarplusw', 'znunu', 'qcd', 'ttz') :
      (dummy,(tn,te)) = getBinYieldUncs(inDir,bkg,binMet[0],nj,nb,nt,mtb,'')
      #if bkg == 'ttbarplusw' :
      #  if binMet[0] == 250 : print ''
      #  print dummy
      n += tn
      e += te**2
      s += ' & ' + str(round(tn,2)) + ' $\\pm$ ' + str(round(te,2))
    s += ' & ' + str(round(n,2)) + ' $\\pm$ ' + str(round(sqrt(e),2))
    s += ' & ' + str(getDataYield(inDir,'',binMet[0],nj,nb,nt,mtb,'',''))
    s += ' \\\\ \n'
  return s

# get the total number of events in the sr for a given signal point
def getTotalEvents(inDir,sig) :
  dummyFiles = os.listdir(os.path.join(inDir,sig))
  n = 0
  for df in dummyFiles :
    if not 'cr' in df :
      f = os.path.join(inDir,sig,df)
      n += getYield(f,sig)
  return n

# return the yield +/- stat +/- syst for the given process in the given bin
def getBinYieldUncs(inDir,process,met,nj,nb,nt,mtb,cr='',sig='') :
  y = 0
  if cr=='' and process == 'ttbarplusw' :
    # replace raw MC ttbarplusw with estimate from 1LCR
    met1L = met if nt==0 else 250
    mc0L = getYield(inDir,process,met  ,nj,nb,nt,mtb,''        ,sig)
    mc1L = getYield(inDir,process,met1L,nj,1 ,nt,mtb,'onelepcr',sig)
    tf = mc0L / mc1L
    y = tf * getDataYield(inDir,process,met1L,nj,1,nt,mtb,'onelepcr')
  else :
    y = getYield(inDir,process,met,nj,nb,nt,mtb,cr,sig)
  stat = 0
  syst = 0
  stsy = 0
  for unc in sources[(process if cr=='' else cr)] :
    if unc[2] == 'stat' : stat += getUncSquared(inDir,unc[0],process,met,nj,nb,nt,mtb,cr,sig)
    if unc[2] == 'syst' : syst += getUncSquared(inDir,unc[0],process,met,nj,nb,nt,mtb,cr,sig)
    stsy += getUncSquared(inDir,unc[0],process,met,nj,nb,nt,mtb,cr,sig)
  stat = sqrt(stat) * y
  syst = sqrt(syst) * y
  stsy = sqrt(stsy) * y
  return ( str(round(y,2))+' $\\pm$ '+str(round(stat,2))+' (stat.) $\\pm$ '+str(round(syst,2))+' (syst.)', (y,stsy) ) 

# get the yield for the given bin
# if met<0, inDir is assumed to be the full path+filename
def getYield(inDir,process,met=-1,nj=-1,nb=-1,nt=-1,mtb=-1,cr='',sig='') :
  if met<0 : fname = inDir
  else     : fname = getFileName(inDir,met,nj,nb,nt,mtb,cr,sig)
  if not os.path.exists(fname) : return 0
  f = open(fname)
  n = ''
  for l in f:
    if len(l) < 1 : continue
    if not 'rate' in l : continue
    if 'T' in sig     : process = 'signal'
    if 'T' in process : process = 'signal'
    n = l.split()[ps[process]-1]
  f.close()
  n = float(n.replace('SIGRATE',''))
  return n

# get the cross-section for the given signal point from the 
# root file in the data directory
def getXsec(sig) :
  mstop = int(sig.split('_')[1])
  xsecfile = TFile('../data/xsecs/stop.root')
  xsechist = TH1D()
  xsechist = xsecfile.Get('xsecs')
  xsec = xsechist.Interpolate(mstop)
  return xsec

# return the number of events and efficiency for selecting
# them (relative to the ALL expected events)
def getEff(inDir,lumi,sig,met,nj,nb,nt,mtb,cr='') :
  n = getYield(inDir,sig,met,nj,nb,nt,mtb,cr,sig)
  x = xsec[sig]
  return n , n/(x*lumi) 

# get and square the unc for the bin/process, returning 0 if it's not there
def getUncSquared(inDir,unc,process,met,nj,nb,nt,mtb,cr='',sig='') :
  u = getRawUnc(inDir,unc,process,met,nj,nb,nt,mtb,cr,sig)
  if u == '-' : return 0
  return u**2
  
if __name__=='__main__' : main()
