#! /usr/bin/python
import os
from math import sqrt
from collections import OrderedDict
import sys

"""Makes the uncertanty tables for the AN for the various backgrounds using the template datacards. If the
uncertanty names change, the "sources" dictornary will need to be updated apropriately. Other backgrounds
can be added as new lists, just make sure that the numbers assigned to each bkg in the "ps" dictionary
is correct. Need to state whether the datacards are for the high mass (hm) or low mass (lm) search.
Usage: python makeUncTables.py <full_path_to_datacard_subdir> <hm|lm>
"""

sr_metbins_hm = OrderedDict()
sr_metbins_lm = OrderedDict()

sr_metbins_hm['mtb0_nj5'] =                [250, 300, 400, 500]
sr_metbins_hm['mtb0_nj7'] =                [250, 300, 400, 500]
sr_metbins_hm['mtb175_nj5_nt0_nw0'] =      [250, 350, 450, 550]
sr_metbins_hm['mtb175_nj7_nt0_nw0'] =      [250, 350, 450, 550]
sr_metbins_hm['mtb175_nj5t_nt0_nw1t'] =    [250, 350, 450, 550, 650]
sr_metbins_hm['mtb175_nj5t_nt1t_nw0'] =    [250, 350, 450, 550, 650]
sr_metbins_hm['mtb175_nj5t_nt1t_nw1t'] =   [250, 300, 400, 500]
"""
  'nb1_mtb0_nj5' :                [250, 300, 400, 500],
  'nb1_mtb0_nj7' :                [250, 300, 400, 500],
  'nb2_mtb0_nj5' :                [250, 300, 400, 500],
  'nb2_mtb0_nj7' :                [250, 300, 400, 500],
  'nb1_mtb175_nj5_nt0_nw0' :      [250, 350, 450, 550],
  'nb1_mtb175_nj7_nt0_nw0' :      [250, 350, 450, 550],
  'nb1_mtb175_nj5t_nt0_nw1t' :    [250, 350, 450, 550, 650],
  'nb1_mtb175_nj5t_nt1t_nw0' :    [250, 350, 450, 550, 650],
  'nb1_mtb175_nj5t_nt1t_nw1t' :   [250, 300, 400, 500],
  'nb2_mtb175_nj5_nt0_nw0' :      [250, 350, 450, 550],
  'nb2_mtb175_nj7_nt0_nw0' :      [250, 350, 450, 550],
  'nb2_mtb175_nj5t_nt0_nw1t' :    [250, 350, 450, 550, 650],
  'nb2_mtb175_nj5t_nt1t_nw0' :    [250, 350, 450, 550, 650],
  'nb2_mtb175_nj5t_nt1t_nw1t' :   [250, 300, 400, 500]
"""

sr_metbins_lm['nb0_highboost'] =        [     450, 550, 650, 750]
#sr_metbins_lm['nb0_highboost_lownj'] =        [     450, 550, 650, 750]
#sr_metbins_lm['nb0_highboost_highnj'] =       [     450, 550, 650, 750]
sr_metbins_lm['nb1_medboost'] =        [300, 400, 500, 600]
#sr_metbins_lm['nb1_medboost_lowptb'] =        [300, 400, 500, 600]
#sr_metbins_lm['nb1_medboost_medptb'] =        [300, 400, 500, 600]
sr_metbins_lm['nb1_highboost'] =            [450, 550, 650, 750]
#sr_metbins_lm['nb1_highboost_lowptb'] =            [450, 550, 650, 750]
#sr_metbins_lm['nb1_highboost_medptb'] =            [450, 550, 650, 750]
sr_metbins_lm['nb2_medboost'] =        [300, 400, 500, 600]
#sr_metbins_lm['nb2_medboost_lowptb'] =        [300, 400, 500, 600]
#sr_metbins_lm['nb2_medboost_medptb'] =        [300, 400, 500, 600]
sr_metbins_lm['nb2_highboost'] =            [450, 550, 650, 750]
#sr_metbins_lm['nb2_highboost_lowptb'] =            [450, 550, 650, 750]
#sr_metbins_lm['nb2_highboost_medptb'] =            [450, 550, 650, 750]

