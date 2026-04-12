#!/usr/bin/env python3

from __future__ import annotations

import html
import json
import re
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

ISA_SUMMARIES = {
    "NOP": "No operation.",
    "HXBR": "Exchange H and Br.",
    "ADD": "A <- A + C + M[B]. If result >= 10 set C=1, else set C=0 and arm skip.",
    "SC": "Set carry: C <- 1.",
    "TF 1": "Skip if F1 input is zero.",
    "TIR": "Skip if D03 is zero.",
    "MTA": "A <- M[B].",
    "MTA 1": "A <- M[B], then Br <- Br XOR 1.",
    "MTA 2": "A <- M[B], then Br <- Br XOR 2.",
    "MTA 3": "A <- M[B], then Br <- Br XOR 3.",
    "EXC": "Exchange A <-> M[B].",
    "EXC 1": "Exchange A <-> M[B], then Br <- Br XOR 1.",
    "EXC 2": "Exchange A <-> M[B], then Br <- Br XOR 2.",
    "EXC 3": "Exchange A <-> M[B], then Br <- Br XOR 3.",
    "EXC-": "Exchange A <-> M[B], then decrement Bd. Emulator skips on wrap when Bd becomes 15.",
    "EXC- 1": "Exchange A <-> M[B], Br <- Br XOR 1, then decrement Bd. Emulator skips on wrap when Bd becomes 15.",
    "EXC- 2": "Exchange A <-> M[B], Br <- Br XOR 2, then decrement Bd. Emulator skips on wrap when Bd becomes 15.",
    "EXC- 3": "Exchange A <-> M[B], Br <- Br XOR 3, then decrement Bd. Emulator skips on wrap when Bd becomes 15.",
    "EXC+": "Exchange A <-> M[B], then increment Bd. Emulator skips on wrap when Bd becomes 0 or 13; wrap rule is uncertain.",
    "EXC+ 1": "Exchange A <-> M[B], Br <- Br XOR 1, then increment Bd. Emulator skips on wrap when Bd becomes 0 or 13; wrap rule is uncertain.",
    "EXC+ 2": "Exchange A <-> M[B], Br <- Br XOR 2, then increment Bd. Emulator skips on wrap when Bd becomes 0 or 13; wrap rule is uncertain.",
    "EXC+ 3": "Exchange A <-> M[B], Br <- Br XOR 3, then increment Bd. Emulator skips on wrap when Bd becomes 0 or 13; wrap rule is uncertain.",
    "DSPA": "Drive segment outputs directly: A to Sa..Sd, H to Se..Sg, Sp <- ~C.",
    "DSPS": "Drive segment outputs from PLA decode of A, with Sp <- ~C.",
    "AD": "A <- A + M[B].",
    "LBL": "Two-byte load of B from the next ROM byte. Successive-LBL behavior is uncertain in the emulator.",
    "TF 2": "Skip if F2 input is zero.",
    "TKB": "Read keyboard inputs via D into K and skip if any key is active.",
    "COMP": "A <- ~A.",
    "AXO": "Exchange A and serial buffer.",
    "SUB": "Subtract/borrow primitive: tmp <- ~A + C + M[B], A <- tmp. If tmp > 15 set C=1 and arm skip, else C=0.",
    "RSC": "Reset carry: C <- 0.",
    "TF 3": "Skip if F3 input is zero.",
    "BTD": "D <- Bd and force BLK low for one cycle.",
    "0TA": "A <- 0.",
    "HXA": "Exchange H and A.",
    "TAM": "Skip if A == M[B].",
    "LDF": "Two-byte flag load. Masked bits in next ROM byte update F1..F3.",
    "READ": "A <- K.",
    "TIN": "Skip if INB == 1.",
    "RET": "Return by popping SA into P and shifting SB up into SA.",
    "RETS": "Set skip, then execute RET. Effectively return and skip next instruction at caller.",
    "RSM 8": "Clear bit 8 in M[B].",
    "BTA": "A <- Bd.",
    "TM 1": "Skip if tested bit 1 of M[B] is zero.",
    "TM 2": "Skip if tested bit 2 of M[B] is zero.",
    "TM 4": "Skip if tested bit 4 of M[B] is zero.",
    "TM 8": "Skip if tested bit 8 of M[B] is zero.",
    "RSM 1": "Clear bit 1 in M[B].",
    "SM 1": "Set bit 1 in M[B].",
    "SM 8": "Set bit 8 in M[B].",
    "RSM 4": "Clear bit 4 in M[B].",
    "RSM 2": "Clear bit 2 in M[B].",
    "TC": "Skip if C == 0.",
    "SM 2": "Set bit 2 in M[B].",
    "SM 4": "Set bit 4 in M[B].",
    "ATB": "Bd <- A.",
    "ADX 1": "A <- A + 1. Arm skip if result does not overflow 4 bits.",
    "ADX 2": "A <- A + 2. Arm skip if result does not overflow 4 bits.",
    "ADX 3": "A <- A + 3. Arm skip if result does not overflow 4 bits.",
    "ADX 4": "A <- A + 4. Arm skip if result does not overflow 4 bits.",
    "ADX 5": "A <- A + 5. Arm skip if result does not overflow 4 bits.",
    "ADX 6": "A <- A + 6. Used as decimal correction. No skip on non-overflow because n == 6 is special.",
    "ADX 7": "A <- A + 7. Arm skip if result does not overflow 4 bits.",
    "ADX 8": "A <- A + 8. Arm skip if result does not overflow 4 bits.",
    "ADX 9": "A <- A + 9. Arm skip if result does not overflow 4 bits.",
    "ADX 10": "A <- A + 10. Arm skip if result does not overflow 4 bits.",
    "ADX 11": "A <- A + 11. Arm skip if result does not overflow 4 bits.",
    "ADX 12": "A <- A + 12. Arm skip if result does not overflow 4 bits.",
    "ADX 13": "A <- A + 13. Arm skip if result does not overflow 4 bits.",
    "ADX 14": "A <- A + 14. Arm skip if result does not overflow 4 bits.",
    "ADX 15": "A <- A + 15. Arm skip if result does not overflow 4 bits.",
    "LG": "Two-byte long transfer. Target page comes from opcode nibble and one bit from the second byte. Bit 6 of the second byte selects long call versus long go.",
    "LM 0": "M[B] <- 0, then Bd <- Bd + 1.",
    "LM 1": "M[B] <- 1, then Bd <- Bd + 1.",
    "LM 2": "M[B] <- 2, then Bd <- Bd + 1.",
    "LM 3": "M[B] <- 3, then Bd <- Bd + 1.",
    "LM 4": "M[B] <- 4, then Bd <- Bd + 1.",
    "LM 5": "M[B] <- 5, then Bd <- Bd + 1.",
    "LM 6": "M[B] <- 6, then Bd <- Bd + 1.",
    "LM 7": "M[B] <- 7, then Bd <- Bd + 1.",
    "LM 8": "M[B] <- 8, then Bd <- Bd + 1.",
    "LM 9": "M[B] <- 9, then Bd <- Bd + 1.",
    "LM 10": "M[B] <- 10, then Bd <- Bd + 1.",
    "LM 11": "M[B] <- 11, then Bd <- Bd + 1.",
    "LM 12": "M[B] <- 12, then Bd <- Bd + 1.",
    "LM 13": "M[B] <- 13, then Bd <- Bd + 1.",
    "LM 14": "M[B] <- 14, then Bd <- Bd + 1.",
    "LM 15": "M[B] <- 15, then Bd <- Bd + 1.",
    "CALL": "Transfer to page 037, word xx. If not already on page 036/037, push return state into SA/SB.",
    "GO": "Jump to raw word xx within the current page. If executed on page 037, page changes to 036.",
    "LB": "Load B from encoded register/digit, but only the first LB in a consecutive run takes effect in the emulator.",
}

DISASM_RE = re.compile(r"^\s*([0-7]{4})\s+@([0-7]{4})\s+([0-7]{3})\s+(.*)$")


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


def parse_disassembly(path: Path) -> tuple[list[dict[str, object]], dict[int, int]]:
    lines: list[dict[str, object]] = []
    logical_to_line: dict[int, int] = {}
    pending_labels: list[str] = []

    for raw_line in path.read_text().splitlines():
        match = DISASM_RE.match(raw_line)
        if match:
            logical = int(match.group(1), 8)
            physical = int(match.group(2), 8)
            opcode = int(match.group(3), 8)
            body = match.group(4)
            line_obj = {
                "type": "instr",
                "logical": logical,
                "physical": physical,
                "opcode": opcode,
                "body": body.rstrip(),
                "labels": pending_labels,
                "text": raw_line,
            }
            logical_to_line[logical] = len(lines)
            lines.append(line_obj)
            pending_labels = []
            continue

        stripped = raw_line.strip()
        if stripped.endswith(":") and not stripped.startswith(";"):
            pending_labels.append(stripped[:-1])
            lines.append({"type": "label", "text": raw_line, "name": stripped[:-1]})
            continue

        if raw_line.startswith("; PAGE"):
            lines.append({"type": "page", "text": raw_line})
            continue

        lines.append({"type": "text", "text": raw_line})

    return lines, logical_to_line


