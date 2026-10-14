// Ticket 05 spike fixture (2026-10-14 ET). Throwaway: written for spike (a), not DX100 code.
// Build: clang++ -std=c++17 -c -emit-llvm -g -O0 [-DBUGGY] fixture.cpp -o fixture.bc
// The three dx100 calls are declared only. SAW replaces each with an assumed spec (an
// override); those specs alone change the ghost state (see spike.saw).
// -DBUGGY removes the wait that covers the read: the negative control.

// One command, as the program hands it to the issue call. SAW reads the fields by name
// through debug information (llvm_field), as the real translator will (map 16 item 3).
// It sits at global scope: SAW 1.6 cannot resolve llvm_field names of a struct inside a
// namespace (run exp_ns_field; ticket 05 Answer).
struct Command {
  int kind;           // 0 = stream load (the only kind used here)
  int dst_tile;       // destination tile, 0 <= dst_tile < 8
  unsigned base;      // source offset (not used by the proof)
  unsigned range;     // elements to load
};

namespace dx100 {

// 8 tiles: the ghost array size in spike.saw.
void issue(const Command* cmd);         // marks cmd->dst_tile unready
void wait(int tile);                    // marks tile ready
unsigned read(int tile, unsigned idx);  // requires tile ready

}  // namespace dx100

// Two loads into distinct tiles a and b. Only b is waited before the read, so tile a is
// still unready when b is read. A per-tile ghost array tells the two apart; one flag for
// "some command pending" would reject the safe variant.
unsigned kernel(int a, int b, unsigned base) {
  Command ca{0, a, base, 4};
  Command cb{0, b, base + 4, 4};
  dx100::issue(&ca);
  dx100::issue(&cb);
#ifndef BUGGY
  dx100::wait(b);  // the covering wait for the reads below
#endif
  unsigned sum = 0;
  for (unsigned i = 0; i < 4; ++i) sum += dx100::read(b, i);
  dx100::wait(a);
  return sum;
}
