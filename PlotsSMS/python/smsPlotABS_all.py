import ROOT as rt
from array import *
from sms import *
from color import *
import CMS_lumi
import math
class smsPlotABS_all(object):
    # modelname is the sms name (see sms.py)
    # histo is the 2D xsec map
    # obsLimits is a list of opbserved limits [NOMINAL, +1SIGMA, -1SIGMA]
    # expLimits is a list of expected limits [NOMINAL, +1SIGMA, -1SIGMA]
    # label is a label referring to the analysis (e.g. RA1, RA2, RA2b, etc)

    def __init__(self, modelname, histo, obsLimits, expLimits, energy, lumi, preliminary, label):
        self.standardDef(modelname, histo, obsLimits, expLimits, energy, lumi, preliminary)
        self.LABEL = label
        self.c = rt.TCanvas("cABS_%s" %label,"cABS_%s" %label,300,300)
        self.histo = []
        self.histo.append(histo[i]['histogram'] for i in histo)

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

        self.c.SetRightMargin(0.1)
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
        #if self.model.modelname in ('T2tb', 'T2bW'):
        #    self.emptyHisto.GetXaxis().SetNdivisions(505)
        if self.model.modelname in ('T1tttt', 'T1ttbb', 'T5tttt', 'T5ttcc'):
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
        graphWhite.SetPoint(2,self.model.Xmax, self.model.Ymax*0.55)
        graphWhite.SetPoint(3,self.model.Xmin, self.model.Ymax*0.55)
        graphWhite.SetPoint(4,self.model.Xmin, self.model.Ymax)
        graphWhite.Draw("FSAME")
        graphWhite.Draw("LSAME")
        self.c.graphWhite = graphWhite
       	CMS_lumi.writeExtraText = 1
	CMS_lumi.extraText = "Supplementary"
	#CMS_lumi.lumi_13TeV="2.3 fb^{-1}"
	CMS_lumi.lumi_13TeV="137.0 fb^{-1}"

	CMS_lumi.lumi_sqrtS = "13 TeV"  
	iPos=0
	CMS_lumi.CMS_lumi(self.c,4, iPos)
        # CMS LABEL
        textCMS = rt.TLatex(0.25,0.96,"  %s " %(self.preliminary))
        textCMS.SetNDC()
        textCMS.SetTextAlign(13)
        textCMS.SetTextFont(52)
        textCMS.SetTextSize(0.030)
        #textCMS.Draw()
        self.c.textCMS = textCMS
        # MODEL LABEL
        textModelLabel= rt.TLatex(0.16,0.92,"%s" %self.model.label)
        textModelLabel.SetNDC()
        textModelLabel.SetTextAlign(13)
        textModelLabel.SetTextFont(42)
        textModelLabel.SetTextSize(0.035)
        #textModelLabel.SetTextSize(0.03)
        textModelLabel.Draw()
        self.c.textModelLabel = textModelLabel
        # NLO NLL XSEC
        textNLONLL = rt.TLatex(0.285, 0.90, "Approx. NNLO+NNLL exclusion")
        textNLONLL.SetNDC()
        textNLONLL.SetTextAlign(13)
        textNLONLL.SetTextFont(42)
        textNLONLL.SetTextSize(0.03)
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
        LObs.SetLineColor(rt.kBlack)
        LObs.SetLineStyle(1)
        LObs.SetLineWidth(4)
        LObs.SetMarkerStyle(20)
        LObs.SetPoint(0,self.model.Xmin+70*xRange/100, self.model.Ymax-0.55*yRange/100*10)
        LObs.SetPoint(1,self.model.Xmin+77*xRange/100, self.model.Ymax-0.55*yRange/100*10)

        textObs = rt.TLatex(self.model.Xmin+79*xRange/100, self.model.Ymax-0.65*yRange/100*10, "Observed")
        textObs.SetTextFont(42)
        textObs.SetTextSize(0.035)
        textObs.Draw()
        self.c.textObs = textObs

        LExp = rt.TGraph(2)
        LExp.SetName("LExp")
        LExp.SetTitle("LExp")
        LExp.SetLineColor(rt.kBlack)
        LExp.SetLineStyle(7)
        LExp.SetLineWidth(4)
        LExp.SetPoint(0,self.model.Xmin+70*xRange/100, self.model.Ymax-1.10*yRange/100*10)
        LExp.SetPoint(1,self.model.Xmin+77*xRange/100, self.model.Ymax-1.10*yRange/100*10)
        
        textExp = rt.TLatex(self.model.Xmin+79*xRange/100, self.model.Ymax-1.20*yRange/100*10, "Expected")
        textExp.SetTextFont(42)
        textExp.SetTextSize(0.035)
        textExp.Draw()
        self.c.textExp = textExp

        LObs.Draw("LSAME")
        LExp.Draw("LSAME")

        sigLabelDY = 0.59
        LT2tt = rt.TGraph(2)
        LT2tt.SetName("LT2tt")
        LT2tt.SetTitle("LT2tt")
        LT2tt.SetLineColor(color(self.EXP["T2tt"]['colorLine']))
        LT2tt.SetLineStyle(1)
        LT2tt.SetLineWidth(4)
        LT2tt.SetPoint(0,self.model.Xmin+3*xRange/100,  self.model.Ymax-1.0*yRange/100*10)
        LT2tt.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-1.0*yRange/100*10)
        LT2tt.Draw("LSAME")
        self.c.LT2tt = LT2tt
        
        textT2tt = rt.TLatex(self.model.Xmin+13*xRange/100, self.model.Ymax-1.20*yRange/100*10, self.model.label_T2tt)
        textT2tt.SetTextFont(42)
        textT2tt.SetTextSize(0.028)
        textT2tt.Draw()
        self.c.textT2tt = textT2tt
        
        LT2bW = rt.TGraph(2)
        LT2bW.SetName("LT2bW")
        LT2bW.SetTitle("LT2bW")
        LT2bW.SetLineColor(color(self.EXP["T2bW"]['colorLine']))
        LT2bW.SetLineStyle(1)
        LT2bW.SetLineWidth(4)
        LT2bW.SetPoint(0,self.model.Xmin+3*xRange/100,  self.model.Ymax-(1.0 + sigLabelDY*1)*yRange/100*10)
        LT2bW.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-(1.0 + sigLabelDY*1)*yRange/100*10)
        LT2bW.Draw("LSAME")
        self.c.LT2bW = LT2bW
        
        textT2bW = rt.TLatex(self.model.Xmin+13*xRange/100, self.model.Ymax-(1.20 + sigLabelDY*1)*yRange/100*10, self.model.label_T2bW)
        textT2bW.SetTextFont(42)
        textT2bW.SetTextSize(0.028)
        textT2bW.Draw()
        self.c.textT2bW = textT2bW
        
        LT2tb = rt.TGraph(2)
        LT2tb.SetName("LT2tb")
        LT2tb.SetTitle("LT2tb")
        LT2tb.SetLineColor(color(self.EXP["T2tb"]['colorLine']))
        LT2tb.SetLineStyle(1)
        LT2tb.SetLineWidth(4)
        LT2tb.SetPoint(0,self.model.Xmin+3*xRange/100,  self.model.Ymax-(1.0 + sigLabelDY*2)*yRange/100*10)
        LT2tb.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-(1.0 + sigLabelDY*2)*yRange/100*10)
        LT2tb.Draw("LSAME")
        self.c.LT2tb = LT2tb
        
        textT2tb = rt.TLatex(self.model.Xmin+13*xRange/100, self.model.Ymax-(1.20 + sigLabelDY*2)*yRange/100*10, self.model.label_T2tb)
        textT2tb.SetTextFont(42)
        textT2tb.SetTextSize(0.028)
        textT2tb.Draw()
        self.c.textT2tb = textT2tb
        
        LT2fbd = rt.TGraph(2)
        LT2fbd.SetName("LT2fbd")
        LT2fbd.SetTitle("LT2fbd")
        LT2fbd.SetLineColor(color(self.EXP["T2fbd"]['colorLine']))
        LT2fbd.SetLineStyle(1)
        LT2fbd.SetLineWidth(4)
        LT2fbd.SetPoint(0,self.model.Xmin+3*xRange/100,  self.model.Ymax-(1.0 + sigLabelDY*3)*yRange/100*10)
        LT2fbd.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-(1.0 + sigLabelDY*3)*yRange/100*10)
        LT2fbd.Draw("LSAME")
        self.c.LT2fbd = LT2fbd
        
        textT2fbd = rt.TLatex(self.model.Xmin+13*xRange/100, self.model.Ymax-(1.20 + sigLabelDY*3)*yRange/100*10, self.model.label_T2fbd)
        textT2fbd.SetTextFont(42)
        textT2fbd.SetTextSize(0.028)
        textT2fbd.Draw()
        self.c.textT2fbd = textT2fbd
        
        LT2bWC = rt.TGraph(2)
        LT2bWC.SetName("LT2bWC")
        LT2bWC.SetTitle("LT2bWC")
        LT2bWC.SetLineColor(color(self.EXP["T2bWC"]['colorLine']))
        LT2bWC.SetLineStyle(1)
        LT2bWC.SetLineWidth(4)
        LT2bWC.SetPoint(0,self.model.Xmin+3*xRange/100,  self.model.Ymax-(1.0 + sigLabelDY*4)*yRange/100*10)
        LT2bWC.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-(1.0 + sigLabelDY*4)*yRange/100*10)
        LT2bWC.Draw("LSAME")
        self.c.LT2bWC = LT2bWC
        
        textT2bWC = rt.TLatex(self.model.Xmin+13*xRange/100, self.model.Ymax-(1.20 + sigLabelDY*4)*yRange/100*10, self.model.label_T2bWC)
        textT2bWC.SetTextFont(42)
        textT2bWC.SetTextSize(0.028)
        textT2bWC.Draw()
        self.c.textT2bWC = textT2bWC
        
        LT2cc = rt.TGraph(2)
        LT2cc.SetName("LT2cc")
        LT2cc.SetTitle("LT2cc")
        LT2cc.SetLineColor(color(self.EXP["T2cc"]['colorLine']))
        LT2cc.SetLineStyle(1)
        LT2cc.SetLineWidth(4)
        LT2cc.SetPoint(0,self.model.Xmin+3*xRange/100,  self.model.Ymax-(1.0 + sigLabelDY*5)*yRange/100*10)
        LT2cc.SetPoint(1,self.model.Xmin+10*xRange/100, self.model.Ymax-(1.0 + sigLabelDY*5)*yRange/100*10)
        LT2cc.Draw("LSAME")
        self.c.LT2cc = LT2cc
        
        textT2cc = rt.TLatex(self.model.Xmin+13*xRange/100, self.model.Ymax-(1.20 + sigLabelDY*5)*yRange/100*10, self.model.label_T2cc)
        textT2cc.SetTextFont(42)
        textT2cc.SetTextSize(0.028)
        textT2cc.Draw()
        self.c.textT2cc = textT2cc
        
        self.c.LObs = LObs
        self.c.LExp = LExp

    def DrawDiagonal(self):
        diagLineMX = rt.TGraph(2)
        diagLineMX.SetName("diagLineMX")
        diagLineMX.SetTitle("diagLineMX")
        diagLineMX.SetLineColor(rt.kGray)
        diagLineMX.SetLineStyle(2)
        diagLineMX.SetLineWidth(2)
        diagLineMX.SetMarkerStyle(20)
        diagLineMX.SetPoint(0,self.model.Ymin,self.model.Ymin)
        diagLineMX.SetPoint(1,self.model.Ymax,self.model.Ymax)
        diagLineMX.Draw("LSAME")
        self.c.diagLineMX = diagLineMX
        tdiagonalMX = rt.TLatex(300, 300+37.5,"m_{#tilde{t}} = m_{#tilde{#chi}_{1}^{0}}")
        tdiagonalMX.SetTextAngle(math.degrees(math.atan(float(self.model.Xmax)/float(self.model.Ymax))))
        tdiagonalMX.SetTextColor(rt.kGray+2)
        tdiagonalMX.SetTextAlign(11)
        tdiagonalMX.SetTextSize(0.025)
        tdiagonalMX.Draw("SAME")
        self.c.tdiagonalMX = tdiagonalMX

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
        tdiagonalMW = rt.TLatex(300, 300-75,"m_{#tilde{t}} = m_{W} + m_{#tilde{#chi}_{1}^{0}}")
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
        tdiagonal = rt.TLatex(400, 400-172.5,"m_{#tilde{t}} = m_{t} + m_{#tilde{#chi}_{1}^{0}}")
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
        diagonal.SetFillColor(rt.kGray)
        diagonal.SetLineColor(rt.kGray)
        diagonal.SetLineStyle(2)
        diagonal.Draw("FSAME")
        diagonal.Draw("LSAME")
        self.c.diagonal = diagonal

    def DrawLines(self):
        # observed
        for i in self.SIGNAL:
            for obs in self.OBS[i]['nominal'] :
                obs.SetLineColor(color(self.OBS[i]['colorLine']))
                obs.SetLineStyle(1)
                obs.SetLineWidth(4)
        # expected
            for exp in self.EXP[i]['nominal'] :
                exp.SetLineColor(color(self.EXP[i]['colorLine']))
                exp.SetLineStyle(7)
                exp.SetLineWidth(4)        
        # DRAW LINES
            for exp in self.EXP[i]['nominal'] :
                exp.Draw("LSAME")
            for obs in self.OBS[i]['nominal'] :
                obs.Draw("LSAME")
