#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


ROM_SIZE = 2048
RAW_ROM_SIZE = 1536

LFSR_SEQUENCE = [
    0o000, 0o040, 0o020, 0o010, 0o004, 0o002, 0o041, 0o060,
    0o030, 0o014, 0o006, 0o043, 0o021, 0o050, 0o024, 0o012,
    0o045, 0o062, 0o071, 0o074, 0o036, 0o057, 0o027, 0o013,
    0o005, 0o042, 0o061, 0o070, 0o034, 0o016, 0o047, 0o023,
    0o011, 0o044, 0o022, 0o051, 0o064, 0o032, 0o055, 0o066,
    0o073, 0o035, 0o056, 0o067, 0o033, 0o015, 0o046, 0o063,
    0o031, 0o054, 0o026, 0o053, 0o025, 0o052, 0o065, 0o072,
    0o075, 0o076, 0o077, 0o037, 0o017, 0o007, 0o003, 0o001,
]
LFSR_INDEX_BY_WORD = {word: idx for idx, word in enumerate(LFSR_SEQUENCE)}


def load_rom(path: Path) -> list[int]:
    data = bytearray(path.read_bytes())
    if len(data) == RAW_ROM_SIZE:
        data.extend(b"\x00" * (ROM_SIZE - len(data)))
        for index in range(0x5FF, 0x1FF, -1):
            data[index + 0x200] = data[index]
        for index in range(0x200, 0x400):
            data[index] = 0
        return list(data)
    if len(data) != ROM_SIZE:
        raise ValueError(f"unsupported ROM size: {len(data)}")
    return list(data)


def oct4(n: int) -> str:
    return format(n, "04o")


def hex2(n: int) -> str:
    return format(n, "02X")


def next_lfsr(word: int) -> int:
    return LFSR_SEQUENCE[(LFSR_INDEX_BY_WORD[word & 0x3F] + 1) & 0x3F]


def is_two_byte_opcode(op: int) -> bool:
    return op == 0x13 or op == 0x33 or (op & 0xF0) == 0x60


def valid_d12_addr(addr: int) -> bool:
    return (addr & 0x0F) >= 0x04


