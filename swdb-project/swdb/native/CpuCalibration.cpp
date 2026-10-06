// Portable native wall-time kernels, no counter/runtime instrumentation.
// Created 2026-10-06 ET. Useful bytes count executed source elements, not bus bytes.
#include "CpuWork.h"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <numeric>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <vector>
#ifdef __linux__
#include <pthread.h>
#include <sched.h>
#endif
struct Data {
    std::vector<float> a,b,out;
    std::vector<uint32_t> index;
    std::vector<uint64_t> next, heads, offsets, evict;
    uint64_t n=0; double sum=0;
};
struct Work { uint64_t iterations, accesses, useful, helper; };
static void pin(int cpu) {
#ifdef __linux__
    if (cpu >= 0) {
        cpu_set_t mask; CPU_ZERO(&mask); CPU_SET(cpu, &mask);
        if (pthread_setaffinity_np(pthread_self(), sizeof(mask), &mask)) std::abort();
    }
#else
    (void)cpu;
#endif
}
static void prepare(Data &d, const std::string &shape, uint64_t bytes, int chains, uint64_t seed) {
    std::mt19937_64 rng(seed);
    if (shape == "pointer_chase") {
        d.n = std::max<uint64_t>(chains, bytes / 64 / chains * chains);
        d.next.resize(d.n * 8); d.heads.resize(chains);
        std::vector<uint64_t> order(d.n); std::iota(order.begin(), order.end(), 0);
        std::shuffle(order.begin(), order.end(), rng);
        for (int c=0; c<chains; ++c) {
            uint64_t start=c*d.n/chains, end=(c+1)*d.n/chains;
            d.heads[c]=order[start]*8;
            for (uint64_t i=start; i<end; ++i) d.next[order[i]*8]=order[i+1==end?start:i+1]*8;
        }
    } else if (shape.rfind("compute_",0)==0) d.n=1024;
    else {
        uint64_t per = shape=="data_dependent_merge" ? 8 :
                       (shape=="single_valued_indirect" || shape=="ranged_indirect" ? 8 : 8);
        d.n=std::max<uint64_t>(32, bytes/per/32*32);
        d.a.resize(d.n);
        if (shape=="data_dependent_merge") d.out.resize(d.n);
        else if (shape!="single_valued_indirect" && shape!="ranged_indirect") d.b.resize(d.n);
        for (uint64_t i=0;i<d.n;++i) { d.a[i]=float(i % 127) / 127; if(!d.b.empty()) d.b[i]=0; }
        if (shape=="single_valued_indirect" || shape=="ranged_indirect") {
            d.index.resize(d.n); std::iota(d.index.begin(),d.index.end(),0);
            std::shuffle(d.index.begin(),d.index.end(),rng);
            if(shape=="ranged_indirect") { d.offsets.resize(d.n/16+1);
                for(uint64_t r=0;r<=d.n/16;++r) d.offsets[r]=r*16; }
        }
        if (shape=="data_dependent_merge") {
            d.a.resize(d.n/2); d.b.resize(d.n/2);
            for(uint64_t i=0;i<d.n/2;++i) { d.a[i]=float(2*i); d.b[i]=float(2*i+1); }
        }
    }
}
static Work kernel(Data &d, const std::string &s, uint64_t passes, int chains, uint64_t seed) {
    uint64_t n=d.n, loads=0; double sum=0;
    if(s=="compute_integer") sum=double(compute_integer(n*passes,seed));
    else if(s=="compute_floating_point") sum=compute_floating_point(n*passes,seed);
    else if(s=="compute_branch") sum=double(compute_branch(n*passes,seed));
    else if(s=="compute_atomic") sum=double(compute_atomic(n*passes,seed));
    else if(s=="pointer_chase") {
        for(uint64_t p=0;p<passes;++p)
            for(uint64_t i=0;i<n/uint64_t(chains);++i)
                for(int c=0;c<chains;++c) d.heads[c]=d.next[d.heads[c]];
        for(auto h:d.heads) sum+=double(h); loads=n*passes;
    } else if(s=="single_valued_indirect") {
        for(uint64_t p=0;p<passes;++p) for(uint64_t i=0;i<n;++i) sum+=d.a[d.index[i]];
        loads=n*passes;
    } else if(s=="ranged_indirect") {
        // Offset-defined fixed-fanout 16; indices remain random, helper work is retained.
        for(uint64_t p=0;p<passes;++p) for(uint64_t row=0;row<n/16;++row)
            for(uint64_t i=d.offsets[row];i<d.offsets[row+1];++i) sum+=d.a[d.index[i]];
        loads=n*passes;
    } else if(s=="data_dependent_merge") {
        for(uint64_t p=0;p<passes;++p) {
            uint64_t i=0,j=0,k=0;
            while(i<n/2 && j<n/2) {
                if(d.a[i]<d.b[j]) d.out[k++]=d.a[i++]; else d.out[k++]=d.b[j++];
            }
            while(i<n/2) d.out[k++]=d.a[i++];
            while(j<n/2) d.out[k++]=d.b[j++];
            std::atomic_signal_fence(std::memory_order_seq_cst);
        }
        loads=(3*n-1)*passes; sum=d.out[n-1];
    } else {
        for(uint64_t p=0;p<passes;++p) {
            for(uint64_t i=0;i<n;++i) d.b[i]=d.a[i]*2+1;
            std::atomic_signal_fence(std::memory_order_seq_cst);
        }
        sum=d.b[n-1]; loads=2*n*passes;
    }
    d.sum=sum;
    if(s.rfind("compute_",0)==0) return {n*passes,0,0,0};
    if(s=="pointer_chase") return {loads,loads,8*loads,0};
    if(s=="single_valued_indirect" || s=="ranged_indirect")
        return {loads,loads,4*loads,4*loads + (s=="ranged_indirect" ? loads : 0)};
    return {n*passes,loads,4*loads,0};
}
int main(int argc,char **argv) {
    if(argc!=10) return 2;
    std::string shape=argv[1]; int threads=std::stoi(argv[2]),chains=std::stoi(argv[4]),reps=std::stoi(argv[5]);
    uint64_t bytes=std::stoull(argv[3]),seed=std::stoull(argv[7]),eviction=std::stoull(argv[9]); double minimum=std::stod(argv[6]);
    std::vector<int> cpus; std::stringstream cpuinput(argv[8]); std::string item;
    while(std::getline(cpuinput,item,',')) cpus.push_back(std::stoi(item));
    if(int(cpus.size())<threads) return 3;
    std::vector<Data> data(threads); std::vector<Work> work(threads);
    std::mutex mutex; std::condition_variable cv; int ready=0,done=0,generation=0; bool quit=false;
    uint64_t passes=1, trial_seed=seed; bool evicting=false; std::vector<std::thread> workers;
    for(int w=0;w<threads;++w) workers.emplace_back([&,w] {
        pin(cpus[w]); prepare(data[w],shape,bytes/threads,chains,seed+w);
        if(shape=="cache_cold_stream") data[w].evict.resize(eviction/threads/8, seed+w);
        std::unique_lock<std::mutex> lock(mutex); ++ready; cv.notify_all(); int seen=0;
        while(true) {
            cv.wait(lock,[&]{return quit || generation>seen;}); if(quit) break;
            seen=generation; auto p=passes, s=trial_seed; lock.unlock();
            if(evicting) { volatile uint64_t sum=0; for(uint64_t i=0;i<data[w].evict.size();i+=8) sum+=data[w].evict[i]; data[w].sum=double(sum); }
            else work[w]=kernel(data[w],shape,p,chains,s+w);
            lock.lock(); ++done; cv.notify_all();
        }
    });
    {std::unique_lock<std::mutex> lock(mutex);cv.wait(lock,[&]{return ready==threads;});}
    auto run=[&](uint64_t p) {
        std::unique_lock<std::mutex> lock(mutex);passes=p;done=0;++trial_seed;
        if(shape=="cache_cold_stream") { evicting=true; ++generation; cv.notify_all();
            cv.wait(lock,[&]{return done==threads;});done=0;evicting=false; }
        auto start=std::chrono::steady_clock::now();++generation;cv.notify_all();
        cv.wait(lock,[&]{return done==threads;});
        return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    };
    double pilot=run(1); uint64_t frozen=1;
    while(shape!="cache_cold_stream" && pilot<minimum && frozen<(1ULL<<30)) { frozen*=2;pilot=run(frozen); }
    std::cout<<std::setprecision(17)<<"{\"trials\":[";
    for(int r=0;r<reps;++r) {
        double sec=run(frozen); uint64_t its=0,access=0,useful=0,helper=0; double checksum=0;
        for(int w=0;w<threads;++w) {its+=work[w].iterations;access+=work[w].accesses;useful+=work[w].useful;helper+=work[w].helper;checksum+=data[w].sum;}
        if(r)std::cout<<',';
        std::cout<<"{\"seconds\":"<<sec<<",\"iterations\":"<<its<<",\"accesses\":"<<access<<",\"useful_bytes\":"<<useful<<",\"helper_bytes\":"<<helper<<",\"checksum\":"<<checksum<<",\"worker_iterations\":[";
        for(int w=0;w<threads;++w) {if(w)std::cout<<',';std::cout<<work[w].iterations;}
        std::cout<<"]}";
    }
    std::cout<<"],\"passes\":"<<frozen<<",\"pilot_seconds\":"<<pilot<<"}\n";
    {std::lock_guard<std::mutex> lock(mutex);quit=true;cv.notify_all();}
    for(auto &t:workers)t.join();
}
