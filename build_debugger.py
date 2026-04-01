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
      background: linear-gradient(180deg, #f7f3eb 0%, #efe7da 100%);
      color: var(--ink);
      font-family: var(--font-ui);
    }}
    .app {{
      display: grid;
      grid-template-columns: 420px 1fr;
      min-height: 100vh;
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
    }}
    .status-strip span {{
      background: #f5eee1;
      border: 1px solid var(--line);
      padding: 4px 8px;
      border-radius: 999px;
    }}
    .ram-wrap {{
      padding: 0 14px 14px;
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
    }}
    .right {{
      display: grid;
      grid-template-rows: auto 1fr auto;
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
      padding: 0 14px;
      border-left: 4px solid transparent;
      cursor: default;
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
    .line.selected {{
      background: var(--sel-hi);
      border-left-color: #4377b8;
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
    .trace {{
      border-top: 1px solid var(--line);
      padding: 10px 14px 14px;
      background: #fbf6ed;
    }}
    .trace h2 {{
      margin: 0 0 8px;
      font-size: 14px;
    }}
    .trace-list {{
      max-height: 150px;
      overflow: auto;
      font-family: var(--font-code);
      font-size: 12px;
      line-height: 1.45;
      color: var(--muted);
      white-space: pre-wrap;
    }}
    @media (max-width: 1100px) {{
      .app {{
        grid-template-columns: 1fr;
      }}
      .left {{
        order: 2;
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
            Self-contained debugger for the Sinclair Cambridge Programmable ROM.
            Code view is driven by the current best annotated listing in
            <code>analysis/sinclaircambridgeprogrammable.dan.txt</code>.
          </div>
          <div class="toolbar">
            <button class="primary" id="step-btn">Step</button>
            <button id="step10-btn">Step 10</button>
            <button id="run100-btn">Run 100</button>
            <button id="reset-btn">Reset</button>
            <button id="apply-btn">Apply Edits</button>
            <button id="goto-pc-btn">Scroll To PC</button>
          </div>
          <div class="status-strip" id="status-strip"></div>
        </div>
      </div>

      <div class="panel">
        <div class="section">
          <div class="grid register-grid" id="register-grid"></div>
          <div class="small-note">
            Edit any register field, then use <strong>Apply Edits</strong>.
            Click any instruction line on the right to move the PC there.
            RAM is shown below as hex digits.
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="section">
          <div class="grid register-grid" id="flag-grid"></div>
        </div>
      </div>

      <div class="panel">
        <div class="section">
          <strong>RAM (128 nibbles)</strong>
          <div class="small-note">
            Displayed as 8 rows × 16 columns to match the emulator's 128-nibble working RAM.
            The current <code>B = (Br &lt;&lt; 4) | Bd</code> cell is highlighted.
          </div>
        </div>
        <div class="ram-wrap">
          <div class="ram-grid" id="ram-grid"></div>
        </div>
      </div>
    </div>

    <div class="panel right">
      <div class="code-header">
        <div class="title">Annotated Disassembly</div>
        <div class="meta" id="code-meta"></div>
      </div>
      <div class="disasm" id="disasm"></div>
      <div class="trace">
        <h2>Recent Execution</h2>
        <div class="trace-list" id="trace-list"></div>
      </div>
    </div>
  </div>

  <script>
    const ROM = __ROM_JSON__;
    const LFSR_SEQUENCE = __LFSR_JSON__;
    const OPCODES = __OPCODES_JSON__;
    const DISASM_LINES = __DISASM_JSON__;
    const LOGICAL_TO_LINE = __LOGICAL_MAP_JSON__;
    const LFSR_INDEX_BY_WORD = Object.fromEntries(LFSR_SEQUENCE.map((word, index) => [word, index]));
    const SEGMENT_DATA = [0x7f, 0x40, 0x79, 0x24, 0x30, 0x19, 0x12, 0x02, 0x78, 0x10, 0x06, 0x23, 0x06, 0x66, 0x6f, 0x01, 0x02, 0x08, 0x04];

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
    }};

    const trace = [];
    let selectedLogical = null;

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

    function getLogicalPC() {{
      return ((state.Pp & 0x1F) << 6) | LFSR_INDEX_BY_WORD[state.Pw & 0x3F];
    }}

    function setPCFromLogical(logical) {{
      const page = (logical >> 6) & 0x1F;
      const index = logical & 0x3F;
      state.Pp = page;
      state.Pw = LFSR_SEQUENCE[index];
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
      return 0;
    }}

    function noteTrace(message) {{
      trace.unshift(message);
      if (trace.length > 40) {{
        trace.length = 40;
      }}
    }}

    function resetState() {{
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
      trace.length = 0;
      selectedLogical = null;
      renderAll();
    }}

    function isTwoByteOpcode(op) {{
      return op === 0x13 || op === 0x33 || (op >= 0x60 && op <= 0x6F);
    }}

    function normaliseNibble(v) {{
      return v & 0xF;
    }}

    function stepOne() {{
      const beforeLogical = getLogicalPC();
      const beforeRaw = getRawPC();
      const opcode = currentOpcode();
      const opName = OPCODES[opcode] || `OP ${hex(opcode, 2)}`;
      let nextpc = getNextPc(state.Pw);
      state.blk = 1;
      let notLB = true;

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
            state.A = state.A + state.C + state.M[getB()];
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
            state.A = state.M[getB()];
            state.Br ^= ((opcode >> 4) & 0x3);
            break;
          case 0x07: case 0x17: case 0x27: case 0x37:
            tmp = state.A;
            state.A = state.M[getB()];
            state.M[getB()] = normaliseNibble(tmp);
            state.Br ^= ((opcode >> 4) & 0x3);
            break;
          case 0x08: case 0x18: case 0x28: case 0x38:
            tmp = state.A;
            state.A = state.M[getB()];
            state.M[getB()] = normaliseNibble(tmp);
            state.Br ^= ((opcode >> 4) & 0x3);
            state.Bd = (state.Bd - 1) & 0xF;
            if (state.Bd === 15) state.skip = true;
            break;
          case 0x09: case 0x19: case 0x29: case 0x39:
            tmp = state.A;
            state.A = state.M[getB()];
            state.M[getB()] = normaliseNibble(tmp);
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
              if (tmp === 0x0A) state.Bd = 5;
              else if (tmp >= 0x0B) state.Bd = tmp;
            }}
            state.wasLB = true;
            notLB = false;
            break;
          case 0x10:
            state.S = ((state.H & 0x7) << 4) | (state.A & 0xF);
            break;
          case 0x11:
            state.S = SEGMENT_DATA[state.A] ?? 0;
            break;
          case 0x12:
            state.A = normaliseNibble(state.A + state.M[getB()]);
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
            state.K = kinput(state.D);
            if (state.K > 0) state.skip = true;
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
            tmp = (~state.A & 0xF) + state.C + state.M[getB()];
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
            state.D = state.Bd & 0xF;
            state.blk = 0;
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
            if (state.A === state.M[getB()]) state.skip = true;
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
            state.A = state.K & 0xF;
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
            state.M[getB()] &= 0x7;
            break;
          case 0x43:
            state.A = state.Bd & 0xF;
            break;
          case 0x44:
            if ((state.M[getB()] & 0x1) === 0) state.skip = true;
            break;
          case 0x45:
            if ((state.M[getB()] & 0x2) === 0) state.skip = true;
            break;
          case 0x46:
            if ((state.M[getB()] & 0x4) === 0) state.skip = true;
            break;
          case 0x47:
            if ((state.M[getB()] & 0x8) === 0) state.skip = true;
            break;
          case 0x48:
            state.M[getB()] &= 0xE;
            break;
          case 0x49:
            state.M[getB()] |= 0x1;
            break;
          case 0x4A:
            state.M[getB()] |= 0x8;
            break;
          case 0x4B:
            state.M[getB()] &= 0xB;
            break;
          case 0x4C:
            state.M[getB()] &= 0xD;
            break;
          case 0x4D:
            if (state.C === 0) state.skip = true;
            break;
          case 0x4E:
            state.M[getB()] |= 0x2;
            break;
          case 0x4F:
            state.M[getB()] |= 0x4;
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
              state.M[getB()] = opcode & 0x0F;
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
        noteTrace(`${oct(beforeLogical, 4)} @${oct(beforeRaw, 4)}  ${opName}`);
      }}

      state.Pw = nextpc & 0x3F;
      renderAll();
    }}

    function renderRegisterGrid() {{
      const root = document.getElementById("register-grid");
      const fields = [
        ["logical_pc", oct(getLogicalPC(), 4)],
        ["page", oct(state.Pp, 2)],
        ["word", oct(state.Pw, 2)],
        ["raw_pc", oct(getRawPC(), 4)],
        ["SA", oct(state.SA, 4)],
        ["SB", oct(state.SB, 4)],
        ["A", hex(state.A, 1)],
        ["H", hex(state.H, 1)],
        ["Br", hex(state.Br, 1)],
        ["Bd", hex(state.Bd, 1)],
        ["B", hex(getB(), 2)],
        ["C", String(state.C)],
        ["D", hex(state.D, 1)],
        ["K", hex(state.K, 1)],
        ["serbuf", hex(state.serbuf, 1)],
        ["S", hex(state.S, 2)],
      ];
      root.innerHTML = fields.map(([name, value]) => `
        <div class="field">
          <label for="reg-${{name}}">${{name}}</label>
          <input id="reg-${{name}}" data-reg="${{name}}" value="${{value}}">
        </div>
      `).join("");
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
      root.innerHTML = flags.map(([name, value]) => `
        <div class="field checkbox">
          <input type="checkbox" id="flag-${{name}}" data-flag="${{name}}" ${{value ? "checked" : ""}}>
          <label for="flag-${{name}}">${{name}}</label>
        </div>
      `).join("");
    }}

    function renderStatus() {{
      const status = document.getElementById("status-strip");
      status.innerHTML = `
        <span>logical ${oct(getLogicalPC(), 4)}</span>
        <span>raw ${oct(getRawPC(), 4)}</span>
        <span>opcode ${oct(currentOpcode(), 3)}</span>
        <span>${OPCODES[currentOpcode()] || "?"}</span>
        <span>B=${hex(getB(), 2)}</span>
      `;
      document.getElementById("code-meta").textContent =
        `PC ${oct(getLogicalPC(), 4)}  raw ${oct(getRawPC(), 4)}  B ${hex(getB(), 2)}`;
    }}

    function renderRam() {{
      const grid = document.getElementById("ram-grid");
      const current = getB();
      let html = `<div></div>`;
      for (let col = 0; col < 16; col++) {{
        html += `<div class="ram-head">${hex(col, 1)}</div>`;
      }}
      for (let row = 0; row < 8; row++) {{
        html += `<div class="ram-row-label">${hex(row, 1)}x</div>`;
        for (let col = 0; col < 16; col++) {{
          const idx = row * 16 + col;
          const cls = idx === current ? "ram-cell current" : "ram-cell";
          html += `<input class="${{cls}}" data-ram="${{idx}}" value="${{hex(state.M[idx], 1)}}">`;
        }}
      }}
      grid.innerHTML = html;
    }}

    function renderDisasm() {{
      const root = document.getElementById("disasm");
      const currentLogical = getLogicalPC();
      root.innerHTML = DISASM_LINES.map((line, index) => {{
        const classes = ["line", line.type];
        if (line.type === "instr" && line.logical === currentLogical) classes.push("current");
        if (line.type === "instr" && line.logical === selectedLogical) classes.push("selected");
        const logicalAttr = line.type === "instr" ? ` data-logical="${{line.logical}}"` : "";
        const safe = (line.text || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        return `<div class="${{classes.join(" ")}}" data-index="${{index}}"${{logicalAttr}}>${{safe}}</div>`;
      }}).join("");
    }}

    function renderTrace() {{
      document.getElementById("trace-list").textContent = trace.join("\\n");
    }}

    function renderAll() {{
      renderRegisterGrid();
      renderFlagGrid();
      renderStatus();
      renderRam();
      renderDisasm();
      renderTrace();
    }}

    function parseOctal(text) {{
      const cleaned = text.trim();
      return cleaned === "" ? 0 : parseInt(cleaned, 8);
    }}

    function parseHex(text) {{
      const cleaned = text.trim();
      return cleaned === "" ? 0 : parseInt(cleaned, 16);
    }}

    function applyEdits() {{
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
          case "K":
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

      renderAll();
    }}

    function scrollToPc() {{
      const idx = LOGICAL_TO_LINE[String(getLogicalPC())];
      if (idx == null) return;
      const el = document.querySelector(`.line[data-index="${{idx}}"]`);
      if (el) el.scrollIntoView({{block: "center"}});
    }}

    function stepMany(count) {{
      for (let i = 0; i < count; i++) {{
        stepOne();
      }}
    }}

    document.getElementById("step-btn").addEventListener("click", () => stepOne());
    document.getElementById("step10-btn").addEventListener("click", () => stepMany(10));
    document.getElementById("run100-btn").addEventListener("click", () => stepMany(100));
    document.getElementById("reset-btn").addEventListener("click", () => resetState());
    document.getElementById("apply-btn").addEventListener("click", () => applyEdits());
    document.getElementById("goto-pc-btn").addEventListener("click", () => scrollToPc());

    document.getElementById("disasm").addEventListener("click", (event) => {{
      const line = event.target.closest(".line.instr");
      if (!line) return;
      selectedLogical = Number(line.dataset.logical);
      setPCFromLogical(selectedLogical);
      renderAll();
      scrollToPc();
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
        .replace("__DISASM_JSON__", disasm_json)
        .replace("__LOGICAL_MAP_JSON__", logical_map_json)
    )


def main() -> None:
    root = Path(__file__).resolve().parent
    rom_path = root / "sinclaircambridgeprogrammable.bin"
    disasm_path = root / "analysis" / "sinclaircambridgeprogrammable.dan.txt"
    output_path = root / "analysis" / "mm5799_debugger.html"

    rom = load_rom(rom_path)
    disasm_lines, logical_to_line = parse_disassembly(disasm_path)
    output_path.write_text(build_html(rom, disasm_lines, logical_to_line))
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