@dataclass
class DebuggerCPU:
    rom: list[int]
    Pp: int = 0
    Pw: int = 0
    SA: int = 0
    SB: int = 0
    A: int = 0
    H: int = 0
    C: int = 0
    Br: int = 0
    Bd: int = 0
    M: list[int] = field(default_factory=lambda: [0] * 128)
    F1: int = 0
    F2: int = 0
    F3: int = 0
    INB: int = 0
    SI: int = 0
    SO: int = 0
    serbuf: int = 0
    blk: int = 1
    skip: bool = False
    wasLB: bool = False
    D: int = 0

    def raw_pc(self) -> int:
        return ((self.Pp & 0x1F) << 6) | (self.Pw & 0x3F)

    def logical_pc(self) -> int:
        return ((self.Pp & 0x1F) << 6) | LFSR_INDEX_BY_WORD[self.Pw & 0x3F]

    def rom_byte(self, page: int, word: int) -> int:
        return self.rom[((page & 0x1F) << 6) | (word & 0x3F)]

    def current_opcode(self) -> int:
        return self.rom[self.raw_pc()]

    def get_b(self) -> int:
        return ((self.Br & 0x7) << 4) | (self.Bd & 0xF)

    def read_mem(self, addr: int) -> int:
        return self.M[addr & 0x7F] & 0xF

    def write_mem(self, addr: int, value: int) -> None:
        self.M[addr & 0x7F] = value & 0xF

    def step(self) -> tuple[int, int]:
        before_raw = self.raw_pc()
        before_logical = self.logical_pc()
        opcode = self.current_opcode()
        nextpc = next_lfsr(self.Pw)
        self.blk = 1
        not_lb = True

        if self.skip:
            self.skip = False
            if is_two_byte_opcode(opcode):
                nextpc = next_lfsr(nextpc)
        else:
            tmp = 0
            if opcode == 0x00:
                pass
            elif opcode == 0x01:
                tmp = self.H
                self.H = self.Br
                self.Br = tmp & 0x7
            elif opcode == 0x02:
                self.A = self.A + self.C + self.read_mem(self.get_b())
                if self.A >= 10:
                    self.C = 1
                else:
                    self.C = 0
                    self.skip = True
                self.A &= 0xF
            elif opcode == 0x03:
                self.C = 1
            elif opcode == 0x04:
                if self.F1 == 0:
                    self.skip = True
            elif opcode == 0x05:
                if (self.D & 0x4) == 0:
                    self.skip = True
            elif opcode in (0x06, 0x16, 0x26, 0x36):
                self.A = self.read_mem(self.get_b())
                self.Br ^= ((opcode >> 4) & 0x3)
            elif opcode in (0x07, 0x17, 0x27, 0x37):
                tmp = self.A
                addr = self.get_b()
                self.A = self.read_mem(addr)
                self.write_mem(addr, tmp)
                self.Br ^= ((opcode >> 4) & 0x3)
            elif opcode in (0x08, 0x18, 0x28, 0x38):
                tmp = self.A
                addr = self.get_b()
                self.A = self.read_mem(addr)
                self.write_mem(addr, tmp)
                self.Br ^= ((opcode >> 4) & 0x3)
                self.Bd = (self.Bd - 1) & 0xF
                if self.Bd == 0xF:
                    self.skip = True
            elif opcode in (0x09, 0x19, 0x29, 0x39):
                tmp = self.A
                addr = self.get_b()
                self.A = self.read_mem(addr)
                self.write_mem(addr, tmp)
                self.Br ^= ((opcode >> 4) & 0x3)
                self.Bd = (self.Bd + 1) & 0xF
                if self.Bd == 0 or self.Bd == 13:
                    self.skip = True
            elif (opcode & 0xC0) == 0x00 and (opcode & 0x0F) >= 0x0A:
                if not self.wasLB:
                    self.Br = (opcode >> 4) & 0x3
                    tmp = opcode & 0x0F
                    if tmp == 0x0A:
                        self.Bd = 5
                    elif tmp >= 0x0B:
                        self.Bd = tmp
                self.wasLB = True
                not_lb = False
            elif opcode == 0x10:
                pass
            elif opcode == 0x11:
                pass
            elif opcode == 0x12:
                self.A = (self.A + self.read_mem(self.get_b())) & 0xF
            elif opcode == 0x13:
                second = self.rom_byte(self.Pp, nextpc)
                self.Br = (second >> 4) & 0x7
                self.Bd = second & 0xF
                nextpc = next_lfsr(nextpc)
            elif opcode == 0x14:
                if self.F2 == 0:
                    self.skip = True
            elif opcode == 0x15:
                liveK = 0
                if liveK > 0:
                    self.skip = True
            elif opcode == 0x20:
                self.A = (~self.A) & 0xF
            elif opcode == 0x21:
                tmp = self.A
                self.A = self.serbuf & 0xF
                self.serbuf = tmp & 0xF
            elif opcode == 0x22:
                tmp = ((~self.A) & 0xF) + self.C + self.read_mem(self.get_b())
                self.A = tmp & 0xF
                if tmp > 15:
                    self.C = 1
                    self.skip = True
                else:
                    self.C = 0
            elif opcode == 0x23:
                self.C = 0
            elif opcode == 0x24:
                if self.F3 == 0:
                    self.skip = True
            elif opcode == 0x25:
                self.D = self.Bd & 0xF
                self.blk = 0
            elif opcode == 0x30:
                self.A = 0
            elif opcode == 0x31:
                tmp = self.A
                self.A = self.H & 0xF
                self.H = tmp & 0xF
            elif opcode == 0x32:
                if self.A == self.read_mem(self.get_b()):
                    self.skip = True
            elif opcode == 0x33:
                second = self.rom_byte(self.Pp, nextpc)
                if (second & 0x20) == 0:
                    self.F3 = 1 if (second & 0x10) else 0
                if (second & 0x08) == 0:
                    self.F2 = 1 if (second & 0x04) else 0
                if (second & 0x02) == 0:
                    self.F1 = 1 if (second & 0x01) else 0
                nextpc = next_lfsr(nextpc)
            elif opcode == 0x34:
                self.A = 0
            elif opcode == 0x35:
                if self.INB == 1:
                    self.skip = True
            elif opcode == 0x40 or opcode == 0x41:
                if opcode == 0x41:
                    self.skip = True
                tmp = self.SA
                self.SA = self.SB
                nextpc = tmp & 0x3F
                self.Pp = (tmp >> 6) & 0x1F
            elif opcode == 0x42:
                self.write_mem(self.get_b(), self.read_mem(self.get_b()) & 0x7)
            elif opcode == 0x43:
                self.A = self.Bd & 0xF
            elif opcode == 0x44:
                if (self.read_mem(self.get_b()) & 0x1) == 0:
                    self.skip = True
            elif opcode == 0x45:
                if (self.read_mem(self.get_b()) & 0x2) == 0:
                    self.skip = True
            elif opcode == 0x46:
                if (self.read_mem(self.get_b()) & 0x4) == 0:
                    self.skip = True
            elif opcode == 0x47:
                if (self.read_mem(self.get_b()) & 0x8) == 0:
                    self.skip = True
            elif opcode == 0x48:
                self.write_mem(self.get_b(), self.read_mem(self.get_b()) & 0xE)
            elif opcode == 0x49:
                self.write_mem(self.get_b(), self.read_mem(self.get_b()) | 0x1)
            elif opcode == 0x4A:
                self.write_mem(self.get_b(), self.read_mem(self.get_b()) | 0x8)
            elif opcode == 0x4B:
                self.write_mem(self.get_b(), self.read_mem(self.get_b()) & 0xB)
            elif opcode == 0x4C:
                self.write_mem(self.get_b(), self.read_mem(self.get_b()) & 0xD)
            elif opcode == 0x4D:
                if self.C == 0:
                    self.skip = True
            elif opcode == 0x4E:
                self.write_mem(self.get_b(), self.read_mem(self.get_b()) | 0x2)
            elif opcode == 0x4F:
                self.write_mem(self.get_b(), self.read_mem(self.get_b()) | 0x4)
            elif opcode == 0x50:
                self.Bd = self.A & 0xF
            elif 0x51 <= opcode <= 0x5F:
                tmp = opcode & 0x0F
                if self.A + tmp < 16 and tmp != 6:
                    self.skip = True
                self.A = (self.A + tmp) & 0xF
            elif 0x60 <= opcode <= 0x6F:
                second = self.rom_byte(self.Pp, nextpc)
                if (second & 0x40) == 0:
                    self.SB = self.SA
                    self.SA = ((self.Pp & 0x1F) << 6) | next_lfsr(nextpc)
                self.Pp = (((15 - (opcode & 0x0F)) << 1) | ((second >> 7) & 1)) & 0x1F
                nextpc = second & 0x3F
            elif 0x70 <= opcode <= 0x7F:
                self.write_mem(self.get_b(), opcode & 0x0F)
                self.Bd = (self.Bd + 1) & 0xF
            elif 0x80 <= opcode <= 0xBF:
                if (self.Pp & 0x1E) != 0x1E:
                    self.SB = self.SA
                    self.SA = ((self.Pp & 0x1F) << 6) | nextpc
                self.Pp = 0x1F
                nextpc = opcode & 0x3F
            elif 0xC0 <= opcode <= 0xFF:
                nextpc = opcode & 0x3F
                if self.Pp == 0x1F:
                    self.Pp = 0x1E
            else:
                raise AssertionError(f"unhandled opcode {opcode:02x}")

        if not_lb:
            self.wasLB = False
        self.Pw = nextpc & 0x3F
        return before_logical, before_raw


