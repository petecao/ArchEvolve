"""2026-10-16 ET. Inert concrete one-step/partial-loop refinement inputs.

The unchanged complete backend supplies the concrete query, wait, completion and
memory effects. A prospective CBMC theorem must establish the one-step relation
before a WP quotient proof can be composed with it. This producer grants neither
premise authority nor verifier admission. The logical query is absent the source
header. Its same-entry assumed rule remains explicit.
"""
import hashlib
import re

BACKEND_SHA = 'c37481e56517d29729ffc83f2eb538cc5b5cb8ce5ab831babae3287cb332956f'


def need(value, message):
    if not value:
        raise ValueError(message)


def function_body(source, name):
    """Capture one fixed C definition, counting braces outside strings/comments."""
    matches = list(re.finditer(r'^static\s+(?:unsigned|void|uint64_t)\s+' + re.escape(name) + r'\s*\([^;]*?\)\s*\{', source, re.M))
    need(len(matches) == 1, 'one exact concrete definition required: ' + name)
    start = matches[0].start()
    cursor = matches[0].end() - 1
    depth = 0
    while cursor < len(source):
        if source.startswith('/*', cursor):
            end = source.find('*/', cursor + 2)
            need(end >= 0, 'unterminated C comment')
            cursor = end + 2
            continue
        if source.startswith('//', cursor):
            end = source.find('\n', cursor + 2)
            cursor = len(source) if end < 0 else end + 1
            continue
        char = source[cursor]
        if char in ('"', "'"):
            quote = char
            cursor += 1
            while cursor < len(source):
                if source[cursor] == '\\':
                    cursor += 2
                elif source[cursor] == quote:
                    cursor += 1
                    break
                else:
                    cursor += 1
            else:
                raise ValueError('unterminated C literal')
            continue
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return source[start:cursor + 1]
        cursor += 1
    raise ValueError('unterminated C function: ' + name)


CALLER = '''uint32_t fixture_ready_until_one(uint32_t before, uint32_t issued) {
    dxb_construct(before, issued);
    while (dxc_get_tile_ready(0) == 0) {
    }
    return dxb_observe();
}
'''

ZERO_CALLER = '''uint32_t fixture_ready_after_zero(uint32_t before, uint32_t issued) {
    dxb_construct(before, issued);
    unsigned ready = dxc_get_tile_ready(0);
    if (ready == 0) return dxb_observe();
    return issued;
}
'''

LOOP = r'''    /*@ loop invariant dxb_issued == issued;
        loop invariant dxb_pending <= 1;
        loop invariant dxb_pending == 0 ==> dxb_visible == issued;
        loop assigns dxb_pending, dxb_visible;
    */
'''

WP_PREFIX = r'''/*2026-10-16 ET. Conditional quotient; concrete one-step theorem required. */
#include <stdint.h>
static unsigned dxb_pending;
static uint32_t dxb_visible, dxb_issued;

/* An independent total nondeterministic primitive, not a progress premise. */
/*@ terminates \true;
    assigns \nothing;
    ensures \result <= 1;
*/
unsigned dxb_choice(void);

/*@ assigns dxb_pending, dxb_visible, dxb_issued;
    ensures dxb_pending == 1 && dxb_visible == before && dxb_issued == issued;
*/
static void dxb_construct(uint32_t before, uint32_t issued) {
    dxb_pending = 1;
    dxb_visible = before;
    dxb_issued = issued;
}

/* The single-step CBMC target relates this exact quotient to the unchanged
   complete backend query/wait/cover/action/memory closure. */
/*@ requires tile == 0;
    requires dxb_pending <= 1;
    requires dxb_pending == 0 ==> dxb_visible == dxb_issued;
    terminates \true;
    assigns dxb_pending, dxb_visible;
    ensures \result <= 1;
    ensures dxb_pending <= 1;
    ensures dxb_pending == 0 ==> dxb_visible == dxb_issued;
    ensures \result == 1 ==> dxb_pending == 0;
    ensures \result == 0 ==> dxb_pending == 1;
*/
static unsigned dxc_get_tile_ready(unsigned tile) {
    (void)tile;
    if (dxb_pending == 0) return 1;
    unsigned answer = dxb_choice();
    if (answer == 1) {
        dxb_visible = dxb_issued;
        dxb_pending = 0;
    }
    return answer;
}

/*@ requires dxb_pending == 0;
    requires dxb_visible == dxb_issued;
    assigns \nothing;
    ensures \result == dxb_issued;
*/
static uint32_t dxb_observe(void) {
    return dxb_visible;
}

/*@ terminates \false;
    assigns dxb_pending, dxb_visible, dxb_issued;
    ensures \result == issued;
*/
'''