cat_labels = {
  'mtb0_nj5' :              '$\\mtb < 175$~\\GeV, $5 \\leq \\nj < 7$',
  'mtb0_nj7' :              '$\\mtb < 175$~\\GeV, $\\nj \\geq 7$',
  'mtb175_nj5_nt0_nw0' :    '$\\mtb > 175$~\\GeV, $\\nt = 0, \\nw = 0$, $5 \\leq \\nj < 7$',
  'mtb175_nj7_nt0_nw0' :    '$\\mtb > 175$~\\GeV, $\\nt = 0, \\nw = 0$, $\\nj \\geq 7$',
  'mtb175_nj5t_nt0_nw1t' :  '$\\mtb > 175$~\\GeV, $\\nt = 0, \\nw \\geq 1$, $\\nj \\geq 5$',
  'mtb175_nj5t_nt1t_nw0' :  '$\\mtb > 175$~\\GeV, $\\nt \\geq 1, \\nw = 0$, $\\nj \\geq 5$',
  'mtb175_nj5t_nt1t_nw1t' : '$\\mtb > 175$~\\GeV, $\\nt \\geq 1, \\nw \\geq 1$, $\\nj \\geq 5$',
  'nb0_highboost' :         '$\\nb = 0, \\ptisr > 500$~\\GeV',
  'nb0_highboost_lownj' :   '$\\nb = 0, \\ptisr > 500$~\\GeV, $2 \\leq \\nj < 6$',
  'nb0_highboost_highnj' :  '$\\nb = 0, \\ptisr > 500$~\\GeV, $\\nj \\geq 7$',
  'nb1_medboost' :          '$\\nb = 1, 250 < \\ptisr \\leq 500$~\\GeV',
  'nb1_medboost_lowptb' :   '$\\nb = 1, 250 < \\ptisr \\leq 500$~\\GeV, $20 \\leq \\ptb < 40$~\\GeV',
  'nb1_medboost_medptb' :   '$\\nb = 1, 250 < \\ptisr \\leq 500$~\\GeV, $40 \\leq \\ptb < 70$~\\GeV',
  'nb1_highboost' :         '$\\nb = 1, \\ptisr > 500$~\\GeV',
  'nb1_highboost_lowptb' :  '$\\nb = 1, \\ptisr > 500$~\\GeV, $20 \\leq \\ptb < 40$~\\GeV',
  'nb1_highboost_medptb' :  '$\\nb = 1, \\ptisr > 500$~\\GeV, $40 \\leq \\ptb < 70$~\\GeV',
  'nb2_medboost' :          '$\\nb \\geq 2, 250 < \\ptisr \\leq 500$~\\GeV',
  'nb2_medboost_lowptb' :   '$\\nb \\geq 2, 250 < \\ptisr \\leq 500$~\\GeV, $40 \\leq \\ptbonetwo < 100$~\\GeV',
  'nb2_medboost_medptb' :   '$\\nb \\geq 2, 250 < \\ptisr \\leq 500$~\\GeV, $100 \\leq \\ptbonetwo < 160$~\\GeV',
  'nb2_highboost' :         '$\\nb \\geq 2, \\ptisr > 500$~\\GeV',
  'nb2_highboost_lowptb' :  '$\\nb \\geq 2, \\ptisr > 500$~\\GeV, $40 \\leq \\ptbonetwo < 100$~\\GeV',
  'nb2_highboost_medptb' :  '$\\nb \\geq 2, \\ptisr > 500$~\\GeV, $100 \\leq \\ptbonetwo < 160$~\\GeV'
}

