#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


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

LFSR_INDEX_BY_WORD = {word: index for index, word in enumerate(LFSR_SEQUENCE)}

OPCODES = [
    "NOP", "HXBR", "ADD", "SC", "TF 1", "TIR", "MTA", "EXC",
    "EXC-", "EXC+", "LB 0,5", "LB 0,11", "LB 0,12", "LB 0,13", "LB 0,14", "LB 0,15",
    "DSPA", "DSPS", "AD", "LBL", "TF 2", "TKB", "MTA 1", "EXC 1",
    "EXC- 1", "EXC+ 1", "LB 1,5", "LB 1,11", "LB 1,12", "LB 1,13", "LB 1,14", "LB 1,15",
    "COMP", "AXO", "SUB", "RSC", "TF 3", "BTD", "MTA 2", "EXC 2",
    "EXC- 2", "EXC+ 2", "LB 2,5", "LB 2,11", "LB 2,12", "LB 2,13", "LB 2,14", "LB 2,15",
    "0TA", "HXA", "TAM", "LDF", "READ", "TIN", "MTA 3", "EXC 3",
    "EXC- 3", "EXC+ 3", "LB 3,5", "LB 3,11", "LB 3,12", "LB 3,13", "LB 3,14", "LB 3,15",
    "RET", "RETS", "RSM 8", "BTA", "TM 1", "TM 2", "TM 4", "TM 8",
    "RSM 1", "SM 1", "SM 8", "RSM 4", "RSM 2", "TC", "SM 2", "SM 4",
    "ATB", "ADX 1", "ADX 2", "ADX 3", "ADX 4", "ADX 5", "ADX 6", "ADX 7",
    "ADX 8", "ADX 9", "ADX 10", "ADX 11", "ADX 12", "ADX 13", "ADX 14", "ADX 15",
    "LG", "LG", "LG", "LG", "LG", "LG", "LG", "LG",
    "LG", "LG", "LG", "LG", "LG", "LG", "LG", "LG",
    "LM 0", "LM 1", "LM 2", "LM 3", "LM 4", "LM 5", "LM 6", "LM 7",
    "LM 8", "LM 9", "LM 10", "LM 11", "LM 12", "LM 13", "LM 14", "LM 15",
] + ["CALL"] * 64 + ["GO"] * 64

NAMED_OPCODES = {
    0x0A: "LB MAIN_FIELD",
    0x0B: "LB FLAG_011",
    0x0C: "LB FLAG_A",
    0x0D: "LB FLAG_013",
    0x0E: "LB FLAG_B",
    0x0F: "LB FLAG_C",
    0x1A: "LB ANNUNCIATOR",
    0x1B: "LB SELECT_STATE",
    0x1C: "LB SCAN_STATE",
    0x1D: "LB MODE_STATE_C",
    0x1E: "LB MODE_STATE_A",
    0x1F: "LB MODE_STATE_B",
    0x2A: "LB WORK_2_5",
    0x2B: "LB WORK_2_11",
    0x2C: "LB WORK_2_12",
    0x2D: "LB WORK_2_13",
    0x2E: "LB WORK_2_14",
    0x2F: "LB WORK_2_15",
    0x3F: "LB EXP_STATE",
}

