// 2026-10-16 ET. Synthetic original-API rule fixtures; prospective source only.
// No program, compiler, native agreement or formal result is implied here.
#include "MAA_gem5.hpp"
#include <cstdint>

std::uint32_t whole_same_thread_read_during_store() {
    // One complete 64-byte line lies within this source allocation. The
    // separately owned mapping must keep its physical base 64-byte aligned.
    std::uint32_t data[16] = {7, 11};
    alloc_MAA();
    init_MAA();
    clear_mem_region();
    add_mem_region(data, data + 16);
    int lower = get_new_reg<std::int32_t>(0);
    int upper = get_new_reg<std::int32_t>(1);
    int stride = get_new_reg<std::int32_t>(1);
    int payload = get_new_tile<std::uint32_t>();
    maa_stream_load<std::uint32_t>(data, lower, upper, stride, payload);
    wait_ready(payload);
    maa_stream_store<std::uint32_t>(data, lower, upper, stride, payload);
    // The value is unchanged, so only the unfinished-write hazard can refute
    // this source access. The later wait cannot protect an earlier CPU read.
    std::uint32_t observed = data[0];
    wait_ready(payload);
    return observed;
}

std::uint32_t whole_same_thread_write_during_gather() {
    // One complete 64-byte line lies within this source allocation. The
    // separately owned mapping must keep its physical base 64-byte aligned.
    std::uint32_t data[16] = {7, 11};
    alloc_MAA();
    init_MAA();
    clear_mem_region();
    add_mem_region(data, data + 16);
    int lower = get_new_reg<std::int32_t>(0);
    int upper = get_new_reg<std::int32_t>(1);
    int stride = get_new_reg<std::int32_t>(1);
    int index = get_new_tile<std::uint32_t>();
    int result = get_new_tile<std::uint32_t>();
    maa_stream_load<std::uint32_t>(data, lower, upper, stride, index);
    wait_ready(index);
    std::uint32_t *index_data = get_cacheable_tile_pointer<std::uint32_t>(index);
    index_data[0] = 0;
    maa_indirect_load<std::uint32_t>(data, index, result);
    // Both sides touch data[0] and the CPU side writes. Its expected return9
    // deliberately agrees with ordinary execution if the hazard were omitted.
    data[0] = 9;
    wait_ready(result);
    return data[0];
}

std::uint32_t whole_same_thread_read_during_gather() {
    // One complete 64-byte line lies within this source allocation. The
    // separately owned mapping must keep its physical base 64-byte aligned.
    std::uint32_t data[16] = {7, 11};
    alloc_MAA();
    init_MAA();
    clear_mem_region();
    add_mem_region(data, data + 16);
    int lower = get_new_reg<std::int32_t>(0);
    int upper = get_new_reg<std::int32_t>(1);
    int stride = get_new_reg<std::int32_t>(1);
    int index = get_new_tile<std::uint32_t>();
    int result = get_new_tile<std::uint32_t>();
    maa_stream_load<std::uint32_t>(data, lower, upper, stride, index);
    wait_ready(index);
    std::uint32_t *index_data = get_cacheable_tile_pointer<std::uint32_t>(index);
    index_data[0] = 0;
    maa_indirect_load<std::uint32_t>(data, index, result);
    // A read/read overlap is permitted. Complete the command before the
    // source array leaves scope, independently of the earlier CPU observation.
    std::uint32_t observed = data[0];
    wait_ready(result);
    return observed;
}
