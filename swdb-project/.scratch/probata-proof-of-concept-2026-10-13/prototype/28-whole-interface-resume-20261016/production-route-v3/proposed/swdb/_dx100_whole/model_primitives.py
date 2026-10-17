"""2026-10-16 ET. Exact pure checked-model primitives; portable composition owns I/O."""

class Refused(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise Refused(message)


def check_contract_inventory(calls, declarations):
    """Future validator seam: deleting even one source-name contract refuses.

    This structural gate does not establish the bodies' value correspondence;
    exact checked_design identity and source/model pins provide that boundary.
    """
    need(type(calls) is list and len(calls) == 26
         and len({row.get("call") for row in calls if type(row) is dict}) == 26,
         "exactly one checked-body contract for every interface name required")
    need({row["call"] for row in calls} == {row["name"] for row in declarations},
         "complete original interface contract inventory required")
    for row in calls:
        actual = row.get("source_declarations")
        expected = [item for item in declarations if item["name"] == row["call"]]
        need(type(actual) is list and len(actual) == len(expected),
             "every overload declaration needs its original source binding")


def hook_text(choice_budget):
    """All finite choices use independent harness draws and a fatal budget.

    These are future harness draws, not zero-initialized ghost assumptions. The
    public harness consumer must fill every uint32 entry independently before
    the source unit executes, and bind that draw plan in its method identity.
    Modulo maps the entire uint32 domain onto every positive uint32-sized choice domain; the draw count budget is independent of the alternative count.
    No source/capacity check or desired result is assumed by this emitter.
    """
    need(type(choice_budget) is int and 1 <= choice_budget <= 256,
         "bounded independently drawn choice table required")
    return """/* Checked-body hooks: preserve every ordinary property. */
#include <stdint.h>
#include <stddef.h>
#ifndef SWDB_CHECK
#error "public checked-property hooks must precede model assembly"
#endif
static uint32_t dws_choice_table[%d];
static unsigned dws_choice_used;
static unsigned dws_model_choose(unsigned alternatives) {
  SWDB_CHECK(alternatives>0,"whole-choice-domain");
  SWDB_CHECK(dws_choice_used<%du,"whole-choice-capacity");
  return dws_choice_table[dws_choice_used++] %% alternatives;
}
#define DXM_CHECK(condition,rule) SWDB_CHECK((condition),rule)
#define DXM_CHOOSE(alternatives) dws_model_choose(alternatives)
""" % (choice_budget, choice_budget)