def wp_without_loop_annotation():
    return WP_PREFIX + CALLER


def remove_loop_annotation(source):
    need(source.count(LOOP) == 1, 'one exact loop annotation required')
    return source.replace(LOOP, '', 1)


CONCRETE_PREFIX = r'''/*2026-10-16 ET. Fixed constructed one-command model scope only. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if defined(SWDB_CBMC)
extern unsigned nondet_uint(void);
extern uint32_t nondet_u32(void);
#define DXM_CHECK(c, rule) __CPROVER_assert((c), (rule))
#else
static void dxb_failure(const char *rule) {
    fprintf(stderr, "ready_failure=%s\n", rule);
    exit(17);
}
#define DXM_CHECK(c, rule) do { if (!(c)) dxb_failure(rule); } while (0)
#endif
#define DXM_NODES 16
#define DXM_CELLS 1
#define DXM_EVENTS 2
#define DXM_HISTORY 2
#define DXA_ACTIONS 1
#define DXC_COMMANDS 1
static unsigned dxb_answer, dxb_calls;
#if !defined(SWDB_CBMC)
static unsigned long long dxb_prefix;
static unsigned dxb_poll;
#endif
static unsigned dxb_concrete_choice(unsigned count) {
    DXM_CHECK(count == 2, "ready.choice.arity");
    ++dxb_calls;
#if !defined(SWDB_CBMC)
    if (dxb_poll) return dxb_calls <= dxb_prefix ? 0 : 1;
#endif
    return dxb_answer;
}
#define DXM_CHOOSE(n) dxb_concrete_choice(n)
'''

CONCRETE_SUFFIX = r'''
/* An explicit synthetic receiver, never an allocation/ownership grant.
   Zero-initialized static storage is a fresh program scope, not a reset of a
   live trace. Only the listed one command/action/four immutable nodes exist. */
static void dxb_state(unsigned pending, uint32_t before, uint32_t issued) {
    dxc_count = 1; dxc_constructing = 0;
    dxm_count = 4; dxa_count = 1;
    dxm_event_count = pending ? 0 : 1;
    dxm_memory[0] = pending ? before : issued;
    dxm_initialized[0] = 1;
    dxm_events[0] = (struct dxm_write_event){0, issued};
    for (unsigned i = 0; i < 4; ++i) {
        dxm_nodes[i].kind = 1;
        dxm_nodes[i].settled = 1;
    }
    dxm_nodes[0].value = 0;
    dxm_nodes[1].value = 1;
    dxm_nodes[2].value = issued;
    dxm_nodes[3].value = 0;
    dxc_commands[0] = (struct dxc_command){
        .thread = 0, .pending = pending, .bound = 1, .root = 0, .access = 2,
        .region = -1, .ready_roles = 1, .begin = 4096, .end = 4100
    };
    dxa_actions[0] = (struct dxa_action){
        .command = 0, .dtype = 0, .base = 0, .extent = 1, .index = 3,
        .value = 2, .active = 1, .done = pending ? 0 : 1, .kind = 0,
        .old_result = UINT_MAX
    };
    dxb_calls = 0;
}
static void dxb_construct(uint32_t before, uint32_t issued) {
    dxb_state(1, before, issued);
}
static uint32_t dxb_observe(void) {
    dxc_cpu_memory_access(0, 4096, 4100, 0);
    DXM_CHECK(dxc_commands[0].pending == 0, "ready.pending.read");
    DXM_CHECK(dxm_initialized[0] == 1, "ready.initialized.read");
    return (uint32_t)dxm_memory[0];
}
static void dxb_step(unsigned pending, uint32_t before, uint32_t issued, unsigned answer) {
    before = pending ? before : issued;
    dxb_answer = answer;
    dxb_state(pending, before, issued);
    unsigned ready = dxc_get_tile_ready(0);
    unsigned completed = !pending || answer == 1;
    DXM_CHECK(ready == (completed ? 1u : 0u), "ready.refinement.answer");
    DXM_CHECK(dxc_commands[0].pending == (completed ? 0u : 1u), "ready.refinement.pending");
    DXM_CHECK(dxm_memory[0] == (completed ? issued : before), "ready.refinement.value");
    DXM_CHECK(dxm_event_count == (completed ? 1u : 0u), "ready.refinement.event_count");
    DXM_CHECK(dxa_actions[0].done == (completed ? 1u : 0u), "ready.refinement.action");
    DXM_CHECK(dxb_calls == pending, "ready.refinement.choice_count");
    DXM_CHECK(dxc_count == 1 && dxc_constructing == 0 && dxm_count == 4 &&
        dxa_count == 1 && dxm_initialized[0] == 1 &&
        dxc_commands[0].thread == 0 && dxc_commands[0].access == 2 &&
        dxc_commands[0].region == -1 &&
        dxc_commands[0].ready_roles == 1 && dxc_commands[0].root == 0 &&
        dxc_commands[0].bound == 1 && dxc_commands[0].begin == 4096 &&
        dxc_commands[0].end == 4100 && dxc_commands[0].dependencies == 0 &&
        dxa_actions[0].command == 0 && dxa_actions[0].dtype == 0 &&
        dxa_actions[0].base == 0 && dxa_actions[0].extent == 1 &&
        dxa_actions[0].index == 3 && dxa_actions[0].value == 2 &&
        dxa_actions[0].active == 1 && dxa_actions[0].kind == 0 &&
        dxm_nodes[0].kind == 1 && dxm_nodes[1].kind == 1 &&
        dxm_nodes[2].kind == 1 && dxm_nodes[3].kind == 1 &&
        dxm_nodes[0].settled == 1 && dxm_nodes[0].value == 0 &&
        dxm_nodes[1].settled == 1 && dxm_nodes[1].value == 1 &&
        dxm_nodes[2].settled == 1 && dxm_nodes[2].value == issued &&
        dxm_nodes[3].settled == 1 && dxm_nodes[3].value == 0,
        "ready.refinement.frame");
    if (completed) DXM_CHECK(dxb_observe() == issued, "ready.refinement.read");
}
'''

