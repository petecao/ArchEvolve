# Probata verifier lineup on mbit10 (ticket 56). Source before any install or verifier run:
#   . /data1/yanruj/probata-verifiers/env.sh
# HOME is redirected so that no tool (opam, why3, SARL/CIVL, Java prefs, caches) writes under /home/yanruj.
export PROBATA=/data1/yanruj/probata-verifiers
export PROBATA_REAL_HOME=${PROBATA_REAL_HOME:-$HOME}
export HOME=$PROBATA/home
export XDG_CACHE_HOME=$HOME/.cache XDG_CONFIG_HOME=$HOME/.config XDG_DATA_HOME=$HOME/.local/share
export TMPDIR=$PROBATA/tmp
export OPAMROOT=$PROBATA/opam OPAMNOENVNOTICE=1 OPAMYES=1 OPAMJOBS=8 OPAMCOLOR=never
export WHY3CONFIG=$HOME/.why3.conf
export LLVM22=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64
export SAWBIN=$PROBATA/saw-1.6/saw-1.6-ubuntu-24.04-X64-with-solvers/bin
export CRUX=$PROBATA/crux-llvm-0.12/crux-llvm-0.12-ubuntu-24.04-X64
export CIVL_JAR=$PROBATA/civl-1.23/civl-1.23/lib/civl-complete.jar
export GENMC=$PROBATA/genmc-0.19.0/build/bin/genmc
export JAVA=/usr/lib/jvm/java-21-openjdk-amd64/bin/java
# $PROBATA/bin holds symlinks: z3 5.1.0, cvc5 1.2.1, cbmc 6.11.0 tools, opam 2.6.1, crux-llvm, saw.
export PATH=$PROBATA/bin:$LLVM22/bin:/usr/local/bin:/usr/bin:/bin
mkdir -p "$HOME" "$TMPDIR"
