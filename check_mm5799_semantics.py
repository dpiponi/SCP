#!/usr/bin/env python3
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class State:
    A: int
    C: int
    Br: int
    Bd: int
    skip: bool
    mem_b: int
    was_lb: bool = False


def debugger_add(s: State) -> State:
    a = s.A + s.C + s.mem_b
    if a >= 10:
        c = 1
        skip = False
    else:
        c = 0
        skip = True
    return replace(s, A=a & 0xF, C=c, skip=skip)


def mame_add(s: State) -> State:
    a = s.A + s.mem_b + s.C
    c = 1 if a >= 10 else 0
    return replace(s, A=a & 0xF, C=c, skip=(c == 0))


def debugger_sub(s: State) -> State:
    tmp = (~s.A & 0xF) + s.C + s.mem_b
    if tmp > 15:
        c = 1
        skip = True
    else:
        c = 0
        skip = False
    return replace(s, A=tmp & 0xF, C=c, skip=skip)


def mame_sub(s: State) -> State:
    a = (s.A ^ 0xF) + s.mem_b + s.C
    c = (a >> 4) & 1
    return replace(s, A=a & 0xF, C=c, skip=bool(c))


def debugger_adx(s: State, x: int) -> State:
    skip = (s.A + x < 16) and x != 6
    return replace(s, A=(s.A + x) & 0xF, skip=skip)


def mame_adx(s: State, x: int) -> State:
    a = s.A + x
    skip = ((~a) & 0x10) != 0 and x != 6
    return replace(s, A=a & 0xF, skip=skip)


def debugger_excm(s: State, xor_br: int) -> State:
    br = s.Br ^ xor_br
    bd = (s.Bd - 1) & 0xF
    return State(A=s.mem_b, C=s.C, Br=br, Bd=bd, skip=(bd == 0xF), mem_b=s.A, was_lb=s.was_lb)


def mame_excm(s: State, xor_br: int) -> State:
    br = s.Br ^ xor_br
    bd = (s.Bd - 1) & 0xF
    return State(A=s.mem_b, C=s.C, Br=br, Bd=bd, skip=((bd & 0xF) == 0xF), mem_b=s.A, was_lb=s.was_lb)


def debugger_excp(s: State, xor_br: int) -> State:
    br = s.Br ^ xor_br
    bd = (s.Bd + 1) & 0xF
    return State(A=s.mem_b, C=s.C, Br=br, Bd=bd, skip=(bd == 0 or bd == 13), mem_b=s.A, was_lb=s.was_lb)


def mame_excp(s: State, xor_br: int) -> State:
    br = s.Br ^ xor_br
    bd = (s.Bd + 1) & 0xF
    return State(A=s.mem_b, C=s.C, Br=br, Bd=bd, skip=((bd & 0xF) == 0 or (bd & 0xF) == 13), mem_b=s.A, was_lb=s.was_lb)


def debugger_lb(opcode: int, s: State) -> State:
    br = s.Br
    bd = s.Bd
    if not s.was_lb:
        br = (opcode >> 4) & 0x3
        tmp = opcode & 0x0F
        if tmp == 0x0A:
            bd = 5
        elif tmp >= 0x0B:
            bd = tmp
    return replace(s, Br=br, Bd=bd, was_lb=True)


def mame_prev_is_lb(prev_opcode: int) -> bool:
    return (prev_opcode & 0xC0) == 0x00 and (prev_opcode & 0x0F) >= 0x0A


def mame_lb(opcode: int, s: State, prev_opcode: int) -> State:
    if mame_prev_is_lb(prev_opcode):
        return replace(s)
    x = opcode & 0x0F
    if x == 10:
        x = 5
    b = ((opcode & 0x30) | x) & 0x7F
    return replace(s, Br=(b >> 4) & 0x7, Bd=b & 0xF)


def compare_named(name: str, gen_states, dbg_fn, mame_fn):
    mismatches = []
    for st in gen_states():
        a = dbg_fn(st)
        b = mame_fn(st)
        if a != b:
            mismatches.append((st, a, b))
            if len(mismatches) >= 8:
                break
    print(f"{name}: {'OK' if not mismatches else f'{len(mismatches)} mismatches (showing first {len(mismatches)})'}")
    for st, a, b in mismatches:
        print("  state =", st)
        print("  dbg   =", a)
        print("  mame  =", b)


def gen_small_states():
    for A in range(16):
        for C in (0, 1):
            for Br in range(8):
                for Bd in range(16):
                    for mem_b in range(16):
                        yield State(A=A, C=C, Br=Br, Bd=Bd, skip=False, mem_b=mem_b, was_lb=False)


def gen_lb_states():
    for Br in range(8):
        for Bd in range(16):
            for was_lb in (False, True):
                yield State(A=0, C=0, Br=Br, Bd=Bd, skip=False, mem_b=0, was_lb=was_lb)


def main():
    compare_named("ADD", gen_small_states, debugger_add, mame_add)
    compare_named("SUB", gen_small_states, debugger_sub, mame_sub)
    for x in range(1, 16):
        compare_named(f"ADX {x}", gen_small_states, lambda s, x=x: debugger_adx(s, x), lambda s, x=x: mame_adx(s, x))
    for xor_br, opcode_name in enumerate(("EXC-", "EXC- 1", "EXC- 2", "EXC- 3")):
        compare_named(opcode_name, gen_small_states, lambda s, x=xor_br: debugger_excm(s, x), lambda s, x=xor_br: mame_excm(s, x))
    for xor_br, opcode_name in enumerate(("EXC+", "EXC+ 1", "EXC+ 2", "EXC+ 3")):
        compare_named(opcode_name, gen_small_states, lambda s, x=xor_br: debugger_excp(s, x), lambda s, x=xor_br: mame_excp(s, x))

    lb_opcodes = [op for op in range(0x100) if (op & 0xC0) == 0 and (op & 0x0F) >= 0x0A]
    print("LB family:")
    shown = 0
    mismatches = 0
    for op in lb_opcodes:
        for prev in range(0x100):
            for st in gen_lb_states():
                if st.was_lb != mame_prev_is_lb(prev):
                    continue
                dbg = debugger_lb(op, st)
                mame = mame_lb(op, st, prev)
                dbg_cmp = replace(dbg, skip=False)
                mame_cmp = replace(mame, skip=False, was_lb=dbg.was_lb)
                if dbg_cmp != mame_cmp:
                    mismatches += 1
                    if shown < 8:
                        shown += 1
                        print(f"  opcode={op:#04x} prev={prev:#04x} state={st}")
                        print("    dbg  =", dbg_cmp)
                        print("    mame =", mame_cmp)
    print(f"LB family: {'OK' if mismatches == 0 else f'{mismatches} mismatches'}")


if __name__ == '__main__':
    main()
