import ROOT as rt
import math
from array import *
from sms import *
from smsPlotABS_Sig_v2 import *

# class producing the 2D plot with xsec colors
class smsPlotXSEC_SIG_v2(smsPlotABS):

    def __init__(self, modelname, histo, histo_cut, obsLimits, expLimits, expLimits_Cut, energy, lumi, preliminary, label):
        self.standardDef(modelname, histo, histo_cut, obsLimits, expLimits, expLimits_Cut, energy, lumi, preliminary)
        self.LABEL = label
        # canvas for the plot
        self.c = rt.TCanvas("cCONT_%s" %label,"cCONT_%s" %label,600,600)
        self.histo = histo['histogram_sig']
        self.histo_cut = histo_cut['histogram_sig_cut']
        # canvas style
        self.setStyle()
        self.setStyleCOLZ()

    # define the plot canvas
    def setStyleCOLZ(self):        
        # set z axis
        self.histo.GetZaxis().SetLabelFont(42)
        self.histo.GetZaxis().SetTitleFont(42)
        self.histo.GetZaxis().SetLabelSize(0.035)
        self.histo.GetZaxis().SetTitleSize(0.035)
        self.histo.SetMinimum(self.model.Zmin)
        self.histo.SetMaximum(self.model.Zmax)

        self.histo_cut.GetZaxis().SetLabelFont(42)
        self.histo_cut.GetZaxis().SetTitleFont(42)
        self.histo_cut.GetZaxis().SetLabelSize(0.035)
        self.histo_cut.GetZaxis().SetTitleSize(0.035)
        self.histo_cut.SetMinimum(self.model.Zmin)
        self.histo_cut.SetMaximum(self.model.Zmax)

        # define the palette for z axis
        NRGBs = 5
        NCont = 255
        stops = array("d",[0.00, 0.34, 0.61, 0.84, 1.00])
        red= array("d",[0.50, 0.50, 1.00, 1.00, 1.00])
        green = array("d",[ 0.50, 1.00, 1.00, 0.60, 0.50])
        blue = array("d",[1.00, 1.00, 0.50, 0.40, 0.50])
        rt.TColor.CreateGradientColorTable(NRGBs, stops, red, green, blue, NCont)
        rt.gStyle.SetNumberContours(NCont)
        
        self.c.cd()
        self.histo.Draw("colz")
        self.histo_cut.Draw("colz")
        
        rt.gPad.Update()
        palette = self.histo.GetListOfFunctions().FindObject("palette")
        palette = self.histo_cut.GetListOfFunctions().FindObject("palette")
        palette.SetX1NDC(1.-0.18)
        palette.SetY1NDC(0.14)
        palette.SetX2NDC(1.-0.13)
        palette.SetY2NDC(1.-0.08)
        palette.SetLabelFont(42)
        palette.SetLabelSize(0.035)

    def DrawPaletteLabel(self, Method):
        if Method == 0: textCOLZ = rt.TLatex(0.98,0.15,"#frac{Sig_{cut} - Sig}{Sig}")
        if Method == 1: textCOLZ = rt.TLatex(0.98,0.15,"Sig_{cut} - Sig")
        if Method == 2: textCOLZ = rt.TLatex(0.98,0.15,"Sig_{cut}/Sig")
        if Method == 3: textCOLZ = rt.TLatex(0.98,0.15,"#frac{Sig_{cut} - Sig}{#sqrt{Sig}}")
        textCOLZ.SetNDC()
        #textCOLZ.SetTextAlign(13)
        textCOLZ.SetTextFont(42)
        textCOLZ.SetTextSize(0.045)
        textCOLZ.SetTextAngle(90)
        textCOLZ.Draw()
        self.c.textCOLZ = textCOLZ

    def CompHist(self, Method):
	Value = []
	for ibinx in range(1, self.histo.GetNbinsX()+1):
		for ibiny in range(1, self.histo.GetNbinsY()+1):
			if Method == 0: 
				if self.histo.GetBinContent(ibinx, ibiny) != 0: newVal = (self.histo_cut.GetBinContent(ibinx, ibiny) - self.histo.GetBinContent(ibinx, ibiny))/self.histo.GetBinContent(ibinx, ibiny) # Relative Diference Nomalized
				else: 						newVal = 0
			if Method == 1: newVal = (self.histo_cut.GetBinContent(ibinx, ibiny) - self.histo.GetBinContent(ibinx, ibiny)) #Absolute value of Diff
			if Method == 2: 
				if self.histo.GetBinContent(ibinx, ibiny) != 0: newVal = (self.histo_cut.GetBinContent(ibinx, ibiny)/self.histo.GetBinContent(ibinx, ibiny)) #Percentage 
				else:						newVal = 0
			if Method == 3: 
				if self.histo.GetBinContent(ibinx, ibiny) != 0: newVal = (self.histo_cut.GetBinContent(ibinx, ibiny) - self.histo.GetBinContent(ibinx, ibiny))/math.sqrt(self.histo.GetBinContent(ibinx, ibiny))
				else:						newVal = 0
			#print("X: %f, Y: %f, Sigma_cut: %f, Sigma: %f, newVal: %f" %(ibinx, ibiny, self.histo_cut.GetBinContent(ibinx, ibiny), self.histo.GetBinContent(ibinx, ibiny), newVal))
			self.histo.SetBinContent(ibinx, ibiny, newVal)
			Value.append(newVal)
	#self.histo.SetMaximum(max(Value))
	#self.histo.SetMinimum(min(Value))
	if Method == 0:
		self.histo.SetMaximum(0.1)
		self.histo.SetMinimum(-0.1)
	if Method == 1:
		self.histo.SetMaximum(0.1)
		self.histo.SetMinimum(-0.1)
	if Method == 2:
		self.histo.SetMaximum(1.10)
		self.histo.SetMinimum(0.9)
	if Method == 3:
		self.histo.SetMaximum(0.1)
		self.histo.SetMinimum(-0.1)
            
    def Draw(self, Method):
        self.emptyHisto.GetXaxis().SetRangeUser(self.model.Xmin, self.model.Xmax)
        self.emptyHisto.GetYaxis().SetRangeUser(self.model.Ymin, self.model.Ymax)
        self.emptyHisto.Draw()	
        self.histo.Draw("COLZSAME")
        #self.DrawLines()
        if self.model.diagOn:
            self.DrawDiagonal()
        self.DrawText()
        #self.DrawLegend()
        self.DrawPaletteLabel(Method)
        
