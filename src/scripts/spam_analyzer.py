import argparse
import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
import re
import time

import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from .sync_logger import ClientLogger

parser = argparse.ArgumentParser()
parser.add_argument("--run-id", "-i", type=int, default=1, dest="run_id")
parser.add_argument("--show-lost", action="store_true", dest="show_lost", help="Show lost (not sent or not recvd) and quit.")
parsed = parser.parse_args()
    
run_id: int = parsed.run_id
show_lost: bool = parsed.show_lost

log_path = Path("log") / f"spam_bots-{run_id}.txt"

@dataclass()
class Message:
    sent_ns: int | None = None
    recv_ns: int | None = None


messages: dict[str, Message] = {}

lines_read: int = 0
sent_count: int = 0
recv_count: int = 0

with open(log_path, mode="r") as f:

    while line:=f.readline():
        line = line.split(" ")
        op = line[0]
        msg_hash = line[1]
        monotonic_ns = int(line[2])

        msg = messages.get(msg_hash)

        if not msg:
            msg = Message()
            messages[msg_hash] = msg

        if op == "SENT":
            sent_count += 1
            if msg.sent_ns:
                print(f"sent_ns of {msg_hash} already exists!")

            msg.sent_ns = monotonic_ns
        elif op == "RECV":
            recv_count += 1
            if msg.recv_ns:
                print(f"recv_ns of {msg_hash} already exists!")

            msg.recv_ns = monotonic_ns
        else:
            print(f"unknown operation: {op}")

        lines_read += 1

def percentile(sorted_values: list[int], p: float) -> float:
    """p в диапазоне 0..100. Простая реализация через индекс."""
    if not sorted_values:
        return 0.0
    # ceil(p/100 * N) - 1, но не меньше 0 и не больше N-1
    idx = max(0, min(len(sorted_values) - 1, int((p / 100) * len(sorted_values) + 0.999999) - 1))
    return float(sorted_values[idx])

def run_default():
    print(f"Lines read: {lines_read}")
    print(f"Sent: {sent_count}")
    print(f"Received: {recv_count}")
    print()

    diffs: list[int] = []

    for msg in messages.values():
        if not msg.sent_ns or not msg.recv_ns:
            continue
        diff = msg.recv_ns - msg.sent_ns
        diffs.append(diff)

    ns_per_s = 10**9
    diffs.sort()

    print(f"Diff count: {len(diffs)}")
    if diffs:
        print(f"Average diff: {sum(diffs)/len(diffs)/ns_per_s:.6f} s")
        print(f"Min:          {diffs[0]/ns_per_s:.6f} s")
        print(f"p50:          {percentile(diffs, 50)/ns_per_s:.6f} s")
        print(f"p95:          {percentile(diffs, 95)/ns_per_s:.6f} s")
        print(f"p99:          {percentile(diffs, 99)/ns_per_s:.6f} s")
        print(f"Max:          {diffs[-1]/ns_per_s:.6f} s")

def run_show_lost():
    for hash, msg in messages.items():
        if msg.sent_ns and msg.recv_ns:
            continue
        
        print(f"{hash} SENT {msg.sent_ns} RECV {msg.recv_ns}")

if not show_lost:
    run_default()
else:
    run_show_lost()
