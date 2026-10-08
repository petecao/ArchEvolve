"""PHI bulk-phase/visibility contract; no arithmetic/coherence/timing model."""


class BulkPhase:
    def __init__(
        self,
        *,
        relaxed_atomic,
        no_intervening_reads,
        contiguous_physical,
        bins_proven,
        needs_old_value=False,
        ordered_fp_bits=False,
        mixed_conventional_atomics=False
    ):
        if any(
            type(x) is not bool
            for x in [
                relaxed_atomic,
                no_intervening_reads,
                contiguous_physical,
                bins_proven,
                needs_old_value,
                ordered_fp_bits,
                mixed_conventional_atomics,
            ]
        ):
            raise ValueError("explicit typed adoption obligations")
        if (
            not all(
                [
                    relaxed_atomic,
                    no_intervening_reads,
                    contiguous_physical,
                    bins_proven,
                ]
            )
            or needs_old_value
            or ordered_fp_bits
            or mixed_conventional_atomics
        ):
            raise ValueError("outside examined bulk commutative mapping")
        self.state = "configured"
        self.pending_bins = set()
        self.private_flushed = False

    def enable_batching(self):
        if self.state != "configured":
            raise ValueError("invalid phase transition")
        self.state = "ingest"

    def record_batched_bin(self, bin_id):
        if self.state != "ingest" or type(bin_id) is not int or bin_id < 0:
            raise ValueError("only first phase may create batching work")
        self.pending_bins.add(bin_id)

    def disable_batching(self):
        if self.state != "ingest":
            raise ValueError("invalid phase transition")
        self.state = "replay"

    def replay_complete(self, bin_id):
        if (
            self.state != "replay"
            or type(bin_id) is not int
            or bin_id not in self.pending_bins
        ):
            raise ValueError("unowned/duplicate bin completion")
        self.pending_bins.remove(bin_id)

    def private_flush_complete(self):
        if self.state != "replay" or self.pending_bins:
            raise ValueError("all batched replay required before final flush")
        self.private_flushed = True

    def sync(self):
        if (
            self.state != "replay"
            or self.pending_bins
            or not self.private_flushed
        ):
            raise ValueError("phi_sync visibility not established")
        self.state = "visible"

    def read(self):
        if self.state != "visible":
            raise ValueError("read before updates fully applied and flushed")
        return "SHARED_CACHE_READ_MERGE_STILL_REQUIRED"

    def page_out(self):
        if self.state == "ingest":
            raise ValueError("disable batching before paging data")
        return "OWNER_MAPPING_TEARDOWN_PROOF_REQUIRED"
