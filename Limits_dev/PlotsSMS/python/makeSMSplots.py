import sys
from inputFile import *
from inputFile_Cut import *
from inputFile_Cut_v2 import *
from smsPlotXSEC import *
from smsPlotXSEC_Cut import *
from smsPlotXSEC_Cut_v2 import *
from smsPlotXSEC_Sig import *
from smsPlotXSEC_Sig_v2 import *
from smsPlotCONT import *
from smsPlotBrazil import *

if __name__ == '__main__':
    # read input arguments
    filename = sys.argv[1]
    modelname = sys.argv[1].split("/")[-1].split("_")[0]
    analysisLabel = sys.argv[1].split("/")[-1].split("_")[1]
    outputname = sys.argv[2]

    # read the config file
    #fileIN = inputFile(filename)
    fileIN = inputFile_Cut(filename)
    fileIN_v2 = inputFile_Cut_v2(filename)
    
    # classic temperature histogra
    xsecPlot = smsPlotXSEC(modelname, fileIN.HISTOGRAM, fileIN.OBSERVED, fileIN.EXPECTED, fileIN.ENERGY, fileIN.LUMI, fileIN.PRELIMINARY, "")
    xsecPlot.Draw()
    xsecPlot.Save("%sXSEC_original" %outputname)

    print fileIN.EXPECTED
    print fileIN.EXPECTED_CUT

    # plot with two different expected limits
    xsecPlot = smsPlotXSEC_CUT(modelname, fileIN.HISTOGRAM, fileIN.OBSERVED, fileIN.EXPECTED, fileIN.EXPECTED_CUT, fileIN.ENERGY, fileIN.LUMI, fileIN.PRELIMINARY, "")
    xsecPlot.Draw()
    xsecPlot.Save("%sXSEC" %outputname)

    # plot with two different expected limits and difference between the two limits 
    xsecPlot_v2 = smsPlotXSEC_CUT_v2(modelname, fileIN_v2.HISTOGRAM, fileIN_v2.HISTOGRAM_CUT, fileIN_v2.OBSERVED, fileIN_v2.EXPECTED, fileIN_v2.EXPECTED_CUT, fileIN_v2.ENERGY, fileIN_v2.LUMI, fileIN_v2.PRELIMINARY, "")
    Method = 2
    xsecPlot_v2.CompHist(Method)
    xsecPlot_v2.Draw(Method)
    if Method == 0: xsecPlot_v2.Save("%sRelDiff_XSEC_comp" %outputname)
    if Method == 1: xsecPlot_v2.Save("%sAbsDiff_XSEC_comp" %outputname)
    if Method == 2: xsecPlot_v2.Save("%sPercDiff_XSEC_comp" %outputname)
    if Method == 3: xsecPlot_v2.Save("%sRelSqrtDiff_XSEC_comp" %outputname)

    # plot with two different expected significance
    xsecPlot_sig = smsPlotXSEC_SIG(modelname, fileIN_v2.HISTOGRAM_SIG, fileIN_v2.OBSERVED, fileIN_v2.EXPECTED, fileIN_v2.EXPECTED_CUT, fileIN_v2.ENERGY, fileIN_v2.LUMI, fileIN_v2.PRELIMINARY, "")
    xsecPlot_sig.CompHist()
    xsecPlot_sig.Draw()
    xsecPlot_sig.Save("%sSIGNIFICANCE" %outputname)

    # plot with two different expected significance and difference between the two significances
    xsecPlot_sig_v2 = smsPlotXSEC_SIG_v2(modelname, fileIN_v2.HISTOGRAM_SIG, fileIN_v2.HISTOGRAM_SIG_CUT, fileIN_v2.OBSERVED, fileIN_v2.EXPECTED, fileIN_v2.EXPECTED_CUT, fileIN_v2.ENERGY, fileIN_v2.LUMI, fileIN_v2.PRELIMINARY, "")
    xsecPlot_sig_v2.CompHist(Method)
    xsecPlot_sig_v2.Draw(Method)
    if Method == 0: xsecPlot_sig_v2.Save("%sRelDiff_SIGNIFICANCE_comp" %outputname)
    if Method == 1: xsecPlot_sig_v2.Save("%sAbsDiff_SIGNIFICANCE_comp" %outputname)
    if Method == 2: xsecPlot_sig_v2.Save("%sPercDiff_SIGNIFICANCE_comp" %outputname)
    if Method == 3: xsecPlot_sig_v2.Save("%sRelSqrtDiff_SIGNIFICANCE_comp" %outputname)

    # only lines
    #contPlot = smsPlotCONT(modelname, fileIN.HISTOGRAM, fileIN.OBSERVED, fileIN.EXPECTED, fileIN.ENERGY, fileIN.LUMI, fileIN.PRELIMINARY, "")
    #contPlot.Draw()
    #contPlot.Save("%sCONT" %outputname)

    # brazilian flag (show only 1 sigma)
    #brazilPlot = smsPlotBrazil(modelname, fileIN.HISTOGRAM, fileIN.OBSERVED, fileIN.EXPECTED, fileIN.ENERGY, fileIN.LUMI, fileIN.PRELIMINARY, "")
    #brazilPlot.Draw()
    #brazilPlot.Save("%sBAND" %outputname)
