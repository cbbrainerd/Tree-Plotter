#include <memory>
#include <string>
#include <map>
#include <vector>
#include <functional>
//ROOT includes
#include "TH2.h"
#include "TH3.h"
#include "TTree.h"
#include "TBranch.h"

class Event;

class baseHistogram {
    virtual void Fill(const Event&,const std::string&) override;
    virtual void addDataset(const char*) override;
    virtual void addDataset(const std::string&) override;
};

template<class Event,class... Doubles> 
class histogram : baseHistogram {
public:
    typedef std::function<std::tuple<Doubles...>(Event)> ffType;
    typedef std::function<Float_t(Event)> wfType;
private:
    ffType fillFunction_;
    wfType weightFunction_;
    std::unique_ptr<TH1> histogramTemplate_;
    std::map<std::string,std::unique_ptr<TH1> > histograms_;
    void histFill(std::tuple<Float_t> f, Float_t w, TH1* h) {
        h->Fill(std::get<0>(f),w);
    }
    void histFill(std::tuple<Float_t,Float_t> f, Float_t w, TH1* h) {
        TH2* h2=static_cast<TH2*>(h);
        h2->Fill(std::get<0>(f),std::get<1>(f),w);
    }
    void histFill(std::tuple<Float_t,Float_t,Float_t> f, Float_t w, TH1* h) { 
        TH3* h3=static_cast<TH3*>(h);
        h3->Fill(std::get<0>(f),std::get<1>(f),std::get<2>(f),w);
    }
    template<class xtype>
    void histFill(xtype x,TH1* h) {
        histFill(x,1,h);
    }
public:
    histogram(std::unique_ptr<TH1> histogramTemplate,std::function<std::tuple<Doubles...>(Event)> fillFunction,std::function<Float_t(Event)> weightFunction) : 
        histogramTemplate_(std::move(histogramTemplate)) , 
        fillFunction_(fillFunction) ,
        weightFunction_(weightFunction)
    {
        histogramTemplate_->SetDirectory(0);
    }
    virtual void addDataset(const char* s) { return addDataset(std::string(s)); }
    virtual void addDataset(const std::string& s) { 
        TH1* tmpHist=histogramTemplate_->Clone();
        tmpHist->SetDirectory(0);
        histograms_.insert(std::make_pair(s,std::unique_ptr<TH1>(tmpHist)));
    }
    void Fill(const Event& event,const std::string& Dataset) {
        std::tuple<Doubles...> result=fillFunction_(event);
        Float_t weight=weightFunction_(event);
        histFill(result,weight,histograms_[Dataset].get());
    }
};

typedef histogram<Event,Float_t> H1;
typedef histogram<Event,Float_t,Float_t> H2;
typedef histogram<Event,Float_t,Float_t,Float_t> H3;

template<int N>
class Plotter<N> {
    std::array<BaseHistogram*,N> histograms;
    std::vector<std::string<Datasets> >;
    Event event;
    const char* treeName;
    std::map<std::string,const char** filenames>;
    void processFile(const char* filename,const std::string& Dataset) {
        TFile* tf=new TFile(filename);
        tf->Get(treeName);
        event.setAddresses(ttree);
        process(tree,Dataset);
        tf->Close();
    }
    void process(TTree* tree,const std::string& Dataset) {
        for(Long64_t i=0;i<tree->GetEntries();++i) {
            tree->GetEntry(i);
            for(auto& element : histograms) element->Fill(event,Dataset);
        }
    }
};
