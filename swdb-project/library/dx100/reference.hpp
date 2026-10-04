// Independent scalar reference semantics. Updated: 2026-10-03 ET.
#pragma once
#include <cstdint>
#include <vector>
#include <utility>
namespace swdb_reference {
inline std::vector<int32_t> gather(const std::vector<int32_t>&base,const std::vector<int32_t>&indices){std::vector<int32_t>out;for(int32_t i:indices)out.push_back(base.at(i));return out;}
inline std::vector<int32_t> stream_load(const std::vector<int32_t>&base,int begin,int end,int stride){std::vector<int32_t>out;for(int i=begin;i<end;i+=stride)out.push_back(base.at(i));return out;}
inline std::vector<std::pair<int32_t,int32_t>> range_loop(const std::vector<int32_t>&lo,const std::vector<int32_t>&hi){std::vector<std::pair<int32_t,int32_t>>out;for(size_t i=0;i<lo.size();++i)for(int32_t j=lo[i];j<hi.at(i);++j)out.push_back({i,j});return out;}
inline std::vector<int32_t> alu_scalar(const std::vector<int32_t>&values,int32_t scalar){std::vector<int32_t>out;for(int32_t v:values)out.push_back(v<scalar);return out;}
inline bool session_begin(bool active){return !active;}
inline bool thread_context(unsigned threads,unsigned cores){return threads<=cores;}
inline int32_t const_i32(int32_t value){return value;}
inline bool wait(bool issued){return issued;}
inline size_t tile_size(const std::vector<int32_t>&values){return values.size();}
inline const int32_t*tile_pointer(const std::vector<int32_t>&values){return values.data();}
}