CONCRETE_MAIN = r'''
#if defined(SWDB_CBMC)
int main(void) {
#if defined(READY_ZERO_READ)
    uint32_t before = nondet_u32(), issued = nondet_u32();
    dxb_answer = 0;
    (void)fixture_ready_after_zero(before, issued);
#else
    unsigned pending = nondet_uint(), answer = nondet_uint();
    uint32_t before = nondet_u32(), issued = nondet_u32();
    __CPROVER_assume(pending <= 1 && answer <= 1);
    dxb_step(pending, before, issued, answer);
#endif
    return 0;
}
#else
/* Canonical decimal protocol, checked before narrowing or backend entry. */
static int dxb_decimal(const char *input, unsigned long long maximum,
                       unsigned long long *output) {
    if (!input || !input[0] || (input[0] == '0' && input[1])) return 0;
    unsigned long long value = 0;
    unsigned count = 0;
    for (const char *cursor = input; *cursor; ++cursor) {
        if (++count > 20 || *cursor < '0' || *cursor > '9') return 0;
        unsigned digit = (unsigned)(*cursor - '0');
        if (digit > maximum || value > (maximum - digit) / 10) return 0;
        value = value * 10 + digit;
    }
    *output = value;
    return 1;
}
int main(int argc, char **argv) {
    if (argc != 5) return 64;
    unsigned long long before_value, issued_value, count;
    if (!dxb_decimal(argv[3], UINT32_MAX, &before_value) ||
        !dxb_decimal(argv[4], UINT32_MAX, &issued_value)) return 64;
    unsigned long long maximum;
    if (strcmp(argv[1], "step") == 0) maximum = 3;
    else if (strcmp(argv[1], "poll") == 0) maximum = 1000000;
    else if (strcmp(argv[1], "zero-read") == 0) maximum = 0;
    else return 64;
    if (!dxb_decimal(argv[2], maximum, &count)) return 64;
    uint32_t before = (uint32_t)before_value, issued = (uint32_t)issued_value;
    printf("ready_begin mode=%s count=%llu before=%u issued=%u\n",
        argv[1], count, (unsigned)before, (unsigned)issued);
    fflush(stdout);
    if (strcmp(argv[1], "step") == 0) {
        unsigned selector = (unsigned)count;
        dxb_step(selector / 2, before, issued, selector % 2);
    } else if (strcmp(argv[1], "poll") == 0) {
        dxb_prefix = count;
        dxb_poll = 1;
        DXM_CHECK(fixture_ready_until_one(before, issued) == issued, "ready.poll.result");
        DXM_CHECK(dxb_calls == dxb_prefix + 1, "ready.poll.prefix");
    } else if (strcmp(argv[1], "zero-read") == 0) {
        dxb_answer = 0;
        (void)fixture_ready_after_zero(before, issued);
        return 18;
    }
    printf("ready_complete calls=%u\n", dxb_calls);
    return 0;
}
#endif
'''


