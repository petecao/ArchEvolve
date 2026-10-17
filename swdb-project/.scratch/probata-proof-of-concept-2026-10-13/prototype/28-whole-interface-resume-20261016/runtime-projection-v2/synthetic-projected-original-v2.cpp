// 2026-10-16 ET. INERT public-source preparation fixture, never executed here.
// Root must obtain actual full-TU/ABI/source/CPU-access certificates first.
#include "dws_original_runtime.hpp"
#include <cassert>
#include <cstdint>

std::uint32_t whole_interface_source_fixture() {
    dws_cxx_array<std::uint32_t,2,0> data = {1, 2};
    dws_cxx_array<std::int32_t,2,1> limits = {0, 1};
    alloc_MAA();
    init_MAA();
    clear_mem_region();
    add_mem_region(data, data + 2);
    add_mem_region(limits, limits + 2);

    int index = get_new_tile<std::uint32_t>();
    int source = get_new_tile<std::uint32_t>();
    int result = get_new_tile<std::uint32_t>();
    int minimum = get_new_tile<std::int32_t>();
    int maximum = get_new_tile<std::int32_t>();
    int output_i = get_new_tile<std::int32_t>();
    int output_j = get_new_tile<std::int32_t>();
    int scalar = get_new_reg<std::uint32_t>(3);
    int spare = get_new_reg<std::uint32_t>();
    set_reg<std::uint32_t>(spare, 4);
    maa_const<std::uint32_t>(3, scalar);
    int min_reg = get_new_reg<std::int32_t>(0);
    int max_reg = get_new_reg<std::int32_t>(2);
    int stride = get_new_reg<std::int32_t>(1);
    int last_i = get_new_reg<std::int32_t>(0);
    int last_j = get_new_reg<std::int32_t>(-1);
    std::uint32_t initial_scalar = get_reg<std::uint32_t>(scalar);
    assert(initial_scalar == 3);
    DataType selected_type = get_data_type<std::uint32_t>();
    assert(selected_type == DataType::UINT32_TYPE);
    DataType other_type = get_data_type<unsigned short>();
    assert(other_type == DataType::MAX);

    // Source stream producers establish sizes and initialized payloads.
    maa_stream_load<std::uint32_t>(data, min_reg, max_reg, stride, index);
    wait_ready(index);
    maa_stream_load<std::uint32_t>(data, min_reg, max_reg, stride, source);
    wait_ready(source);
    maa_stream_load<std::int32_t>(limits, min_reg, max_reg, stride, minimum);
    wait_ready(minimum);
    maa_stream_load<std::int32_t>(limits, min_reg, max_reg, stride, maximum);
    wait_ready(maximum);

    dws_cxx_pointer<std::uint32_t> index_data = get_cacheable_tile_pointer<std::uint32_t>(index);
    dws_cxx_pointer<std::uint32_t> source_data = get_cacheable_tile_pointer<std::uint32_t>(source);
    dws_cxx_pointer<std::uint32_t> result_data = get_cacheable_tile_pointer<std::uint32_t>(result);
    dws_cxx_pointer<std::int32_t> min_data = get_cacheable_tile_pointer<std::int32_t>(minimum);
    dws_cxx_pointer<std::int32_t> max_data = get_cacheable_tile_pointer<std::int32_t>(maximum);
    dws_cxx_address<std::uint32_t> address_only = get_noncacheable_tile_pointer<std::uint32_t>(result);
    (void)address_only;  // No unmodeled noncacheable dereference.
    index_data[0] = 0; index_data[1] = 1;
    source_data[0] = 7; source_data[1] = 9;
    min_data[0] = 0; min_data[1] = 1;
    max_data[0] = 1; max_data[1] = 2;

    maa_alu_scalar<std::uint32_t>(source, scalar, result, Operation_t::ADD_OP);
    wait_ready(result);
    std::uint32_t observed_scalar = result_data[0];
    assert(observed_scalar == 10);
    maa_alu_vector<std::uint32_t>(source, source, result, Operation_t::ADD_OP);
    wait_ready(result);
    std::uint32_t observed_vector = result_data[1];
    assert(observed_vector == 18);
    maa_alu_reduce<std::uint32_t>(source, scalar, Operation_t::ADD_OP);
    wait_ready(source);
    std::uint32_t observed_reduce = get_reg<std::uint32_t>(scalar);
    assert(observed_reduce == 16);
    maa_stream_store<std::uint32_t>(data, min_reg, max_reg, stride, source);
    wait_ready(source);
    std::uint32_t stored0 = data[0], stored1 = data[1];
    assert(stored0 == 7 && stored1 == 9);
    maa_indirect_load<std::uint32_t>(data, index, result);
    wait_ready(result);
    maa_indirect_store_vector<std::uint32_t>(data, index, source, -1, result);
    wait_ready(result);
    maa_indirect_store_scalar<std::uint32_t>(data, index, scalar, -1, result);
    wait_ready(result);
    maa_indirect_rmw_vector<std::uint32_t>(data, index, source, Operation_t::ADD_OP, -1, result);
    wait_ready(result);
    maa_indirect_rmw_scalar<std::uint32_t>(data, index, scalar, Operation_t::ADD_OP, -1, result);
    wait_ready(result);
    std::uint32_t final0 = data[0], final1 = data[1];
    assert(final0 == 39 && final1 == 41);
    maa_range_loop<std::int32_t>(last_i, last_j, minimum, maximum, stride, output_i, output_j);
    wait_ready(output_i);
    std::int32_t final_i = get_reg<std::int32_t>(last_i);
    assert(final_i == 2);
    std::uint16_t result_size = get_tile_size(result);
    assert(result_size == 2);
    print_tile<std::uint32_t>(result);
    return data[0] + data[1];
}
