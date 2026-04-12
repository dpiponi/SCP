#!/usr/bin/env python3
from pathlib import Path
import json

ROM_SIZE = 2048
RAW_ROM_SIZE = 1536

LFSR_SEQUENCE = [
    0o00, 0o40, 0o20, 0o10, 0o04, 0o02, 0o41, 0o60,
    0o30, 0o14, 0o06, 0o43, 0o21, 0o50, 0o24, 0o12,
    0o45, 0o62, 0o71, 0o74, 0o36, 0o57, 0o27, 0o13,
    0o05, 0o42, 0o61, 0o70, 0o34, 0o16, 0o47, 0o23,
    0o11, 0o44, 0o22, 0o51, 0o64, 0o32, 0o55, 0o66,
    0o73, 0o35, 0o56, 0o67, 0o33, 0o15, 0o46, 0o63,
    0o31, 0o54, 0o26, 0o53, 0o25, 0o52, 0o65, 0o72,
    0o75, 0o76, 0o77, 0o37, 0o17, 0o07, 0o03, 0o01,
]


def load_rom(path: Path) -> list[int]:
    data = bytearray(path.read_bytes())
    if len(data) == RAW_ROM_SIZE:
        data.extend(b"\x00" * (ROM_SIZE - len(data)))
        for index in range(0x5FF, 0x1FF, -1):
            data[index + 0x200] = data[index]
        for index in range(0x200, 0x400):
            data[index] = 0
        return list(data)
    if len(data) == ROM_SIZE:
        return list(data)
    if len(data) < ROM_SIZE:
        data.extend(b"\x00" * (ROM_SIZE - len(data)))
        return list(data)
    return list(data[:ROM_SIZE])


def build_html(rom: list[int]) -> str:
    rom_json = json.dumps(rom)
    lfsr_json = json.dumps(LFSR_SEQUENCE)
    html_template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MM5799 Fast Simulator</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      min-height: 100dvh;
      background: #111;
      padding: max(8px, env(safe-area-inset-top)) max(8px, env(safe-area-inset-right))
        max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left));
      overflow: hidden;
    }
    .hardware-wrap {
      position: relative;
      width: min(
        96vw,
        calc(
          (100dvh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 16px)
          * 1671 / 3652
        )
      );
      max-height: calc(100dvh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 16px);
      aspect-ratio: 1671 / 3652;
      overflow: hidden;
      background: url("calculator_cropped_tight10_cleaned_strong.png") center/cover no-repeat;
      user-select: none;
      touch-action: none;
    }
    .hardware-display {
      position: absolute;
      left: 5.07%;
      top: 8.03%;
      width: 89.80%;
      height: 7.91%;
      display: grid;
      grid-template-columns: repeat(9, minmax(0, 1fr));
      gap: 2px;
      pointer-events: none;
    }
    .hardware-digit { position: relative; border-radius: 3px; }
    .hw-sevenseg { position: relative; width: 100%; height: 100%; }
    .hw-seg { position: absolute; background: rgba(255, 28, 40, 0.08); }
    .hw-seg.on { background: rgba(255, 65, 92, 0.9); box-shadow: 0 0 7px rgba(255, 35, 70, 0.52); }
    .hw-seg.a, .hw-seg.d, .hw-seg.g { width: 58%; height: 10%; left: 21%; border-radius: 4px; }
    .hw-seg.a { top: 2%; } .hw-seg.g { top: 45%; } .hw-seg.d { bottom: 2%; }
    .hw-seg.b, .hw-seg.c, .hw-seg.e, .hw-seg.f { width: 12%; height: 34%; border-radius: 4px; }
    .hw-seg.f { left: 6%; top: 7%; } .hw-seg.b { right: 6%; top: 7%; }
    .hw-seg.e { left: 6%; bottom: 7%; } .hw-seg.c { right: 6%; bottom: 7%; }
    .hw-dot {
      position: absolute; right: -8%; bottom: 0; width: 12%; height: 12%;
      border-radius: 50%; background: rgba(255, 35, 70, 0.09);
    }
    .hw-dot.on { background: rgba(255, 92, 120, 0.95); box-shadow: 0 0 7px rgba(255, 55, 86, 0.55); }
    .hw-key {
      position: absolute;
      border: 0;
      border-radius: 0;
      background: transparent;
      cursor: pointer;
      outline: none;
      touch-action: none;
    }
    .hw-key:focus { outline: none; }
  </style>