ps_hm = {'ttbarplusw':3, 'znunu':4, 'rare':5, 'qcd':6, 'onelepcr':3, 'signal':2}
ps_lm = {'ttbarplusw':3, 'znunu':4, 'rare':5, 'qcd':6, 'onelepcr':3, 'signal':2}
sources = {
  'ttbarplusw' : [('corr_e'               , 'Electron veto'              ),
                  ('corr_mu'              , 'Muon veto'                  ),
                  ('corr_tau'             , 'Tau veto'                   ),
                  #('trig_e'               , 'Electron trigger efficiency'),
                  #('trig_mu'              , 'Muon trigger efficiency'    ),
                  ('eff_b_heavy'          , '\\bq-tagging: heavy flavor' ),
                  ('eff_b_light'          , '\\bq-tagging: light flavor' ),
                  #('eff_t'                , 'Top efficiency'             ),
                  #('fake_t'               ,  'Top mis-tagging'           ),
                  #('lostlep_nt1metintunc' , '\\met integration'          ),
                  #('pu'                   , 'Pileup reweighting'         ),
                  ('scale_j'              , 'Jet energy scale'           ),
                  ('ttbarNorm'            , '\\ttbar~normalization'      ),
                  ('wjetsNorm'            , '\\W+jets normalization'     ),
                  ('ttbarplusw_ttptsyst'  , 'Top \\pt'                   ),
                  ('toppt'                , 'Top \\pt'                   ),
                  ('res_met'              , '\\met resolution'           ),
                  ('ttbarplusw_pdfunc'    , 'pdf/$\\alpha_{\\rm S}$ variation'),
                  ('ttbarplusw_scaleunc'  , '$\\mu_R/\\mu_F$ variation'  ),
                  ('ttbarplusw_wpolunc'   , '\\W~polarization'           ),
                  ('mcstat_ttbarplusw_bin', 'Simulation statistics (SR)'),
                  ('lostlep_bin_onelepcr' , 'Data statistics (CR)'       ),
  ],
  'onelepcr' : [('corr_e'                        , 'Electron veto'        ),
                ('corr_mu'                       , 'Muon veto'        ),
#                 ('corr_tau'                      , 'Tau veto'        ),
                ('mcstat_ttbarplusw_bin_onelepcr', 'Simulation statistics'),
                ('lostlep_bin_onelepcr'          , 'Data statistics'       ),
  ],
  'znunu' : [
#              ('corr_e'                        , 'Electron veto'        ),
#              ('corr_mu'                       , 'Muon veto'        ),
#              ('corr_tau'                      , 'Tau veto'        ),
#              ('eff_b_heavy'                   , '\\bq-tagging: heavy flavor' ),
#              ('eff_b_light'                   , '\\bq-tagging: light flavor' ),
             #('fake_t'                        , 'Top mis-tagging'            ),
#              ('pu'                            , 'Pileup reweighting'         ),
             ('scale_j'                       , 'Jet energy scale'           ),
             ('znunu_rzunc'                   , '$R_{\\cPZ}$'                ),
             ('znunu_zgamma_diff'             , '$\\cPZ/\\gamma$ difference' ),
             ('zfromgamma_mcstat_bin'         , 'Simulation statistics (SR)'),
             ('zfromgamma_mcstat_bin_photoncr', 'Simulation statistics (CR)'),
             ('zfromgamma_stat_bin_photoncr'  , 'Data statistics (CR)'       ),
  ],
  'rare' : [('corr_e'        , 'Electron veto'             ),
           ('corr_mu'       , 'Muon veto'                 ),
           ('corr_tau'      , 'Tau veto'                  ),
           ('eff_b_heavy'   , '\\bq-tagging: heavy flavor'),
           ('eff_b_light'   , '\\bq-tagging: light flavor'),
           #('eff_t'         , 'Top efficiency'            ),
           ('lumi'          , 'Luminosity'                ),
           ('pu'            , 'Pileup reweighting'        ),
           ('scale_j'       , 'Jet energy scale'          ),
           ('rareNorm'       , 'Cross section'             ),
           ('rare_pdfscale'    , 'PDF/Scale variation' ),
           #('rare_scaleunc'  , '$\\mu_R/\\mu_F$ variation' ),
           ('mcstat_rare_bin', 'Simulation statistics'    ),
  ],
  'qcd' : [#('corr_tau'          , 'Tau veto'                  ),
           #('eff_b_heavy'       , '\\bq-tagging: heavy flavor'),
           #('eff_b_light'       , '\\bq-tagging: light flavor'),
           #('fake_t'            , 'Top mis-tagging'           ),
           #('pu'                , 'Pileup reweighting'        ),
           ('scale_j'           , 'Jet energy scale'          ),
           ('qcd_bkgsubunc_'    , 'Background subtraction'    ),
           ('qcd_jetresptailunc', 'Jet response tail'         ),
           ('qcd_met_extrapolation' , '\\met integration'),
           ('qcd_num_tfstatunc' , 'Transfer factor, SR'       ),
           ('qcd_den_tfstatunc' , 'Transfer factor, CR'       ),
           ('qcd_stat_bin_qcdcr', 'Data statistics (CR)'      ),
  ],
  #'signal' : [('corr_l'         , 'Lepton veto'               ),
  #            ('eff_b_fsim'     , 'Fast-sim \\bq-tagging'     ),
  #            ('eff_b_heavy'    , '\\bq-tagging'              ),
  #            ('eff_t'          , 'Top efficiency'            ),
  #            ('lumi'           , 'Luminosity'                ),
  #            ('pu'             , 'Pileup reweighting'        ),
  #            ('scale_j'        , 'Jet energy scale'          ),
  #            ('signal_isrunc'  , 'ISR'                       ),
  #            ('signal_scaleunc', 'Scale'                     ),
  #            ('mcstat_signal'  , 'Simulation statistics'    ),
  #],
} # sources

