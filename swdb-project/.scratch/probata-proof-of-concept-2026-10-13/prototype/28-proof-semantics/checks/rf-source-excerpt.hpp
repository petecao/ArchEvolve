// 2026-10-16 ET: exact RF class/constructors at e4fc4af, isolated from gem5 dependencies.
#include <cstring>
#define panic_if(c,...) do { if(c) abort(); } while(0)
namespace gem5 {
class RF {
protected:
    uint8_t *data;
    unsigned int num_regs;

public:
    template <typename T>
    void check_reg_id(int reg_id) {
        panic_if(reg_id < 0 || reg_id >= num_regs, "Invalid reg_id: %d\n", reg_id);
        panic_if(sizeof(T) != 4 && sizeof(T) != 8, "Invalid data type size: %d\n", sizeof(T));
        panic_if(sizeof(T) == 8 && reg_id >= num_regs - 1, "Invalid reg_id for 8-byte data type: %d\n", reg_id);
    }
    template <typename T>
    T getData(int reg_id) {
        check_reg_id<T>(reg_id);
        return *((T *)(data + reg_id * 4));
    }
    uint8_t *getDataPtr(int reg_id) {
        check_reg_id<uint32_t>(reg_id);
        return (uint8_t *)(data + reg_id * 4);
    }
    template <typename T>
    void setData(int reg_id, T _data) {
        check_reg_id<T>(reg_id);
        *((T *)(data + reg_id * 4)) = _data;
    }

public:
    RF(unsigned int _num_regs);
    ~RF();
};
RF::RF(unsigned int _num_regs) : num_regs(_num_regs) {
    data = new uint8_t[num_regs * 4];
    memset(data, 0, num_regs * 4 * sizeof(uint8_t));
}
RF::~RF() {
    assert(data != nullptr);
    delete[] data;
}
}
