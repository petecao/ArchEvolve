unsigned int staged() {
  unsigned int data[2] = {1, 2};
  int tile = get_new_tile<unsigned int>();
  data[0] = 7;
  unsigned int got = data[0];
  assert(got == 7);
  return got;
}
