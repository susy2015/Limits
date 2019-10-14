#if !defined(__CINT__) || defined(__MAKECINT__)
#include "TCanvas.h"
#include "TGraph.h"
#include "TGraph2D.h"
#include "interpolate.h"
#endif

using namespace std;

vector<TGraph*> DrawContours(TGraph2D &g2, int color, int style,
                    TLegend *leg = 0, const string &name = ""){
  vector<TGraph*> out;
  TH2D* hist = g2.GetHistogram();
  TVirtualHistPainter* histptr = hist->GetPainter();
  TList *l = histptr->GetContourList(1.);
  if(!l)
    return out;
  bool added = false;
  int max_points = -1;
  for(int i = 0; i < l->GetSize(); ++i){
    TGraph *g = static_cast<TGraph*>(l->At(i));
    if(g == 0) {
      continue;
    }
    //int n_points = g->GetN();
    out.push_back(g);
    g->SetLineColor(color);
    g->SetLineStyle(style);
    g->SetLineWidth(5);
    g->Draw("L same");
    if(!added && leg && name != ""){
      leg->AddEntry(g, name.c_str(), "l");
      added = true;
    }
  }
  return out;
}

void SetupColors(){
  const unsigned num = 5;
  const int bands = 255;
  int colors[bands];
  double stops[num] = {0.00, 0.34, 0.61, 0.84, 1.00};
  double red[num] = {0.50, 0.50, 1.00, 1.00, 1.00};
  double green[num] = {0.50, 1.00, 1.00, 0.60, 0.50};
  double blue[num] = {1.00, 1.00, 0.50, 0.40, 0.50};
  /*const unsigned num = 6;
 *   double red[num] =   {1.,0.,0.,0.,1.,1.};
 *     double green[num] = {0.,0.,1.,1.,1.,0.};
 *       double blue[num] =  {1.,1.,1.,0.,0.,0.};
 *         double stops[num] = {0.,0.2,0.4,0.6,0.8,1.};*/
  int fi = TColor::CreateGradientColorTable(num,stops,red,green,blue,bands);
  for(int i = 0; i < bands; ++i){
    colors[i] = fi+i;
  }
  gStyle->SetNumberContours(bands);
  gStyle->SetPalette(bands, colors);
}

