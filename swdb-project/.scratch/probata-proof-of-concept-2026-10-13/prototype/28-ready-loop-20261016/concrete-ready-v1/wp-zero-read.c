/*2026-10-16 ET. Conditional quotient; concrete one-step theorem required. */
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
uint32_t fixture_ready_after_zero(uint32_t before, uint32_t issued) {
    dxb_construct(before, issued);
    unsigned ready = dxc_get_tile_ready(0);
    if (ready == 0) return dxb_observe();
    return issued;
}
