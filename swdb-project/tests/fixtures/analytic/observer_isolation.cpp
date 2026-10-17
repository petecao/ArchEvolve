// Native weak-ODR runtime-helper fixture; no application evidence. Created: 2026-10-06 ET.
#include <sstream>
#include <iostream>
extern "C" void __swdb_begin();
extern "C" void __swdb_end();
int main(){
  __swdb_begin();
  std::ostringstream value;
  value<<"fixture-output";
  std::cout<<value.str()<<'\n';
  __swdb_end();
}
