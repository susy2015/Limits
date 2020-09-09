import sys
from inputFile import *
from inputFile_all import *
from smsPlotXSEC import *
from smsPlotXSEC_all import *
from smsPlotCONT import *
from smsPlotBrazil import *

if __name__ == '__main__':
    # read input arguments
    filename = sys.argv[1]
    modelname = sys.argv[1].split("/")[-1].split("_")[0]
    analysisLabel = sys.argv[1].split("/")[-1].split("_")[1]
    outputname = sys.argv[2]
    allPlots = True if "T2All" in modelname else False

    # read the config file
    fileIN = inputFile(filename) if not allPlots else inputFile_all(filename)    
    signal = ['T2tt', 'T2bW', 'T2tb', 'T2fbd', 'T2bWC', 'T2cc']

    HISTOGRAM = {}
    OBSERVED = {}
    EXPECTED = {}
    if allPlots:
        HISTOGRAM = {'T2tt': fileIN.HISTOGRAM_T2tt, 'T2bW': fileIN.HISTOGRAM_T2bW, 'T2tb': fileIN.HISTOGRAM_T2tb, 'T2fbd': fileIN.HISTOGRAM_T2fbd, 'T2bWC': fileIN.HISTOGRAM_T2bWC, 'T2cc': fileIN.HISTOGRAM_T2cc}
        OBSERVED =  {'T2tt': fileIN.OBSERVED_T2tt,  'T2bW': fileIN.OBSERVED_T2bW,  'T2tb': fileIN.OBSERVED_T2tb,  'T2fbd': fileIN.OBSERVED_T2fbd,  'T2bWC': fileIN.OBSERVED_T2bWC,  'T2cc': fileIN.OBSERVED_T2cc}
        EXPECTED =  {'T2tt': fileIN.EXPECTED_T2tt,  'T2bW': fileIN.EXPECTED_T2bW,  'T2tb': fileIN.EXPECTED_T2tb,  'T2fbd': fileIN.EXPECTED_T2fbd,  'T2bWC': fileIN.EXPECTED_T2bWC,  'T2cc': fileIN.EXPECTED_T2cc}

    # classic temperature histogra
    if not allPlots:
        xsecPlot = smsPlotXSEC(modelname, fileIN.HISTOGRAM, fileIN.OBSERVED, fileIN.EXPECTED, fileIN.ENERGY, fileIN.LUMI, fileIN.PRELIMINARY, "")
        xsecPlot.Draw()
        xsecPlot.Save("%sXSEC" %outputname)
    else:
        xsecPlot = smsPlotXSEC_all(modelname, HISTOGRAM, OBSERVED, EXPECTED, fileIN.ENERGY, fileIN.LUMI, fileIN.PRELIMINARY, "", signal)
        xsecPlot.Draw()
        xsecPlot.Save("%sXSEC" %outputname)

    # brazilian flag (show only 1 sigma)
    #brazilPlot = smsPlotBrazil(modelname, fileIN.HISTOGRAM, fileIN.OBSERVED, fileIN.EXPECTED, fileIN.ENERGY, fileIN.LUMI, fileIN.PRELIMINARY, "")
    #brazilPlot.Draw()
    #brazilPlot.Save("%sBAND" %outputname)
