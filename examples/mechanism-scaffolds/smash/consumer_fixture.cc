// New integer-only source fixture for SMASH Algorithm 1 coordinate use.
// .at() checks output bounds without changing the printed index arithmetic.
#include <cassert>
#include <cstddef>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

using Word = long long;
using Vec = std::vector<Word>;

Vec printedLoop(std::size_t rows, std::size_t rowInd,
                std::size_t colInd, const Vec &block, const Vec &x)
{
    Vec C(rows, 0);
    for (std::size_t ctrElmt = 0; ctrElmt < block.size(); ++ctrElmt) {
        C.at(rowInd + ctrElmt) += block.at(ctrElmt) *
                                 x.at(colInd + ctrElmt);
    }
    return C;
}

Vec flatBlockConsumer(std::size_t rows, std::size_t columns,
                      std::size_t flatStart, const Vec &block, const Vec &x)
{
    if (rows == 0 || columns == 0 ||
        rows > std::numeric_limits<std::size_t>::max() / columns ||
        x.size() != columns ||
        flatStart > rows * columns ||
        block.size() > rows * columns - flatStart) {
        throw std::invalid_argument("incomplete declared block");
    }
    Vec C(rows, 0);
    for (std::size_t lane = 0; lane < block.size(); ++lane) {
        const auto flat = flatStart + lane;
        C.at(flat / columns) += block.at(lane) * x.at(flat % columns);
    }
    return C;
}

int main()
{
    // These tiny bounded fixtures cannot overflow integer arithmetic.
    const Vec x{10, 20, 30, 40};
    const auto expected = Vec{50, 0};
    assert(printedLoop(2, 0, 0, Vec{1, 2}, x) != expected);
    assert(flatBlockConsumer(2, 4, 0, Vec{1, 2}, x) == expected);
    bool bounds = false;
    try {
        (void)printedLoop(2, 1, 0, Vec{1, 2}, x);
    } catch (const std::out_of_range &) {
        bounds = true;
    }
    assert(bounds);
    assert(flatBlockConsumer(2, 4, 4, Vec{1, 2}, x) == Vec({0, 50}));
    assert(flatBlockConsumer(2, 4, 3, Vec{3, 4}, x) == Vec({120, 40}));
    assert(flatBlockConsumer(2, 4, 0, Vec{0, 2}, x) == Vec({40, 0}));
    bool invalid = false;
    try {
        (void)flatBlockConsumer(2, 4, 7, Vec{1, 2}, x);
    } catch (const std::invalid_argument &) {
        invalid = true;
    }
    assert(invalid);
    bool overflow = false;
    try {
        (void)flatBlockConsumer(std::numeric_limits<std::size_t>::max(),
                                4, 0, Vec{1}, x);
    } catch (const std::invalid_argument &) {
        overflow = true;
    }
    assert(overflow);
    std::cout << "within-row mismatch and row-end overflow reproduced; "
                 "flat lane mapping and bounds PASS\n";
}
