# Sinclair Cambridge Programmable MM5799 Notes

## Current assessment

- `sinclaircambridgeprogrammable.bin` is the working ROM image to treat as canonical for disassembly.
- `sinclaircambridgeprogrammableraw.bin` is not a second meaningful program revision. It differs from the cleaned ROM in 1528 of 1536 bytes, so it is best treated as a noisy source extraction.
- The MM5799 uses a 64-word LFSR sequence for the low 6 bits of the program counter. A straight linear hex dump is therefore not execution order.
- Sean Riddle's original tools already encode two critical hardware facts:
  - 1.5K ROMs are expanded into a 2K address space with pages 8-15 left empty.
  - MM5799 instruction fetch uses the LFSR word order inside each 64-word page.

## What is in this directory

- [mm5799dasm.c](/Users/dan/Sinclair/mm5799dasm.c): Sean Riddle's original Windows-oriented disassembler.
- [mm5799emu.cpp](/Users/dan/Sinclair/mm5799emu.cpp): partial emulator with useful notes about unresolved MM5799 behavior.
- [sinclaircambridgeprogrammable.bin](/Users/dan/Sinclair/sinclaircambridgeprogrammable.bin): cleaned ROM image to analyze.
- [sinclaircambridgeprogrammableraw.bin](/Users/dan/Sinclair/sinclaircambridgeprogrammableraw.bin): raw extraction, useful only as provenance.
- [sinclaircambridgeprogrammable.txt](/Users/dan/Sinclair/sinclaircambridgeprogrammable.txt): hardware and keypad matrix notes.
- [Sinclair_Cambridge_Programmable.pdf](/Users/dan/Sinclair/Sinclair_Cambridge_Programmable.pdf): operating manual for the calculator, useful for user-facing vocabulary and program model.
- [nationalcopsi.pdf](/Users/dan/Sinclair/nationalcopsi.pdf): MOS/LSI databook scan with MM5799 documentation, but OCR is effectively absent.

## Practical implications for an annotated disassembly

- Treat the cleaned ROM as the base text.
- Keep the raw ROM around only to document provenance and uncertainty; because almost every byte differs, it is not suitable for local "suspect bit" marking by direct comparison.
- Build annotations around recognizable structures first:
  - reset path and early CALL fan-out
  - repeated `LBL`/`CALL` regions that likely represent dispatch tables
  - display scan and keyboard scan loops
  - entry points reachable from the `RUN`, arithmetic, and memory-related keys

## Tooling added here

- [mm5799_analyze.py](/Users/dan/Sinclair/mm5799_analyze.py): portable Python helper that can:
  - summarize ROM opcode distributions
  - compare cleaned vs raw ROMs
  - emit a full disassembly in MM5799 logical execution order

## Suggested next step

Use the generated disassembly as the main working text, then annotate one functional area at a time, starting with page 0 reset flow and the page 1 `LBL`/`CALL` table region.
