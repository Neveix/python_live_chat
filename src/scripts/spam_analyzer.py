import argparse
from dataclasses import dataclass
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--run-id", "-i", type=int, default=1, dest="run_id")
parser.add_argument("--show-lost", action="store_true", dest="show_lost",
                    help="Show lost (not sent or not recvd) and quit.")
parsed = parser.parse_args()

run_id: int = parsed.run_id
show_lost: bool = parsed.show_lost

log_path = Path("log") / f"spam_bots-{run_id}.txt"


@dataclass
class Message:
    sent_ns: int | None = None
    srv_recv_ns: int | None = None
    recv_ns: int | None = None


messages: dict[str, Message] = {}
lines_read = sent_count = recv_count = srv_recv_count = 0

with open(log_path, mode="r") as f:
    while line := f.readline():
        parts = line.split()
        if len(parts) != 3:
            print(f"malformed line: {line!r}")
            continue
        op, msg_hash, ns_str = parts
        monotonic_ns = int(ns_str)

        msg = messages.setdefault(msg_hash, Message())

        if op == "SENT":
            sent_count += 1
            if msg.sent_ns is not None:
                print(f"sent_ns of {msg_hash} already exists!")
            msg.sent_ns = monotonic_ns
        elif op == "SRV_RECV":
            srv_recv_count += 1
            if msg.srv_recv_ns is not None:
                print(f"srv_recv_ns of {msg_hash} already exists!")
            msg.srv_recv_ns = monotonic_ns
        elif op == "RECV":
            recv_count += 1
            if msg.recv_ns is not None:
                print(f"recv_ns of {msg_hash} already exists!")
            msg.recv_ns = monotonic_ns
        else:
            print(f"unknown operation: {op}")

        lines_read += 1


def percentile(sorted_values: list[int], p: float) -> float:
    if not sorted_values:
        return 0.0
    idx = max(0, min(len(sorted_values) - 1,
                     int((p / 100) * len(sorted_values) + 0.999999) - 1))
    return float(sorted_values[idx])


NS_PER_S = 10**9


def print_stats(name: str, diffs_ns: list[int]) -> None:
    """Печатает min/p50/p95/p99/max/avg для списка задержек в наносекундах."""
    if not diffs_ns:
        print(f"{name}: no data")
        return
    diffs_ns = sorted(diffs_ns)
    print(f"{name} (n={len(diffs_ns)}):")
    print(f"  avg: {sum(diffs_ns) / len(diffs_ns) / NS_PER_S:.6f} s")
    print(f"  min: {diffs_ns[0] / NS_PER_S:.6f} s")
    print(f"  p50: {percentile(diffs_ns, 50) / NS_PER_S:.6f} s")
    print(f"  p95: {percentile(diffs_ns, 95) / NS_PER_S:.6f} s")
    print(f"  p99: {percentile(diffs_ns, 99) / NS_PER_S:.6f} s")
    print(f"  max: {diffs_ns[-1] / NS_PER_S:.6f} s")


def run_default() -> None:
    print(f"Lines read: {lines_read}")
    print(f"Sent:       {sent_count}")
    print(f"Srv recv:   {srv_recv_count}")
    print(f"Received:   {recv_count}")
    print()

    bot_to_srv: list[int] = []
    srv_to_obs: list[int] = []
    end_to_end: list[int] = []

    for msg in messages.values():
        if msg.sent_ns is not None and msg.srv_recv_ns is not None:
            bot_to_srv.append(msg.srv_recv_ns - msg.sent_ns)
        if msg.srv_recv_ns is not None and msg.recv_ns is not None:
            srv_to_obs.append(msg.recv_ns - msg.srv_recv_ns)
        if msg.sent_ns is not None and msg.recv_ns is not None:
            end_to_end.append(msg.recv_ns - msg.sent_ns)

    print_stats("bot -> server", bot_to_srv)
    print()
    print_stats("server -> observer", srv_to_obs)
    print()
    print_stats("end-to-end (bot -> observer)", end_to_end)


def run_show_lost() -> None:
    lost_any = False
    for msg_hash, msg in messages.items():
        missing = []
        if msg.sent_ns is None:
            missing.append("SENT")
        if msg.srv_recv_ns is None:
            missing.append("SRV_RECV")
        if msg.recv_ns is None:
            missing.append("RECV")
        if not missing:
            continue
        lost_any = True
        print(f"{msg_hash}  missing: {', '.join(missing)}  "
              f"(sent={msg.sent_ns} srv_recv={msg.srv_recv_ns} recv={msg.recv_ns})")

    if not lost_any:
        print("no lost messages")
    else:
        # сводка по типам потерь
        only_no_recv = sum(1 for m in messages.values()
                           if m.sent_ns is not None and m.srv_recv_ns is not None and m.recv_ns is None)
        no_srv_recv = sum(1 for m in messages.values()
                          if m.sent_ns is not None and m.srv_recv_ns is None)
        no_sent = sum(1 for m in messages.values() if m.sent_ns is None)
        print()
        print(f"sent but no SRV_RECV (lost before/at server): {no_srv_recv}")
        print(f"SRV_RECV but no RECV (lost after server):    {only_no_recv}")
        print(f"no SENT (received without send?):            {no_sent}")


if not show_lost:
    run_default()
else:
    run_show_lost()
