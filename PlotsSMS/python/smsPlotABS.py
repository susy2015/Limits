import ROOT as rt
from array import *
from sms import *
from color import *
import CMS_lumi
import math
class smsPlotABS(object):
    # modelname is the sms name (see sms.py)
    # histo is the 2D xsec map
    # obsLimits is a list of opbserved limits [NOMINAL, +1SIGMA, -1SIGMA]
    # expLimits is a list of expected limits [NOMINAL, +1SIGMA, -1SIGMA]
    # label is a label referring to the analysis (e.g. RA1, RA2, RA2b, etc)

    def __init__(self, modelname, histo, obsLimits, expLimits, energy, lumi, preliminary, label):
        self.standardDef(modelname, histo, obsLimits, expLimits, energy, lumi, preliminary)
        self.LABEL = label
        self.c = rt.TCanvas("cABS_%s" %label,"cABS_%s" %label,300,300)
        self.histo = histo

    def standardDef(self, modelname, histo, obsLimits, expLimits, energy, lumi, preliminary):
        # which SMS?
        self.model = sms(modelname)
        self.OBS = obsLimits
        self.EXP = expLimits
        self.lumi = lumi
        self.energy = energy
        self.preliminary = preliminary
        # create the reference empty histo
        self.emptyhisto = self.emptyHistogramFromModel()

    def emptyHistogramFromModel(self):
        self.emptyHisto = rt.TH2D("emptyHisto", "", 1, self.model.Xmin, self.model.Xmax, 1, self.model.Ymin, self.model.Ymax)
        
    # define the plot canvas
    def setStyle(self):
        # canvas style
        rt.gStyle.SetOptStat(0)
        rt.gStyle.SetOptTitle(0)        

        self.c.SetLogz()
        self.c.SetTickx(1)
        self.c.SetTicky(1)

        self.c.SetRightMargin(0.19)
        self.c.SetTopMargin(0.08)
        self.c.SetLeftMargin(0.14)
        self.c.SetBottomMargin(0.14)

        # set x axis
        self.emptyHisto.GetXaxis().SetLabelFont(42)
        self.emptyHisto.GetXaxis().SetLabelSize(0.035)
        self.emptyHisto.GetXaxis().SetTitleFont(42)
        self.emptyHisto.GetXaxis().SetTitleSize(0.05)
        self.emptyHisto.GetXaxis().SetTitleOffset(1.2)
        self.emptyHisto.GetXaxis().SetTitle(self.model.sParticle)
        if self.model.modelname in ('T2tb', 'T2bW'):
            self.emptyHisto.GetXaxis().SetNdivisions(505)
        #self.emptyHisto.GetXaxis().CenterTitle(True)

        # set y axis
        self.emptyHisto.GetYaxis().SetLabelFont(42)
        self.emptyHisto.GetYaxis().SetLabelSize(0.035)
        self.emptyHisto.GetYaxis().SetTitleFont(42)
        self.emptyHisto.GetYaxis().SetTitleSize(0.05)
        self.emptyHisto.GetYaxis().SetTitleOffset(1.3)
        self.emptyHisto.GetYaxis().SetTitle(self.model.LSP)
        #self.emptyHisto.GetYaxis().CenterTitle(True)
                
    def DrawText(self):
        #redraw axes
        self.c.RedrawAxis()
        # white background
        graphWhite = rt.TGraph(5)
        graphWhite.SetName("white")
        graphWhite.SetTitle("white")
        graphWhite.SetFillColor(rt.kWhite)
        graphWhite.SetFillStyle(1001)
        graphWhite.SetLineColor(rt.kBlack)
        graphWhite.SetLineStyle(1)
        graphWhite.SetLineWidth(3)
        graphWhite.SetPoint(0,self.model.Xmin, self.model.Ymax)
        graphWhite.SetPoint(1,self.model.Xmax, self.model.Ymax)
        graphWhite.SetPoint(2,self.model.Xmax, self.model.Ymax*0.75)
        graphWhite.SetPoint(3,self.model.Xmin, self.model.Ymax*0.75)
        #graphWhite.SetPoint(2,self.model.Xmax, self.model.Ymax*0.8)
        #graphWhite.SetPoint(3,self.model.Xmin, self.model.Ymax*0.8)
        graphWhite.SetPoint(4,self.model.Xmin, self.model.Ymax)
        graphWhite.Draw("FSAME")
        graphWhite.Draw("LSAME")
        self.c.graphWhite = graphWhite
       	CMS_lumi.writeExtraText = 1
	CMS_lumi.extraText = "Preliminary"
	#CMS_lumi.lumi_13TeV="2.3 fb^{-1}"
	CMS_lumi.lumi_13TeV="35.9 fb^{-1}"

	CMS_lumi.lumi_sqrtS = "13 TeV"  
	iPos=0
	CMS_lumi.CMS_lumi(self.c,4, iPos)
        # CMS LABEL
        textCMS = rt.TLatex(0.25,0.96,"  %s " %(self.preliminary))
        textCMS.SetNDC()
        textCMS.SetTextAlign(13)
        textCMS.SetTextFont(52)
        textCMS.SetTextSize(0.038)
        #textCMS.Draw()
        self.c.textCMS = textCMS
        # MODEL LABEL
        if self.model.extraText :
            textModelLabel= rt.TLatex(0.15,0.915,"%s" %self.model.label)
        else :
            textModelLabel = rt.TLatex(0.15, 0.90, "%s   NLO+NLL exclusion" % self.model.label)
        textModelLabel.SetNDC()
        textModelLabel.SetTextAlign(13)
        textModelLabel.SetTextFont(42)
        textModelLabel.SetTextSize(0.035)
        #textModelLabel.SetTextSize(0.03)
        textModelLabel.Draw()
        self.c.textModelLabel = textModelLabel
        # NLO NLL XSEC
        textNLONLL = rt.TLatex(0.15, 0.855, "NLO+NLL exclusion")
        textNLONLL.SetNDC()
        textNLONLL.SetTextAlign(13)
        textNLONLL.SetTextFont(42)
        textNLONLL.SetTextSize(0.035)
        if self.model.extraText :
            textNLONLL.Draw()
        self.c.textNLONLL = textNLONLL

    def Save(self,label):
        # save the output
        self.c.SaveAs("%s.pdf" %label)
        
    def DrawLegend(self):
        xRange = self.model.Xmax-self.model.Xmin
        yRange = self.model.Ymax-self.model.Ymin
        
        LObs = rt.TGraph(2)
        LObs.SetName("LObs")
        LObs.SetTitle("LObs")
        LObs.SetLineColor(color(self.OBS['colorLine']))
        LObs.SetLineStyle(1)
        LObs.SetLineWidth(4)
        LObs.SetMarkerStyle(20)
        if self.model.extraText :
            LObs.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.50*yRange/100*10)
            LObs.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.50*yRange/100*10)
        else :
            LObs.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.35*yRange/100*10)
            LObs.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.35*yRange/100*10)

        LObsP = rt.TGraph(2)
        LObsP.SetName("LObsP")
        LObsP.SetTitle("LObsP")
        LObsP.SetLineColor(color(self.OBS['colorLine']))
        LObsP.SetLineStyle(1)
        LObsP.SetLineWidth(2)
        LObsP.SetMarkerStyle(20)
        if self.model.extraText :
            LObsP.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.35*yRange/100*10)
            LObsP.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.35*yRange/100*10)
        else :
            LObsP.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.20*yRange/100*10)
            LObsP.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.20*yRange/100*10)

        LObsM = rt.TGraph(2)
        LObsM.SetName("LObsM")
        LObsM.SetTitle("LObsM")
        LObsM.SetLineColor(color(self.OBS['colorLine']))
        LObsM.SetLineStyle(1)
        LObsM.SetLineWidth(2)
        LObsM.SetMarkerStyle(20)
        if self.model.extraText :
            LObsM.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.65*yRange/100*10)
            LObsM.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.65*yRange/100*10)
        else :
            LObsM.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.50*yRange/100*10)
            LObsM.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.50*yRange/100*10)

        if self.model.extraText :
            textObs = rt.TLatex(self.model.Xmin+11*xRange/100, self.model.Ymax-1.65*yRange/100*10, "Observed #pm 1 #sigma_{theory}")
        else :
            textObs = rt.TLatex(self.model.Xmin+11*xRange/100, self.model.Ymax-1.50*yRange/100*10, "Observed #pm 1 #sigma_{theory}")
        #textObs = rt.TLatex(self.model.Xmin+11*xRange/100, self.model.Ymax-1.50*yRange/100*10, "Observed")
        textObs.SetTextFont(42)
        textObs.SetTextSize(0.040)
        textObs.Draw()
        self.c.textObs = textObs

        if self.model.extraText :
            textExtra1 = rt.TLatex(self.model.Xmin+65*xRange/100, self.model.Ymax-1.65*yRange/100*10, self.model.extratext1)
            textExtra1.SetTextFont(42)
            textExtra1.SetTextSize(0.030)
            textExtra1.Draw()
            self.c.textExtra1 = textExtra1

        LExpP = rt.TGraph(2)
        LExpP.SetName("LExpP")
        LExpP.SetTitle("LExpP")
        LExpP.SetLineColor(color(self.EXP['colorLine']))
        LExpP.SetLineStyle(7)
        LExpP.SetLineWidth(2)  
        #LExpP.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.20*yRange/100*10)
        #LExpP.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.20*yRange/100*10)
        if self.model.extraText :
            LExpP.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-2.00*yRange/100*10)
            LExpP.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-2.00*yRange/100*10)
        else :
            LExpP.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.85*yRange/100*10)
            LExpP.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.85*yRange/100*10)

        LExp = rt.TGraph(2)
        LExp.SetName("LExp")
        LExp.SetTitle("LExp")
        LExp.SetLineColor(color(self.EXP['colorLine']))
        LExp.SetLineStyle(7)
        LExp.SetLineWidth(4)
        #LExp.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.35*yRange/100*10)
        #LExp.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.35*yRange/100*10)
        if self.model.extraText :
            LExp.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-2.15*yRange/100*10)
            LExp.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-2.15*yRange/100*10)
        else :
            LExp.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-2.00*yRange/100*10)
            LExp.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-2.00*yRange/100*10)
        
        LExpM = rt.TGraph(2)
        LExpM.SetName("LExpM")
        LExpM.SetTitle("LExpM")
        LExpM.SetLineColor(color(self.EXP['colorLine']))
        LExpM.SetLineStyle(7)
        LExpM.SetLineWidth(2)  
        #LExpM.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-1.50*yRange/100*10)
        #LExpM.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.50*yRange/100*10)
        if self.model.extraText :
            LExpM.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-2.30*yRange/100*10)
            LExpM.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-2.30*yRange/100*10)
        else :
            LExpM.SetPoint(0,self.model.Xmin+3*xRange/100, self.model.Ymax-2.15*yRange/100*10)
            LExpM.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-2.15*yRange/100*10)

        if self.model.extraText :
            textExp = rt.TLatex(self.model.Xmin+11*xRange/100, self.model.Ymax-2.30*yRange/100*10, "Expected #pm 1 #sigma_{experiment}")
        else :
            textExp = rt.TLatex(self.model.Xmin+11*xRange/100, self.model.Ymax-2.15*yRange/100*10, "Expected #pm 1 #sigma_{experiment}")
        #textExp = rt.TLatex(self.model.Xmin+11*xRange/100, self.model.Ymax-1.50*yRange/100*10, "Expected #pm 1 #sigma_{experiment}")
        textExp.SetTextFont(42)
        textExp.SetTextSize(0.040)
        textExp.Draw()
        self.c.textExp = textExp

        if self.model.extraText :
            textExtra2 = rt.TLatex(self.model.Xmin+65*xRange/100, self.model.Ymax-2.30*yRange/100*10, self.model.extratext2)
            textExtra2.SetTextFont(42)
            textExtra2.SetTextSize(0.030)
            textExtra2.Draw()
            self.c.textExtra2 = textExtra2

        LObs.Draw("LSAME")
        LObsM.Draw("LSAME")
        LObsP.Draw("LSAME")
        LExp.Draw("LSAME")
        LExpM.Draw("LSAME")
        LExpP.Draw("LSAME")
        
        self.c.LObs = LObs
        self.c.LObsM = LObsM
        self.c.LObsP = LObsP
        self.c.LExp = LExp
        self.c.LExpM = LExpM
        self.c.LExpP = LExpP

    def DrawDiagonal(self):
        if self.model.modelname == 'T2tt':
            diagLineMW = rt.TGraph(2)
            diagLineMW.SetName("diagLineMW")
            diagLineMW.SetTitle("diagLineMW")
            diagLineMW.SetLineColor(rt.kGray)
            diagLineMW.SetLineStyle(2)
            diagLineMW.SetLineWidth(2)
            diagLineMW.SetMarkerStyle(20)
            diagLineMW.SetPoint(0,80+self.model.Ymin,self.model.Ymin)
            diagLineMW.SetPoint(1,80+self.model.Ymax,self.model.Ymax)
            diagLineMW.Draw("LSAME")
            self.c.diagLineMW = diagLineMW
            tdiagonalMW = rt.TLatex(540, 540-75,"m_{#tilde{t}} = m_{W} + m_{#tilde{#chi}_{1}^{0}}")
            tdiagonalMW.SetTextAngle(math.degrees(math.atan(float(self.model.Xmax)/float(self.model.Ymax))))
            tdiagonalMW.SetTextColor(rt.kGray+2)
            tdiagonalMW.SetTextAlign(11)
            tdiagonalMW.SetTextSize(0.025)
            tdiagonalMW.Draw("SAME")
            self.c.tdiagonalMW = tdiagonalMW

            diagLine = rt.TGraph(2)
            diagLine.SetName("diagLine")
            diagLine.SetTitle("diagLine")
            diagLine.SetLineColor(rt.kGray)
            diagLine.SetLineStyle(2)
            diagLine.SetLineWidth(2)
            diagLine.SetMarkerStyle(20)
            diagLine.SetPoint(0,172.5+self.model.Ymin,self.model.Ymin)
            diagLine.SetPoint(1,172.5+self.model.Ymax,self.model.Ymax)
            diagLine.Draw("LSAME")
            self.c.diagLine = diagLine
            tdiagonal = rt.TLatex(640, 640-172.5,"m_{#tilde{t}} = m_{t} + m_{#tilde{#chi}_{1}^{0}}")
            tdiagonal.SetTextAngle(math.degrees(math.atan(float(self.model.Xmax)/float(self.model.Ymax))))
            tdiagonal.SetTextColor(rt.kGray+2)
            tdiagonal.SetTextAlign(11)
            tdiagonal.SetTextSize(0.025)
            tdiagonal.Draw("SAME")
            self.c.tdiagonal = tdiagonal

            diagonal = rt.TGraph(4)
            diagonal.SetPoint(0,150.0,0.0)
            diagonal.SetPoint(1,262.5,112.5)
            diagonal.SetPoint(2,287.5,87.5)
            diagonal.SetPoint(3,200.0,0.0)
            diagonal.SetName("diagonal")
            diagonal.SetFillColor(rt.kWhite)
            diagonal.SetLineColor(rt.kWhite)
            diagonal.SetLineStyle(2)
            diagonal.Draw("FSAME")
            diagonal.Draw("LSAME")
            self.c.diagonal = diagonal

        if self.model.modelname in ('T2bW','T2tb'):
            diagLine = rt.TGraph(2)
            diagLine.SetName("diagLine")
            diagLine.SetTitle("diagLine")
            diagLine.SetLineColor(rt.kGray)
            diagLine.SetLineStyle(2)
            diagLine.SetLineWidth(2)
            diagLine.SetMarkerStyle(20)
            diagLine.SetPoint(0,172.5+self.model.Ymin,self.model.Ymin)
            diagLine.SetPoint(1,172.5+self.model.Ymax,self.model.Ymax)
            diagLine.Draw("LSAME")
            self.c.diagLine = diagLine
            tdiagonal = rt.TLatex(350, 350-172.5,"m_{#tilde{t}} = m_{t} + m_{#tilde{#chi}_{1}^{0}}")
            tdiagonal.SetTextAngle(math.degrees(math.atan(float(self.model.Xmax)/float(self.model.Ymax))))
            tdiagonal.SetTextColor(rt.kGray+2)
            tdiagonal.SetTextAlign(11)
            tdiagonal.SetTextSize(0.025)
            tdiagonal.Draw("SAME")
            self.c.tdiagonal = tdiagonal
        
    def DrawLines(self):
        # observed
        for obs in self.OBS['nominal'] :
            obs.SetLineColor(color(self.OBS['colorLine']))
            obs.SetLineStyle(1)
            obs.SetLineWidth(4)
        # observed + 1sigma
        for obs in self.OBS['plus'] :
            obs.SetLineColor(color(self.OBS['colorLine']))
            obs.SetLineStyle(1)
            obs.SetLineWidth(2)        
        # observed - 1sigma
        for obs in self.OBS['minus'] :
            obs.SetLineColor(color(self.OBS['colorLine']))
            obs.SetLineStyle(1)
            obs.SetLineWidth(2)        
        # expected + 1sigma
        for exp in self.EXP['plus'] :
            exp.SetLineColor(color(self.EXP['colorLine']))
            exp.SetLineStyle(7)
            exp.SetLineWidth(2)                
        # expected
        for exp in self.EXP['nominal'] :
            exp.SetLineColor(color(self.EXP['colorLine']))
            exp.SetLineStyle(7)
            exp.SetLineWidth(4)        
        # expected - 1sigma
        for exp in self.EXP['minus'] :
            exp.SetLineColor(color(self.EXP['colorLine']))
            exp.SetLineStyle(7)
            exp.SetLineWidth(2)                        
        # DRAW LINES
        for exp in self.EXP['nominal'] :
            exp.Draw("LSAME")
        for exp in self.EXP['plus'] :
            exp.Draw("LSAME")
        for exp in self.EXP['minus'] :
            exp.Draw("LSAME")
        for obs in self.OBS['nominal'] :
            obs.Draw("LSAME")
        for obs in self.OBS['plus'] :
            obs.Draw("LSAME")
        for obs in self.OBS['minus'] :
            obs.Draw("LSAME")

        