def main() :
  args = sys.argv[1:]
  if not args:
    print('usage: makeUncTables.py <directory with template datacards> <hm/lm>')
    sys.exit(1)
  inDir = args[0]
  search = args[1]
  
  # LLB 1LCR table
  if search=='hm' :
      print '\n\n\n', '='*5, 'Making onelepcr unc table...', '\n\n'
      print makeTable(inDir,search,sr_metbins_hm,'onelepcr','onelepcr')
  else :
      print '\n\n\n', '='*5, 'Making onelepcr unc table...', '\n\n'
      print makeTable(inDir,search,sr_metbins_lm,'onelepcr','onelepcr')
  
  # tables for the various bkgs
  if search=='hm' :
    for k in ('ttbarplusw', 'znunu', 'qcd', 'rare') :
      print '\n\n\n', '='*5, 'Making', k, 'unc table...', '\n\n'
      print makeTable(inDir,search,sr_metbins_hm,k)
  else :
    for k in ('ttbarplusw', 'znunu', 'qcd', 'rare') :
      print '\n\n\n', '='*5, 'Making', k, 'unc table...', '\n\n'
      print makeTable(inDir,search,sr_metbins_lm,k)
  print '\n\n\n'

  # tables for signal unc
  #print '\n\n\n', '='*5, 'Making signal unc table...', '\n\n'
  #sigs = ('T2tt_700_1', 'T2tt_600_200', 'T2tt_300_200') #, 'T2tt_325_200', 'T2tt_250_150')
  ##sigs = ('T2tb_550_1','T2tb_650_150','T2tb_500_200')
  #for k in sigs :
  #  print '\n\n\n', '='*5, 'Making', k, 'unc table...', '\n\n'
  #  print makeTable(inDir,k)
  #print '\n\n\n'

# piece together blocks for the given bkg/cr
def makeTable(inDir, search, cats, bkg, cr='') :
  s = '\\begin{table}[!!htbp] \n'
  s += '\\begin{center} \n'
  for cat in cats :
    s += makeBlock(inDir, search, cat, bkg, cr)
  s += '\\caption{\\label{tab:' + bkg + '-unc} '
  s += 'All the relative uncertainties per bin for the '
  if bkg == 'ttbarplusw' :
    s += 'lost lepton '
  elif bkg == 'qcd' :
    s += 'QCD '
  elif bkg == 'znunu' :
    s += '\\znunu~'
  elif bkg == 'rare' :
    s += '\\rare~'
  s += 'background estimation. Other than the simulation and data statistics, each one is taken to be correlated across all bins. '
  if bkg == 'znunu' : s += 'For the $R_{\\cPZ}$ correction, bins with different $\\nb$ are correlated separately.} \n'
  else : s += '} \n'
  s += '\\end{center} \n'
  s += '\\end{table} \n'
  return s

