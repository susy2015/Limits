#if !defined(__CINT__) || defined(__MAKECINT__)
#include "TCanvas.h"
#include "TGraph.h"
#include "TGraph2D.h"
#endif

using namespace std;

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

void makeSigScanPlots(const TString inputFileName = "significances_T2tt.root", const TString name = "T2tt")
{

  SetupColors();

  TFile* inputFile = new TFile(inputFileName);

  TH2D* hsig = (TH2D*)inputFile->Get("hsig");

  vector<double> mstops, mlsps;
  vector<double> sig;

  for(int ibinx = 1; ibinx <= hsig->GetNbinsX()+1; ++ibinx) {
    for(int ibiny = 1; ibiny <= hsig->GetNbinsY()+1; ++ibiny) {
      if(hsig->GetBinContent(ibinx, ibiny) != 0.0) {
        mstops.push_back(hsig->GetXaxis()->GetBinLowEdge(ibinx));
        mlsps.push_back(hsig->GetYaxis()->GetBinLowEdge(ibiny));
        sig.push_back(hsig->GetBinContent(ibinx, ibiny));
        printf("MStop: %4.2f, MLSP: %4.2f, Significance: %4.2f\n", mstops.back(), mlsps.back(), sig.back());
      }
    }
  }

  TGraph2D gsig("gsig", ";m_{stop} [GeV];m_{LSP} [GeV]", sig.size(), &mstops.at(0), &mlsps.at(0), &sig.at(0));
  TGraph dots(mstops.size(), &mstops.at(0), &mlsps.at(0));

  double xmin = *min_element(mstops.cbegin(), mstops.cend());
  double xmax = *max_element(mstops.cbegin(), mstops.cend());
  double ymin = *min_element(mlsps.cbegin(), mlsps.cend());
  double ymax = *max_element(mlsps.cbegin(), mlsps.cend());
  double xbin_size = 12.5;
  double ybin_size = (name=="T2tt" || name=="T2bW" || name=="T2tb") ? 12.5 : 5;
  int nxbins = max(1, min(500, static_cast<int>(ceil((xmax-xmin)/xbin_size))));
  int nybins = max(1, min(500, static_cast<int>(ceil((ymax-ymin)/ybin_size))));
  printf("XMin: %4.2f, XMax: %4.2f, YMin: %4.2f, YMax: %4.2f, NXBins: %d, NYBins: %d\n", xmin, xmax, ymin, ymax, nxbins, nybins);
  gsig.SetNpx(nxbins);
  gsig.SetNpy(nybins);

  TH2D *hsigcorr = gsig.GetHistogram();
  if(!hsigcorr) throw runtime_error("Could not retrieve histogram");
  hsig->SetTitle(";m_{stop} [GeV];m_{LSP} [GeV]");
  hsigcorr->SetTitle(";m_{stop} [GeV];m_{LSP} [GeV]");

  TCanvas c("","",800,800);
  //c.SetLogz();
  hsigcorr->SetMinimum(*min_element(sig.cbegin(), sig.cend()));
  hsigcorr->SetMaximum(*max_element(sig.cbegin(), sig.cend()));
//  hsigcorr->GetYaxis()->SetRangeUser(0.0,450.0);
  hsigcorr->GetYaxis()->SetTitleOffset(1.5);
  hsigcorr->GetZaxis()->SetRangeUser(0.0,5.0);
  gsig.Draw("colz");
  //TLegend l(gStyle->GetPadLeftMargin(), 1.-gStyle->GetPadTopMargin(),
  //          1.-gStyle->GetPadRightMargin(), 1.);
  //l.SetNColumns(2);
  //l.SetBorderSize(0);
//  dots.Draw("p same");
  c.Print("sig_scan_"+name+".pdf");

  // set empty bins to -99
  for (int ix=1; ix<hsigcorr->GetNbinsX()+1; ++ix){
    for (int iy=1; iy<hsigcorr->GetNbinsY()+1; ++iy){
      if (hsigcorr->GetBinContent(ix, iy)==0){
        hsigcorr->SetBinContent(ix, iy, -99);
      }
    }
  }

  TFile file("sig_scan_"+name+".root","recreate");
  hsigcorr->Write("hsig_corr");
  gsig.Write("gsig_corr");
  file.Close();


}
