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

template<class Event,class... Doubles> 
class histogram {
private:
    std::function<std::tuple<Doubles...>(Event)> fillFunction_;
    std::function<Float_t(Event)> weightFunction_;
    std::unique_ptr<TH1> histogramTemplate_;
    std::map<std::string,std::unique_ptr<TH1> > histograms_;
public:
    histogram(std::unique_ptr<TH1> histogramTemplate,std::function<std::tuple<Doubles...>(Event)> fillFunction,std::function<Float_t(Event)> weightFunction) : 
        histogramTemplate_(std::move(histogramTemplate)) , 
        fillFunction_(fillFunction) ,
        weightFunction_(weightFunction)
    {
        histogramTemplate_->SetDirectory(0);
    }
    Bool_t addDataset(const char* s) { return addDataset(std::string(s)); }
    Bool_t addDataset(const std::string& s) { 
        TH1* tmpHist=histogramTemplate_->Clone();
        tmpHist->SetDirectory(0);
        histograms_.insert(std::make_pair(s,std::unique_ptr<TH1>(tmpHist)));
    }
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
    void Fill(const Event& event,const std::string& Dataset) {
        std::tuple<Doubles...> result=fillFunction_(event);
        Float_t weight=weightFunction_(event);
        histFill(result,weight,histograms_[Dataset].get());
    }
};

typedef histogram<Event,Float_t> H1;
typedef histogram<Event,Float_t,Float_t> H2;
typedef histogram<Event,Float_t,Float_t,Float_t> H3;
