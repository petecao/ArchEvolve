#define assert(expr) (static_cast <bool> (expr) ? void (0) : __assert_fail (#expr, __FILE__, __LINE__, __ASSERT_FUNCTION))