SEMANTIC_LABELS = {
    0o0172: "SCAN_BACK_OVER_ZEROES",
    0o3604: "ADD_DIGIT_WITH_CARRY",
    0o3600: "SET_CURRENT_BIT8",
    0o3620: "PROPAGATE_CARRY",
    0o3627: "SUB_DIGIT_COMPARE",
    0o3613: "RIPPLE_INCREMENT_MAIN_FIELD",
    0o3652: "SWAP_FIELD2_BACKWARD",
    0o3657: "SWAP_FIELD1_BACKWARD",
    0o3664: "INCREMENT_CURRENT_DIGIT",
    0o3670: "ZERO_FIELD_BACKWARD_ALT",
    0o3674: "ZERO_FIELD_BACKWARD",
    0o3700: "TEST_CURRENT_DIGIT_ZERO",
    0o3702: "LOAD_FLAG_A_PTR",
    0o3703: "LOAD_FLAG_011_PTR",
    0o3706: "INCREMENT_ANNUNCIATOR",
    0o3716: "RIPPLE_INCREMENT_FROM_CURRENT_PTR",
    0o3717: "LOAD_SCAN_STATE_PTR",
    0o3714: "LOAD_FLAG_B_PTR",
    0o3721: "LOAD_FLAG_C_PTR",
    0o3722: "ZERO_FROM_CURRENT_PTR",
    0o3723: "ZERO_MAIN_FIELD",
    0o3725: "WALK_MAIN_FIELD",
    0o3730: "SCAN_BACK_MAIN_FIELD_ZEROES",
    0o3720: "LOAD_WORK_2_15_PTR",
    0o3735: "LOAD_FLAG_B_PTR_ALT",
    0o3740: "LOAD_ANNUNCIATOR_PTR",
    0o3743: "LOAD_WORK_2_15_PTR_ALT1",
    0o3744: "LOAD_WORK_2_12_PTR",
    0o3736: "SUBTRACT_WITH_BORROW",
    0o3747: "LOAD_PTR_1_7",
    0o3715: "LOAD_WORK_2_14_PTR",
    0o3752: "LOAD_WORK_2_15_PTR_ALT2",
    0o3761: "LOAD_WORK_2_14_PTR_ALT",
    0o3764: "LOAD_WORK_2_5_PTR",
    0o3643: "STAGE_FLAG_A_IN_WORK2",
    0o3767: "SWAP_FLAG_A_FIELD1_BACKWARD",
    0o3776: "SET_FLAG_A_BIT8",
    0o3777: "SET_FLAG_A_BIT8_ENTRY",
    0o3705: "RIPPLE_INCREMENT_MAIN_FIELD_ENTRY",
    0o3746: "STAGE_FLAG_A_IN_WORK2_ENTRY",
    0o2400: "POST_DECODE_BOOKKEEPING",
    0o2413: "UPDATE_WORK2_12_STAGE",
    0o2434: "FINALIZE_POST_DECODE_STATE",
    0o2462: "LATCH_MODE_STATE_B_FROM_POST_DECODE",
    0o2500: "POST_DECODE_WORK_UPDATE",
    0o2552: "CHECK_WORK2_12_MATCH",
    0o0520: "PROGRAM_STEP_COMPARE",
    0o0542: "PROGRAM_STEP_REINIT",
    0o0551: "RESET_PROGRAM_STEP_STAGE",
    0o0561: "ADVANCE_PROGRAM_STEP_STAGE",
}


def lfsr_pc(offset: int) -> int:
    return (offset & 0x7C0) | LFSR_SEQUENCE[offset & 0x3F]


def logical_offset_for_page_word(page: int, word: int) -> int:
    return page * 64 + LFSR_INDEX_BY_WORD[word & 0x3F]


def default_label_for_offset(offset: int) -> str:
    if offset in SEMANTIC_LABELS:
        return SEMANTIC_LABELS[offset]
    page = offset // 64
    word = LFSR_SEQUENCE[offset & 0x3F]
    return f"P{page:02o}_W{word:03o}"


def load_rom(path: Path) -> bytearray:
    data = bytearray(path.read_bytes())
    if len(data) == RAW_ROM_SIZE:
        data.extend(b"\x00" * (ROM_SIZE - len(data)))
        for index in range(0x5FF, 0x1FF, -1):
            data[index + 0x200] = data[index]
        for index in range(0x200, 0x400):
            data[index] = 0
        return data
    if len(data) != ROM_SIZE:
        raise ValueError(f"{path} has unsupported size {len(data)} bytes")
    return data


def compare_roms(clean_path: Path, raw_path: Path) -> str:
    clean = clean_path.read_bytes()
    raw = raw_path.read_bytes()
    if len(clean) != len(raw):
        raise ValueError("ROM sizes differ")

    differing = [index for index, (a, b) in enumerate(zip(clean, raw)) if a != b]
    matching = [index for index, (a, b) in enumerate(zip(clean, raw)) if a == b]
    lines = [
        f"clean_rom: {clean_path.name}",
        f"raw_rom:   {raw_path.name}",
        f"size:      {len(clean)} bytes",
        f"different: {len(differing)} bytes ({len(differing) / len(clean) * 100:.2f}%)",
        f"matching:  {len(matching)} bytes",
        "",
        "matching byte offsets:",
    ]
    if matching:
        lines.extend(f"  0x{index:03x}: 0x{clean[index]:02x}" for index in matching)
    else:
        lines.append("  none")

    lines.extend(["", "difference density by 256-byte chunk:"])
    for chunk_start in range(0, len(clean), 0x100):
        chunk_diffs = sum(
            1 for index in differing if chunk_start <= index < chunk_start + 0x100
        )
        lines.append(f"  0x{chunk_start:03x}-0x{chunk_start + 0xFF:03x}: {chunk_diffs}")

    return "\n".join(lines)