@dataclass
class MameCPU:
    rom: list[int]
    pc: int = 0
    prev_pc: int = 0
    op: int = 0
    prev_op: int = 0
    arg: int = 0
    a: int = 0
    h: int = 0
    b: int = 0
    c: int = 0
    skip: bool = False
    sa: int = 0
    sb: int = 0
    serial: int = 0
    f: int = 0
    do: int = 0
    blk: int = 1
    mem: list[int] = field(default_factory=lambda: [0] * 128)

    def ram_r(self) -> int:
        addr = self.b & 0x7F
        if not valid_d12_addr(addr):
            return 0
        return self.mem[addr] & 0xF

    def ram_w(self, data: int) -> None:
        addr = self.b & 0x7F
        if valid_d12_addr(addr):
            self.mem[addr] = data & 0xF

    def cycle(self) -> None:
        self.serial = (self.serial >> 1) & 0xF

    def increment_pc(self) -> None:
        feed = 1 if ((self.pc & 0x3E) == 0) else 0
        feed ^= ((self.pc >> 1) ^ self.pc) & 1
        self.pc = (self.pc & ~0x3F) | ((self.pc >> 1) & 0x1F) | (feed << 5)

    def pop_pc(self) -> None:
        self.pc = self.sa
        self.sa = self.sb

    def push_pc(self) -> None:
        self.sb = self.sa
        self.sa = self.pc

    def step(self) -> tuple[int, int]:
        before_pc = self.pc
        before_logical = ((self.pc >> 6) << 6) | LFSR_INDEX_BY_WORD[self.pc & 0x3F]
        self.prev_op = self.op
        self.prev_pc = self.pc
        if self.prev_op == 0x25:
            self.blk = 0

        self.op = self.rom[self.pc]
        self.increment_pc()
        self.cycle()
        if self.op != 0x25 or self.skip:
            self.blk = 1

        if self.op == 0x13 or self.op == 0x33 or (self.op & 0xF0) == 0x60:
            self.arg = self.rom[self.pc]
            self.increment_pc()
            self.cycle()

        if self.skip:
            self.skip = False
            self.op = 0
            return before_logical, before_pc

        op = self.op
        if (op & 0xC0) == 0x00:
            if op == 0x00:
                pass
            elif op == 0x10:
                pass
            elif op == 0x20:
                self.a ^= 0xF
            elif op == 0x30:
                self.a = 0
            elif op == 0x01:
                h = self.h
                self.h = self.b >> 4
                self.b = ((h << 4) | (self.b & 0xF)) & 0x7F
            elif op == 0x11:
                pass
            elif op == 0x21:
                s = self.serial
                self.serial = self.a
                self.a = s
            elif op == 0x31:
                h = self.h
                self.h = self.a
                self.a = h
            elif op == 0x02:
                self.a = self.a + self.ram_r() + self.c
                self.c = 1 if self.a >= 10 else 0
                self.a &= 0xF
                self.skip = not bool(self.c)
            elif op == 0x12:
                self.a = (self.a + self.ram_r()) & 0xF
            elif op == 0x22:
                self.a = (self.a ^ 0xF) + self.ram_r() + self.c
                self.c = (self.a >> 4) & 1
                self.a &= 0xF
                self.skip = bool(self.c)
            elif op == 0x32:
                self.skip = self.a == self.ram_r()
            elif op == 0x03:
                self.c = 1
            elif op == 0x13:
                self.b = self.arg & 0x7F
            elif op == 0x23:
                self.c = 0
            elif op == 0x33:
                second = self.arg
                if (second & 0x20) == 0:
                    self.f = (self.f & ~0x4) | (0x4 if (second & 0x10) else 0)
                if (second & 0x08) == 0:
                    self.f = (self.f & ~0x2) | (0x2 if (second & 0x04) else 0)
                if (second & 0x02) == 0:
                    self.f = (self.f & ~0x1) | (0x1 if (second & 0x01) else 0)
            elif op == 0x34:
                self.a = 0
            elif op == 0x05:
                d = self.do >> 2
                self.skip = not bool(d & 1)
            elif op == 0x15:
                self.skip = False
            elif op == 0x25:
                self.do = (~self.b) & 0xF
            elif op == 0x35:
                t = True  # read_inb == 0, active high option true
                self.skip = t
            elif op in (0x04, 0x14, 0x24):
                bit = (op >> 4) & 0x3
                self.skip = not ((self.f >> bit) & 1)
            elif op in (0x06, 0x16, 0x26, 0x36):
                self.a = self.ram_r()
                self.b ^= op & 0x30
            elif op in (0x07, 0x17, 0x27, 0x37):
                a = self.a
                self.a = self.ram_r()
                self.ram_w(a)
                self.b ^= op & 0x30
            elif op in (0x08, 0x18, 0x28, 0x38):
                a = self.a
                self.a = self.ram_r()
                self.ram_w(a)
                self.b ^= op & 0x30
                self.b = (self.b & ~0xF) | ((self.b - 1) & 0xF)
                self.skip = (self.b & 0xF) == 0xF
            elif op in (0x09, 0x19, 0x29, 0x39):
                a = self.a
                self.a = self.ram_r()
                self.ram_w(a)
                self.b ^= op & 0x30
                self.b = (self.b & ~0xF) | ((self.b + 1) & 0xF)
                self.skip = (self.b & 0xF) == 0 or (self.b & 0xF) == 13
            else:
                if (self.prev_op & 0xC0) != 0x00 or (self.prev_op & 0x0F) < 0x0A:
                    x = op & 0x0F
                    if x == 10:
                        x = 5
                    self.b = ((op & 0x30) | x) & 0x7F
        elif (op & 0xC0) == 0x40:
            if (op & 0x30) == 0x00:
                if op == 0x40:
                    self.pop_pc()
                elif op == 0x41:
                    self.pop_pc()
                    self.skip = True
                elif op == 0x42:
                    self.ram_w(self.ram_r() & ~0x8)
                elif op == 0x43:
                    self.a = self.b & 0xF
                elif op == 0x44:
                    self.skip = not bool(self.ram_r() & 0x1)
                elif op == 0x45:
                    self.skip = not bool(self.ram_r() & 0x2)
                elif op == 0x46:
                    self.skip = not bool(self.ram_r() & 0x4)
                elif op == 0x47:
                    self.skip = not bool(self.ram_r() & 0x8)
                elif op == 0x48:
                    self.ram_w(self.ram_r() & ~0x1)
                elif op == 0x49:
                    self.ram_w(self.ram_r() | 0x1)
                elif op == 0x4A:
                    self.ram_w(self.ram_r() | 0x8)
                elif op == 0x4B:
                    self.ram_w(self.ram_r() & ~0x4)
                elif op == 0x4C:
                    self.ram_w(self.ram_r() & ~0x2)
                elif op == 0x4D:
                    self.skip = not self.c
                elif op == 0x4E:
                    self.ram_w(self.ram_r() | 0x2)
                elif op == 0x4F:
                    self.ram_w(self.ram_r() | 0x4)
            elif (op & 0x30) == 0x10:
                if (op & 0x0F) != 0:
                    x = op & 0xF
                    self.a += x
                    self.skip = ((~self.a) & 0x10) != 0 and x != 6
                    self.a &= 0xF
                else:
                    self.b = (self.b & ~0xF) | self.a
            elif (op & 0x30) == 0x20:
                if (~self.arg & 0x40) != 0:
                    self.push_pc()
                self.pc = ((~op << 7) & 0x780) | ((self.arg >> 1) & 0x40) | (self.arg & 0x3F)
            elif (op & 0x30) == 0x30:
                self.ram_w(op & 0x0F)
                self.b = (self.b & ~0xF) | ((self.b + 1) & 0xF)
        elif (op & 0xC0) == 0x80:
            if (self.pc & 0x780) != 0x780:
                self.push_pc()
            self.pc = (op & 0x3F) | 0x7C0
        else:
            if (self.pc & 0x780) == 0x780:
                self.pc &= ~0x40
            self.pc = (self.pc & ~0x3F) | (op & 0x3F)

        return before_logical, before_pc

    def canonical(self) -> dict[str, object]:
        return {
            "raw_pc": self.pc,
            "logical_pc": ((self.pc >> 6) << 6) | LFSR_INDEX_BY_WORD[self.pc & 0x3F],
            "A": self.a & 0xF,
            "H": self.h & 0xF,
            "B": self.b & 0x7F,
            "C": self.c & 1,
            "SA": self.sa & 0x7FF,
            "SB": self.sb & 0x7FF,
            "skip": bool(self.skip),
            "F": self.f & 0xF,
            "serial": self.serial & 0xF,
            "blk": self.blk & 1,
            "mem": tuple((self.mem[i] & 0xF) if valid_d12_addr(i) else 0 for i in range(128)),
            "holes": tuple(self.mem[i] & 0xF for i in range(128) if not valid_d12_addr(i)),
        }


