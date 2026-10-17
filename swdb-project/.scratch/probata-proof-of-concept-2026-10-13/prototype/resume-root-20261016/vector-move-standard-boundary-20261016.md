# Vector move observation boundary

Created: 2026-10-16 ET.

The C++17 primary draft gives a move-constructed container the source's former
elements, but gives the moved-from source a valid, unspecified state. Neither the
general nor allocator-aware constructor table promises a zero source size.
Sources: [N4659 moved-from state](https://timsong-cpp.github.io/cppwp/n4659/lib.types.movedfrom)
and [N4659 container requirements, tables 83 and 86](https://timsong-cpp.github.io/cppwp/n4659/container.requirements.general).
The [current primary draft](https://eel.is/c++draft/lib.types.movedfrom) retains
that distinction.

The existing selected C model actually zeroes the source header, while its public
postcondition only promises validity plus destination data/size transfer. A
mathematical source-empty duty can describe that exact C implementation. It does
not establish a portable zero-size observation on the original C++ source under
the standard-only library assumption.

The new, unexecuted closed move fixture will observe the transferred destination
value and perform valid cleanup without asserting a particular moved-from size.
A stronger libc++ observation would require an explicit implementation-specific
contract and evidence. Existing scientific records and their identities are
preserved; no historical result is relabeled.