def build_html(rom: list[int], disasm_lines: list[dict[str, object]], logical_to_line: dict[int, int]) -> str:
    rom_json = json.dumps(rom)
    lfsr_json = json.dumps(LFSR_SEQUENCE)
    opcodes_json = json.dumps(OPCODES)
    isa_summaries_json = json.dumps(ISA_SUMMARIES)
    disasm_json = json.dumps(disasm_lines)
    logical_map_json = json.dumps({str(k): v for k, v in logical_to_line.items()})

    html_template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MM5799 Step Debugger</title>
  <style>
    :root {{
      --bg: #f3efe6;
      --panel: #fffaf0;
      --ink: #1f1a14;
      --muted: #74685b;
      --line: #d9cdbd;
      --accent: #0f6b5c;
      --accent-soft: #d4efe9;
      --warn: #8f3d00;
      --ram-hi: #fff1c7;
      --pc-hi: #d9f4cf;
      --sel-hi: #cde6ff;
      --font-ui: "Avenir Next", "Segoe UI", sans-serif;
      --font-code: "SF Mono", "Menlo", "Consolas", monospace;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      height: 100vh;
      overflow: hidden;
      background: linear-gradient(180deg, #f7f3eb 0%, #efe7da 100%);
      color: var(--ink);
      font-family: var(--font-ui);
    }}
    .app {{
      display: grid;
      grid-template-columns: 400px 460px 1fr;
      height: 100vh;
      gap: 12px;
      padding: 12px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      box-shadow: 0 8px 30px rgba(40, 32, 20, 0.06);
      overflow: hidden;
    }}
    .left {{
      display: grid;
      grid-template-rows: auto auto auto 1fr;
      gap: 12px;
      min-height: 0;
      overflow: hidden;
    }}
    .left > .panel {{
      min-height: 0;
    }}
    .middle {{
      display: grid;
      grid-template-rows: 1fr;
      gap: 12px;
      min-height: 0;
      overflow: auto;
    }}
    .section {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
    }}
    .section:last-child {{ border-bottom: 0; }}
    h1 {{
      margin: 0 0 6px;
      font-size: 20px;
      line-height: 1.2;
    }}
    .subtitle {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }}
    button {{
      border: 1px solid var(--line);
      background: white;
      color: var(--ink);
      padding: 8px 12px;
      border-radius: 999px;
      font: inherit;
      cursor: pointer;
    }}
    button.primary {{
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }}
    button:disabled {{
      opacity: 0.55;
      cursor: default;
    }}
    button:hover {{ filter: brightness(0.98); }}
    .grid {{
      display: grid;
      gap: 8px;
    }}
    .register-grid {{
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }}
    .field {{
      display: grid;
      gap: 4px;
    }}
    .field label {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .field input {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 7px 8px;
      background: white;
      color: var(--ink);
      font-family: var(--font-code);
      font-size: 13px;
    }}
    .field.checkbox {{
      grid-template-columns: auto 1fr;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 7px 8px;
      background: white;
    }}
    .field.checkbox label {{
      font-size: 12px;
      color: var(--ink);
      text-transform: none;
      letter-spacing: 0;
    }}
    .toolbar-option {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: white;
      font-size: 12px;
    }}
    .toolbar-option input[type="number"] {{
      width: 64px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 4px 6px;
      font: inherit;
      font-family: var(--font-code);
    }}
    .toolbar-option input[type="text"] {{
      width: 40px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 4px 6px;
      font: inherit;
      font-family: var(--font-code);
      text-align: center;
    }}
    .keypad-wrap {{
      display: grid;
      gap: 8px;
    }}
    .keypad-top {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }}
    .keypad-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }}
    .keypad-controls {{
      display: grid;
      gap: 8px;
      margin-bottom: 4px;
    }}
    .key {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: white;
      padding: 10px 8px;
      text-align: center;
      font: inherit;
      font-family: var(--font-code);
      font-weight: 600;
      line-height: 1;
      cursor: pointer;
      transition: background 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
      min-height: 42px;
    }}
    .key.active {{
      background: #ffcc5c;
      border-color: #b36a00;
      box-shadow: inset 0 0 0 2px rgba(179, 106, 0, 0.24);
    }}
    .key.scanned {{
      border-color: #4b7db8;
      box-shadow: inset 0 0 0 2px rgba(67, 119, 184, 0.22);
    }}
    .key.active.scanned {{
      background: #d8f0da;
      border-color: #2c8f4d;
      box-shadow: inset 0 0 0 2px rgba(44, 143, 77, 0.22);
    }}
    .key-meta {{
      color: var(--muted);
      font-size: 11px;
      line-height: 1.3;
    }}
    .small-note {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 8px;
      line-height: 1.4;
    }}
    .status-strip {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-family: var(--font-code);
      font-size: 13px;
      margin-top: 8px;
      min-height: 34px;
      align-items: flex-start;
    }}
    .status-strip span {{
      background: #f5eee1;
      border: 1px solid var(--line);
      padding: 4px 8px;
      border-radius: 999px;
    }}
    .status-strip span.pending-skip {{
      background: #ffe5c9;
      border-color: #d58b3f;
      color: #7a3f00;
      font-weight: 700;
    }}
    .status-strip span.pending-skip.idle {{
      visibility: hidden;
    }}
    .ram-wrap {{
      padding: 0 14px 14px;
      overflow: auto;
      min-height: 0;
    }}
    .ram-panel {{
      display: grid;
      grid-template-rows: auto 1fr;
      min-height: 0;
    }}
    .ram-grid {{
      display: grid;
      grid-template-columns: 48px repeat(16, 1fr);
      gap: 4px;
      align-items: center;
      font-family: var(--font-code);
      font-size: 12px;
    }}
    .ram-head, .ram-row-label {{
      color: var(--muted);
      text-align: center;
      border-radius: 6px;
      padding: 2px 0;
    }}
    .ram-head.current, .ram-row-label.current {{
      background: #fde6a8;
      color: #6a4a00;
      font-weight: 700;
    }}
    .ram-cell {{
      width: 100%;
      min-width: 0;
      border: 1px solid var(--line);
      background: white;
      border-radius: 6px;
      padding: 4px 0;
      text-align: center;
      font-family: var(--font-code);
      font-size: 12px;
    }}
    .ram-cell.current {{
      background: var(--ram-hi);
      border-color: #d4a72a;
      box-shadow: inset 0 0 0 2px #b47a00;
      font-weight: 700;
    }}
    .ram-cell.selected {{
      border-color: #4377b8;
      box-shadow: inset 0 0 0 2px rgba(67, 119, 184, 0.35);
    }}
    .ram-cell.watch {{
      border-color: #a22a2a;
      box-shadow: inset 0 0 0 2px rgba(162, 42, 42, 0.18);
    }}
    .ram-cell.current.watch {{
      box-shadow: inset 0 0 0 2px #b47a00, 0 0 0 1px rgba(162, 42, 42, 0.35);
    }}
    .ram-cell.current.selected {{
      box-shadow: inset 0 0 0 2px #b47a00, 0 0 0 1px rgba(67, 119, 184, 0.55);
    }}
    .display-wrap {{
      display: grid;
      gap: 10px;
    }}
    .hardware-panel {{
      overflow: auto;
    }}
    .hardware-wrap {{
      position: relative;
      width: 100%;
      max-width: 440px;
      margin: 0 auto;
      aspect-ratio: 1671 / 3652;
      border: 1px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
      background: url("calculator_cropped_tight10_cleaned_strong.png") center/cover no-repeat;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2);
      touch-action: manipulation;
      user-select: none;
    }}
    .hardware-display {{
      position: absolute;
      left: 5.07%;
      top: 8.03%;
      width: 89.80%;
      height: 7.91%;
      display: grid;
      grid-template-columns: repeat(9, minmax(0, 1fr));
      gap: 2px;
      pointer-events: none;
    }}
    .hardware-digit {{
      position: relative;
      border-radius: 3px;
    }}
    .hardware-digit.active {{
      box-shadow: inset 0 0 0 1px rgba(80, 160, 255, 0.7);
    }}
    .hardware-digit.selected {{
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.85);
    }}
    .hw-sevenseg {{
      position: relative;
      width: 100%;
      height: 100%;
    }}
    .hw-seg {{
      position: absolute;
      background: rgba(255, 28, 40, 0.08);
      transition: background 80ms linear, box-shadow 80ms linear;
    }}
    .hw-seg.on {{
      background: rgba(255, 65, 92, 0.9);
      box-shadow: 0 0 7px rgba(255, 35, 70, 0.52);
    }}
    .hw-seg.a, .hw-seg.d, .hw-seg.g {{
      width: 58%;
      height: 10%;
      left: 21%;
      border-radius: 4px;
    }}
    .hw-seg.a {{ top: 2%; }}
    .hw-seg.g {{ top: 45%; }}
    .hw-seg.d {{ bottom: 2%; }}
    .hw-seg.b, .hw-seg.c, .hw-seg.e, .hw-seg.f {{
      width: 12%;
      height: 34%;
      border-radius: 4px;
    }}
    .hw-seg.f {{ left: 6%; top: 7%; }}
    .hw-seg.b {{ right: 6%; top: 7%; }}
    .hw-seg.e {{ left: 6%; bottom: 7%; }}
    .hw-seg.c {{ right: 6%; bottom: 7%; }}
    .hw-dot {{
      position: absolute;
      right: -8%;
      bottom: 0;
      width: 12%;
      height: 12%;
      border-radius: 50%;
      background: rgba(255, 35, 70, 0.09);
    }}
    .hw-dot.on {{
      background: rgba(255, 92, 120, 0.95);
      box-shadow: 0 0 7px rgba(255, 55, 86, 0.55);
    }}
    .hw-key {{
      position: absolute;
      border: 1px solid transparent;
      border-radius: 12px;
      background: transparent;
      cursor: pointer;
      transition: box-shadow 100ms linear, background 100ms linear, border-color 100ms linear;
    }}
    .hw-key.active {{
      border-color: rgba(71, 129, 205, 0.95);
      background: rgba(71, 129, 205, 0.2);
      box-shadow: inset 0 0 0 1px rgba(71, 129, 205, 0.55);
    }}
    .hw-key.scanned {{
      border-color: rgba(44, 159, 86, 0.95);
      background: rgba(44, 159, 86, 0.25);
      box-shadow: inset 0 0 0 1px rgba(44, 159, 86, 0.55);
    }}
    .hw-key.active.scanned {{
      border-width: 2px;
      box-shadow: inset 0 0 0 1px rgba(44, 159, 86, 0.75);
    }}
    .display-status {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 12px;
      color: var(--muted);
    }}
    .display-status span {{
      min-width: 96px;
    }}
    .calc-display {{
      display: grid;
      grid-template-columns: repeat(9, minmax(0, 1fr));
      gap: 8px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: linear-gradient(180deg, #0f1514, #182120);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    }}
    .calc-digit {{
      min-height: 72px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.08);
      background: linear-gradient(180deg, rgba(35,53,49,0.96), rgba(20,31,29,0.96));
      color: #86ffbb;
      display: grid;
      align-items: start;
      justify-items: center;
      padding: 4px 4px 2px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
    }}
    .calc-digit.active {{
      border-color: rgba(134,255,187,0.45);
      box-shadow: inset 0 0 0 1px rgba(134,255,187,0.2), 0 0 0 1px rgba(134,255,187,0.08);
    }}
    .calc-digit.selected {{
      border-color: rgba(95, 166, 255, 0.35);
      box-shadow: inset 0 0 0 1px rgba(95, 166, 255, 0.16);
    }}
    .sevenseg {{
      position: relative;
      width: 34px;
      height: 56px;
      margin-top: 2px;
    }}
    .seg {{
      position: absolute;
      background: rgba(134,255,187,0.10);
      box-shadow: inset 0 0 0 1px rgba(134,255,187,0.05);
      transition: background 80ms linear, box-shadow 80ms linear;
    }}
    .seg.on {{
      background: #86ffbb;
      box-shadow: 0 0 10px rgba(134,255,187,0.34);
    }}
    .seg.a, .seg.d, .seg.g {{
      width: 18px;
      height: 5px;
      left: 8px;
      border-radius: 4px;
    }}
    .seg.a {{ top: 0; }}
    .seg.g {{ top: 25px; }}
    .seg.d {{ bottom: 0; }}
    .seg.b, .seg.c, .seg.e, .seg.f {{
      width: 5px;
      height: 18px;
      border-radius: 4px;
    }}
    .seg.f {{ left: 2px; top: 4px; }}
    .seg.b {{ right: 2px; top: 4px; }}
    .seg.e {{ left: 2px; bottom: 4px; }}
    .seg.c {{ right: 2px; bottom: 4px; }}
    .calc-dot {{
      position: absolute;
      right: -2px;
      bottom: -2px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: rgba(134,255,187,0.16);
    }}
    .calc-dot.on {{
      background: #baffd6;
      box-shadow: 0 0 8px rgba(186,255,214,0.35);
    }}
    .right {{
      display: grid;
      grid-template-rows: auto 1fr;
      min-height: 0;
    }}
    .code-header {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
    }}
    .code-header .title {{
      font-size: 15px;
      font-weight: 600;
    }}
    .code-header .meta {{
      color: var(--muted);
      font-size: 12px;
    }}
    .disasm {{
      overflow: auto;
      min-height: 0;
      font-family: var(--font-code);
      font-size: 13px;
      line-height: 1.5;
      padding: 8px 0;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.45), rgba(255,255,255,0.7)),
        repeating-linear-gradient(180deg, transparent, transparent 28px, rgba(122, 104, 80, 0.045) 28px, rgba(122, 104, 80, 0.045) 29px);
    }}
    .line {{
      white-space: pre;
      padding: 0 14px 0 28px;
      border-left: 4px solid transparent;
      cursor: default;
      position: relative;
    }}
    .line.instr {{
      cursor: pointer;
    }}
    .line.instr:hover {{
      background: #f3efe8;
    }}
    .line.current {{
      background: var(--pc-hi);
      border-left-color: var(--accent);
    }}
    .line.previous {{
      background: #e3f3ee;
      border-left-color: #5d9d8c;
    }}
    .line.selected {{
      background: var(--sel-hi);
      border-left-color: #4377b8;
    }}
    .line.current.selected {{
      background: linear-gradient(90deg, var(--pc-hi), #eef9e9);
      border-left-color: var(--accent);
      box-shadow: inset 0 0 0 1px rgba(15, 107, 92, 0.14);
    }}
    .line.breakpoint::before {{
      content: "";
      position: absolute;
      left: 9px;
      top: 50%;
      width: 10px;
      height: 10px;
      margin-top: -5px;
      border-radius: 50%;
      background: #c23b22;
      box-shadow: 0 0 0 1px rgba(92, 20, 10, 0.18);
    }}
    .line.current.breakpoint::before {{
      background: #0f6b5c;
      box-shadow: 0 0 0 1px rgba(15, 107, 92, 0.2);
    }}
    .line.page {{
      color: var(--warn);
      font-weight: 600;
      margin-top: 8px;
    }}
    .line.label {{
      color: #7a3f19;
      font-weight: 600;
    }}
    .op-tip {{
      text-decoration: underline dotted rgba(15, 107, 92, 0.55);
      text-underline-offset: 2px;
      cursor: help;
    }}
    @media (max-width: 1100px) {{
      body {{
        height: auto;
        overflow: auto;
      }}
      .app {{
        grid-template-columns: 1fr;
        height: auto;
      }}
      .left {{
        order: 2;
        overflow: visible;
      }}
      .middle {{
        order: 3;
        overflow: visible;
      }}
      .right {{
        order: 1;
        min-height: 60vh;
      }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <div class="left">
      <div class="panel">
        <div class="section">
          <h1>MM5799 Step Debugger</h1>
          <div class="subtitle">
            Code view is driven by the current best annotated listing in
            <code>analysis/sinclaircambridgeprogrammable.dan.asm</code>.
          </div>
          <div class="toolbar">
            <button class="primary" id="step-btn">Step</button>
            <button id="stepover-btn">To RET</button>
            <button id="step10-btn">Step 10</button>
            <button id="continue-btn">Continue</button>
            <button id="reset-btn">Reset</button>
            <button id="apply-btn">Apply Edits</button>
            <button id="goto-pc-btn">Scroll To PC</button>
            <button id="goto-writer-btn">Go To Writer</button>
            <label class="toolbar-option" for="animate-toggle">
              <input type="checkbox" id="animate-toggle" checked>
              <span>Animate</span>
            </label>
            <label class="toolbar-option" for="breakpoints-toggle">
              <input type="checkbox" id="breakpoints-toggle" checked>
              <span>Breakpoints</span>
            </label>
            <label class="toolbar-option" for="animate-delay">
              <span>Delay ms</span>
              <input type="number" id="animate-delay" min="0" max="2000" step="10" value="0">
            </label>
            <label class="toolbar-option" for="lb05-value">
              <span>LB(r,5)</span>
              <input type="text" id="lb05-value" value="4" placeholder="hex">
            </label>
          </div>
          <div class="status-strip" id="status-strip"></div>
        </div>
      </div>

      <div class="panel">
        <div class="section">
          <div class="grid register-grid" id="register-grid"></div>
        </div>
      </div>

      <div class="panel ram-panel">
        <div class="section">
          <strong>RAM (128 nibbles)</strong>
        </div>
        <div class="ram-wrap">
          <div class="ram-grid" id="ram-grid"></div>
        </div>
      </div>
    </div>

    <div class="middle">
      <div class="panel hardware-panel">
        <div class="section">
          <strong>Hardware</strong>
          <div class="hardware-wrap" id="hardware-wrap"></div>
          <div class="small-note">
            Hold keys on the photo. Blue = held, green = currently scanned row.
          </div>
          <div class="keypad-wrap" id="keypad"></div>
          <div class="keypad-controls">
            <label class="toolbar-option" for="force-k">
              <span>Force K</span>
              <input type="text" id="force-k" value="" placeholder="hex">
            </label>
          </div>
        </div>
      </div>
    </div>

    <div class="panel right">
      <div class="code-header">
        <div class="title">Annotated Disassembly</div>
        <div class="meta" id="code-meta"></div>
      </div>
      <div class="disasm" id="disasm"></div>
    </div>
  </div>

  <script>
    const ROM = __ROM_JSON__;
    const LFSR_SEQUENCE = __LFSR_JSON__;
    const OPCODES = __OPCODES_JSON__;
    const DISASM_LINES = __DISASM_JSON__;
    const ISA_SUMMARIES = __ISA_SUMMARIES_JSON__;
    const LOGICAL_TO_LINE = __LOGICAL_MAP_JSON__;
    const LFSR_INDEX_BY_WORD = Object.fromEntries(LFSR_SEQUENCE.map((word, index) => [word, index]));
    const SEGMENT_DATA = [0x7f, 0x40, 0x79, 0x24, 0x30, 0x19, 0x12, 0x02, 0x78, 0x10, 0x06, 0x23, 0x06, 0x66, 0x6f, 0x01, 0x02, 0x08, 0x04];
    const SEGMENT_GLYPHS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "b", "F", "G", "E", " ", "-", "c", "?"];
    const NET_TO_BIT = {{K1: 0x1, K2: 0x2, K3: 0x4, K4: 0x8}};
    const KEYS = [
      {id: "shift", label: "^v", row: 3, net: "K4", group: "top"},
      {id: "cce", label: "C/CE", row: 4, net: "K4", group: "top"},
      {id: "run", label: "RUN", row: 5, net: "K4", group: "top"},
      {id: "0", label: "0", row: 3, net: "K1", group: "main"},
      {id: "6", label: "6", row: 3, net: "K2", group: "main"},
      {id: "eq", label: "=", row: 3, net: "K3", group: "main"},
      {id: "1", label: "1", row: 4, net: "K1", group: "main"},
      {id: "2", label: "2", row: 5, net: "K1", group: "main"},
      {id: "3", label: "3", row: 6, net: "K1", group: "main"},
      {id: "4", label: "4", row: 7, net: "K1", group: "main"},
      {id: "5", label: "5", row: 8, net: "K1", group: "main"},
      {id: "7", label: "7", row: 4, net: "K2", group: "main"},
      {id: "8", label: "8", row: 5, net: "K2", group: "main"},
      {id: "9", label: "9", row: 6, net: "K2", group: "main"},
      {id: "ee", label: "EE", row: 7, net: "K2", group: "main"},
      {id: "plus", label: "+", row: 6, net: "K3", group: "main"},
      {id: "minus", label: "-", row: 4, net: "K3", group: "main"},
      {id: "mul", label: "x", row: 7, net: "K3", group: "main"},
      {id: "div", label: "/", row: 5, net: "K3", group: "main"},
    ].map((key) => ({{...key, bit: NET_TO_BIT[key.net]}}));
    const KEY_BY_ID = Object.fromEntries(KEYS.map((key) => [key.id, key]));
    // Physical keypad order (top-left by row):
    // [EE, ^/v, C/CE, ON/OFF]
    // [7, 8, 9, RUN]
    // [4, 5, 6, /]
    // [1, 2, 3, x]
    // [0, =, +, -]
    const KEY_HOTSPOTS = {
      shift: {col: 1, row: 0}, cce: {col: 2, row: 0}, run: {col: 3, row: 1},
      "0": {col: 0, row: 4}, "1": {col: 0, row: 3}, "2": {col: 1, row: 3}, "3": {col: 2, row: 3},
      "4": {col: 0, row: 2}, "5": {col: 1, row: 2}, "6": {col: 2, row: 2},
      "7": {col: 0, row: 1}, "8": {col: 1, row: 1}, "9": {col: 2, row: 1},
      ee: {col: 0, row: 0}, eq: {col: 1, row: 4}, plus: {col: 2, row: 4},
      minus: {col: 3, row: 4}, mul: {col: 3, row: 3}, div: {col: 3, row: 2},
    };

    const state = {{
      Pp: 0,
      Pw: 0,
      SA: 0,
      SB: 0,
      A: 0,
      H: 0,
      C: 0,
      Br: 0,
      Bd: 0,
      M: new Array(128).fill(0),
      F1: 0,
      F2: 0,
      F3: 0,
      S: 0,
      K: 0,
      D: 0,
      INB: 0,
      SI: 0,
      SO: 0,
      serbuf: 0,
      blk: 1,
      skip: false,
      wasLB: false,
      dsReg: new Array(9).fill(0),
      dsScan: 0,
      displayPos: 0,
      displayActive: -1,
      displaySelected: 0,
      visibleDigits: new Array(9).fill(0),
      visibleGlyphs: new Array(9).fill(" "),
    }};

    let selectedLogical = null;
    let previousLogicalPC = null;
    let currentExecutingLogical = null;
    let isRunning = false;
    let stopRequested = false;
    const breakpoints = new Set();
    const ramWriteWatchpoints = new Set();
    const pressedKeys = new Set();
    let heldMouseKey = null;
    let lastRamWriteWatchHit = null;
    let selectedRamAddr = null;
    const lastWriteLogicalByAddr = new Array(128).fill(null);

    function decodedScanRow(d) {{
      return (d & 0xF) + 2;
    }}

    function oct(n, width = 0) {{
      const value = (n >>> 0).toString(8);
      return value.padStart(width, "0");
    }}

    function hex(n, width = 0) {{
      const value = (n >>> 0).toString(16).toUpperCase();
      return value.padStart(width, "0");
    }}

    function getB() {{
      return ((state.Br & 0x7) << 4) | (state.Bd & 0xF);
    }}

    function setBFromParts(br, bd) {{
      state.Br = br & 0x7;
      state.Bd = bd & 0xF;
    }}

    function getRawPC() {{
      return ((state.Pp & 0x1F) << 6) | (state.Pw & 0x3F);
    }}

    function dpBit() {{
      return state.C ? 0 : 0x80;
    }}

    const GLYPH_SEGMENTS = {{
      " ": [],
      "?": ["a", "b", "g", "e"],
      "0": ["a", "b", "c", "d", "e", "f"],
      "1": ["b", "c"],
      "2": ["a", "b", "d", "e", "g"],
      "3": ["a", "b", "c", "d", "g"],
      "4": ["b", "c", "f", "g"],
      "5": ["a", "c", "d", "f", "g"],
      "6": ["a", "c", "d", "e", "f", "g"],
      "7": ["a", "b", "c"],
      "8": ["a", "b", "c", "d", "e", "f", "g"],
      "9": ["a", "b", "c", "d", "f", "g"],
      "A": ["a", "b", "c", "e", "f", "g"],
      "b": ["g"],
      "C": ["a", "d", "e", "f"],
      "c": ["d", "e", "g"],
      "d": ["b", "c", "d", "e", "g"],
      "E": ["a", "d", "e", "f", "g"],
      "F": ["a", "e", "f", "g"],
      "G": ["a", "c", "d", "e", "f"],
      "-": ["g"],
    }};

    function activeDisplayDigit() {{
      return state.displayActive;
    }}

    function displayDigitIndexFromD(d) {{
      const value = d & 0xF;
      if (value === 0xF) return 0;
      if (value <= 7) return value + 1;
      return value % 9;
    }}

    function clockDs8874FromD(oldD, newD) {{
      const oldClock = oldD & 0x1;
      const newClock = newD & 0x1;
      if (!oldClock && newClock) {{
        for (let i = 8; i > 0; i--) {{
          state.dsReg[i] = state.dsReg[i - 1] & 0x1;
        }}
        state.dsReg[0] = (newD >> 3) & 0x1;
        state.dsScan = (state.dsScan + 1) % 9;
      }}
    }}

    function latchVisibleDisplayDigit(glyph = null) {{
      const active = state.displaySelected % 9;
      state.displayActive = active;
      state.visibleDigits[active] = state.S & 0xFF;
      if (glyph != null) state.visibleGlyphs[active] = glyph;
    }}

    function getLogicalPC() {{
      return ((state.Pp & 0x1F) << 6) | LFSR_INDEX_BY_WORD[state.Pw & 0x3F];
    }}

    function setPCFromLogical(logical) {{
      const page = (logical >> 6) & 0x1F;
      const index = logical & 0x3F;
      state.Pp = page;
      state.Pw = LFSR_SEQUENCE[index];
      // Jumping into the middle of code should not preserve transient decode state
      // from whatever instruction happened to execute previously.
      state.skip = false;
      state.wasLB = false;
      previousLogicalPC = null;
    }}

    function getNextPc(word) {{
      const idx = LFSR_INDEX_BY_WORD[word & 0x3F];
      return LFSR_SEQUENCE[(idx + 1) & 0x3F];
    }}

    function currentOpcode() {{
      return ROM[getRawPC()];
    }}

    function romByte(page, word) {{
      return ROM[((page & 0x1F) << 6) | (word & 0x3F)];
    }}

    function kinput(_d) {{
      let mask = 0;
      const forcedEl = document.getElementById("force-k");
      if (forcedEl) {{
        const forced = (forcedEl.value || "").trim().toUpperCase().replace(/[^0-9A-F]/g, "");
        if (forced !== "") mask = parseInt(forced.slice(-1), 16) & 0xF;
        else mask = expectedKForD(_d);
      }} else {{
        mask = expectedKForD(_d);
      }}
      return mask & 0xF;
    }}

    function lb05Value() {{
      const el = document.getElementById("lb05-value");
      if (!el) return 4;
      const raw = (el.value || "").trim().toUpperCase().replace(/[^0-9A-F]/g, "");
      if (raw === "") return 4;
      return parseInt(raw.slice(-1), 16) & 0xF;
    }}

    function expectedKForD(_d) {{
      const row = decodedScanRow(_d);
      let mask = 0;
      for (const keyId of pressedKeys) {{
        const key = KEY_BY_ID[keyId];
        if (key && key.row === row) mask |= key.bit;
      }}
      return mask & 0xF;
    }}

    function heldKeySummaryForD(_d) {{
      const row = decodedScanRow(_d);
      const heldKeys = KEYS.filter((key) => pressedKeys.has(key.id));
      const heldOnRow = heldKeys.filter((key) => key.row === row);
      return {
        held: heldKeys.map((key) => key.label).join(",") || "--",
        onRow: heldOnRow.map((key) => key.label).join(",") || "--",
        rowMask: heldOnRow.reduce((mask, key) => mask | key.bit, 0) & 0xF,
      };
    }}

    function noteTrace(message) {{
      return;
    }}

    function resetState() {{
      if (isRunning) return;
      state.Pp = 0;
      state.Pw = 0;
      state.SA = 0;
      state.SB = 0;
      state.A = 0;
      state.H = 0;
      state.C = 0;
      state.Br = 0;
      state.Bd = 0;
      state.M.fill(0);
      state.F1 = 0;
      state.F2 = 0;
      state.F3 = 0;
      state.S = 0;
      state.K = 0;
      state.D = 0;
      state.INB = 0;
      state.SI = 0;
      state.SO = 0;
      state.serbuf = 0;
      state.blk = 1;
      state.skip = false;
      state.wasLB = false;
      state.dsReg.fill(0);
      state.dsScan = 0;
      state.displayPos = 0;
      state.displayActive = -1;
      state.displaySelected = 0;
      state.visibleDigits.fill(0);
      state.visibleGlyphs.fill(" ");
      previousLogicalPC = null;
      stopRequested = false;
      selectedLogical = null;
      selectedRamAddr = null;
      lastWriteLogicalByAddr.fill(null);
      pressedKeys.clear();
      heldMouseKey = null;
      renderAll();
    }}

    function isTwoByteOpcode(op) {{
      return op === 0x13 || op === 0x33 || (op >= 0x60 && op <= 0x6F);
    }}

    function normaliseNibble(v) {{
      return v & 0xF;
    }}

    function readMem(addr) {{
      return state.M[addr & 0x7F] & 0xF;
    }}

    function writeMem(addr, value) {{
      const index = addr & 0x7F;
      state.M[index] = normaliseNibble(value);
      lastWriteLogicalByAddr[index] = currentExecutingLogical;
      if (ramWriteWatchpoints.has(index)) {{
        lastRamWriteWatchHit = index;
      }}
    }}

    function stepOne(syncInputs = true, renderUi = true) {{
      if (isRunning && syncInputs) return;
      if (syncInputs) syncUiToState();
      lastRamWriteWatchHit = null;
      selectedLogical = null;
      const beforeLogical = getLogicalPC();
      const beforeRaw = getRawPC();
      currentExecutingLogical = beforeLogical;
      const opcode = currentOpcode();
      const opName = OPCODES[opcode] || `OP ${hex(opcode, 2)}`;
      let nextpc = getNextPc(state.Pw);
      state.blk = 1;
      let notLB = true;
      let dspsExecuted = false;

      if (state.skip) {{
        state.skip = false;
        if (isTwoByteOpcode(opcode)) {{
          nextpc = getNextPc(nextpc);
        }}
        noteTrace(`${oct(beforeLogical, 4)} skipped ${opName}`);
      }} else {{
        let tmp = 0;
        switch (opcode) {{
          case 0x00: break;
          case 0x01:
            tmp = state.H;
            state.H = state.Br;
            state.Br = tmp & 0x7;
            break;
          case 0x02:
            state.A = state.A + state.C + readMem(getB());
            if (state.A >= 10) {{
              state.C = 1;
            }} else {{
              state.C = 0;
              state.skip = true;
            }}
            state.A &= 0xF;
            break;
          case 0x03:
            state.C = 1;
            break;
          case 0x04:
            if (state.F1 === 0) state.skip = true;
            break;
          case 0x05:
            if ((state.D & 0x4) === 0) state.skip = true;
            break;
          case 0x06: case 0x16: case 0x26: case 0x36:
            state.A = readMem(getB());
            state.Br ^= ((opcode >> 4) & 0x3);
            break;
          case 0x07: case 0x17: case 0x27: case 0x37:
            tmp = state.A;
            {{
              const addr = getB();
              state.A = readMem(addr);
              writeMem(addr, tmp);
            }}
            state.Br ^= ((opcode >> 4) & 0x3);
            break;
          case 0x08: case 0x18: case 0x28: case 0x38:
            tmp = state.A;
            {{
              const addr = getB();
              state.A = readMem(addr);
              writeMem(addr, tmp);
            }}
            state.Br ^= ((opcode >> 4) & 0x3);
            state.Bd = (state.Bd - 1) & 0xF;
            if (state.Bd === 15) state.skip = true;
            break;
          case 0x09: case 0x19: case 0x29: case 0x39:
            tmp = state.A;
            {{
              const addr = getB();
              state.A = readMem(addr);
              writeMem(addr, tmp);
            }}
            state.Br ^= ((opcode >> 4) & 0x3);
            state.Bd = (state.Bd + 1) & 0xF;
            if (state.Bd === 0 || state.Bd === 13) state.skip = true;
            break;
          case 0x0A: case 0x0B: case 0x0C: case 0x0D: case 0x0E: case 0x0F:
          case 0x1A: case 0x1B: case 0x1C: case 0x1D: case 0x1E: case 0x1F:
          case 0x2A: case 0x2B: case 0x2C: case 0x2D: case 0x2E: case 0x2F:
          case 0x3A: case 0x3B: case 0x3C: case 0x3D: case 0x3E: case 0x3F:
            if (!state.wasLB) {{
              state.Br = (opcode >> 4) & 0x3;
              tmp = opcode & 0x0F;
              if (tmp === 0x0A) state.Bd = lb05Value();
              else if (tmp >= 0x0B) state.Bd = tmp;
            }}
            state.wasLB = true;
            notLB = false;
            break;
          case 0x10:
            state.S = (((state.H & 0x7) << 4) | (state.A & 0xF) | dpBit()) & 0xFF;
            break;
          case 0x11:
            dspsExecuted = true;
            state.S = (((SEGMENT_DATA[state.A] ?? 0) & 0x7F) | dpBit()) & 0xFF;
            if (beforeLogical !== 0o215) {{
              latchVisibleDisplayDigit(SEGMENT_GLYPHS[state.A] || "?");
            }}
            break;
          case 0x12:
            state.A = normaliseNibble(state.A + readMem(getB()));
            break;
          case 0x13:
            {{
              const second = romByte(state.Pp, nextpc);
              setBFromParts((second >> 4) & 0x7, second & 0xF);
              nextpc = getNextPc(nextpc);
            }}
            break;
          case 0x14:
            if (state.F2 === 0) state.skip = true;
            break;
          case 0x15:
            {{
              const held = heldKeySummaryForD(state.D);
              const liveK = kinput(state.D);
              state.F2 = (liveK & 0x4) ? 0 : 1;
              if (liveK > 0) state.skip = true;
              noteTrace(
                `TKB D=${hex(state.D, 1)} row=${decodedScanRow(state.D)} ` +
                `held=${held.held} onRow=${held.onRow} rowMask=${hex(held.rowMask, 1)} ` +
                `live=${hex(liveK, 1)} ` +
                `skip=${state.skip ? 1 : 0}`
              );
            }}
            break;
          case 0x20:
            state.A = normaliseNibble(~state.A);
            break;
          case 0x21:
            tmp = state.A;
            state.A = state.serbuf & 0xF;
            state.serbuf = tmp & 0xF;
            break;
          case 0x22:
            tmp = (~state.A & 0xF) + state.C + readMem(getB());
            state.A = tmp & 0xF;
            if (tmp > 15) {{
              state.C = 1;
              state.skip = true;
            }} else {{
              state.C = 0;
            }}
            break;
          case 0x23:
            state.C = 0;
            break;
          case 0x24:
            if (state.F3 === 0) state.skip = true;
            break;
          case 0x25:
            tmp = state.D & 0xF;
            state.D = state.Bd & 0xF;
            state.blk = 0;
            clockDs8874FromD(tmp, state.D);
            state.displaySelected = displayDigitIndexFromD(state.Bd);
            break;
          case 0x30:
            state.A = 0;
            break;
          case 0x31:
            tmp = state.A;
            state.A = state.H & 0xF;
            state.H = tmp & 0xF;
            break;
          case 0x32:
            if (state.A === readMem(getB())) state.skip = true;
            break;
          case 0x33:
            {{
              const second = romByte(state.Pp, nextpc);
              if ((second & 0x20) === 0) state.F3 = (second & 0x10) ? 1 : 0;
              if ((second & 0x08) === 0) state.F2 = (second & 0x04) ? 1 : 0;
              if ((second & 0x02) === 0) state.F1 = (second & 0x01) ? 1 : 0;
              nextpc = getNextPc(nextpc);
            }}
            break;
          case 0x34:
            state.A = kinput(state.D) & 0xF;
            break;
          case 0x35:
            if (state.INB === 1) state.skip = true;
            break;
          case 0x40:
          case 0x41:
            if (opcode === 0x41) state.skip = true;
            tmp = state.SA;
            state.SA = state.SB;
            nextpc = tmp & 0x3F;
            state.Pp = (tmp >> 6) & 0x1F;
            break;
          case 0x42:
            writeMem(getB(), readMem(getB()) & 0x7);
            break;
          case 0x43:
            state.A = state.Bd & 0xF;
            break;
          case 0x44:
            if ((readMem(getB()) & 0x1) === 0) state.skip = true;
            break;
          case 0x45:
            if ((readMem(getB()) & 0x2) === 0) state.skip = true;
            break;
          case 0x46:
            if ((readMem(getB()) & 0x4) === 0) state.skip = true;
            break;
          case 0x47:
            if ((readMem(getB()) & 0x8) === 0) state.skip = true;
            break;
          case 0x48:
            writeMem(getB(), readMem(getB()) & 0xE);
            break;
          case 0x49:
            writeMem(getB(), readMem(getB()) | 0x1);
            break;
          case 0x4A:
            writeMem(getB(), readMem(getB()) | 0x8);
            break;
          case 0x4B:
            writeMem(getB(), readMem(getB()) & 0xB);
            break;
          case 0x4C:
            writeMem(getB(), readMem(getB()) & 0xD);
            break;
          case 0x4D:
            if (state.C === 0) state.skip = true;
            break;
          case 0x4E:
            writeMem(getB(), readMem(getB()) | 0x2);
            break;
          case 0x4F:
            writeMem(getB(), readMem(getB()) | 0x4);
            break;
          case 0x50:
            state.Bd = state.A & 0xF;
            break;
          case 0x51: case 0x52: case 0x53: case 0x54: case 0x55: case 0x56: case 0x57:
          case 0x58: case 0x59: case 0x5A: case 0x5B: case 0x5C: case 0x5D: case 0x5E: case 0x5F:
            tmp = opcode & 0x0F;
            if (state.A + tmp < 16 && tmp !== 6) state.skip = true;
            state.A = normaliseNibble(state.A + tmp);
            break;
          case 0x60: case 0x61: case 0x62: case 0x63: case 0x64: case 0x65: case 0x66: case 0x67:
          case 0x68: case 0x69: case 0x6A: case 0x6B: case 0x6C: case 0x6D: case 0x6E: case 0x6F:
            {{
              const second = romByte(state.Pp, nextpc);
              if ((second & 0x40) === 0) {{
                state.SB = state.SA;
                state.SA = ((state.Pp & 0x1F) << 6) | getNextPc(nextpc);
              }}
              state.Pp = (((15 - (opcode & 0x0F)) << 1) | ((second >> 7) & 1)) & 0x1F;
              nextpc = second & 0x3F;
            }}
            break;
          default:
            if (opcode >= 0x70 && opcode <= 0x7F) {{
              writeMem(getB(), opcode & 0x0F);
              state.Bd = (state.Bd + 1) & 0xF;
            }} else if (opcode >= 0x80 && opcode <= 0xBF) {{
              if ((state.Pp & 0x1E) !== 0x1E) {{
                state.SB = state.SA;
                state.SA = ((state.Pp & 0x1F) << 6) | nextpc;
              }}
              state.Pp = 0x1F;
              nextpc = opcode & 0x3F;
            }} else if (opcode >= 0xC0 && opcode <= 0xFF) {{
              nextpc = opcode & 0x3F;
              if (state.Pp === 0x1F) state.Pp = 0x1E;
            }}
            break;
        }}
        if (notLB) state.wasLB = false;
        const suffix = state.skip ? "  [skip armed]" : "";
        noteTrace(`${oct(beforeLogical, 4)} @${oct(beforeRaw, 4)}  ${opName}${suffix}`);
      }}

      state.Pw = nextpc & 0x3F;
      previousLogicalPC = beforeLogical;
      currentExecutingLogical = null;
      if (lastRamWriteWatchHit != null) {{
        noteTrace(`write breakpoint RAM[${hex(lastRamWriteWatchHit >> 4, 1)},${hex(lastRamWriteWatchHit & 0xF, 1)}]=${hex(readMem(lastRamWriteWatchHit), 1)}`);
      }}
      if (renderUi) {{
        renderAll();
        scrollToPc();
      }}
      return {{
        dspsExecuted,
        watchHit: lastRamWriteWatchHit != null,
      }};
    }}

    function renderRegisterGrid() {{
      const root = document.getElementById("register-grid");
      const fields = [
        ["logical_pc", oct(getLogicalPC(), 4)],
        ["raw_pc", oct(getRawPC(), 4)],
        ["SA", oct(state.SA, 4)],
        ["SB", oct(state.SB, 4)],
        ["A", hex(state.A, 1)],
        ["H", hex(state.H, 1)],
        ["B", hex(getB(), 2)],
        ["C", String(state.C)],
        ["D", hex(state.D, 1)],
        ["K", hex(kinput(state.D), 1)],
        ["serbuf", hex(state.serbuf, 1)],
        ["S", hex(state.S, 2)],
      ];
      if (!root.dataset.initialized) {{
        root.innerHTML = fields.map(([name, value]) => `
          <div class="field">
            <label for="reg-${{name}}">${{name}}</label>
            <input id="reg-${{name}}" data-reg="${{name}}" value="${{value}}">
          </div>
        `).join("");
        root.dataset.initialized = "1";
        return;
      }}
      for (const [name, value] of fields) {{
        const input = document.getElementById(`reg-${name}`);
        if (input && document.activeElement !== input) input.value = value;
      }}
    }}

    function renderFlagGrid() {{
      const root = document.getElementById("flag-grid");
      const flags = [
        ["skip", state.skip],
        ["wasLB", state.wasLB],
        ["F1", state.F1],
        ["F2", state.F2],
        ["F3", state.F3],
        ["INB", state.INB],
        ["SI", state.SI],
        ["SO", state.SO],
        ["blk", state.blk],
      ];
      if (!root.dataset.initialized) {{
        root.innerHTML = flags.map(([name, value]) => `
          <div class="field checkbox">
            <input type="checkbox" id="flag-${{name}}" data-flag="${{name}}" ${{value ? "checked" : ""}}>
            <label for="flag-${{name}}">${{name}}</label>
          </div>
        `).join("");
        root.dataset.initialized = "1";
        return;
      }}
      for (const [name, value] of flags) {{
        const input = document.getElementById(`flag-${name}`);
        if (input) input.checked = !!value;
      }}
    }}

    function renderStatus() {{
      const status = document.getElementById("status-strip");
      const b = getB();
      const row = b >> 4;
      const col = b & 0xF;
      const value = state.M[b] & 0xF;
      const selected = selectedRamAddr == null ? null : (selectedRamAddr & 0x7F);
      const selRow = selected == null ? null : (selected >> 4);
      const selCol = selected == null ? null : (selected & 0xF);
      const selWrite = selected == null ? null : lastWriteLogicalByAddr[selected];
      status.innerHTML = `
        <span>logical ${oct(getLogicalPC(), 4)}</span>
        <span>prev ${previousLogicalPC == null ? "----" : oct(previousLogicalPC, 4)}</span>
        <span>raw ${oct(getRawPC(), 4)}</span>
        <span>opcode ${oct(currentOpcode(), 3)}</span>
        <span>${OPCODES[currentOpcode()] || "?"}</span>
        <span>B=${hex(b, 2)}</span>
        <span>RAM[${hex(row, 1)},${hex(col, 1)}]=${hex(value, 1)}</span>
        <span>sel ${selected == null ? "--" : `RAM[${hex(selRow, 1)},${hex(selCol, 1)}]`}</span>
        <span>writer ${selWrite == null ? "----" : oct(selWrite, 4)}</span>
        <span class="pending-skip${state.skip ? "" : " idle"}">next instruction will be skipped</span>
      `;
      document.getElementById("code-meta").textContent =
        `PC ${oct(getLogicalPC(), 4)}  prev ${previousLogicalPC == null ? "----" : oct(previousLogicalPC, 4)}  raw ${oct(getRawPC(), 4)}  B ${hex(b, 2)}  RAM[${hex(row, 1)},${hex(col, 1)}]=${hex(value, 1)}`;
    }}

    function renderRam() {{
      const grid = document.getElementById("ram-grid");
      const current = getB();
      const currentRow = current >> 4;
      const currentCol = current & 0xF;
      if (!grid.dataset.initialized) {{
        let html = `<div></div>`;
        for (let col = 0; col < 16; col++) {{
          const headCls = col === currentCol ? "ram-head current" : "ram-head";
          html += `<div class="${{headCls}}" data-ram-head="${col}">${hex(col, 1)}</div>`;
        }}
        for (let row = 0; row < 8; row++) {{
          const rowCls = row === currentRow ? "ram-row-label current" : "ram-row-label";
          html += `<div class="${{rowCls}}" data-ram-row="${row}">${hex(row, 1)}x</div>`;
          for (let col = 0; col < 16; col++) {{
            const idx = row * 16 + col;
            const classes = ["ram-cell"];
            if (idx === current) classes.push("current");
            if (idx === selectedRamAddr) classes.push("selected");
            if (ramWriteWatchpoints.has(idx)) classes.push("watch");
            const writer = lastWriteLogicalByAddr[idx];
            const title = `${idx === current ? "B points here. " : ""}${idx === selectedRamAddr ? "Selected. " : ""}RAM[${hex(row, 1)},${hex(col, 1)}]${ramWriteWatchpoints.has(idx) ? " [write breakpoint]" : ""}${writer == null ? "" : ` [last write ${oct(writer, 4)}]`}`;
            html += `<input class="${{classes.join(" ")}}" title="${{title}}" data-ram="${{idx}}" inputmode="text" autocapitalize="characters" autocomplete="off" spellcheck="false" maxlength="1" value="${{hex(state.M[idx], 1)}}">`;
          }}
        }}
        grid.innerHTML = html;
        grid.dataset.initialized = "1";
        return;
      }}
      for (let col = 0; col < 16; col++) {{
        const head = grid.querySelector(`[data-ram-head="${col}"]`);
        if (head) head.className = col === currentCol ? "ram-head current" : "ram-head";
      }}
      for (let row = 0; row < 8; row++) {{
        const label = grid.querySelector(`[data-ram-row="${row}"]`);
        if (label) label.className = row === currentRow ? "ram-row-label current" : "ram-row-label";
        for (let col = 0; col < 16; col++) {{
          const idx = row * 16 + col;
          const input = grid.querySelector(`[data-ram="${idx}"]`);
          if (!input) continue;
          const classes = ["ram-cell"];
          if (idx === current) classes.push("current");
          if (idx === selectedRamAddr) classes.push("selected");
          if (ramWriteWatchpoints.has(idx)) classes.push("watch");
          input.className = classes.join(" ");
          const writer = lastWriteLogicalByAddr[idx];
          input.title = `${idx === current ? "B points here. " : ""}${idx === selectedRamAddr ? "Selected. " : ""}RAM[${hex(row, 1)},${hex(col, 1)}]${ramWriteWatchpoints.has(idx) ? " [write breakpoint]" : ""}${writer == null ? "" : ` [last write ${oct(writer, 4)}]`}`;
          if (document.activeElement !== input) input.value = hex(state.M[idx], 1);
        }}
      }}
    }}

    function renderDisasm() {{
      const root = document.getElementById("disasm");
      const currentLogical = getLogicalPC();
      const previousLogical = previousLogicalPC;
      if (root.dataset.initialized) {{
        for (const line of root.querySelectorAll(".line.instr")) {{
          const logical = Number(line.dataset.logical);
          line.classList.toggle("current", logical === currentLogical);
          line.classList.toggle("previous", logical === previousLogical && logical !== currentLogical);
          line.classList.toggle("selected", logical === selectedLogical);
          line.classList.toggle("breakpoint", breakpoints.has(logical));
        }}
        return;
      }}
      const escapeHtml = (text) =>
        (text || "")
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;");
      root.innerHTML = DISASM_LINES.map((line, index) => {{
        const classes = ["line", line.type];
        if (line.type === "instr" && line.logical === currentLogical) classes.push("current");
        if (line.type === "instr" && line.logical === previousLogical && line.logical !== currentLogical) classes.push("previous");
        if (line.type === "instr" && line.logical === selectedLogical) classes.push("selected");
        if (line.type === "instr" && breakpoints.has(line.logical)) classes.push("breakpoint");
        const logicalAttr = line.type === "instr" ? ` data-logical="${{line.logical}}"` : "";
        if (line.type !== "instr") {{
          const safe = escapeHtml(line.text || "");
          return `<div class="${{classes.join(" ")}}" data-index="${{index}}"${{logicalAttr}}>${{safe}}</div>`;
        }}
        const body = line.body || "";
        const bodyMatch = body.match(/^(\\S+)(\\s*)(.*)$/);
        let bodyHtml = escapeHtml(body);
        if (bodyMatch) {{
          const opToken = bodyMatch[1];
          const gap = bodyMatch[2] || "";
          const tail = bodyMatch[3] || "";
          const summary = ISA_SUMMARIES[opToken] || ISA_SUMMARIES[OPCODES[line.opcode]] || "";
          const titleAttr = summary ? ` title="${{escapeHtml(summary)}}"` : "";
          bodyHtml =
            `<span class="op-tip"${{titleAttr}}>${{escapeHtml(opToken)}}</span>` +
            `${{escapeHtml(gap)}}${{escapeHtml(tail)}}`;
        }}
        const prefix =
          `${{oct(line.logical, 4)}} @${{oct(line.physical, 4)}}  ${{oct(line.opcode, 3)}}  `;
        return `<div class="${{classes.join(" ")}}" data-index="${{index}}"${{logicalAttr}}>${{prefix}}${{bodyHtml}}</div>`;
      }}).join("");
      root.dataset.initialized = "1";
    }}

    function renderTrace() {{
      return;
    }}

    function renderHardware() {{
      const root = document.getElementById("hardware-wrap");
      if (!root) return;
      const active = activeDisplayDigit();
      const selected = state.displaySelected % 9;
      const segNames = ["a", "b", "c", "d", "e", "f", "g"];
      const digits = [];
      for (let i = 0; i < 9; i++) {{
        const seg = state.visibleDigits[i] & 0xFF;
        const glyph = state.visibleGlyphs[i] || " ";
        const lit = new Set(GLYPH_SEGMENTS[glyph] || GLYPH_SEGMENTS["?"]);
        const segHtml = segNames.map((name) => `<div class="hw-seg ${name}${lit.has(name) ? " on" : ""}"></div>`).join("");
        digits.push(`
          <div class="hardware-digit${active === i ? " active" : ""}${selected === i ? " selected" : ""}" title="digit ${i} seg=${hex(seg, 2)} reg=${state.dsReg[i] & 1}">
            <div class="hw-sevenseg">
              ${segHtml}
              <div class="hw-dot${seg & 0x80 ? " on" : ""}"></div>
            </div>
          </div>
        `);
      }}
      const scanRow = decodedScanRow(state.D);
      const keys = KEYS.map((key) => {{
        const p = KEY_HOTSPOTS[key.id];
        if (!p) return "";
        const left = 17.06 + p.col * 22.23 - 15.62 / 2;
        const top = 52.15 + p.row * 10.18 - 5.94 / 2;
        const activeCls = pressedKeys.has(key.id) ? " active" : "";
        const scannedCls = key.row === scanRow ? " scanned" : "";
        return `<button class="hw-key${activeCls}${scannedCls}" type="button" data-key="${key.id}" style="left:${left}%;top:${top}%;width:15.62%;height:5.94%;" title="${key.label}"></button>`;
      }}).join("");
      const powerLeft = 17.06 + 3 * 22.23 - 15.62 / 2;
      const powerTop = 52.15 + 0 * 10.18 - 5.94 / 2;
      const power = `<button class="hw-key" type="button" data-action="power" style="left:${powerLeft}%;top:${powerTop}%;width:15.62%;height:5.94%;" title="ON/OFF (mapped to Reset)"></button>`;
      root.innerHTML = `
        <div class="hardware-display">${digits.join("")}</div>
        ${keys}
        ${power}
      `;
    }}

    function renderDisplay() {{
      const root = document.getElementById("display-wrap");
      if (!root) return;
      const active = activeDisplayDigit();
      const selected = state.displaySelected % 9;
      const digits = [];
      const segNames = ["a", "b", "c", "d", "e", "f", "g"];
      for (let i = 0; i < 9; i++) {{
        const seg = state.visibleDigits[i] & 0xFF;
        const glyph = state.visibleGlyphs[i] || " ";
        const lit = new Set(GLYPH_SEGMENTS[glyph] || GLYPH_SEGMENTS["?"]);
        const segHtml = segNames.map((name) => `<div class="seg ${name}${lit.has(name) ? " on" : ""}"></div>`).join("");
        digits.push(`
          <div class="calc-digit${active === i ? " active" : ""}${selected === i ? " selected" : ""}" title="digit ${i} seg=${hex(seg, 2)} reg=${state.dsReg[i] & 1}">
            <div class="sevenseg">
              ${segHtml}
              <div class="calc-dot${seg & 0x80 ? " on" : ""}"></div>
            </div>
          </div>
        `);
      }}
      root.innerHTML = `
        <div class="display-status">
          <span>latched digit=${active >= 0 ? active : "--"}</span>
          <span>selected digit=${selected}</span>
          <span>scan=${state.dsScan}</span>
          <span>DS reg=${state.dsReg.map((bit) => bit ? "1" : "0").join("")}</span>
          <span>S=${hex(state.S, 2)}</span>
        </div>
        <div class="calc-display">${digits.join("")}</div>
      `;
    }}

    function renderKeypad() {{
      const root = document.getElementById("keypad");
      if (!root) return;
      root.innerHTML = "";
    }}

    function renderAll() {{
      renderRegisterGrid();
      renderHardware();
      renderDisplay();
      renderKeypad();
      renderStatus();
      renderRam();
      renderDisasm();
      renderTrace();
      updateControls();
    }}

    function renderDisplayFast() {{
      renderHardware();
      renderStatus();
    }}

    function updateControls() {{
      for (const id of ["step-btn", "stepover-btn", "step10-btn", "continue-btn", "reset-btn", "apply-btn"]) {{
        const el = document.getElementById(id);
        if (el) el.disabled = isRunning;
      }}
      const gotoWriter = document.getElementById("goto-writer-btn");
      if (gotoWriter) gotoWriter.disabled = isRunning || selectedRamAddr == null || lastWriteLogicalByAddr[selectedRamAddr & 0x7F] == null;
    }}

    function parseNumber(text, fallbackBase = 10) {{
      const cleaned = text.trim();
      if (cleaned === "") return 0;
      if (/^[-+]?0x[0-9a-f]+$/i.test(cleaned)) return parseInt(cleaned, 16);
      if (/^[-+]?0o[0-7]+$/i.test(cleaned)) {{
        const sign = cleaned[0] === "-" ? -1 : 1;
        const digits = cleaned.replace(/^[-+]?0o/i, "");
        return sign * parseInt(digits, 8);
      }}
      if (/[a-f]/i.test(cleaned)) return parseInt(cleaned, 16);
      return parseInt(cleaned, fallbackBase);
    }}

    function parseHex(text) {{
      return parseNumber(text, 16);
    }}

    function parseOctal(text) {{
      return parseNumber(text, 8);
    }}

    function syncUiToState() {{
      const regInputs = document.querySelectorAll("[data-reg]");
      for (const input of regInputs) {{
        const name = input.dataset.reg;
        const value = input.value;
        switch (name) {{
          case "logical_pc":
            setPCFromLogical(parseOctal(value) & 0x7FF);
            break;
          case "page":
            state.Pp = parseOctal(value) & 0x1F;
            break;
          case "word":
            state.Pw = parseOctal(value) & 0x3F;
            break;
          case "raw_pc":
            {{
              const raw = parseOctal(value) & 0x7FF;
              state.Pp = (raw >> 6) & 0x1F;
              state.Pw = raw & 0x3F;
            }}
            break;
          case "SA":
          case "SB":
            state[name] = parseOctal(value) & 0x7FF;
            break;
          case "A":
          case "H":
          case "Br":
          case "Bd":
          case "D":
          case "serbuf":
            state[name] = parseHex(value) & 0xF;
            break;
          case "B":
            {{
              const b = parseHex(value) & 0x7F;
              state.Br = (b >> 4) & 0x7;
              state.Bd = b & 0xF;
            }}
            break;
          case "C":
            state.C = Number(value) ? 1 : 0;
            break;
          case "S":
            state.S = parseHex(value) & 0xFF;
            break;
        }}
      }}

      for (const input of document.querySelectorAll("[data-ram]")) {{
        const idx = Number(input.dataset.ram);
        state.M[idx] = parseHex(input.value) & 0xF;
      }}

      for (const input of document.querySelectorAll("[data-flag]")) {{
        const name = input.dataset.flag;
        state[name] = input.checked ? 1 : 0;
      }}
    }}

    function applyEdits() {{
      syncUiToState();
      renderAll();
      scrollToPc();
    }}

    function scrollToPc() {{
      const idx = LOGICAL_TO_LINE[String(getLogicalPC())];
      if (idx == null) return;
      const el = document.querySelector(`.line[data-index="${{idx}}"]`);
      if (el) el.scrollIntoView({{block: "center"}});
    }}

    function focusRamCell(index) {{
      const wrapped = ((index % 128) + 128) % 128;
      const el = document.querySelector(`[data-ram="${wrapped}"]`);
      if (!el) return;
      el.focus();
      el.select();
    }}

    function gotoWriterForSelectedRam() {{
      if (selectedRamAddr == null) return;
      const logical = lastWriteLogicalByAddr[selectedRamAddr & 0x7F];
      if (logical == null) return;
      setPCFromLogical(logical);
      renderAll();
      scrollToPc();
    }}

    function stopForRamWriteWatchpoint() {{
      if (lastRamWriteWatchHit == null) return false;
      renderAll();
      scrollToPc();
      return true;
    }}

    function animationEnabled() {{
      return document.getElementById("animate-toggle").checked;
    }}

    function animationDelayMs() {{
      const raw = Number(document.getElementById("animate-delay").value);
      if (!Number.isFinite(raw)) return 80;
      return Math.max(0, Math.min(2000, raw));
    }}

    function breakpointsEnabled() {{
      const el = document.getElementById("breakpoints-toggle");
      return !el || el.checked;
    }}

    function sleep(ms) {{
      return new Promise((resolve) => setTimeout(resolve, ms));
    }}

    function nextPaint() {{
      return new Promise((resolve) => requestAnimationFrame(() => resolve()));
    }}

    function renderStopState() {{
      renderAll();
      scrollToPc();
    }}

    function shouldStopAtBreakpoint(i) {{
      return i > 0 && breakpointsEnabled() && breakpoints.has(getLogicalPC());
    }}

    function returnWouldExecuteNow() {{
      const opcode = currentOpcode();
      return !state.skip && (opcode === 0x40 || opcode === 0x41);
    }}

    async function maybeAnimateStepResult(result, animated, i) {{
      if (stopForRamWriteWatchpoint()) return true;
      if (animated) {{
        await nextPaint();
        const delay = animationDelayMs();
        if (delay > 0) await sleep(delay);
      }} else {{
        if (result && result.dspsExecuted) {{
          renderDisplayFast();
          await nextPaint();
        }} else if ((i & 0x3F) === 0x3F) {{
          await sleep(0);
        }}
      }}
      return false;
    }}

    function stepMany(count) {{
      syncUiToState();
      for (let i = 0; i < count; i++) {{
        if (shouldStopAtBreakpoint(i)) {{
          noteTrace(`stopped at breakpoint ${oct(getLogicalPC(), 4)}`);
          renderStopState();
          return;
        }}
        const result = stepOne(false, false);
        if (lastRamWriteWatchHit != null) {{
          renderStopState();
          return;
        }}
        if (result && result.dspsExecuted) renderDisplayFast();
      }}
    }}

    async function runAnimatedSteps(count) {{
      if (isRunning) return;
      syncUiToState();
      stopRequested = false;
      isRunning = true;
      updateControls();
      try {{
        for (let i = 0; i < count; i++) {{
          if (stopRequested) {{
            noteTrace("run stopped by Escape");
            renderStopState();
            return;
          }}
          if (shouldStopAtBreakpoint(i)) {{
            noteTrace(`stopped at breakpoint ${oct(getLogicalPC(), 4)}`);
            renderStopState();
            return;
          }}
          const result = stepOne(false, true);
          if (await maybeAnimateStepResult(result, true, i)) return;
        }}
      }} finally {{
        isRunning = false;
        stopRequested = false;
        updateControls();
      }}
    }}

    async function continueExecution(maxSteps = 1000000) {{
      if (isRunning) return;
      syncUiToState();
      stopRequested = false;
      isRunning = true;
      updateControls();
      try {{
        for (let i = 0; i < maxSteps; i++) {{
          const animated = animationEnabled();
          if (stopRequested) {{
            noteTrace("continue stopped by Escape");
            renderStopState();
            return;
          }}
          if (shouldStopAtBreakpoint(i)) {{
            noteTrace(`stopped at breakpoint ${oct(getLogicalPC(), 4)}`);
            renderStopState();
            return;
          }}
          const result = stepOne(false, animated);
          if (await maybeAnimateStepResult(result, animated, i)) return;
        }}
        noteTrace(`continue stopped after ${maxSteps} steps`);
        renderTrace();
      }} finally {{
        isRunning = false;
        stopRequested = false;
        updateControls();
      }}
    }}

    function stepUntilReturn(maxSteps = 10000) {{
      syncUiToState();
      for (let i = 0; i < maxSteps; i++) {{
        if (shouldStopAtBreakpoint(i)) {{
          noteTrace(`stopped at breakpoint ${oct(getLogicalPC(), 4)}`);
          renderStopState();
          return;
        }}
        if (returnWouldExecuteNow()) {{
          renderStopState();
          return;
        }}
        const result = stepOne(false, false);
        if (lastRamWriteWatchHit != null) {{
          renderStopState();
          return;
        }}
        if (result && result.dspsExecuted) renderDisplayFast();
      }}
      noteTrace(`step-until-return stopped after ${maxSteps} steps without executing RET/RETS`);
      renderTrace();
    }}

    async function stepUntilReturnAnimated(maxSteps = 10000) {{
      if (isRunning) return;
      syncUiToState();
      stopRequested = false;
      isRunning = true;
      updateControls();
      try {{
        for (let i = 0; i < maxSteps; i++) {{
          if (stopRequested) {{
            noteTrace("run-to-return stopped by Escape");
            renderStopState();
            return;
          }}
          if (shouldStopAtBreakpoint(i)) {{
            noteTrace(`stopped at breakpoint ${oct(getLogicalPC(), 4)}`);
            renderStopState();
            return;
          }}
          if (returnWouldExecuteNow()) {{
            renderStopState();
            return;
          }}
          const result = stepOne(false, true);
          if (await maybeAnimateStepResult(result, true, i)) return;
        }}
        noteTrace(`step-until-return stopped after ${maxSteps} steps without executing RET/RETS`);
        renderTrace();
      }} finally {{
        isRunning = false;
        stopRequested = false;
        updateControls();
      }}
    }}

    document.getElementById("step-btn").addEventListener("click", () => stepOne());
    document.getElementById("stepover-btn").addEventListener("click", () => {{
      if (animationEnabled()) stepUntilReturnAnimated();
      else stepUntilReturn();
    }});
    document.getElementById("step10-btn").addEventListener("click", () => {{
      if (animationEnabled()) runAnimatedSteps(10);
      else stepMany(10);
    }});
    document.getElementById("continue-btn").addEventListener("click", () => continueExecution());
    document.getElementById("reset-btn").addEventListener("click", () => resetState());
    document.getElementById("apply-btn").addEventListener("click", () => applyEdits());
    document.getElementById("goto-pc-btn").addEventListener("click", () => scrollToPc());
    document.getElementById("goto-writer-btn").addEventListener("click", () => gotoWriterForSelectedRam());

    document.getElementById("disasm").addEventListener("click", (event) => {{
      const line = event.target.closest(".line.instr");
      if (!line) return;
      if (event.metaKey) {{
        const logical = Number(line.dataset.logical);
        if (breakpoints.has(logical)) breakpoints.delete(logical);
        else breakpoints.add(logical);
        renderDisasm();
        return;
      }}
      selectedLogical = Number(line.dataset.logical);
      setPCFromLogical(selectedLogical);
      renderAll();
      scrollToPc();
    }});

    document.getElementById("ram-grid").addEventListener("input", (event) => {{
      const input = event.target.closest("[data-ram]");
      if (!input) return;
      const idx = Number(input.dataset.ram);
      selectedRamAddr = idx;
      const raw = (input.value || "").toUpperCase().replace(/[^0-9A-F]/g, "");
      input.value = raw.slice(-1);
      state.M[idx] = parseHex(input.value || "0") & 0xF;
      if (input.value.length === 1) {{
        focusRamCell(idx + 1);
      }}
      renderStatus();
      renderRam();
      updateControls();
    }});

    document.getElementById("ram-grid").addEventListener("click", (event) => {{
      const input = event.target.closest("[data-ram]");
      if (!input || event.metaKey) return;
      selectedRamAddr = Number(input.dataset.ram);
      renderStatus();
      renderRam();
      updateControls();
    }});

    document.getElementById("ram-grid").addEventListener("pointerdown", (event) => {{
      const input = event.target.closest("[data-ram]");
      if (!input) return;
      const idx = Number(input.dataset.ram);
      if (!event.metaKey) return;
      event.preventDefault();
      if (ramWriteWatchpoints.has(idx)) ramWriteWatchpoints.delete(idx);
      else ramWriteWatchpoints.add(idx);
      renderRam();
      renderStatus();
      updateControls();
    }});

    document.getElementById("ram-grid").addEventListener("keydown", (event) => {{
      const input = event.target.closest("[data-ram]");
      if (!input) return;
      const idx = Number(input.dataset.ram);
      if (event.key === "ArrowRight") {{
        event.preventDefault();
        focusRamCell(idx + 1);
      }} else if (event.key === "ArrowLeft") {{
        event.preventDefault();
        focusRamCell(idx - 1);
      }} else if (event.key === "ArrowDown") {{
        event.preventDefault();
        focusRamCell(idx + 16);
      }} else if (event.key === "ArrowUp") {{
        event.preventDefault();
        focusRamCell(idx - 16);
      }}
    }});

    const handleKeyMouseDown = (event) => {{
      const actionEl = event.target.closest("[data-action]");
      if (actionEl && actionEl.dataset.action === "power") {{
        event.preventDefault();
        resetState();
        return;
      }}
      const keyEl = event.target.closest("[data-key]");
      if (!keyEl) return;
      event.preventDefault();
      const keyId = keyEl.dataset.key;
      pressedKeys.add(keyId);
      heldMouseKey = keyId;
      renderKeypad();
      renderHardware();
    }};

    const handleKeyMouseUp = () => {{
      if (!heldMouseKey) return;
      pressedKeys.delete(heldMouseKey);
      heldMouseKey = null;
      renderKeypad();
      renderHardware();
    }};

    document.getElementById("keypad").addEventListener("mousedown", handleKeyMouseDown);
    document.getElementById("hardware-wrap").addEventListener("mousedown", handleKeyMouseDown);
    document.addEventListener("mouseup", handleKeyMouseUp);

    document.getElementById("force-k").addEventListener("input", (event) => {{
      const input = event.target;
      const raw = (input.value || "").toUpperCase().replace(/[^0-9A-F]/g, "");
      input.value = raw.slice(-1);
      renderKeypad();
    }});

    document.getElementById("lb05-value").addEventListener("input", (event) => {{
      const input = event.target;
      const raw = (input.value || "").toUpperCase().replace(/[^0-9A-F]/g, "");
      input.value = raw.slice(-1);
      renderStatus();
      renderTrace();
    }});

    document.addEventListener("keydown", (event) => {{
      const target = event.target;
      const tag = target && target.tagName ? target.tagName.toUpperCase() : "";
      if (event.key === "Escape" && isRunning) {{
        event.preventDefault();
        stopRequested = true;
        return;
      }}
      if (tag === "INPUT" || tag === "TEXTAREA" || (target && target.isContentEditable)) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (event.key === "s" || event.key === "S") {{
        event.preventDefault();
        stepOne();
      }} else if (event.key === "r" || event.key === "R") {{
        event.preventDefault();
        if (animationEnabled()) stepUntilReturnAnimated();
        else stepUntilReturn();
      }} else if (event.key === "c" || event.key === "C") {{
        event.preventDefault();
        continueExecution();
      }}
    }});

    resetState();
  </script>
</body>
</html>
"""
    return (
        html_template
        .replace("{{", "{")
        .replace("}}", "}")
        .replace("__ROM_JSON__", rom_json)
        .replace("__LFSR_JSON__", lfsr_json)
        .replace("__OPCODES_JSON__", opcodes_json)
        .replace("__ISA_SUMMARIES_JSON__", isa_summaries_json)
        .replace("__DISASM_JSON__", disasm_json)
        .replace("__LOGICAL_MAP_JSON__", logical_map_json)
    )


def main() -> None:
    root = Path(__file__).resolve().parent
    rom_path = root / "sinclaircambridgeprogrammable.bin"
    disasm_path = root / "analysis" / "sinclaircambridgeprogrammable.dan.asm"
    output_path = root / "analysis" / "mm5799_debugger.html"

    rom = load_rom(rom_path)
    disasm_lines, logical_to_line = parse_disassembly(disasm_path)
    output_path.write_text(build_html(rom, disasm_lines, logical_to_line))
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