def rom_summary(name: str, rom: bytearray) -> str:
    counts = Counter(rom[lfsr_pc(offset)] for offset in range(ROM_SIZE))
    lines = [
        name,
        f"  zero bytes: {counts[0]}",
        f"  CALL/GO opcodes: {sum(counts[index] for index in range(0x80, 0x100))}",
        f"  LG opcodes: {sum(counts[index] for index in range(0x60, 0x70))}",
        f"  LBL opcodes: {counts[0x13]}",
        f"  LDF opcodes: {counts[0x33]}",
        "  most common bytes:",
    ]
    for byte_value, count in counts.most_common(12):
        lines.append(f"    0x{byte_value:02x}: {count}")
    return "\n".join(lines)


def opcode_name(opcode: int, use_names: bool) -> str:
    if use_names and opcode in NAMED_OPCODES:
        return NAMED_OPCODES[opcode]
    return OPCODES[opcode]


def normal_branch_target(page: int, opcode: int) -> tuple[int, int] | None:
    if 0x80 <= opcode <= 0xBF:
        return 0o37, opcode & 0x3F
    if 0xC0 <= opcode <= 0xFF:
        return (0o36 if page == 0o37 else page), opcode & 0x3F
    return None


def lg_target(opcode: int, second: int) -> tuple[bool, int, int]:
    is_call = (second & 0x40) == 0
    page = ((15 - (opcode & 0x0F)) << 1) | ((second >> 7) & 1)
    word = second & 0x3F
    return is_call, page, word


def opcode_at(rom: bytearray, offset: int) -> int:
    return rom[lfsr_pc(offset)]


def previous_opcode_offset(offset: int) -> int | None:
    if offset <= 0:
        return None
    candidate = offset - 1
    if opcode_at_cached(candidate) in (0x13, 0x33) or 0x60 <= opcode_at_cached(candidate) <= 0x6F:
        return offset - 2 if offset >= 2 else None
    return candidate


_opcode_cache: dict[int, int] = {}


def opcode_at_cached(offset: int) -> int:
    return _opcode_cache[offset]


def is_routine_entry(offset: int) -> bool:
    if offset % 64 == 0:
        return True
    prev_offset = previous_opcode_offset(offset)
    if prev_offset is None:
        return True
    return opcode_at_cached(prev_offset) in {0x40, 0x41} or 0xC0 <= opcode_at_cached(prev_offset) <= 0xFF