def prepare(backend):
    need(type(backend) is bytes and hashlib.sha256(backend).hexdigest() == BACKEND_SHA,
         'exact unchanged complete backend required')
    text = backend.decode('utf-8')
    functions = {}
    for name in ('dxc_get_tile_ready', 'dxc_wait_tile', 'dxc_cover', 'dxm_cover',
                 'dxa_complete', 'dxm_device_write', 'dxm_value', 'dxc_cpu_memory_access'):
        body = function_body(text, name)
        functions[name] = {'body': body, 'sha256': hashlib.sha256(body.encode()).hexdigest()}
    wp = WP_PREFIX + CALLER.replace('    while (', LOOP + '    while (', 1)
    need(remove_loop_annotation(wp) == wp_without_loop_annotation(), 'caller-only loop annotation inverse differs')
    concrete = CONCRETE_PREFIX + text + '\n' + CONCRETE_SUFFIX + CALLER + ZERO_CALLER + CONCRETE_MAIN
    return {
        'date': '2026-10-16 ET',
        'schema': 'prospective-concrete-readiness-refinement-2',
        'backend_sha256': BACKEND_SHA,
        'concrete_functions': functions,
        'concrete_c': concrete,
        'concrete_c_sha256': hashlib.sha256(concrete.encode()).hexdigest(),
        'wp_c': wp,
        'wp_c_sha256': hashlib.sha256(wp.encode()).hexdigest(),
        'wp_negative_c': WP_PREFIX + ZERO_CALLER,
        'wp_negative_c_sha256': hashlib.sha256((WP_PREFIX + ZERO_CALLER).encode()).hexdigest(),
        'caller_sha256': hashlib.sha256(CALLER.encode()).hexdigest(),
        'topology': {'commands': 1, 'actions': 1, 'immutable_nodes': 4,
                     'ordinary_cells': 1, 'thread': 0, 'counted_tile': 0,
                     'dtype': 'uint32_t', 'other_activity': False},
        'correctness': 'partial correctness; infinite zero observations remain permitted',
        'same_entry_logical_rule': 'finite_logical_ready',
        'original_header_query': None,
        'native_control_plan': native_controls(),
        'required_acceptance': [
            'An actual complete one-step CBMC result with every property and actual loop unwinding checks; all states in the stated relation, including completed/stuttering states.',
            'An actual ordinary WP ledger for every quotient helper and the unbounded caller, all RTE/init/frame goals and healthy nonproof smokes.',
            'Exact same-entry physical rules and typed TraceUnit context plus separately checked constructed receiver facts.',
            'Independent source relation review and actual native full-backend zero-prefix/completion plus failing-zero-read controls.',
            'Dedicated public partial-summary method, fresh source/producer rechecks and exact refinement/loop records; no generic SourceUnit or original-header claim.',
        ],
        'refinement_accepted': False,
        'public_adoption': False,
    }


def native_controls():
    """Prospective fixed argv/readback checks; none is executed by preparation."""
    rows = []
    def add(argv, exit_code):
        rows.append({'argv': list(argv), 'expected_exit': exit_code,
                     'actual_execution': False})
    for selector in range(4):
        for before, issued in ((0, 0), (0, 4294967295), (4294967295, 0), (3, 7)):
            add(('step', str(selector), str(before), str(issued)), 0)
    for prefix in (0, 1, 17, 10000):
        add(('poll', str(prefix), '3', '7'), 0)
    for before in (3, 7):
        add(('zero-read', '0', str(before), '7'), 17)
    for value in ('', '-1', '+1', '00', '7junk', '4294967296', '18446744073709551616'):
        add(('step', '0', value, '7'), 64)
        add(('step', '0', '3', value), 64)
    for value in ('', '00', '4', '4294967296', '18446744073709551616', '0junk'):
        add(('step', value, '3', '7'), 64)
    for value in ('1000001', '-1', '1junk'):
        add(('poll', value, '3', '7'), 64)
    add(('zero-read', '1', '3', '7'), 64)
    add(('other-mode', '0', '3', '7'), 64)
    return rows
