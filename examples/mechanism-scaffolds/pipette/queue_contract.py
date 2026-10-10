"""Paper-grounded abstract QRM lifecycle; not RTL/timing or an ISA emulator."""
from dataclasses import dataclass


class Blocked(Exception):
    pass


@dataclass(frozen=True)
class Ticket:
    queue: int
    position: int
    serial: int
    kind: str


@dataclass
class Entry:
    bits: int
    control: bool
    ticket: Ticket


class Queue:
    def __init__(self, capacity, producer, consumer):
        self.capacity = capacity
        self.producer = producer
        self.consumer = consumer
        self.head_spec = (
            self.head_commit
        ) = self.tail_spec = self.tail_commit = 0
        self.entries = {}
        self.dequeues = {}


class QRM:
    def __init__(self, physical_budget=148, max_queues=16):
        if type(physical_budget) is not int or not 1 <= physical_budget <= 148:
            raise ValueError("prototype physical budget")
        if type(max_queues) is not int or not 1 <= max_queues <= 16:
            raise ValueError("prototype queue count")
        self.budget = physical_budget
        self.max_queues = max_queues
        self.queues = {}
        self.serial = 0

    def configure(self, queue, capacity, producer, consumer):
        if any(
            type(x) is not int or x < 0
            for x in [queue, capacity, producer, consumer]
        ):
            raise ValueError("typed queue/actor/capacity")
        if producer == consumer or not 1 <= capacity <= 32:
            raise ValueError("point-to-point distinct actors and finite queue")
        if queue in self.queues and self.queues[queue].entries:
            raise ValueError("cannot remap active queue")
        if queue not in self.queues and len(self.queues) == self.max_queues:
            raise ValueError("finite queue count")
        reserved = sum(
            q.capacity for key, q in self.queues.items() if key != queue
        )
        if reserved + capacity > self.budget:
            raise ValueError("aggregate PRF allocation exceeded")
        self.queues[queue] = Queue(capacity, producer, consumer)

    def issue_enqueue(self, queue, actor, bits, control=False):
        if type(queue) is not int or type(actor) is not int:
            raise ValueError("typed queue and actor")
        q = self.queues[queue]
        if (
            actor != q.producer
            or type(bits) is not int
            or not 0 <= bits < 2**64
            or type(control) is not bool
        ):
            raise ValueError("wrong producer or raw word type")
        if q.tail_spec - q.head_commit == q.capacity:
            raise Blocked("full until committed dequeue")
        self.serial += 1
        t = Ticket(queue, q.tail_spec, self.serial, "enqueue")
        q.entries[q.tail_spec] = Entry(bits, control, t)
        q.tail_spec += 1
        return t

    def commit_enqueue(self, ticket):
        if type(ticket) is not Ticket:
            raise ValueError("opaque minted ticket required")
        q = self.queues[ticket.queue]
        e = q.entries.get(ticket.position)
        if (
            not e
            or e.ticket is not ticket
            or ticket.kind != "enqueue"
            or ticket.position != q.tail_commit
        ):
            raise ValueError("stale/out-of-order enqueue commit")
        q.tail_commit += 1

    def issue_dequeue(self, queue, actor):
        if type(queue) is not int or type(actor) is not int:
            raise ValueError("typed queue and actor")
        q = self.queues[queue]
        if actor != q.consumer:
            raise ValueError("wrong consumer")
        if q.head_spec == q.tail_commit:
            raise Blocked("no committed value")
        e = q.entries[q.head_spec]
        self.serial += 1
        ticket = Ticket(queue, q.head_spec, self.serial, "dequeue")
        q.dequeues[q.head_spec] = ticket
        q.head_spec += 1
        # Control delivery identifies handler redirection, not ordinary data.
        return ticket, {
            "kind": "control" if e.control else "data",
            "bits": e.bits,
            "queue": queue,
        }

    def commit_dequeue(self, ticket):
        if type(ticket) is not Ticket:
            raise ValueError("opaque minted ticket required")
        q = self.queues[ticket.queue]
        if (
            ticket.kind != "dequeue"
            or ticket.position != q.head_commit
            or q.dequeues.get(ticket.position) is not ticket
        ):
            raise ValueError("stale/out-of-order dequeue commit")
        del q.entries[ticket.position]
        del q.dequeues[ticket.position]
        q.head_commit += 1

    def peek_data(self, queue, actor):
        if type(queue) is not int or type(actor) is not int:
            raise ValueError("typed queue and actor")
        q = self.queues[queue]
        if actor != q.consumer:
            raise ValueError("wrong consumer")
        if q.head_spec == q.tail_commit:
            raise Blocked("empty")
        e = q.entries[q.head_spec]
        if e.control:
            raise NotImplementedError("CV peek handler microstate not modeled")
        return e.bits

    def squash_producer(self, queue, actor):
        if type(queue) is not int or type(actor) is not int:
            raise ValueError("typed queue and actor")
        q = self.queues[queue]
        if actor != q.producer:
            raise ValueError("wrong producer")
        for position in range(q.tail_commit, q.tail_spec):
            del q.entries[position]
        q.tail_spec = q.tail_commit

    def squash_consumer(self, queue, actor):
        if type(queue) is not int or type(actor) is not int:
            raise ValueError("typed queue and actor")
        q = self.queues[queue]
        if actor != q.consumer:
            raise ValueError("wrong consumer")
        q.dequeues.clear()
        q.head_spec = q.head_commit
