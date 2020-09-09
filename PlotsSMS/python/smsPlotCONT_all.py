import ROOT as rt
from array import *
from sms import *
from color import *
from smsPlotABS import *

# class producing the 2D plot with contours
class smsPlotCONT_all(smsPlotABS):

    def __init__(self, modelname, histo_T2tt, obsLimits_T2tt, expLimits_T2tt, histo_T2bW, obsLimits_T2bW, expLimits_T2bW, histo_T2tb, obsLimits_T2tb, expLimits_T2tb, histo_T2fbd, obsLimits_T2fbd, expLimits_T2fbd, histo_T2bWC, obsLimits_T2bWC, expLimits_T2bWC, histo_T2cc, obsLimits_T2cc, expLimits_T2cc, energy, lumi, preliminary, label):
        self.standardDef(modelname, histo_T2tt, obsLimits_T2tt, expLimits_T2tt, energy, lumi, preliminary)
        self.LABEL = label
        # canvas for the plot
        self.c = rt.TCanvas("cCONT_%s" %label,"cCONT_%s" %label,600,600)
        self.histo_T2tt = self.emptyHistogram(histo_T2tt)
        # canvas style
        self.setStyle()

    # empty copy of the existing histogram
    def emptyHistogram(self, h):
        return rt.TH2D("%sEMPTY" %h['histogram'].GetName(), "%sEMPTY" %h['histogram'].GetTitle(),
                       h['histogram'].GetXaxis().GetNbins(), h['histogram'].GetXaxis().GetXmin(), h['histogram'].GetXaxis().GetXmax(),
                       h['histogram'].GetYaxis().GetNbins(), h['histogram'].GetYaxis().GetXmin(), h['histogram'].GetYaxis().GetXmax())
                                       
    def Draw(self):
        self.emptyHisto.Draw()
        self.histo_T2tt.Draw("SAME")
        if self.model.diagOn:
            self.DrawDiagonal()
        self.DrawObsArea()
        self.DrawLines()
        self.DrawText()
        self.DrawLegend()

    def DrawObsArea(self):
        # add points to observed to close area
        # this will disappear
        self.OBS['nominal'].SetPoint(self.OBS['nominal'].GetN(), 1300,-1300)
        self.OBS['nominal'].SetPoint(self.OBS['nominal'].GetN(), -1300,-1300)
        # observed

        trasparentColor = rt.gROOT.GetColor(color(self.OBS['colorArea']))
        trasparentColor.SetAlpha(0.5)
        self.OBS['nominal'].SetFillColor(color(self.OBS['colorArea']))
        self.OBS['nominal'].SetLineStyle(1)
        # DRAW AREAS
        self.OBS['nominal'].Draw("FSAME")