</head>
<body>
  <div class="hardware-wrap" id="hardware-wrap"></div>
  <script>
    const ROM = __ROM_JSON__;
    const LFSR_SEQUENCE = __LFSR_JSON__;
    const LFSR_INDEX_BY_WORD = Object.fromEntries(LFSR_SEQUENCE.map((w, i) => [w, i]));
    const SEGMENT_DATA = [0x7f, 0x40, 0x79, 0x24, 0x30, 0x19, 0x12, 0x02, 0x78, 0x10, 0x06, 0x23, 0x06, 0x66, 0x6f, 0x01, 0x02, 0x08, 0x04];
    const SEGMENT_GLYPHS = ["0","1","2","3","4","5","6","7","8","9","A","b","F","G","E"," ","-","c","?"];
    const GLYPH_SEGMENTS = {
      " ": [],
      "?": ["a","b","g","e"],
      "0": ["a","b","c","d","e","f"],
      "1": ["b","c"],
      "2": ["a","b","d","e","g"],
      "3": ["a","b","c","d","g"],
      "4": ["b","c","f","g"],
      "5": ["a","c","d","f","g"],
      "6": ["a","c","d","e","f","g"],
      "7": ["a","b","c"],
      "8": ["a","b","c","d","e","f","g"],
      "9": ["a","b","c","d","f","g"],
      "A": ["a","b","c","e","f","g"],
      "b": ["g"],
      "C": ["a","d","e","f"],
      "c": ["d","e","g"],
      "d": ["b","c","d","e","g"],
      "E": ["a","d","e","f","g"],
      "F": ["a","e","f","g"],
      "G": ["a","c","d","e","f"],
      "-": ["g"],
    };
    const NET_TO_BIT = {K1: 0x1, K2: 0x2, K3: 0x4, K4: 0x8};
    const KEYS = [
      {id: "shift", label: "^v", row: 3, net: "K4"},
      {id: "cce", label: "C/CE", row: 4, net: "K4"},
      {id: "run", label: "RUN", row: 5, net: "K4"},
      {id: "0", label: "0", row: 3, net: "K1"},
      {id: "6", label: "6", row: 3, net: "K2"},
      {id: "eq", label: "=", row: 3, net: "K3"},
      {id: "1", label: "1", row: 4, net: "K1"},
      {id: "2", label: "2", row: 5, net: "K1"},
      {id: "3", label: "3", row: 6, net: "K1"},
      {id: "4", label: "4", row: 7, net: "K1"},
      {id: "5", label: "5", row: 8, net: "K1"},
      {id: "7", label: "7", row: 4, net: "K2"},
      {id: "8", label: "8", row: 5, net: "K2"},
      {id: "9", label: "9", row: 6, net: "K2"},
      {id: "ee", label: "EE", row: 7, net: "K2"},
      {id: "plus", label: "+", row: 6, net: "K3"},
      {id: "minus", label: "-", row: 4, net: "K3"},
      {id: "mul", label: "x", row: 7, net: "K3"},
      {id: "div", label: "/", row: 5, net: "K3"},
    ].map((k) => ({...k, bit: NET_TO_BIT[k.net]}));
    const KEY_HOTSPOTS = {
      shift: {col: 1, row: 0}, cce: {col: 2, row: 0}, run: {col: 3, row: 1},
      "0": {col: 0, row: 4}, "1": {col: 0, row: 3}, "2": {col: 1, row: 3}, "3": {col: 2, row: 3},
      "4": {col: 0, row: 2}, "5": {col: 1, row: 2}, "6": {col: 2, row: 2},
      "7": {col: 0, row: 1}, "8": {col: 1, row: 1}, "9": {col: 2, row: 1},
      ee: {col: 0, row: 0}, eq: {col: 1, row: 4}, plus: {col: 2, row: 4},
      minus: {col: 3, row: 4}, mul: {col: 3, row: 3}, div: {col: 3, row: 2},
    };
    const HW_SEG_NAMES = ["a", "b", "c", "d", "e", "f", "g"];

    const state = {
      Pp: 0, Pw: 0, SA: 0, SB: 0, A: 0, H: 0, C: 0, Br: 0, Bd: 0,
      M: new Array(128).fill(0),
      F1: 0, F2: 0, F3: 0, S: 0, D: 0, INB: 0, serbuf: 0,
      blk: 1, skip: false, wasLB: false,
      displaySelected: 0,
      visibleDigits: new Array(9).fill(0), visibleGlyphs: new Array(9).fill(" "),
    };

    let running = false;
    let powerEnabled = false;
    let heldKeyId = null;
    let suppressMouseUntil = 0;
    const pressedKeys = new Set();
    const hwDigitEls = [];
    const hwDigitSegEls = [];
    const hwDotEls = [];

    const normaliseNibble = (v) => v & 0xF;
    const getB = () => ((state.Br & 0x7) << 4) | (state.Bd & 0xF);
    const setBFromParts = (br, bd) => { state.Br = br & 0x7; state.Bd = bd & 0xF; };
    const getRawPC = () => ((state.Pp & 0x1F) << 6) | (state.Pw & 0x3F);
    const getLogicalPC = () => ((state.Pp & 0x1F) << 6) | LFSR_INDEX_BY_WORD[state.Pw & 0x3F];
    const getNextPc = (word) => LFSR_SEQUENCE[(LFSR_INDEX_BY_WORD[word & 0x3F] + 1) & 0x3F];
    const currentOpcode = () => ROM[getRawPC()];
    const romByte = (page, word) => ROM[((page & 0x1F) << 6) | (word & 0x3F)];
    const readMem = (addr) => state.M[addr & 0x7F] & 0xF;
    const writeMem = (addr, value) => { state.M[addr & 0x7F] = normaliseNibble(value); };
    const decodedScanRow = (d) => (d & 0xF) + 2;
    const dpBit = () => state.C ? 0 : 0x80;
    const isTwoByteOpcode = (op) => op === 0x13 || op === 0x33 || (op >= 0x60 && op <= 0x6F);
    const lb05Value = () => 4;

    function expectedKForD(d) {
      const row = decodedScanRow(d);
      let mask = 0;
      for (const key of KEYS) if (pressedKeys.has(key.id) && key.row === row) mask |= key.bit;
      return mask & 0xF;
    }
    const kinput = (d) => expectedKForD(d) & 0xF;

    function displayDigitIndexFromD(d) {
      const v = d & 0xF;
      if (v === 0xF) return 0;
      if (v <= 7) return v + 1;
      return v % 9;
    }

    function latchVisibleDisplayDigit(glyph = null) {
      const active = state.displaySelected % 9;
      state.visibleDigits[active] = state.S & 0xFF;
      if (glyph != null) state.visibleGlyphs[active] = glyph;
    }

    function blankDisplay() {
      state.displaySelected = 0;
      state.visibleDigits.fill(0);
      state.visibleGlyphs.fill(" ");
    }

    function ensureHardwareDom() {
      const root = document.getElementById("hardware-wrap");
      if (!root || root.dataset.initialized) return;
      const display = document.createElement("div");
      display.className = "hardware-display";
      for (let i = 0; i < 9; i++) {
        const digit = document.createElement("div");
        digit.className = "hardware-digit";
        const seven = document.createElement("div");
        seven.className = "hw-sevenseg";
        const segRefs = [];
        for (const name of HW_SEG_NAMES) {
          const seg = document.createElement("div");
          seg.className = `hw-seg ${name}`;
          seven.appendChild(seg);
          segRefs.push(seg);
        }
        const dot = document.createElement("div");
        dot.className = "hw-dot";
        seven.appendChild(dot);
        digit.appendChild(seven);
        display.appendChild(digit);
        hwDigitEls[i] = digit;
        hwDigitSegEls[i] = segRefs;
        hwDotEls[i] = dot;
      }
      root.appendChild(display);

      for (const key of KEYS) {
        const p = KEY_HOTSPOTS[key.id];
        if (!p) continue;
        const left = 17.06 + p.col * 22.23 - 15.62 / 2;
        const top = 52.15 + p.row * 10.18 - 5.94 / 2;
        const btn = document.createElement("button");
        btn.className = "hw-key";
        btn.type = "button";
        btn.dataset.key = key.id;
        btn.title = key.label;
        btn.style.left = `${left}%`;
        btn.style.top = `${top}%`;
        btn.style.width = "15.62%";
        btn.style.height = "5.94%";
        bindPressHandlers(btn);
        root.appendChild(btn);
      }

      const powerLeft = 17.06 + 3 * 22.23 - 15.62 / 2;
      const powerTop = 52.15 + 0 * 10.18 - 5.94 / 2;
      const power = document.createElement("button");
      power.className = "hw-key";
      power.type = "button";
      power.dataset.action = "power";
      power.title = "ON/OFF (mapped to Reset)";
      power.style.left = `${powerLeft}%`;
      power.style.top = `${powerTop}%`;
      power.style.width = "15.62%";
      power.style.height = "5.94%";
      bindPressHandlers(power);
      root.appendChild(power);
      root.dataset.initialized = "1";
    }

    function renderHardware() {
      ensureHardwareDom();
      for (let i = 0; i < 9; i++) {
        const seg = state.visibleDigits[i] & 0xFF;
        const glyph = state.visibleGlyphs[i] || " ";
        const lit = new Set(GLYPH_SEGMENTS[glyph] || GLYPH_SEGMENTS["?"]);
        const segEls = hwDigitSegEls[i];
        for (let s = 0; s < HW_SEG_NAMES.length; s++) segEls[s].classList.toggle("on", lit.has(HW_SEG_NAMES[s]));
        hwDotEls[i].classList.toggle("on", !!(seg & 0x80));
      }
    }

    function resetState() {
      running = false;
      state.Pp = 0; state.Pw = 0; state.SA = 0; state.SB = 0;
      state.A = 0; state.H = 0; state.C = 0; state.Br = 0; state.Bd = 0;
      state.M.fill(0);
      state.F1 = 0; state.F2 = 0; state.F3 = 0; state.S = 0; state.D = 0;
      state.INB = 0; state.serbuf = 0; state.blk = 1;
      state.skip = false; state.wasLB = false;
      blankDisplay();
      pressedKeys.clear();
      heldKeyId = null;
      renderHardware();
    }

    function powerOnStart() {
      powerEnabled = true;
      resetState();
      run();
    }

    function powerOffStop() {
      powerEnabled = false;
      running = false;
      blankDisplay();
      pressedKeys.clear();
      heldKeyId = null;
      renderHardware();
    }

    function stepOne() {
      const opcode = currentOpcode();
      let nextpc = getNextPc(state.Pw);
      state.blk = 1;
      let notLB = true;
      let tmp = 0;
      const beforeLogical = getLogicalPC();

      if (state.skip) {
        state.skip = false;
        if (isTwoByteOpcode(opcode)) nextpc = getNextPc(nextpc);
      } else {
        switch (opcode) {
          case 0x00: break;
          case 0x01: tmp = state.H; state.H = state.Br; state.Br = tmp & 0x7; break;
          case 0x02:
            state.A = state.A + state.C + readMem(getB());
            if (state.A >= 10) state.C = 1; else { state.C = 0; state.skip = true; }
            state.A &= 0xF;
            break;
          case 0x03: state.C = 1; break;
          case 0x04: if (state.F1 === 0) state.skip = true; break;
          case 0x05: if ((state.D & 0x4) === 0) state.skip = true; break;
          case 0x06: case 0x16: case 0x26: case 0x36:
            state.A = readMem(getB()); state.Br ^= ((opcode >> 4) & 0x3); break;
          case 0x07: case 0x17: case 0x27: case 0x37:
            tmp = state.A; { const a = getB(); state.A = readMem(a); writeMem(a, tmp); } state.Br ^= ((opcode >> 4) & 0x3); break;
          case 0x08: case 0x18: case 0x28: case 0x38:
            tmp = state.A; { const a = getB(); state.A = readMem(a); writeMem(a, tmp); }
            state.Br ^= ((opcode >> 4) & 0x3); state.Bd = (state.Bd - 1) & 0xF; if (state.Bd === 15) state.skip = true; break;
          case 0x09: case 0x19: case 0x29: case 0x39:
            tmp = state.A; { const a = getB(); state.A = readMem(a); writeMem(a, tmp); }
            state.Br ^= ((opcode >> 4) & 0x3); state.Bd = (state.Bd + 1) & 0xF; if (state.Bd === 0 || state.Bd === 13) state.skip = true; break;
          case 0x0A: case 0x0B: case 0x0C: case 0x0D: case 0x0E: case 0x0F:
          case 0x1A: case 0x1B: case 0x1C: case 0x1D: case 0x1E: case 0x1F:
          case 0x2A: case 0x2B: case 0x2C: case 0x2D: case 0x2E: case 0x2F:
          case 0x3A: case 0x3B: case 0x3C: case 0x3D: case 0x3E: case 0x3F:
            if (!state.wasLB) { state.Br = (opcode >> 4) & 0x3; tmp = opcode & 0x0F; if (tmp === 0x0A) state.Bd = lb05Value(); else if (tmp >= 0x0B) state.Bd = tmp; }
            state.wasLB = true; notLB = false; break;
          case 0x10: state.S = (((state.H & 0x7) << 4) | (state.A & 0xF) | dpBit()) & 0xFF; break;
          case 0x11:
            state.S = (((SEGMENT_DATA[state.A] ?? 0) & 0x7F) | dpBit()) & 0xFF;
            if (beforeLogical !== 0o215) latchVisibleDisplayDigit(SEGMENT_GLYPHS[state.A] || "?");
            break;
          case 0x12: state.A = normaliseNibble(state.A + readMem(getB())); break;
          case 0x13: { const second = romByte(state.Pp, nextpc); setBFromParts((second >> 4) & 0x7, second & 0xF); nextpc = getNextPc(nextpc); } break;
          case 0x14: if (state.F2 === 0) state.skip = true; break;
          case 0x15: { const liveK = kinput(state.D); state.F2 = (liveK & 0x4) ? 0 : 1; if (liveK > 0) state.skip = true; } break;
          case 0x20: state.A = normaliseNibble(~state.A); break;
          case 0x21: tmp = state.A; state.A = state.serbuf & 0xF; state.serbuf = tmp & 0xF; break;
          case 0x22: tmp = (~state.A & 0xF) + state.C + readMem(getB()); state.A = tmp & 0xF; if (tmp > 15) { state.C = 1; state.skip = true; } else state.C = 0; break;
          case 0x23: state.C = 0; break;
          case 0x24: if (state.F3 === 0) state.skip = true; break;
          case 0x25: state.D = state.Bd & 0xF; state.blk = 0; state.displaySelected = displayDigitIndexFromD(state.Bd); break;
          case 0x30: state.A = 0; break;
          case 0x31: tmp = state.A; state.A = state.H & 0xF; state.H = tmp & 0xF; break;
          case 0x32: if (state.A === readMem(getB())) state.skip = true; break;
          case 0x33: { const second = romByte(state.Pp, nextpc); if ((second & 0x20) === 0) state.F3 = (second & 0x10) ? 1 : 0; if ((second & 0x08) === 0) state.F2 = (second & 0x04) ? 1 : 0; if ((second & 0x02) === 0) state.F1 = (second & 0x01) ? 1 : 0; nextpc = getNextPc(nextpc); } break;
          case 0x34: state.A = kinput(state.D) & 0xF; break;
          case 0x35: if (state.INB === 1) state.skip = true; break;
          case 0x40: case 0x41: if (opcode === 0x41) state.skip = true; tmp = state.SA; state.SA = state.SB; nextpc = tmp & 0x3F; state.Pp = (tmp >> 6) & 0x1F; break;
          case 0x42: writeMem(getB(), readMem(getB()) & 0x7); break;
          case 0x43: state.A = state.Bd & 0xF; break;
          case 0x44: if ((readMem(getB()) & 0x1) === 0) state.skip = true; break;
          case 0x45: if ((readMem(getB()) & 0x2) === 0) state.skip = true; break;
          case 0x46: if ((readMem(getB()) & 0x4) === 0) state.skip = true; break;
          case 0x47: if ((readMem(getB()) & 0x8) === 0) state.skip = true; break;
          case 0x48: writeMem(getB(), readMem(getB()) & 0xE); break;
          case 0x49: writeMem(getB(), readMem(getB()) | 0x1); break;
          case 0x4A: writeMem(getB(), readMem(getB()) | 0x8); break;
          case 0x4B: writeMem(getB(), readMem(getB()) & 0xB); break;
          case 0x4C: writeMem(getB(), readMem(getB()) & 0xD); break;
          case 0x4D: if (state.C === 0) state.skip = true; break;
          case 0x4E: writeMem(getB(), readMem(getB()) | 0x2); break;
          case 0x4F: writeMem(getB(), readMem(getB()) | 0x4); break;
          case 0x50: state.Bd = state.A & 0xF; break;
          case 0x51: case 0x52: case 0x53: case 0x54: case 0x55: case 0x56: case 0x57:
          case 0x58: case 0x59: case 0x5A: case 0x5B: case 0x5C: case 0x5D: case 0x5E: case 0x5F:
            tmp = opcode & 0x0F; if (state.A + tmp < 16 && tmp !== 6) state.skip = true; state.A = normaliseNibble(state.A + tmp); break;
          case 0x60: case 0x61: case 0x62: case 0x63: case 0x64: case 0x65: case 0x66: case 0x67:
          case 0x68: case 0x69: case 0x6A: case 0x6B: case 0x6C: case 0x6D: case 0x6E: case 0x6F:
            { const second = romByte(state.Pp, nextpc);
              if ((second & 0x40) === 0) { state.SB = state.SA; state.SA = ((state.Pp & 0x1F) << 6) | getNextPc(nextpc); }
              state.Pp = (((15 - (opcode & 0x0F)) << 1) | ((second >> 7) & 1)) & 0x1F;
              nextpc = second & 0x3F; } break;
          default:
            if (opcode >= 0x70 && opcode <= 0x7F) { writeMem(getB(), opcode & 0x0F); state.Bd = (state.Bd + 1) & 0xF; }
            else if (opcode >= 0x80 && opcode <= 0xBF) {
              if ((state.Pp & 0x1E) !== 0x1E) { state.SB = state.SA; state.SA = ((state.Pp & 0x1F) << 6) | nextpc; }
              state.Pp = 0x1F; nextpc = opcode & 0x3F;
            } else if (opcode >= 0xC0 && opcode <= 0xFF) {
              nextpc = opcode & 0x3F; if (state.Pp === 0x1F) state.Pp = 0x1E;
            }
            break;
        }
        if (notLB) state.wasLB = false;
      }
      state.Pw = nextpc & 0x3F;
    }

    function frame() {
      if (!running) return;
      const steps = 12000;
      for (let i = 0; i < steps; i++) stepOne();
      renderHardware();
      requestAnimationFrame(frame);
    }

    function run() {
      if (!powerEnabled) return;
      if (!running) { running = true; requestAnimationFrame(frame); }
    }

    function targetElement(event) {
      if (event.currentTarget && event.currentTarget.dataset) return event.currentTarget;
      if (event.target && event.target.dataset) return event.target;
      return null;
    }

    const handlePressStart = (event) => {
      const el = targetElement(event);
      if (!el) return;
      const actionEl = el.dataset.action ? el : null;
      if (actionEl && actionEl.dataset.action === "power") {
        event.preventDefault();
        if (powerEnabled) powerOffStop(); else powerOnStart();
        return;
      }
      const keyEl = el.dataset.key ? el : null;
      if (!keyEl) return;
      event.preventDefault();
      const keyId = keyEl.dataset.key;
      pressedKeys.add(keyId);
      heldKeyId = keyId;
      renderHardware();
    };
    const handlePressEnd = () => {
      if (!heldKeyId) return;
      pressedKeys.delete(heldKeyId);
      heldKeyId = null;
      renderHardware();
    };

    const handleTouchStart = (event) => {
      suppressMouseUntil = Date.now() + 800;
      handlePressStart(event);
    };

    const handleMouseStart = (event) => {
      if (Date.now() < suppressMouseUntil) return;
      handlePressStart(event);
    };

    const handleTouchEnd = () => handlePressEnd();
    const handleMouseEnd = () => {
      if (Date.now() < suppressMouseUntil) return;
      handlePressEnd();
    };

    function bindPressHandlers(el) {
      el.addEventListener("touchstart", handleTouchStart, {passive: false});
      el.addEventListener("mousedown", handleMouseStart);
    }

    document.addEventListener("touchend", handleTouchEnd, {passive: false});
    document.addEventListener("touchcancel", handleTouchEnd, {passive: false});
    document.addEventListener("mouseup", handleMouseEnd);

    powerOffStop();
  </script>
</body>
</html>
"""
    return (
        html_template
        .replace("__ROM_JSON__", rom_json)
        .replace("__LFSR_JSON__", lfsr_json)
    )


def main() -> None:
    root = Path(__file__).resolve().parent
    rom_path = root / "sinclaircambridgeprogrammable.bin"
    output_path = root / "analysis" / "mm5799_simulator.html"
    rom = load_rom(rom_path)
    output_path.write_text(build_html(rom))
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
