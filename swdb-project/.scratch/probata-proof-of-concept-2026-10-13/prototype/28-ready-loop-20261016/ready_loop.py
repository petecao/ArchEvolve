"""2026-10-16 ET. Prospective one-command readiness quotient, no admission.

This isolates the unbounded polling proof from the finite whole-model replay.
The concrete-model/source refinement is a separate mandatory obligation. It is
never an original interface declaration or a generic WP summary fallback.
"""
import hashlib

MODEL_SHA = 'c37481e56517d29729ffc83f2eb538cc5b5cb8ce5ab831babae3287cb332956f'
METHOD = 'method.wp-dx100-ready-partial-v1'


def need(value, message):
    if not value:
        raise ValueError(message)


def step(pending, visible, issued, answer):
    """Total mathematical quotient transition over the exact selected domain.

    A completed command has already installed its issued value. A pending
    command permits either answer; only one installs the write and covers it.
    Repetition of zero has no budget or progress effect.
    """
    need(type(pending) is int and pending in (0, 1), 'exact pending bit required')
    need(type(answer) is int and answer in (0, 1), 'exact nondeterministic answer bit required')
    need(all(type(x) is int and 0 <= x < 2**32 for x in (visible, issued)),
         'exact unsigned32 tile values required')
    need(pending == 1 or visible == issued, 'completed command must have installed its write')
    if pending == 0 or answer == 1:
        return 1, 0, issued
    return 0, 1, visible


C_SOURCE = r'''/*2026-10-16 ET. Prospective isolated readiness quotient only.
 * One owned physical tile, one bound pending write, no dependency/other issue.
 * No actual header query, concrete-model refinement or source admission.
 */
#include <stdint.h>

/* Logical nondeterministic observation, independently chosen on each call.
 * This permits any finite zero prefix and the infinite all-zero behavior.
 * The primitive observation returns; the polling caller need not terminate.
 */
/*@ terminates \true;
    assigns \nothing;
    ensures \result <= 1;
*/
unsigned swdb_ready_choice(void);

/*@ terminates \false;
    assigns \nothing;
    ensures \result == issued;
*/
uint32_t fixture_ready_until_one(uint32_t before, uint32_t issued) {
    unsigned pending = 1;
    uint32_t visible = before;
    unsigned ready = 0;
    /*@ loop invariant pending <= 1;
        loop invariant ready <= 1;
        loop invariant pending == 0 ==> visible == issued;
        loop invariant ready == 1 ==> pending == 0;
        loop assigns pending, visible, ready;
    */
    while (ready == 0) {
        if (pending == 0) {
            ready = 1;
        } else {
            ready = swdb_ready_choice();
            if (ready == 1) {
                visible = issued;
                pending = 0;
            }
        }
    }
    /*@ assert ready == 1; */
    /*@ assert pending == 0; */
    return visible;
}

/* Negative witness: a permitted zero observation covers nothing. The access
 * obligation must fail even when the old value happens to equal issued.
 */
/*@ assigns \nothing; ensures \result == issued; */
uint32_t fixture_ready_zero_read(uint32_t before, uint32_t issued) {
    unsigned pending = 1;
    uint32_t visible = before;
    unsigned ready = 0;
    /*@ assert ready == 0; */
    /*@ assert pending == 0; */
    return visible;
}
'''


def prepare(backend):
    """Return inert proof inputs with every unproved bridge stated explicitly."""
    need(type(backend) is bytes and hashlib.sha256(backend).hexdigest() == MODEL_SHA,
         'exact whole-model source bytes required')
    need(b'static unsigned dxc_get_tile_ready(unsigned tile)' in backend
         and b'if (ready) dxc_wait_tile(tile);' in backend,
         'logical query and covering-wait source anchors required')
    return {
        'date': '2026-10-16 ET',
        'kind': 'prospective-one-command-readiness-quotient-1',
        'method': METHOD,
        'model_sha256': MODEL_SHA,
        'logical_query': 'dxc_get_tile_ready',
        'source_interface_call': None,
        'topology': {'pending_commands': 1, 'thread': 0, 'physical_tile': 0,
                     'owned_physical_tiles': [0], 'operand_bytes': 4,
                     'dependencies': [], 'other_issues_during_poll': False},
        'correctness': 'partial; no fairness or eventual-ready premise',
        'C_source': C_SOURCE,
        'C_source_sha256': hashlib.sha256(C_SOURCE.encode()).hexdigest(),
        'required_bridges': [
            'Exact fixed synthetic event/source spans, receiver and issued write image.',
            'One-command concrete-model query/wait/completion quotient correspondence.',
            'The same new0.2 entry and explicit MMIO/visibility assumption references.',
            'Dedicated partial method and all ordinary RTE/frame/init/smoke goals.',
            'Original source native/negative replay and public proof records.',
        ],
        'concrete_model_refinement_admitted': False,
        'public_source_or_ticket_acceptance': False,
    }