def debugger_canonical(cpu: DebuggerCPU) -> dict[str, object]:
    mem = tuple((cpu.M[i] & 0xF) for i in range(128))
    return {
        "raw_pc": cpu.raw_pc(),
        "logical_pc": cpu.logical_pc(),
        "A": cpu.A & 0xF,
        "H": cpu.H & 0xF,
        "B": cpu.get_b() & 0x7F,
        "C": cpu.C & 1,
        "SA": cpu.SA & 0x7FF,
        "SB": cpu.SB & 0x7FF,
        "skip": bool(cpu.skip),
        "F": ((cpu.F3 & 1) << 2) | ((cpu.F2 & 1) << 1) | (cpu.F1 & 1),
        "serial": cpu.serbuf & 0xF,
        "blk": cpu.blk & 1,
        "mem": tuple((mem[i] if valid_d12_addr(i) else 0) for i in range(128)),
        "holes": tuple(mem[i] for i in range(128) if not valid_d12_addr(i)),
    }


def first_diff(a: dict[str, object], b: dict[str, object], include_blk: bool = False) -> str | None:
    keys = ["raw_pc", "logical_pc", "A", "H", "B", "C", "SA", "SB", "skip", "F", "serial", "mem", "holes"]
    if include_blk:
        keys.append("blk")
    for key in keys:
        if a[key] != b[key]:
            return key
    return None


