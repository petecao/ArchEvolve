"""Diagnostic wrapper preserving the pinned author's internal ROI. Updated: 2026-09-26."""

AUTHOR_ROI = 'bfs.dx100.traversal.v1'
HOOKS = {'m5_reset_stats': 'activate source scopes, then forward the actual reset',
         'm5_dump_stats': 'deactivate source scopes, then forward the actual dump'}


def driver(source, model, function, diagnostic):
    """Reuse trusted result checking, preserving the original internal exit."""
    from swdb.dx100_candidate import SUPPRESSED, driver as complete_driver
    text = complete_driver(source, model, function, diagnostic, trusted_graph=False)
    noop = '\n'.join(f'#define {name}(...) ((void)0)' for name in SUPPRESSED)
    hooks = '''inline void swdb_author_reset_stats(uint64_t delay, uint64_t period) {
  ::swdb_profile::start();
  m5_reset_stats(delay, period);
}
inline void swdb_author_dump_stats(uint64_t delay, uint64_t period) {
  ::swdb_profile::stop();
  m5_dump_stats(delay, period);
}
#define m5_reset_stats swdb_author_reset_stats
#define m5_dump_stats swdb_author_dump_stats'''
    if text.count(noop) != 1:
        raise ValueError('trusted driver suppression template changed')
    text = text.replace(noop, hooks)
    # Only remove generated outer events. The included, separately hashed
    # author translation unit retains its own work/reset/dump/exit sequence.
    for line in (
        '  std::cout << "ROI started: 4 configured threads" << std::endl;\n',
        '  m5_work_begin(0, 0);\n', '  m5_reset_stats(0, 0);\n',
        '  ::swdb_profile::start();\n', '  ::swdb_profile::stop();\n',
        '  m5_dump_stats(0, 0);\n', '  m5_work_end(0, 0);\n',
        '  std::cout << "ROI End!!!" << std::endl;\n', '  m5_exit(0);\n'):
        # start/stop also occur in the forwarding hooks: remove the last
        # occurrence, which belongs to the trusted generated main.
        position = text.rfind(line)
        if position < 0:
            raise ValueError('trusted outer event template changed')
        text = text[:position] + text[position + len(line):]
    return text.replace('Complete BFS call only.', 'Author traversal ROI; independent source-scope diagnostic.').replace(
        'SWDB complete-call BFS', 'SWDB author-ROI BFS')