# table block for a given bin in (njets, mtb, ntops)
def makeBlock(inDir, search, cat, bkg, cr='') :
  columns = 2*(len(sr_metbins_hm[cat])) + 1 if search == 'hm' else 2*(len(sr_metbins_lm[cat])) + 1
  s = blockHeader(search, cat, columns)
  #sig = ''
  #if 'T2' in bkg :
  #  sig = bkg
  #  bkg = 'signal'
  for source in sources[bkg] :
    #if source[0]=='lostlep_nt1metintunc' and nt!=1 : continue
    #if source[0]=='fake_t'               and nt!=1 : continue
    #if source[0]=='eff_t'                and nt!=1 : continue
    if source[0] in ['toppt', 'res_met', 'trig_e', 'trig_mu', 'ttbarplusw_pdfunc', 'ttbarplusw_scaleunc', 'ttbarplusw_wpolunc'] and search == 'hm' : continue
    elif source[0] in ['ttbarplusw_ttptsyst'] and search == 'lm' : continue
    s += source[1]
    #if cr=='onelepcr' and nt==1 : # combine met bins for nT=1 for the onelepcr
    #  s += ' & \\multicolumn{5}{c|}{' + getUnc(inDir,source[0],bkg,binsMet[0],nj,1,nt,mtb,cr,sig) + '}  \\\\ \n'
    #  continue
    if search == 'hm' :
      for nb in ('nb1','nb2') :
        for metbin in sr_metbins_hm[cat] :
          s += ' & ' + getUnc(inDir,search,source[0],bkg,metbin,nb+'_'+cat,cr)
    else :
      if 'nb0' in cat :
        for nj in ('lownj','highnj') :
          for metbin in sr_metbins_lm[cat] :
            s += ' & ' + getUnc(inDir,search,source[0],bkg,metbin,cat+'_'+nj,cr)
      else :
        for ptb in ('lowptb','medptb') :
          for metbin in sr_metbins_lm[cat] :
            s += ' & ' + getUnc(inDir,search,source[0],bkg,metbin,cat+'_'+ptb,cr)
      #for metbin in sr_metbins_lm[cat] :
      #  s += ' & ' + getUnc(inDir,search,source[0],bkg,metbin,cat,cr)
    s += ' \\\\ \n'
  s += '\\hline\n'
  s += '\\end{tabular} \n'
  s += '} \n'
  return s

# returns the datacard filename for the given bin
#   - use 'sig' to get the datacard for a signal region. if none is given, the template file will be used
#   - use 'cr' to get the file for the CR
def getFileName(inDir, search, metbin, cat, cr='', sig='') :
  fname = 'bin_'+str(metbin)+'_'+cat+'.txt'
  if cr=='onelepcr' : fname = fname.replace('bin_','onelepcr_bin_onelepcr_')
  if 'T2' in sig : 
    fname = sig+'_'+fname
    return os.path.join(inDir,sig,fname)
  if search == 'hm' :
    fname = 'T2tt_850_100_'+fname
    fname = os.path.join(inDir,'T2tt_850_100',fname)
  else :
    fname = 'T2fbd_375_325_'+fname
    fname = os.path.join(inDir,'T2fbd_375_325',fname)
  return fname

# get and properly format the number for the given bkg, bin
def getUnc(inDir, search, unc, process, metbin, cat, cr='', sig='') :
  if unc == 'lumi' : return '6.2\\%'
  u = getRawUnc(inDir,search,unc,process,metbin,cat,cr,sig)
  if u == '-' or u == ' ' : return u
  return str(int(round(u*100,0)))+'\\%'

# gets the unc for a given bin, bkg as a float or returns '-' if it doesn't exist
def getRawUnc(inDir, search, unc, process, metbin, cat, cr='', sig='') :
  if unc == 'lumi' : return 0.027
  fname = getFileName(inDir,search,metbin,cat,cr,sig)
