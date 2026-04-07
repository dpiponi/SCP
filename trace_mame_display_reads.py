#!/usr/bin/env python3
from __future__ import annotations

from compare_mm5799_lockstep import MameCPU, load_rom, valid_d12_addr, LFSR_INDEX_BY_WORD
from pathlib import Path


class TracingMameCPU(MameCPU):
    def __init__(self, rom):
        super().__init__(rom=rom)
        self.last_row0_read_addr: int | None = None
        self.dsps_events: list[dict[str, int | None]] = []

    def ram_r(self) -> int:
        addr = self.b & 0x7F
        if (addr & 0x70) == 0x00:
            self.last_row0_read_addr = addr
        if not valid_d12_addr(addr):
            return 0
        return self.mem[addr] & 0xF

    def step(self):
        before_pc = self.pc
        before_logical = ((self.pc >> 6) << 6) | LFSR_INDEX_BY_WORD[self.pc & 0x3F]
        before_do = self.do & 0xF
        result = super().step()
        if self.op == 0x11:
            self.dsps_events.append(
                {
                    "logical": before_logical,
                    "raw": before_pc,
                    "D": before_do,
                    "A": self.a & 0xF,
                    "C": self.c & 1,
                    "last_row0_read": self.last_row0_read_addr,
                }
            )
        return result


def canonical_no_blk(cpu: TracingMameCPU):
    return (
        cpu.pc,
        cpu.a & 0xF,
        cpu.h & 0xF,
        cpu.b & 0x7F,
        cpu.c & 1,
        cpu.sa & 0x7FF,
        cpu.sb & 0x7FF,
        bool(cpu.skip),
        cpu.f & 0xF,
        cpu.serial & 0xF,
        tuple((cpu.mem[i] & 0xF) if valid_d12_addr(i) else 0 for i in range(128)),
    )


def main():
    rom = load_rom(Path("sinclaircambridgeprogrammable.bin"))
    cpu = TracingMameCPU(rom)

    seen: dict[tuple, int] = {}
    cycle_start = None
    cycle_len = None
    for step in range(20000):
        key = canonical_no_blk(cpu)
        if key in seen:
            cycle_start = seen[key]
            cycle_len = step - cycle_start
            break
        seen[key] = step
        cpu.step()

    if cycle_start is None or cycle_len is None:
        raise SystemExit("failed to detect steady-state loop")

    cpu = TracingMameCPU(rom)
    for _ in range(cycle_start):
        cpu.step()
    cpu.dsps_events.clear()
    for _ in range(cycle_len):
        cpu.step()

    print(f"cycle_start={cycle_start} cycle_len={cycle_len}")
    print("DSPS events in one steady-state loop:")
    for ev in cpu.dsps_events:
        last = "--" if ev["last_row0_read"] is None else f"{ev['last_row0_read']:02X}"
        print(
            f"logical={ev['logical']:04o} raw={ev['raw']:04o} "
            f"D={ev['D']:X} last_row0_read={last} A={ev['A']:X} C={ev['C']}"
        )


if __name__ == "__main__":
    main()