def run(max_steps: int = 50000, include_blk: bool = False) -> int:
    rom = load_rom(Path("sinclaircambridgeprogrammable.bin"))
    dbg = DebuggerCPU(rom=rom)
    mame = MameCPU(rom=rom)
    seen: dict[tuple[object, ...], int] = {}

    for step in range(max_steps):
        dcanon = debugger_canonical(dbg)
        mcanon = mame.canonical()
        diff = first_diff(dcanon, mcanon, include_blk=include_blk)
        if diff is not None:
            print(f"Mismatch before step {step}, field {diff}")
            print(f"  DBG  raw={oct4(dcanon['raw_pc'])} logical={oct4(dcanon['logical_pc'])} A={dcanon['A']:X} H={dcanon['H']:X} B={hex2(dcanon['B'])} C={dcanon['C']} SA={oct4(dcanon['SA'])} SB={oct4(dcanon['SB'])} skip={int(dcanon['skip'])} F={dcanon['F']:X} serial={dcanon['serial']:X} blk={dcanon['blk']}")
            print(f"  MAME raw={oct4(mcanon['raw_pc'])} logical={oct4(mcanon['logical_pc'])} A={mcanon['A']:X} H={mcanon['H']:X} B={hex2(mcanon['B'])} C={mcanon['C']} SA={oct4(mcanon['SA'])} SB={oct4(mcanon['SB'])} skip={int(mcanon['skip'])} F={mcanon['F']:X} serial={mcanon['serial']:X} blk={mcanon['blk']}")
            if diff in ("mem", "holes"):
                for i in range(128):
                    dv = dcanon["mem"][i] if diff == "mem" else (dbg.M[i] & 0xF)
                    mv = mcanon["mem"][i] if diff == "mem" else ((mame.mem[i] & 0xF) if not valid_d12_addr(i) else 0)
                    if dv != mv:
                        print(f"  First differing RAM at {hex2(i)}: dbg={dv:X} mame={mv:X}")
                        break
            return 1

        key_fields = ["raw_pc", "A", "H", "B", "C", "SA", "SB", "skip", "F", "serial", "mem"]
        if include_blk:
            key_fields.append("blk")
        key = tuple(dcanon[name] for name in key_fields)
        if key in seen:
            start = seen[key]
            print(f"Lockstep cycle detected after {step} steps; cycle starts at step {start} and has length {step - start}.")
            print(f"State: raw={oct4(dcanon['raw_pc'])} logical={oct4(dcanon['logical_pc'])} A={dcanon['A']:X} H={dcanon['H']:X} B={hex2(dcanon['B'])}")
            return 0
        seen[key] = step

        dbg_logical, dbg_raw = dbg.step()
        mame_logical, mame_raw = mame.step()
        if dbg_raw != mame_raw or dbg_logical != mame_logical:
            print(f"Trace divergence in executed instruction at step {step}: dbg {oct4(dbg_logical)}@{oct4(dbg_raw)} vs mame {oct4(mame_logical)}@{oct4(mame_raw)}")
            return 1

    print(f"No mismatch and no repeated full state within {max_steps} steps.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
