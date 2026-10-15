// 2026-10-15 ET: same-spelled unrelated enums must not select a different value or type.
int enum_noise() { enum Flag { Value=0 }; return Value; }
enum Flag { Value=1 };
int enum_value_collision() { return Value; }
bool atomic_enum_collision(int *p,int *e) {
  return __atomic_compare_exchange_n(p,e,9,Value,5,0);
}
int type_noise() { enum class Wide:unsigned char { X=0 }; return 0; }
enum class Wide:long long { X=4294967296LL };
long long enum_type_collision(Wide x) { return (long long)x; }
int mixed_noise() { enum Mixed { X=0 }; return X; }
struct Mixed { long long value; };
int mixed_enum_record_collision() { return sizeof(Mixed); }