void makeScanPlots(const TString inputFileName = "results_T2tt.root", const TString outputFileName = "limit_scan_T2tt.root", bool expectedOnly = false, bool additionalInterpolation = false)
{

  SetupColors();

  TFile* inputFile = new TFile(inputFileName);

  TH2D* hobs = expectedOnly ? 0 : (TH2D*)inputFile->Get("hobs");
  TH2D* hobsdown = expectedOnly ? 0 : (TH2D*)inputFile->Get("hobsdown");
  TH2D* hobsup = expectedOnly ? 0 : (TH2D*)inputFile->Get("hobsup");
  TH2D* hexp = (TH2D*)inputFile->Get("hexp");
  TH2D* hexpdown = (TH2D*)inputFile->Get("hexpdown");
  TH2D* hexpup = (TH2D*)inputFile->Get("hexpup");

  if(additionalInterpolation) {
    if(hobs) hobs = rebin(hobs, "NE");
    if(hobsdown) hobsdown = rebin(hobsdown, "NE");
    if(hobsup) hobsup = rebin(hobsup, "NE");
    hexp = rebin(hexp, "NE");
    hexpdown = rebin(hexpdown, "NE");
    hexpup = rebin(hexpup, "NE");
    if(hobs) hobs = rebin(hobs, "NE");
    if(hobsdown) hobsdown = rebin(hobsdown, "NE");
    if(hobsup) hobsup = rebin(hobsup, "NE");
    hexp = rebin(hexp, "NE");
    hexpdown = rebin(hexpdown, "NE");
    hexpup = rebin(hexpup, "NE");
    hobs = interpolate(hobs, "NE");
    hobsdown = interpolate(hobsdown, "NE");
    hobsup = interpolate(hobsup, "NE");
    hexp = interpolate(hexp, "NE");
    hexpdown = interpolate(hexpdown, "NE");
    hexpup = interpolate(hexpup, "NE");
  }

  vector<double> mstops, mlsps, mstopsxsec, mlspsxsec;
  vector<double> exp, expdown, expup, expxsec;
  vector<double> obs, obsdown, obsup, obsxsec;

  TH2D* hxsecexp = (TH2D*)inputFile->Get("hxsecexp");
  TH2D* hxsecobs = expectedOnly ? hxsecexp : (TH2D*)inputFile->Get("hxsecobs");
  for(int ibinx = 1; ibinx <= hxsecexp->GetNbinsX()+1; ++ibinx) {
    for(int ibiny = 1; ibiny <= hxsecexp->GetNbinsY()+1; ++ibiny) {
      if(hxsecexp->GetBinContent(ibinx, ibiny) != 0.0) {
        mstopsxsec.push_back(hxsecexp->GetXaxis()->GetBinCenter(ibinx));
        mlspsxsec.push_back(hxsecexp->GetYaxis()->GetBinLowEdge(ibiny));
        expxsec.push_back(hxsecexp->GetBinContent(ibinx, ibiny));
        obsxsec.push_back(hxsecobs->GetBinContent(ibinx, ibiny));
      }
    }
  }

  for(int ibinx = 1; ibinx <= hexp->GetNbinsX()+1; ++ibinx) {
    for(int ibiny = 1; ibiny <= hexp->GetNbinsY()+1; ++ibiny) {
      if(hexp->GetBinContent(ibinx, ibiny) != 0.0) {
        mstops.push_back(hexp->GetXaxis()->GetBinCenter(ibinx));
        mlsps.push_back(hexp->GetYaxis()->GetBinLowEdge(ibiny));
        obs.push_back(hobs ? hobs->GetBinContent(ibinx, ibiny) : hexp->GetBinContent(ibinx, ibiny));
        obsdown.push_back(hobsdown ? hobsdown->GetBinContent(ibinx, ibiny) : hexpdown->GetBinContent(ibinx, ibiny));
        obsup.push_back(hobsup ? hobsup->GetBinContent(ibinx, ibiny) : hexpup->GetBinContent(ibinx, ibiny));
        exp.push_back(hexp->GetBinContent(ibinx, ibiny));
        expdown.push_back(hexpdown->GetBinContent(ibinx, ibiny));
        expup.push_back(hexpup->GetBinContent(ibinx, ibiny));
        printf("MStop: %4.2f, MLSP: %4.2f, Limit: %4.2f, (+1: %4.2f, -1: %4.2f), Obs Limit: %4.2f (+1 theory: %4.2f, -1 theory: %4.2f)\n", mstops.back(), mlsps.back(), exp.back(), expup.back(), expdown.back(), obs.back(), obsup.back(), obsdown.back());
      }
    }
  }

  TGraph2D glimexp("glimexp", "Cross-Section Limit", expxsec.size(), &mstopsxsec.at(0), &mlspsxsec.at(0), &expxsec.at(0));
  TGraph2D glimobs("glimobs", "Cross-Section Limit", obsxsec.size(), &mstopsxsec.at(0), &mlspsxsec.at(0), &obsxsec.at(0));
  TGraph2D gexp("gexp", "Expected Limit", exp.size(), &mstops.at(0), &mlsps.at(0), &exp.at(0));
  TGraph2D gexpdown("gexpdown", "Expected  -1#sigma Limit", expdown.size(), &mstops.at(0), &mlsps.at(0), &expdown.at(0));
  TGraph2D gexpup("gexpup", "Expected  -1#sigma Limit", expup.size(), &mstops.at(0), &mlsps.at(0), &expup.at(0));
  TGraph2D gobs("gobs", "Observed Limit", obs.size(), &mstops.at(0), &mlsps.at(0), &obs.at(0));
  TGraph2D gobsdown("gobsdown", "Observed  -1#sigma (theory) Limit", obsdown.size(), &mstops.at(0), &mlsps.at(0), &obsdown.at(0));
  TGraph2D gobsup("gobsup", "Observed  -1#sigma (theory) Limit", obsup.size(), &mstops.at(0), &mlsps.at(0), &obsup.at(0));
  TGraph dots(mstops.size(), &mstops.at(0), &mlsps.at(0));

  double xmin = *min_element(mstops.cbegin(), mstops.cend());
  double xmax = *max_element(mstops.cbegin(), mstops.cend());
  double ymin = *min_element(mlsps.cbegin(), mlsps.cend());
  double ymax = *max_element(mlsps.cbegin(), mlsps.cend());
  double xbin_size = 12.5, ybin_size = 12.5;

  if (inputFileName.Contains("T2fbd") || inputFileName.Contains("T2bWL") || inputFileName.Contains("T2cc")){
    ybin_size = 5;
  }

  int nxbins = max(1, min(1000, static_cast<int>(ceil((xmax-xmin)/xbin_size))));
  int nybins = max(1, min(1000, static_cast<int>(ceil((ymax-ymin)/ybin_size))));
  printf("XMin: %4.2f, XMax: %4.2f, YMin: %4.2f, YMax: %4.2f, NXBins: %d, NYBins: %d\n", xmin, xmax, ymin, ymax, nxbins, nybins);
  glimexp.SetNpx(nxbins);
  glimexp.SetNpy(nybins);
  glimobs.SetNpx(nxbins);
  glimobs.SetNpy(nybins);

  TH2D *hlimexp = glimexp.GetHistogram();
  if(!hlimexp) throw runtime_error("Could not retrieve histogram");
  hlimexp->SetTitle(";m_{stop} [GeV];m_{LSP} [GeV]");

  TH2D *hlimobs = glimobs.GetHistogram();
  if(!hlimobs) throw runtime_error("Could not retrieve histogram");
  hlimobs->SetTitle(";m_{stop} [GeV];m_{LSP} [GeV]");

  TCanvas c("","",800,800);
  c.SetLogz();
  hlimobs->SetMinimum(*min_element(obsxsec.cbegin(), obsxsec.cend()));
  hlimobs->SetMaximum(*max_element(obsxsec.cbegin(), obsxsec.cend()));
  glimobs.Draw("colz");
  TLegend l(gStyle->GetPadLeftMargin(), 1.-gStyle->GetPadTopMargin(),
            1.-gStyle->GetPadRightMargin(), 1.);
  l.SetNColumns(2);
  l.SetBorderSize(0);
  vector<TGraph*> cobsup = DrawContours(gobsup, 1, 2, &l, "ObsUp");
  vector<TGraph*> cobsdown = DrawContours(gobsdown, 1, 2, &l, "ObsDown");
  vector<TGraph*> cobs = DrawContours(gobs, 1, 1, &l, "Observed");
  vector<TGraph*> cexpup = DrawContours(gexpup, 2, 2, &l, "ExpUp");
  vector<TGraph*> cexpdown = DrawContours(gexpdown, 2, 2, &l, "ExpDown");
  vector<TGraph*> cexp = DrawContours(gexp, 2, 1, &l, "Expected");

  l.Draw("same");
  dots.Draw("p same");
  c.Print("limit_scan.pdf");

  TFile file(outputFileName,"recreate");
  hlimexp->Write("hXsec_exp_corr");
  hlimobs->Write("hXsec_obs_corr");
  hxsecexp->Write("hXsec_exp");
  hxsecobs->Write("hXsec_obs");

  TString gname = "graph_smoothed";

  for(unsigned int ilim = 0; ilim < cobs.size(); ++ilim) {
    TString add = ilim > 0 ? "_" + TString(to_string(ilim)) : "";
    cobs.at(ilim)->SetName(gname + "_Obs" + add);
    cobs.at(ilim)->Write(gname + "_Obs" + add);
  }
  for(unsigned int ilim = 0; ilim < cobsup.size(); ++ilim) {
    TString add = ilim > 0 ? "_" + TString(to_string(ilim)) : "";
    cobsup.at(ilim)->SetName(gname + "_ObsP" + add);
    cobsup.at(ilim)->Write(gname + "_ObsP" + add);
  }
  for(unsigned int ilim = 0; ilim < cobsdown.size(); ++ilim) {
    TString add = ilim > 0 ? "_" + TString(to_string(ilim)) : "";
    cobsdown.at(ilim)->SetName(gname + "_ObsM" + add);
    cobsdown.at(ilim)->Write(gname + "_ObsM" + add);
  }
  for(unsigned int ilim = 0; ilim < cexp.size(); ++ilim) {
    TString add = ilim > 0 ? "_" + TString(to_string(ilim)) : "";
    cexp.at(ilim)->SetName(gname + "_Exp" + add);
    cexp.at(ilim)->Write(gname + "_Exp" + add);
  }
  for(unsigned int ilim = 0; ilim < cexpup.size(); ++ilim) {
    TString add = ilim > 0 ? "_" + TString(to_string(ilim)) : "";
    cexpup.at(ilim)->SetName(gname + "_ExpP" + add);
    cexpup.at(ilim)->Write(gname + "_ExpP" + add);
  }
  for(unsigned int ilim = 0; ilim < cexpdown.size(); ++ilim) {
    TString add = ilim > 0 ? "_" + TString(to_string(ilim)) : "";
    cexpdown.at(ilim)->SetName(gname + "_ExpM" + add);
    cexpdown.at(ilim)->Write(gname + "_ExpM" + add);
  }

  file.Close();


}
