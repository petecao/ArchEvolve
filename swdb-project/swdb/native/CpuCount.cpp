// Counting-only driver; never used for calibration timing. Created 2026-10-06 ET.
#include "CpuWork.h"
#include <cstdlib>
#include <iostream>
#include <string>
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    uint64_t n = std::strtoull(argv[2], nullptr, 10);
    std::string shape = argv[1];
    if (shape == "integer") std::cout << compute_integer(n, 1);
    else if (shape == "floating_point") std::cout << compute_floating_point(n, 1);
    else if (shape == "branch") std::cout << compute_branch(n, 1);
    else if (shape == "atomic") std::cout << compute_atomic(n, 1);
    else return 2;
    return 0;
}