#   print 'opening file %s'%fname
  if not os.path.exists(fname) : return ' '
  f = open(fname)
  ul = ''
  for l in f:
    if unc in l :
      if unc == 'zfromgamma_mcstat_bin' and 'photon' in l: continue
      ul = l.strip()
  f.close()
  if ul == '' : return '-'
  ul = ul.split() 
  u = 0
  if ul[1] == 'lnN':
    u = ul[ps_hm[process]] if search == 'hm' else ul[ps_lm[process]]
    if u == '-' : return u
    u = (float(u)-1)
  elif ul[1] == 'gmN' :
    s = ul[ps_hm[process]+1] if search == 'hm' else ul[ps_lm[process]+1]
    if s == '-' : return s
    if s == '0' : return 0
    n = float(ul[2])
    u = sqrt(n)/n
  elif ul[1] == 'lnU' :
    #if nt==1 : n = getDataYield(inDir,process,250,nj,1,nt,mtb,'onelepcr')
    #else     : n = getDataYield(inDir,process,met,nj,1,nt,mtb,'onelepcr')
    n = getDataYield(inDir,search,process,metbin,cat,'onelepcr')
    if n<1 : n=1
    u = sqrt(n)/n
  else :
    print '!!!!! Unknown unc type:', ul[1]
    print '!!!!! Needs to be added to getRawUnc'
    return 0
  return u

# returns the 'observation' number from the datacard for the given bin
def getDataYield(inDir, search, process, metbin, cat, cr='', sig='') :
  fname = getFileName(inDir,search,metbin,cat,cr,sig)
  if not os.path.exists(fname) : return 0
  f = open(fname)
  n = ''
  for l in f:
    if len(l) < 1 : continue
    if not 'observation' in l : continue
    n = l.split()[1]
  f.close()
  if n=='' : return '???' # this shouldn't happen unless a file doesn't exist or doesn't have an observation number
  return int(n)

# puts together the bin header for bins of nJets, mtb, nTop, nB
def blockHeader(search, cat, columns) :
  s  = '\\resizebox*{0.9\\textwidth}{!}{ \n'
  s += '\\begin{tabular}{|l|'
  s += '|c'*((columns-1)/2)
  s += '|'
  s += '|c'*((columns-1)/2)
  s += '|} \n'
  s += '\\hline\n'
  s += '\\multicolumn{'+str(columns)+'}{|c|}{'
  s += cat_labels[cat]
  s += '} \\\\ \n'
  s += '\\hline\n'
  if search == 'hm' :
    s += '$\\nb$ & \\multicolumn{'+str((columns-1)/2)+'}{c||}{'
    s += '$1$} & \\multicolumn{'+str((columns-1)/2)+'}{c|}{$\\geq 2$} \\\\ \n'
  elif 'nb0' in cat :
    s += '$\\nj$ & \\multicolumn{'+str((columns-1)/2)+'}{c||}{'
    s += '$2-5$} & \\multicolumn{'+str((columns-1)/2)+'}{c|}{$\\geq 6$} \\\\ \n'
  elif 'nb1' in cat :
    s += '$\\ptb$ [\\GeV] & \\multicolumn{'+str((columns-1)/2)+'}{c||}{'
    s += '$20-40$} & \\multicolumn{'+str((columns-1)/2)+'}{c|}{$40-70$} \\\\ \n'
  else :
    s += '$\\ptbonetwo$  [\\GeV]& \\multicolumn{'+str((columns-1)/2)+'}{c||}{'
    s += '$40-100$} & \\multicolumn{'+str((columns-1)/2)+'}{c|}{$100-160$} \\\\ \n'
  s += '\\hline\n'
  s += '\\met [\\GeV] '
  if search == 'hm' :
    metbins = sr_metbins_hm[cat]
    for ibin in range(len(metbins)-1) :
      s += ' & ' + '$-$'.join([str(metbins[ibin]),str(metbins[ibin+1])])
    s += ' & $>$ ' + str(metbins[-1])
    for ibin in range(len(metbins)-1) :
      s += ' & ' + '$-$'.join([str(metbins[ibin]),str(metbins[ibin+1])])
    s += ' & $>$ ' + str(metbins[-1]) + '\\\\ \n'
  else :
    metbins = sr_metbins_lm[cat]
    for ibin in range(len(metbins)-1) :
      s += ' & ' + '$-$'.join([str(metbins[ibin]),str(metbins[ibin+1])])
    s += ' & $>$ ' + str(metbins[-1])
    for ibin in range(len(metbins)-1) :
      s += ' & ' + '$-$'.join([str(metbins[ibin]),str(metbins[ibin+1])])
    s += ' & $>$ ' + str(metbins[-1]) + '\\\\ \n'
  s += '\\hline\n' 
  return s
  
if __name__=='__main__' : main()
