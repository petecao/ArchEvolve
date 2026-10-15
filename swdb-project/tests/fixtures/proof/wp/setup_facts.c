/* Fresh WP verdict controls, ticket36. Created: 2026-10-15 ET.
   Each CASE isolates one premise defect so a consolidated Valid target cannot hide it. */
#ifndef CASE
#define CASE 0
#endif
#if CASE == 0
/*@ assigns \nothing; ensures \result == x; */
int f(int x) { return x; }
#elif CASE == 1
/*@ logic integer h(integer x); lemma hidden: h(2) == 12; */
/*@ assigns \nothing; */
void f(void) { /*@ assert target: h(2) == 12; */ }
#elif CASE == 2
/*@ requires x > 0; assigns \nothing; ensures \result > 0; */
int g(int x) { return x; }
/*@ assigns \nothing; ensures target: \result > 0; */
int f(void) { return g(0); }
#elif CASE == 3
/*@ terminates \false; assigns \nothing; ensures \result == 42; */
int g(void) { for (;;) {} }
/*@ assigns \nothing; ensures target: \result == 42; */
int f(void) { return g(); }
#elif CASE == 4
/*@ assigns \nothing; ensures target: \result == 42; */
int f(void) { /*@ admit dishonest: \false; */ return 0; }
#elif CASE == 5
/*@ axiomatic injected { axiom dishonest: \false; } */
/*@ assigns \nothing; ensures target: \result == 42; */
int f(void) { return 0; }
#elif CASE == 6
/*@ requires x > 0; requires x < 0; assigns \nothing; ensures target: \result == 42; */
int f(int x) { return 0; }
#elif CASE == 7
/*@ requires 0 <= n <= 10; assigns \nothing; ensures target: \result == 42; */
int f(int n) {
 int i = 0;
 /*@ loop invariant i >= 0; loop invariant i < 0; loop assigns i; loop variant n-i; */
 while (i < n) i++;
 return i;
}
#elif CASE == 8
/*@ assigns \nothing; ensures \result >= 0; */
int maa_summary(void);
/*@ assigns \nothing; ensures target: \result >= 0; */
int f(void) { return maa_summary(); }
#elif CASE == 12
#include "injected.h"
/*@ assigns \nothing; ensures target: \result == 42; */
int f(void) { return 0; }
#elif CASE == 9
/*@ assigns \nothing; ensures target: \result == 42; */
int f(void) { return 0; }
#endif
