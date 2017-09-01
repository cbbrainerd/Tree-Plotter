#include <memory>
#include <string>
#include <map>
#include <vector>
#include <functional>
#include <iostream>
//ROOT includes
#include "TH2.h"
#include "TH3.h"
#include "TTree.h"
#include "TBranch.h"
#include "TFile.h"

class Event;

class baseHistogram {
    virtual void Fill(const Event&,const std::string&);
    virtual void addDataset(const char*);
    virtual void addDataset(const std::string&);
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

template<class Event>
class Plotter {
    std::vector<baseHistogram*> histograms_;
    std::vector<std::string> Datasets_;
    Event event;
    Long64_t eventCount;
    const char* treeName_;
    std::map<std::string,std::vector<const char*> > filenames_;
    void processFile(const char* filename,const std::string& Dataset) {
        TFile* tf=new TFile(filename);
        TTree* tree=tf->Get(treeName_);
        if(!tree) throw tree;
        event.setAddresses(tree);
        processTree(tree,Dataset);
        tf->Close();
    }
    void processTree(TTree* tree,const std::string& Dataset) {
        for(Long64_t i=0;i<tree->GetEntries();++i) {
            tree->GetEntry(i);
            for(auto& element : histograms_) element->Fill(event,Dataset);
            ++eventCount;
            if(not(eventCount % 100000)) std::cout << eventCount << " events processed." << std::endl;
        }
    }
    void processDataset(const std::string& Dataset) {
        std::vector<const char*> filenames=filenames_[Dataset];
        for(auto& filename : filenames) processFile(filename,Dataset);
    }
    void process() {
        for(auto& Dataset : Datasets_) processDataset(Dataset);
    }
    Plotter(const char* treeName,std::vector<std::string> Datasets, std::vector<const char*> filenames) : treeName_(treeName), Datasets_(Datasets) , filenames_(filenames) , eventCount(0) {}
    template<class x>
    void addHistogram(x* p) { addHistogram(static_cast<baseHistogram*>(p)); }
    void addHistogram(baseHistogram* bh) { histograms_.push_back(bh); }
};