def build_label_map(rom: bytearray) -> tuple[dict[int, str], dict[int, int]]:
    global _opcode_cache
    _opcode_cache = {offset: opcode_at(rom, offset) for offset in range(ROM_SIZE)}
    incoming_counts: dict[int, int] = defaultdict(int)
    target_offsets: set[int] = set()
    offset = 0

    while offset < ROM_SIZE:
        page = offset // 64
        opcode = opcode_at_cached(offset)
        target: tuple[int, int] | None = normal_branch_target(page, opcode)
        if target is not None:
            target_offset = logical_offset_for_page_word(*target)
            incoming_counts[target_offset] += 1
            target_offsets.add(target_offset)
        elif 0x60 <= opcode <= 0x6F:
            second = opcode_at_cached(offset + 1)
            _, target_page, target_word = lg_target(opcode, second)
            target_offset = logical_offset_for_page_word(target_page, target_word)
            incoming_counts[target_offset] += 1
            target_offsets.add(target_offset)

        if opcode in (0x13, 0x33) or 0x60 <= opcode <= 0x6F:
            offset += 1
        offset += 1

    label_map: dict[int, str] = {}
    for offset in sorted(target_offsets):
        if offset in SEMANTIC_LABELS:
            label_map[offset] = SEMANTIC_LABELS[offset]
        elif is_routine_entry(offset) and ((offset // 64) in {0o36, 0o37} or incoming_counts[offset] >= 2):
            page = offset // 64
            word = LFSR_SEQUENCE[offset & 0x3F]
            label_map[offset] = f"SUB_P{page:02o}_W{word:03o}"
        else:
            label_map[offset] = default_label_for_offset(offset)

    return label_map, dict(incoming_counts)


def label_for_page_word(page: int, word: int, label_map: dict[int, str]) -> str:
    offset = logical_offset_for_page_word(page, word)
    return label_map.get(offset, default_label_for_offset(offset))


def auto_short_routine_comments(
    rom: bytearray,
    label_map: dict[int, str],
    use_names: bool,
) -> dict[int, str]:
    comments: dict[int, str] = {}
    target_offsets = sorted(label_map)

    for offset in target_offsets:
        if not is_routine_entry(offset):
            continue
        opcode0 = opcode_at_cached(offset)
        opcode1 = opcode_at_cached(offset + 1) if offset + 1 < ROM_SIZE else None
        opcode2 = opcode_at_cached(offset + 2) if offset + 2 < ROM_SIZE else None

        if opcode0 in NAMED_OPCODES and opcode1 == 0x40:
            comments[offset] = f"short routine: {opcode_name(opcode0, use_names)} ; RET"
            continue

        page = offset // 64
        target1 = normal_branch_target(page, opcode1) if opcode1 is not None else None
        if opcode0 in NAMED_OPCODES and target1 is not None and offset not in SEMANTIC_LABELS:
            target_label = label_for_page_word(*target1, label_map)
            comments[offset] = (
                f"short routine: {opcode_name(opcode0, use_names)} ; "
                f"{opcode_name(opcode1, use_names)} {target_label}"
            )
            continue

        if opcode2 == 0x40 and opcode0 in NAMED_OPCODES and opcode1 is not None and offset not in SEMANTIC_LABELS:
            comments[offset] = (
                f"short routine: {opcode_name(opcode0, use_names)} ; "
                f"{opcode_name(opcode1, use_names)} ; RET"
            )

    return comments


def disassemble(
    rom: bytearray,
    comments: dict[int, str] | None = None,
    use_names: bool = False,
) -> Iterable[str]:
    comments = comments or {}
    label_map, _incoming_counts = build_label_map(rom)
    auto_comments = auto_short_routine_comments(rom, label_map, use_names)
    merged_comments = {**auto_comments, **comments}
    offset = 0
    current_page = -1

    while offset < ROM_SIZE:
        page = offset // 64
        if page != current_page:
            current_page = page
            yield ""
            yield f"; PAGE {page:o} (logical offsets {page * 64:04o}-{page * 64 + 63:04o})"

        label = label_map.get(offset)
        if label is not None:
            yield f"{label}:"

        physical = lfsr_pc(offset)
        opcode = rom[physical]
        comment = merged_comments.get(offset)
        suffix = f" ; {comment}" if comment else ""

        if 0x60 <= opcode <= 0x6F:
            second_physical = lfsr_pc(offset + 1)
            second = rom[second_physical]
            is_call, target_page, target_word = lg_target(opcode, second)
            target_label = label_for_page_word(target_page, target_word, label_map)
            long_kind = "LGCALL" if is_call else "LGGO"
            yield (
                f"{offset:04o} @{physical:04o}  {opcode:03o}  {opcode_name(opcode, use_names):<14}"
                f" {long_kind:<6} {target_label}{suffix}"
            )
            offset += 1
            second_comment = merged_comments.get(offset)
            second_suffix = f" ; {second_comment}" if second_comment else ""
            yield (
                f"{offset:04o} @{second_physical:04o}  {second:03o}  "
                f"DATA    {second >> 6},{second & 0x3F:02o}  ; raw LG target byte -> {target_label}"
                f"{second_suffix}"
            )
        else:
            operand = ""
            target = normal_branch_target(page, opcode)
            if target is not None:
                target_page, target_word = target
                operand = f" {label_for_page_word(target_page, target_word, label_map)}"
            yield f"{offset:04o} @{physical:04o}  {opcode:03o}  {opcode_name(opcode, use_names):<14}{operand}{suffix}"
            if opcode in (0x13, 0x33):
                offset += 1
                second_physical = lfsr_pc(offset)
                second = rom[second_physical]
                second_comment = merged_comments.get(offset)
                second_suffix = f" ; {second_comment}" if second_comment else ""
                yield (
                    f"{offset:04o} @{second_physical:04o}  {second:03o}  "
                    f"DATA    {second >> 4},{second & 0x0F}{second_suffix}"
                )

        offset += 1


def build_seed_comments() -> dict[int, str]:
    return {
        0o0000: "reset entry point; starts with a CALL chain rather than inline setup",
        0o0074: "LBL operand, likely part of a dispatch or constant table",
        0o0116: "dense cluster of LBL/CALL patterns suggests a lookup table or keypad/display dispatch",
    }


def build_named_comments() -> dict[int, str]:
    comments = build_seed_comments()
    comments.update(
        {
            0o0001: "reset touches MODE_STATE_C before the fixed-flag tests begin",
            0o0006: "reset seeds SELECT_STATE bit 8 very early",
            0o0057: "reset writes the default ANNUNCIATOR code; likely blank or neutral",
            0o0116: "page 1 opens a standardized field-normalization block",
            0o0123: "repeated CALL 057 pattern now reads as field walking over fixed RAM regions",
            0o0144: "ANNUNCIATOR is consulted in the same normalization region",
            0o0206: "start of the DS8874-facing display-digit path",
            0o0220: "ANNUNCIATOR participates directly in the display loop",
            0o0230: "SCAN_STATE / TKB front-end of the keypad scan path",
            0o2000: "page 20 looks like template stamping plus inline decimal adjustment",
            0o2020: "template site 2,7 used by the page-20 staging family",
            0o2070: "inline decimal-adjust-looking tail (MTA ; ADX 6), not a clean call into page 36",
            0o2200: "page 22 is the strongest current special-entry / edit-state latch handler",
            0o2243: "MODE_STATE_C bit-8 toggling is explicit here",
            0o2302: "page 23 is the clearest early decode boundary after scan state is tested",
            0o2400: "page 24 looks like immediate post-decode bookkeeping",
            0o2500: "page 25 looks like heavier working-register update after decode",
            0o2600: "page 26 looks like cleanup / finalize for the same handler family",
            0o3000: "page 30 couples MAIN_FIELD, ANNUNCIATOR, and EXP_STATE in one special path",
            0o3022: "ANNUNCIATOR is written back in the same page-30 special formatting region",
            0o3071: "rare EXP_STATE access; likely scientific-entry/display-state related",
            0o3200: "page 32 is the strongest current compact compare/threshold worker",
            0o3216: "stamps a conspicuous fixed decimal template into MAIN_FIELD",
            0o3233: "local CALL 032 enters the subtract/compare worker below",
            0o3270: "compact subtract/compare worker: SC, MTA 2, SUB, ADX 10, EXC+ 2",
            0o3400: "page 34 is a mixed control/numeric bridge with annunciator-side behavior",
            0o3470: "specific ANNUNCIATOR state write; reached after MODE_STATE_C bit-8 gating",
            0o3604: "page-36 add/carry worker: add one digit with incoming carry",
            0o3620: "page-36 carry-propagation worker: seed/propagate carry through current digit",
            0o3630: "page-36 subtract/compare worker: one-digit subtract with decimal correction",
            0o3706: "page 37 is helper fabric, not a bytecode VM; this entry selects ANNUNCIATOR",
            0o3717: "helper entry selecting SCAN_STATE",
            0o3724: "helper path anchored on MAIN_FIELD for digit walking",
            0o3736: "helper path that begins with RSC and falls into shared local control",
            0o3760: "helper path on the WORK_2_5 / WORK_2_14 side of the staging family",
        }
    )
    return comments


def main() -> None:
    parser = argparse.ArgumentParser(description="MM5799 ROM analysis helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="summarize one or more ROMs")
    summary_parser.add_argument("rom", nargs="+", type=Path)

    compare_parser = subparsers.add_parser("compare", help="compare cleaned and raw 1.5K ROMs")
    compare_parser.add_argument("clean_rom", type=Path)
    compare_parser.add_argument("raw_rom", type=Path)

    disasm_parser = subparsers.add_parser("disasm", help="disassemble a ROM in LFSR PC order")
    disasm_parser.add_argument("rom", type=Path)
    disasm_parser.add_argument(
        "--annotate",
        action="store_true",
        help="include a small seed set of human comments",
    )
    disasm_parser.add_argument(
        "--named",
        action="store_true",
        help="use named RAM-field aliases and a broader first-pass comment set",
    )

    args = parser.parse_args()

    if args.command == "summary":
        for rom_path in args.rom:
            print(rom_summary(rom_path.name, load_rom(rom_path)))
    elif args.command == "compare":
        print(compare_roms(args.clean_rom, args.raw_rom))
    elif args.command == "disasm":
        if args.named:
            comments = build_named_comments()
        elif args.annotate:
            comments = build_seed_comments()
        else:
            comments = {}
        for line in disassemble(load_rom(args.rom), comments, use_names=args.named):
            print(line)


if __name__ == "__main__":
    main()
