# First-Pass Annotations

This file is a working commentary layer over the generated disassembly in
[analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt).

The intent here is not to pretend we already know the whole machine. It is to
separate three things clearly:

- confirmed instruction behavior from Sean Riddle's emulator source
- structural observations from the cleaned ROM
- inferences about calculator behavior that still need validation

## Confirmed execution model

- The low 6 bits of the MM5799 program counter follow a 64-word LFSR sequence, so
  execution order is not linear ROM byte order.
- The 1.5K Sinclair ROM is mapped into a 2K space with a 0.5K gap for pages 8-15.
- `CALL 000` through `CALL 077` branch into page `037`.
- `GO 000` through `GO 077` branch within the current page, except page `037`
  returns to page `036`.
- `LBL` loads the next ROM word into the 7-bit `B` register.
- `BTD` copies `Bd` to the external digit output lines.
- `TKB` tests keypad inputs.
- `READ` reads the keypad latch into `A`.
- `DSPS` sends `A` through the segment PLA for display output.
- The generated named disassembly now also carries a growing set of semantic
  target labels for the more stable helper and caller entry points.

Those points come from [mm5799emu.cpp](/Users/dan/Sinclair/mm5799emu.cpp).

## Manual-derived facts

Reference: [Sinclair_Cambridge_Programmable.pdf](/Users/dan/Sinclair/Sinclair_Cambridge_Programmable.pdf)

- The calculator is explicitly a 36-step programmable machine.
- The three program-control operations visible to the user are `learn`, `step`, and `run`.
- The program-only instructions exposed on the keyboard are `go to`, `if neg`, and `stop`.
- Number entry inside a program is introduced by `#`.
- Outside programs, the yellow convenience functions are `x^2`, `1/x`, `-x`, and `2x`.
- The manual confirms the machine uses algebraic logic rather than operator precedence.
- The keyboard is tri-modal:
  - plain arithmetic/program entry in the key centers
  - upper-case functions after one shift
  - lower-case functions after two shifts
- The manual’s keyboard vocabulary matches the hardware notes:
  - `RUN`
  - `C/CE`
  - `EE`
  - `+`, `-`, `x`, `/`, `=`
  - scientific functions such as `sin`, `cos`, `tan`, `ln x`, `e^x`, `sqrt`
  - memory operations `sto`, `rcl`, `MEx`

These facts do not identify ROM addresses by themselves, but they sharply constrain what kinds of dispatch and scan behavior we should expect.

## Important addressing correction

- The disassembly prints instructions in logical execution order.
- `CALL` and `GO` operands are not those logical line numbers. They are raw 6-bit MM5799 page-word values.
- To find the actual target in the disassembly, the operand must be mapped back through the inverse of the 64-word LFSR sequence.
- Example:
  - `CALL 057` does not jump to displayed address `3757`.
  - It jumps to the page-037 word whose raw page word is octal `057`, which is displayed at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2070).

This matters because several earlier guesses about the page-037 helper set were too literal.

## Important code/data overlap correction

- Page 037 is not cleanly partitioned into "code words" and "data words".
- Some branch targets land on words that the straight-line disassembly marked as `DATA` only because they were consumed as the second byte of a preceding `LBL`.
- Those same words may still be executable opcodes when reached by `GO` or `CALL`.
- So page-037 helper analysis has to be control-flow driven, not linearly text driven.

## Page 0

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2)

- The reset entry at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L3) is a trampoline chain, not a conventional inline init sequence.
- The repeated pattern at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L12) and [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L18) suggests page-037 service calls are being used very early, probably for common setup.
- The block at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L20) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L39) looks like bit-test dispatch on RAM flags:
  - `TM 8`, `TM 4`, `TM 2` test individual bits in `M(B)`.
  - The following `GO` and `CALL` instructions split control by those bits.
- The pair `LB 0,13`, `LM 0`, `LM 0` at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L40) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L43) looks like explicit RAM clearing.
- The `LBL 4,12` at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L63) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L65) is the first obvious direct load of a specific RAM pointer. That is a useful anchor for later state naming.

Working interpretation:

- Page 0 is startup and early state selection.
- It likely sets one or more status bits, clears at least part of RAM, and then routes into the common service code on page 037 and later pages.
- Some of those early flag tests may be selecting initial keyboard mode or calculator state needed before entering the steady-state scan loop.

## Page 1

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L68)

- Lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L69) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L98) are the first strong table-like region in the ROM.
- There are three consecutive `LBL` records with operands `5,15`, `7,4`, `6,4`, `5,4`, each followed by repeated `CALL 057`.
- That shape is consistent with a list of fixed RAM locations receiving similar handling, not free-flow arithmetic code.
- The cluster at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L99) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L132) looks like a higher-level dispatcher:
  - `CALL 012`, `CALL 005`, `CALL 025`, `CALL 074`, `CALL 072`, `CALL 020`, `CALL 041`
  - two long transfers via `LG`
  - `TC` followed by a branch, which makes carry a control flag here rather than purely arithmetic state
- `CALL 057` is especially important because it is used repeatedly in this page and then later from other parts of the ROM.

Working interpretation:

- Page 1 is probably a structured dispatch/setup page rather than the main scan loop.
- The repeated `LBL` plus `CALL 057` pattern likely initializes or normalizes several RAM-backed calculator fields.
- This is a good candidate for naming state cells once page-037 helpers are better understood.
- Because the user-visible machine has a program mode, a run mode, and step/check behavior, this page may be setting up mode-specific state rather than only numeric registers.

Refined reading with the resolved page-037 helpers:

- The four `LBL` operands in the core table are:
  - `5,15`
  - `7,4`
  - `6,4`
  - `5,4`
- Each of those entries is followed by one or two calls to `CALL 057`, which now looks like the standard field-walk helper.
- So this is no longer best thought of as a generic dispatch table. It is more likely a compact list of fixed RAM fields that are being swept in a standard way.
- Since `CALL 074` now looks like a zeroing wrapper over the same field-walk mechanism, page 1 as a whole is very plausibly doing field normalization across a small set of status or working registers.
- The opening block at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L69) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L82) looks like guard/setup logic around two adjacent state cells before entering that table walk:
  - `MODE_STATE_A` = `1,14`
  - `MODE_STATE_B` = `1,15`
- The later block at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L99) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L132) appears to:
  - select another fixed field family, including `FIELD_5_15`, `FIELD_7_4`, `FIELD_6_4`, `FIELD_5_4`, and later members of the `WORK_2_x` cluster
  - perform one field walk
  - consult status helpers tied to `FLAG_A`, `FLAG_B`, `FLAG_C`, and `ANNUNCIATOR`
  - branch on carry and zero-style conditions
- Taken together, page 1 now reads more like "normalize a fixed set of calculator state fields, then adjust one selected field according to status bits" than like keyboard dispatch.

Updated reading with the `WORK_2_x` model:

- The specific sequence
  - `LB 2,12`
  - later `LB 2,14`, `LM 7`
  - later `LB 2,14`, `MTA`, `ADX 1`
  now fits the same small working-register family later manipulated by pages 24 through 26.
- So page 1 is likely not only normalizing the larger `FIELD_*` blocks. It is also seeding or priming at least part of the `WORK_2_x` staging family very early in control flow.
- That makes page 1 look less like pure startup initialization and more like an early common-entry normalization page for both:
  - long-lived calculator fields
  - short-lived staging/register cells used later by decoded input handlers

## Page 2

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L134)

- Page 2 is the first place where the instruction mix strongly matches external I/O activity.
- The sequence at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L141) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L158) uses:
  - `ATB`
  - `HXA`
  - `DSPS`
  - `BTA`
  - `BTD`
- Those are exactly the kinds of instructions expected in a digit-scan/display-update path.
- The sequence at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L159) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L166) adds `TKB`, which ties the same page to keypad scanning.
- The wiring notes in [sinclaircambridgeprogrammable.txt](/Users/dan/Sinclair/sinclaircambridgeprogrammable.txt#L45) show the keypad is multiplexed by output lines labeled as rows `3` through `8`, which fits the presence of `BTD` writing a digit index.
- The repeated bit tests at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L175) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L197) look like decoding or stepping through per-key/per-digit state.

Working interpretation:

- Page 2 is very likely part of the main display and keyboard scan loop.
- `BTD` probably selects the active digit or scan row.
- `TKB` then tests whether any key in that row is active.
- `DSPS` outputs segment data for the current display position.
- Since the manual shows a three-level keyboard with shifted meanings, the scan loop almost certainly feeds a later decode stage that interprets the same physical key differently depending on mode/shift state.
- The added [DS8874.pdf](/Users/dan/Sinclair/DS8874.pdf) confirms the external driver is a 9-digit shift-input LED driver with:
  - a `CLOCK PULSE` input
  - a `DATA` input
  - nine sequential digit outputs
  - a `LOW BATT OUT` intended to light the left-most decimal point
- That lines up directly with the machine notes:
  - MM5799 `D01` goes to DS8874 clock
  - MM5799 `D04` goes to DS8874 data
  - MM5799 segment outputs `Sa..Sg` and `Sp` provide segment data
- So the page-2 `BTD` usage is now even more plausibly part of the DS8874 digit-shift sequence, not just a generic keypad row drive.
- The Sinclair note that `Sp` also connects to the DS8874 low-battery point matches the DS8874 datasheet statement that the low-battery indication is furnished at digit 9 time through the decimal-point connection.

Refined split inside page 2:

- Display/driver-facing path:
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L141) `ATB`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L144) `HXA`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L148) `DSPS`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L149) `BTA`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L157) `ATB`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L158) `BTD`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L169) `HXA`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L170) `DSPS`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L171) `HXA`
- That sequence is exactly what we would expect for preparing a digit value, converting it to segments, and clocking digit-selection data into the DS8874.
- Keypad-facing path:
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L159) `LB 1,12` (`SCAN_STATE`)
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L160) `TKB`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L163) `TM 4`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L175) `TM 8`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L180) `TM 2`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L188) `TM 1`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L190) `TM 2`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L192) `TM 4`
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L194) `TM 8`
- That second path looks like per-key or per-row decode after `TKB`, very likely testing bits in `SCAN_STATE`, a RAM-backed scan/status nibble associated with the active scan position.
- So page 2 is best understood as an interleaved scan loop:
  - emit segment data and digit/row-selection data toward the DS8874
  - test the active key row
  - branch according to latched state bits for that row or digit position

This is the first page where the code can be tied directly to the machine-level hardware notes with fairly high confidence.

More focused display-loop reading:

- The tightest display-facing core of page 2 is:
  - `LB 0,5`
  - `ATB`
  - `MTA`
  - `HXA`
  - `0TA`
  - `COMP`
  - `SC`
  - `DSPS`
  - `BTA`
  - `RSC`
  - later another `ATB`
  - `BTD`
- In hardware terms, that looks very much like:
  - select one RAM-backed digit source
  - derive or normalize the segment pattern into `A`
  - send it through the segment PLA with `DSPS`
  - then move/clock digit-selection state out through `BTA` / `BTD`
- So page 2 is not just "a scan loop" in the abstract. It very likely contains the real digit-by-digit DS8874 shift routine.

Display-adjacent RAM anchors:

- Inside that tight loop, the only repeatedly selected fixed RAM cells other than `SCAN_STATE` are:
  - `0,5`
  - `1,5` (`ANNUNCIATOR`)
- That is important because it distinguishes them from the many flag and helper cells touched elsewhere.
- Safest current reading:
  - `0,5` and/or `1,5` are much more likely to be display-adjacent numeric/state anchors than generic hidden control flags
  - at least one of them is probably part of the currently visible display-digit path

What can be said safely:

- `0,5` is especially suspect as a display field anchor, because:
  - page 2 selects it directly inside the DS8874-facing loop
  - page 37's `CALL 057` field-walk helper is built on `LB 0,5` plus repeated `EXC+`
  - page 37's `CALL 074` zeroing wrapper also starts from `LB 0,5`
- That combination makes `0,5` a strong candidate for the base of a repeatedly walked visible numeric field.

Likely field extent:

- If `CALL 057` really is the standard digit walker, then starting from `LB 0,5` and advancing with `EXC+` until wrap implies a natural field spanning:
  - `0,5` through `0,15`
- That is an 11-digit internal field, not a 9-digit display-sized field.
- Safest current reading:
  - the `0,5` field is likely a full internal numeric register or display buffer with extra guard/state digits
  - while the visible 9-digit display is probably only a window onto part of that field
- Given the calculator's visibly poor precision, the extra two digits should not be over-read as evidence for a long high-quality guard pipeline.
- A better current bias is:
  - one displayed window of 8 numeric digits plus a sign/error position
  - with the larger internal field absorbing sign, decimal-format, and a small amount of working headroom
  - rather than many hidden high-precision guard digits

Why that matters:

- A pure display-only buffer would more naturally be expected to match the 9 visible digits.
- An 11-digit field is easier to reconcile with:
  - internal mantissa storage plus hidden guard/sign/format digits
  - or a full numeric working register that the display loop only partially renders
- So this pushes `0,5` further toward "real numeric register base" and away from "display-only staging scratch."

- `ANNUNCIATOR` (`1,5`) is also display-adjacent, but currently looks a bit different:
  - page 2 uses it inside the same loop
  - later pages use it in control-heavy logic through `CALL 011` / `CALL 041`
  - so it may be a companion state digit, display cursor/position marker, or display-side status nibble rather than the main mantissa field itself

Leftmost-position / overlay clues:

- The strongest current evidence for a non-mantissa overlay path is not in page 2 itself but in later control-heavy pages.
- In particular:
  - page 34 explicitly reaches `LB 1,5` and writes `LM 4`
  - reset/startup explicitly reaches `LB 1,5` and writes `LM 11`
- Safest current reading:
  - `ANNUNCIATOR` (`1,5`) is more likely than `0,5` to carry a rendered leading-position state such as:
    - sign/error/blank selection
    - or another display-side marker
  - while the `0,5..0,15` field remains the stronger candidate for the underlying numeric digits

Why the direct literal writes matter:

- A normal mantissa or display-buffer digit would be expected to be copied, compared, incremented, or walked in field order.
- `1,5` does get read that way in the page-2 loop, but several later pages also treat it very differently:
  - explicitly select `LB 1,5`
  - immediately store a small literal with `LM n`
  - return or branch away
- That pattern is much easier to read as "set leftmost symbol code" than as ordinary numeric digit handling.
- So `1,5` now looks less like a generic display-adjacent state nibble and more like a genuine annunciator code register.

Correction:

- An earlier read overstated the page-7 evidence by treating a literal-stamping block after `LB 2,5` as if it were writing `1,5`.
- That block belongs to the `2,5` template/staging family, not to `ANNUNCIATOR`.
- The direct literal-write evidence for `ANNUNCIATOR` is therefore narrower but cleaner:
  - reset/startup writes `LM 11`
  - page 34 writes `LM 4`
  - page 2 and several helper paths read or test the same cell in display-adjacent logic
- Of those two literal writes, the reset/startup `LM 11` is the best current candidate for the default leftmost annunciator state, plausibly blank unless later evidence points elsewhere.
- The page-34 write is now a little better constrained:
  - the visible local path is `LB 1,13 ; TM 8 ; GO 037`
  - where raw page-word `037` is the local branch target that lands on `LB 1,5 ; LM 4 ; RET`
  - so `LM 4` is directly gated by `MODE_STATE_C` bit `8`
- Since `MODE_STATE_C` bit `8` is already the best current special-entry latch candidate, `LM 4` is now a plausible candidate for a special-entry annunciator state rather than a generic mode marker.

Link back to the special-entry path:

- Page 22 is still the strongest current setter/clearer for `MODE_STATE_C` bit `8`:
  - it explicitly selects `LB 1,13`
  - then alternates `RSM 8` / `SM 8` in a compact block tied to decoded input state
- Page 34 is now the clearest consumer of that same latch:
  - `LB 1,13`
  - `TM 8`
  - branch straight to `LB 1,5 ; LM 4 ; RET`
- So the cleanest current end-to-end reading is:
  - page 22 establishes or clears a special-entry latch in `MODE_STATE_C`
  - later page 34 consumes that latch and loads a specific leftmost annunciator code into `ANNUNCIATOR`
- That is the tightest internal code evidence so far that the special-entry path is visible on the display, not just buried in hidden control state.

User-observed annunciator behavior:

- The calculator's shift behavior adds an important real-world constraint:
  - one shift state displays `F` in the leftmost digit
  - another shift state displays `G` in the leftmost digit
- That makes it very unlikely that the leftmost position is dedicated only to numeric sign or error indication.
- Instead, the best current reading is:
  - the leftmost visible position is a general annunciator/overlay slot
  - it can show at least:
    - minus
    - `E`
    - `F`
    - `G`
  - depending on mode/control state

Refined display model:

- `0,5..0,15` remains the strongest candidate for the underlying numeric/display field.
- `ANNUNCIATOR` (`1,5`) is now even more likely to be tied to the leftmost visible annunciator slot rather than to an ordinary mantissa digit.
- That also helps explain why `ANNUNCIATOR` appears in both:
  - page-2 display-adjacent logic
  - later control-heavy pages such as the `CALL 011` / `CALL 041` family
- In other words:
  - `0,5..0,15` likely carries the number
  - `1,5` likely helps determine what special symbol, if any, occupies the leftmost displayed position

Why this fits the observed behavior:

- You reported that the machine can show:
  - 8 digits with a preceding minus sign
  - or an `E` error indicator
- That is exactly the sort of visible behavior that suggests:
  - one leftmost display position can be overridden by control state
  - while the remaining positions render ordinary numeric digits from a larger internal field
- So the current best display model is:
  - `0,5..0,15` = underlying numeric/display field
  - `ANNUNCIATOR` (`1,5`) = strong candidate for the leftmost visible overlay or companion display-state cell

Practical consequence:

- The page-2 display loop is now one of the better clues about where the visible numeric registers live.
- The strongest current candidates are:
  - a field anchored at `0,5` for repeatedly walked display digits
  - a companion display-adjacent state cell at `1,5`
- That does not yet prove which one is mantissa, exponent, sign, or cursor state, but it does move `0,5` much closer to "real displayed-number storage" than before.

Annunciator-code caution:

- I still do not have a reliable symbol-to-code table for `1,5`.
- The current evidence supports "annunciator code register" much more strongly than any exact mapping such as:
  - `LM 11` = blank or minus
- Those concrete assignments remain open.

## ROM implications from the manual

- There must be code somewhere for:
  - shifted-key interpretation
  - program-step entry and checking
  - `go to`, `if neg`, and `stop`
  - memory store/recall/exchange
  - scientific functions and angle conversion
- The page-2 scan logic is therefore only the front end of input handling. A later dispatch layer must convert physical key presses into:
  - ordinary arithmetic entry
  - upper-case scientific and memory functions
  - lower-case program/control functions
- The repeated table-driven structures already seen in page 1 and later pages are consistent with this requirement.

## Pages 36 and 37

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1982)

- Page 36 has almost no external-I/O flavor.
- Its instruction mix is dominated by:
  - `ADD`
  - `SUB`
  - `ADX 6`
  - `ADX 10`
  - `SC` / `RSC`
  - `TC` / `RETS`
  - `EXC+` / `EXC-`
- That is exactly the profile expected for digit-level BCD arithmetic and carry/borrow handling.
- So page 36 should be treated as low-level numeric support code, not keyboard decode.

First arithmetic-kernel reading:

- Page 36 now looks less like "generic numeric support" and more like a compact library of digit primitives.
- The three strongest local shapes are:
  - `RSC`, `MTA 2`, `ADD`, `ADX 6`, `EXC+ 2`, `RET`
  - `SC`, `0TA`, `ADD`, `ADX 6`, `EXC+`, `RET`
  - `SUB`, `ADX 10`, `EXC+`, `TC`, `RETS`
- Those are strong matches for decimal-digit arithmetic idioms:
  - add with decimal adjust
  - carry-driven increment/propagate
  - subtract with borrow detection
- The `ADX 6` after `ADD` is especially suggestive of BCD correction.
- The `ADX 10` after `SUB` together with `TC` / `RETS` is especially suggestive of subtract-plus-borrow handling.

Provisional primitive labels:

- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1987) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1995):
  - likely a digit add / decimal-adjust / advance primitive on the `2,x` side.
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1999) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2006):
  - likely a carry-seeded increment or zero-plus-add propagate primitive.
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2007) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2012):
  - likely a digit subtract / borrow-detect primitive.

Useful caller confirmation:

- Page 32 contains a short inline sequence
  - `SC`
  - `MTA 2`
  - `SUB`
  - `ADX 10`
  - `EXC+ 2`
  - `GO 076`
  at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1775).
- That is very close to the page-36 subtract kernel and strengthens the reading that page 36 is exporting reusable BCD digit operations rather than high-level math functions.

First caller-level numeric reading:

- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1775) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1780) now look like a real multi-digit subtract or compare step:
  - seed carry with `SC`
  - load the opposing digit with `MTA 2`
  - subtract
  - decimal-adjust with `ADX 10`
  - advance with `EXC+ 2`
- Because this sequence returns immediately after the step, it looks more like a kernel inside a digit loop than a whole user-visible function.
- Safest current reading:
  - page 32 contains at least one compare/subtract-style digit loop built directly from the same arithmetic idiom as page 36.

Numeric-core priority:

- The next most useful numeric task is to group callers into:
  - subtract/compare loops
  - add/carry-propagation loops
  - shift/normalize loops
- Once those loop families are separated, the higher scientific functions should become much easier to identify from their call patterns.

Important correction:

- `CALL 036` is not a call into page 36 arithmetic.
- Raw call operand `036` maps into page 37's overlapped helper fabric, landing on the `LB 0,5` / `EXC+` / `CALL 057` path.
- So any earlier temptation to read `CALL 036` as "invoke the page-36 numeric kernel" was wrong.

Current add-side status:

- I still do not have a caller outside page 36 that mirrors the full add side as cleanly as page 32 mirrors the subtract side.
- But page 36 itself now looks more deliberately structured than before:
  - raw word `004` enters a tiny add/carry worker:
    - `RSC`
    - `MTA 2`
    - `ADD`
    - `ADX 6`
    - `EXC+ 2`
    - return
  - raw word `020` enters a second add-side worker:
    - `SC`
    - `0TA`
    - `ADD`
    - `ADX 6`
    - `EXC+`
    - return/branch
- The add/subtract kernels are also surrounded by tiny shared tail paths rather than hard stops:
  - `GO 062` / `GO 063` lead into short `EXC 1` / `EXC-` / `RET` cleanup paths
  - `GO 065` leads into a small `0TA` / `EXC-` / branch tail
  - `GO 076` is another immediate local exit path
- The safest structural reading is that these are not unrelated leftovers.
- They look like a tiny local continuation/exit mesh:
  - one path for "advance and finish"
  - one for "clear/normalize and continue"
  - one for short skip/borrow-sensitive exit behavior
- So page 36 is starting to look less like "three isolated arithmetic snippets" and more like a compact micro-library for:
  - one-digit add
  - carry propagation
  - one-digit subtract/compare
  - plus the tiny cleanup/advance exits those kernels need
- Important addressing caution here too:
  - `CALL 020` elsewhere in the ROM is not a call into page 36's raw-word `020`
  - it is the already-resolved page-37 fixed-pointer helper
  - so the add-side workers are clearly present, but their higher-level entry points are still not exposed by simple `CALL 020` searches
- So the asymmetry is no longer "subtract has a worker, add does not."
- It is:
  - subtract/compare has the clearest visible caller match on page 32
  - add/carry is clearly modular inside page 36, but its higher-level callers are still less exposed
- The best weaker clue so far is page 20 at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1115):
  - `MTA`
  - `ADX 6`
  - then immediate control flow out through status logic
- That looks more like inline decimal adjustment or digit normalization than a full add/subtract loop.
- So the numeric-core picture is now:
  - subtract/compare side: one strong caller match plus a clear local worker shape
  - add/carry side: clear local worker shapes in page 36, but only weak higher-level caller matches so far

First shift/normalize clue:

- A separate caller family may be hiding the add side inside normalization rather than explicit add loops.
- Page 22 at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1188) repeatedly uses:
  - `EXC+`
  - `ADX 8`
  - bit set/reset on `SCAN_STATE`
  - `CALL 055`
- That does not look like plain arithmetic, but it does look like staged digit/state movement.
- Safest current reading:
  - some of the decimal-adjust and carry-propagation machinery may be serving normalization or staged entry movement paths rather than appearing as obvious inline "add loops."

Refinement:

- On a closer reread, page 22 is probably better classified as staged entry/state movement than as a numeric normalize loop.
- It is tightly tied to:
  - `SCAN_STATE`
  - `MODE_STATE_C`
  - `CALL 055` on the `WORK_2_12` side
- So page 22 still matters for understanding decimal-like movement, but it is probably closer to entry/edit-state handling than mantissa normalization.

- Page 20 is the cleaner numeric-adjacent normalization candidate.
- It:
  - seeds a fixed `2,7` pattern
  - touches `WORK_2_14`
  - then executes the `MTA` / `ADX 6` decimal-adjust-looking pair
- Safest current reading:
  - page 20 may be a bridge between entry/state staging and numeric normalization, whereas page 22 is mostly entry/state-side movement.

More specific page-20 reading:

- The `2,7` seed is not an isolated constant load.
- It is followed by a fixed sequence of `LM` writes:
  - `LM 6`
  - `LM 9`
  - `LM 2`
  - `LM 7`
  - `LM 5`
  - then `LB 2,14`
  - then `LM 1`
- So page 20 appears to stamp a small fixed pattern into RAM before applying the later decimal-adjust-looking step.
- That makes page 20 look less like a simple arithmetic routine and more like one of:
  - numeric format preparation
  - entry packing
  - display-oriented staging of a formatted numeric state
- The current safest bias is toward format/packing rather than pure display refresh, because the page ends in a numeric-looking `MTA` / `ADX 6` adjustment rather than in obvious display I/O.
- The page ending is now a bit more constrained than before:
  - after the `MTA` / `ADX 6` pair
  - page 20 immediately does local control cleanup (`RSM 4`, local `CALL 062`, local `GO 065`)
  - rather than obviously branching into page-36 add/carry workers
- So page 20 still looks numeric-adjacent, but more like an inline decimal-adjust/normalization tail than a clean higher-level caller of the page-36 add kernels.

Page-21 contrast:

- Page 21 sits close to page 20 in the ROM, but its visible behavior is different.
- It does not expose a similar decimal-adjust tail.
- Instead it looks like a compact control-latch conditioner:
  - repeated bit operations on `SCAN_STATE` (`SM 2`, `RSM 2`, `SM 4`, `RSM 4`)
  - explicit `MODE_STATE_C` (`1,13`) `SM 8`
  - and a short gate through `SELECT_STATE` (`1,11`) `TM 8`
- Safest current reading:
  - page 20 is the more numeric-adjacent member of this local neighborhood
  - page 21 is more about preparing or qualifying control state before the stronger special-entry handling seen on page 22
- That keeps the local split cleaner:
  - page 20 = format/packing plus inline decimal adjustment
  - page 21 = control-latch conditioning
  - page 22 = stronger special-entry / edit-state latch handling

Comparison against the other `2,7` template sites:

- Page 20, page 25, and page 26 all reference `LBL 2,7`, but they do not stamp the same literal shape.
- Page 20 writes the richest pattern:
  - `LM 6`, `LM 9`, `LM 2`, `LM 7`, `LM 5`, then `LM 1` via `WORK_2_14`
- Page 25 writes a shorter pattern:
  - `LM 8`, `LM 0`, `LM 7`, `LM 5`, `LM 1`
- Page 26 only shows a fragment:
  - `DATA 2,7`
  - then `LM 5`
  - before branching away
- So these look more like related staged templates than one universal constant literal.
- Safest current reading:
  - the `2,7` sites are probably formatting or packing templates used at different phases of the same staging family
  - not a single hard-coded numeric constant with one meaning everywhere

`2,9` as a possible secondary template site:

- Page 25 also contains a lone `LBL 2,9` site at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1448).
- Unlike the `2,7` sites, it does not expand into a rich visible `LM` pattern nearby.
- Its local shape is:
  - `CALL 045`
  - `LBL`
  - `DATA 2,9`
  - immediate `GO 002`
- So the safest current reading is weaker:
  - `2,9` is probably another small staging/template marker in the same family
  - but the current evidence is not strong enough to treat it as equivalent to the `2,7` template sites
  - it may be a tail case, alternate format selector, or compact alternate entry into the same packing logic

`CALL 051` after template stamping:

- `CALL 051` shows up repeatedly immediately after template or state selection in the strongest staging pages:
  - page 20 after the rich `2,7` stamp
  - page 24 / page 25 inside the `WORK_2_x` handler family
  - page 26 after the fragmentary `2,7` path
- Raw operand `051` maps into page 37's overlapped helper fabric, not into a long standalone routine.
- So the safest current reading is:
  - `CALL 051` is probably a short follow-on helper or branch point that consumes already-selected staging state
  - it is not, by itself, the whole packing or formatting operation
- That means the visible `LM` template writes and `WORK_2_x` selections remain the more important evidence for format/packing interpretation than the `CALL 051` body itself.

`CALL 031` and `CALL 064` in the same staging family:

- These two calls now appear to split across the same internal `WORK_2_x` divide seen elsewhere.
- Raw operand `031` maps into page 37 at the path beginning:
  - `LB 2,5`
  - `LB 2,14`
  - then onward branch through the helper fabric
- Raw operand `064` maps into page 37 at the path beginning:
  - `LB 2,12`
  - then onward branching through the same overlapped cluster
- So the safest current reading is:
  - `CALL 031` is another short consumer on the `WORK_2_14` side
  - `CALL 064` is another short consumer on the `WORK_2_12` side
- That matches their caller patterns in pages 24, 25, and 26, where they tend to appear right after those respective cells have been selected or updated.

Practical consequence:

- The staging-family picture is now more structured:
  - `CALL 052` / `CALL 054` = `WORK_2_14` side setup wrappers
  - `CALL 055` = `WORK_2_12` side setup wrapper
  - `CALL 031` = `WORK_2_14` side follow-on consumer
  - `CALL 064` = `WORK_2_12` side follow-on consumer
- That makes the `WORK_2_12` versus `WORK_2_14` split look like a real two-path staging design, not just a loose collection of related cells.

Trigger pattern inside pages 24 and 25:

- The split does not currently look like a simple one-bit fork such as "if `TC` then use `WORK_2_14`, else use `WORK_2_12`."
- Instead, the local control flow looks more phased:
  - `WORK_2_14` tends to appear on the setup/update side, together with `LM` writes or `MTA` plus `ADX 1`
  - `WORK_2_12` tends to appear on the check/consume side, together with `MTA 2`, `TAM`, and the `CALL 055` / `CALL 064` path
- So the safest current reading is:
  - `WORK_2_14` behaves more like the side that carries forward or advances staged state
  - `WORK_2_12` behaves more like the side that tests, compares, or consumes staged state
- That is stronger than the earlier vague "two related cells" reading, even though it is still not enough to assign final semantic names.

Comparison against page 5 program-step logic:

- Page 5 does use `CALL 064`, but it does not directly select `WORK_2_12` or `WORK_2_14`.
- Instead it stays focused on:
  - `STEP_LO` / `STEP_HI`
  - `MODE_STATE_A` / `MODE_STATE_B`
  - `MODE_STATE_C`
- So the safest current reading is:
  - the program-step path and the `WORK_2_x` staging path are related only at the level of shared tiny helper fabric
  - page 5 is not strong evidence that program entry is directly implemented on top of the same `WORK_2_12` / `WORK_2_14` two-path design
- That argues for keeping the current models separate:
  - page 5 = program-step bookkeeping
  - pages 24 to 26 = staged input/format family

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2048)

- Page 37 contains the shared entry points reached by `CALL xx`.
- Some of those are true helpers, while some are just wrappers or trampolines.

Provisional helper notes:

- `CALL 000` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2049).
  - This is not a normal local helper body.
  - It immediately performs a long transfer.
  - The landing point is [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1581) on page 27:
    - `0TA`
    - `TAM`
    - `RET`
    - `RETS`
  - That sequence is highly specific:
    - `0TA` clears `A`
    - `TAM` compares `A` against `M(B)` and skips if equal
    - therefore the routine returns with plain `RET` when `M(B)` is nonzero
    - and returns with `RETS` when `M(B)` is zero
  - So `CALL 000` is best interpreted as a common "test current RAM digit for zero" helper.
  - In the named listing, this helper now appears as `TEST_CURRENT_DIGIT_ZERO`.
- `CALL 011` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2081).
  - `LBL 1,5` followed by `RET`.
  - This is a tiny helper that loads a fixed RAM pointer.
- `CALL 020` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2051).
  - Its control flow is easy to misread unless the LFSR page-word addressing is kept in mind.
  - In effect it behaves like:
    - `LB 0,12`
    - then return through a short page-037 wrapper
  - The immediately following `LB 0,11` does not appear to define a second independent action here; in context it is best read as part of an overlapping entry-point layout.
  - So `CALL 020` now looks like another tiny fixed-pointer loader, specifically for RAM location `0,12`.
  - In the named listing, this helper now appears as `LOAD_FLAG_A_PTR`.
- `CALL 024` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2063).
  - This entry is now best read as a pure alias into `CALL 045`.
  - It immediately executes `GO 045`, so it is not an independent routine.
- `CALL 057` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2070).
  - `EXC+`
  - `CALL 057`
  - `RET`
  - This only makes sense if it is an iterative field walker that depends on `EXC+` incrementing `Bd` and skipping on wrap.
  - So `CALL 057` is very likely a standard "step through successive digits in a field" helper.
  - In the named listing, this helper now appears as `WALK_MAIN_FIELD`.
- `CALL 074` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2068).
  - `0TA`
  - `LB 0,5`
  - then into the `CALL 057` helper
  - This strongly suggests a field-clearing or zero-propagation wrapper.
  - In the named listing, this helper now appears as `ZERO_MAIN_FIELD`.
- `CALL 045` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2065).
  - The effective flow is:
    - `LB 2,15`
    - `LB 0,15`
    - `GO 017`
  - The `GO 017` target is one of the overlapped code/data words discussed above.
  - Its raw byte value is octal `114`, which is also opcode `RSM 2`, and it is followed by `RET`.
  - So the practical effect of `CALL 045` is:
    - load a fixed flag cell
    - clear bit `2`
    - return
  - The only remaining ambiguity is which `LB` actually wins if the real chip suppresses successive `LB` instructions. Sean Riddle called that behavior uncertain in the emulator notes.
  - So the strongest safe reading is:
    - `CALL 045` is a standard "clear status bit 2 in a fixed RAM flag cell" helper.
- `CALL 016` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2078).
  - Effective flow:
    - `LB 0,14`
    - `RSC`
    - branch into the same overlapped helper cluster
  - This looks like another tiny status-cell wrapper rather than an arithmetic routine.
  - The safest reading is:
    - select a fixed status cell
    - clear carry
    - continue through shared status logic
- `CALL 021` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2061).
  - It immediately falls into the `CALL 045` path after selecting another fixed RAM pointer.
  - So this also appears to be a status-cell alias entry rather than a substantial subroutine.
- `CALL 041` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2055).
  - It starts with:
    - `LB 1,5`
    - `MTA`
    - `GO 025`
  - Since that branch remains inside the same overlapped page-037 helper cluster, `CALL 041` also appears to belong to this small flag/state service family.
  - It does not look like multi-digit arithmetic.
  - Safest reading:
    - select a fixed state cell
    - load it into `A`
    - branch into shared status logic
- `CALL 066` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2088).
  - `LBL 1,7`
  - `RET`
  - Another tiny fixed-pointer helper.
- `CALL 001` enters at raw page-word `001`, which maps to [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2113).
  - That entry is just `RET`.
  - So `CALL 001` is best treated as a structural no-op return target, not a substantive helper body.
  - Its callers matter because of the state they establish before the call, not because `CALL 001` itself does significant work.
- `CALL 012` enters at raw page-word `012`, which maps to [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2058).
  - This entry lands inside the overlapped helper fabric rather than a clean standalone body.
  - The visible flow begins with `LB 1,12` and then immediately runs into further fixed-cell selection and shared branching.
  - Safest reading:
    - another tiny alias/wrapper into the page-037 state machinery
    - probably associated with `SCAN_STATE` or a closely related fixed-cell path
    - not a long independent routine
- `CALL 014` enters at raw page-word `014`, which maps to [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2050).
  - The visible path starts:
    - `LB 0,13`
    - `TM 8`
    - then branches into the same small overlapped helper cluster that also reaches `CALL 016` / `CALL 045`
  - Safest reading:
    - short status-driven wrapper centered on bit `8` of `0,13`
    - used to choose or normalize a follow-on fixed-cell operation
    - not a self-contained arithmetic or field-walk routine
- `CALL 063` enters at [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2096).
  - Immediate `RET`.
  - This is likely a structural return target used by branches rather than a real subroutine.
- `CALL 043`, `056`, `064`, `067`, `072`, `075`, and `076` still appear to be short dispatch wrappers around the page-037 state machinery rather than self-contained long routines.

Working interpretation:

- Page 37 is a compact service page built out of tiny pointer loaders, field walkers, wrappers, and trampolines.
- The real higher-level behavior is split between:
  - these page-037 entry points
  - page-036 digit arithmetic
  - longer routines elsewhere reached via long transfers
- This matches the overall feel of the ROM, where many pages call tiny common services rather than inlining digit loops everywhere.

## Page 27

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1520)

- Page 27 is the first caller page that can now be read mostly in terms of resolved shared helpers rather than raw mnemonics.
- It is dense with page-037 calls:
  - `CALL 045`
  - `CALL 005`
  - `CALL 012`
  - `CALL 076`
  - `CALL 020`
  - `CALL 016`
  - `CALL 050`
  - `CALL 074`
  - `CALL 072`
  - `CALL 031`
  - `CALL 064`
  - `CALL 014`
  - `CALL 024`
- That instruction mix does not look like user-facing key decode or arithmetic entry. It looks like a higher-level state-management routine built out of standard field and flag primitives.

Useful local observations:

- The page opens with [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1521), a call to the bit-clear helper `CALL 045`.
- It then immediately uses several fixed-pointer helpers and status helpers before branching further:
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1521)
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1527)
  - [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1528)
- In terms of the provisional labels, the page opens by touching:
  - `FLAG_C` via `CALL 045`
  - `FLAG_A` via `CALL 020`
  - `FLAG_B` via `CALL 016`
- The block at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1534) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1540) explicitly tests bit 8 in a status cell and chooses between different helper sequences.
- The pair
  - `LB 0,13`
  - `EXC 2`
  - `ADX 8`
  at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1541) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1544)
  looks like local manipulation of a status or mode nibble rather than a numeric mantissa digit.
- The call cluster at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1556) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1568) repeatedly uses `CALL 064`, `CALL 072`, `CALL 045`, and `CALL 024`, which strongly suggests coordinated updates to a small family of status cells.
- On a fresh reread with the newer `WORK_2_x` model in mind, the visible linear body of page 27 does not directly walk the `WORK_2_x` family.
- So the safest current reading is narrower:
  - page 27 is primarily coordinating fixed flag/status cells
  - and only indirectly interacting with other working families through helper calls
- The tail at lines [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1581) through [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1584) is the `CALL 000` zero-test landing sequence, confirming that page 27 hosts at least one shared utility body as well as caller logic.

Working interpretation:

- Page 27 looks like a mode/state normalization page.
- It probably coordinates a small set of RAM flag cells and one or more short fields, using:
  - fixed-pointer loaders
  - bit-clear helpers
  - zero-test helpers
  - field-walk/field-clear helpers
- Compared with pages 24 through 26, it now looks less like a direct `WORK_2_x` handler page and more like a higher-level flag/control normalizer that other pages can branch through.
- In the current named listing, the broad entry and central state-update body are now labeled:
  - `MODE_STATE_NORMALIZATION`
  - `NORMALIZATION_UPDATE_LOOP`
- This page is a stronger candidate for calculator mode transitions or state cleanup than for raw numeric computation.
- In particular, it may participate in transitions among:
  - ordinary calculation state
  - program learn/check/run state
  - shift/status bookkeeping
- Of the currently named cells, `MODE_STATE_B` is the strongest candidate for carrying the top-level mode bits, because its bit 8 and bit 4 are repeatedly tested and explicitly set/reset across several control-heavy pages.

## Page 5

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L332)

- Page 5 repeatedly alternates between `LBL 1,8` and `LBL 1,9`.
- Those two cells are manipulated together in a highly structured way:
  - they are loaded explicitly several times
  - they are compared with `TAM`
  - they are processed with `CALL 020`, `CALL 024`, `CALL 025`, `CALL 066`, and `CALL 074`
  - `MODE_STATE_B` is also consulted inside the same page
- More specifically, the page contains two direct compare patterns:
  - `LB 1,14`, `MTA`, `LBL 1,8`, `TAM`
  - `LB 1,15`, `MTA`, `LBL 1,9`, `TAM`
- So page 5 is not just "using" the putative step digits. It is explicitly comparing them against the current contents of `1,14` and `1,15`.
- The manual says the calculator uses program step numbers from `00` to `35`.
- A pair of single-digit RAM cells is exactly what that feature would need.

Working interpretation:

- Page 5 is a strong candidate for program-step handling rather than ordinary calculation state.
- The pair `1,8` / `1,9` may therefore be:
  - current program-step digits
  - or closely related learn/check/run bookkeeping digits
- The new compare pattern adds an important caveat:
  - `MODE_STATE_A` and `MODE_STATE_B` are probably not pure flag registers.
  - At least in some submodes they appear to carry digit-like or entry-like state that can be compared against `STEP_LO` and `STEP_HI`.
- This is still an inference, but it is a stronger and more specific one than the earlier generic "table/dispatch" reading.
- In the current named listing, the clearer local bodies are now labeled:
  - `PROGRAM_STEP_COMPARE`
  - `PROGRAM_STEP_REINIT`
  - `RESET_PROGRAM_STEP_STAGE`
  - `ADVANCE_PROGRAM_STEP_STAGE`

Practical consequence:

- If that reading is right, then `MODE_STATE_B` bit tests in pages 5, 31, and 35 may be distinguishing ordinary calculator mode from program-control submodes such as `learn`, `step`, or `run`.

## Page 31

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1716)

- Page 31 opens by loading `MODE_STATE_B` and immediately clearing/testing upper control bits:
  - `LB 1,15`
  - `RSM 8`
  - `TM 4`
- It then enters the same helper family seen elsewhere:
  - `CALL 025`
  - `CALL 045`
  - `CALL 064`
  - `CALL 056`
  - `CALL 074`
  - `CALL 066`
- The page also touches:
  - `1,13`
  - `ANNUNCIATOR` (`1,5`)
  - `WORK_2_14`
- That instruction mix looks like setup or normalization around a mode change, not arithmetic.

Working interpretation:

- Page 31 is a strong candidate for mode-gated initialization or transition logic.
- It appears to:
  - clear or normalize selected control bits in `MODE_STATE_B`
  - use the page-037 flag helpers to prepare related state cells
  - then seed or reload working state including `WORK_2_14`
- In the current program-control hypothesis, page 31 fits naturally as a "prepare state for learn/step/run style behavior" page.
- In the current named listing, the two broad entry blocks are now labeled:
  - `MODE_TRANSITION_PREP`
  - `MODE_TRANSITION_STAGE`

## Page 35

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1948)

- Page 35 again starts from `MODE_STATE_B`:
  - `LB 1,15`
  - `ADX 8`
  - `SM 8`
- Later in the same page it revisits `MODE_STATE_B` and tests `TM 8` through the same helper network.
- Unlike page 5, this page singles out `STEP_HI`:
  - it contains two separate `LBL 1,9` entries
  - but no matching `LBL 1,8`
- It also mixes in:
  - `CALL 020`
  - `CALL 024`
  - `CALL 025`
  - `CALL 016`
  - `CALL 056`
  - `CALL 072`
  - `CALL 076`

Working interpretation:

- Page 35 looks like a control-heavy path that cares specifically about the high step digit or a one-digit coarse program index.
- That makes it a plausible partner to page 5:
  - page 5 handles the full two-digit step pair
  - page 35 handles a narrower test or update path dominated by `STEP_HI` and `MODE_STATE_B`
- This is still provisional, but it is a better fit than treating page 35 as generic mode logic with no connection to program-step state.
- In the current named listing, the broad page-35 blocks are now labeled:
  - `STEP_HI_MODE_PATH`
  - `STEP_HI_UPDATE_LOOP`

## `1,13` as a control-state cell

Reference points:

- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L210)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1148)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1668)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1918)

- `1,13` is touched immediately at reset on page 0, before the machine begins testing the fixed flag cells.
- On page 3 it is tested with:
  - `TM 8`
  - then, later in the same page, `TM 4`
- On page 21 it is explicitly modified bitwise:
  - `LB 1,13`
  - `SM 8`
  - and nearby `TM 4`
- On page 31 it is used as a state latch:
  - `LB 1,13`
  - `SM 4`
  - later `LB 1,13`, `TM 4`
- On page 35 it opens the page:
  - `LB 1,13`
  - `TM 8`
  - before flowing into the `MODE_STATE_B` path

Working interpretation:

- `1,13` behaves much more like a compact control-state latch than like a numeric digit cell.
- Unlike `STEP_LO` and `STEP_HI`, it is not being walked or compared as part of a decimal pair.
- Unlike `MODE_STATE_A` and `MODE_STATE_B`, the strongest evidence for `1,13` is direct bit-level set/test behavior rather than mixed compare-plus-mode behavior.
- So the safest current reading is:
  - `1,13` is another member of the mode/control state cluster
  - but one that currently looks more like a pure bitfield latch than a digit-carrying register

Practical consequence:

- The pages already suspected of program-control behavior are now clustered around four adjacent cells:
  - `MODE_STATE_C` (`1,13`)
  - `MODE_STATE_A` (`1,14`)
  - `MODE_STATE_B` (`1,15`)
  - `SCAN_STATE` (`1,12`)
- That makes the `1,12` through `1,15` block the strongest current candidate for the machine's central scan/mode/program-control state area.

## `1,11` as a selector/latch cell

Reference points:

- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L7)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L275)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L451)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L465)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1061)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1259)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1594)
- [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1896)

- Page 0 touches `1,11` very early in reset and immediately sets bit `8` with `SM 8`.
- Page 4 repeatedly loads `1,11`, tests it through `CALL 000`, and then branches on `TM 4` or `TM 8`.
- Page 6 sets bit `1` in `1,11` with `SM 1`.
- Page 7 tests bit `8` in `1,11`, later revisits the same cell, and then pivots into `SCAN_STATE` (`1,12`) and `ANNUNCIATOR` (`1,5`) logic.
- Page 20 loads `1,11` and immediately runs `ADX 12` / branch logic that looks like table selection rather than long-lived mode storage.
- Page 23 has two separate `LB 1,11` / `TM 8` sequences wrapped around `SCAN_STATE` tests and dispatch calls.
- Page 30 begins with:
  - `LB 1,11`
  - `TM 1`
  - then later `LB 1,11`, `RSM 8`
- Page 34 also touches `1,11` in a short helper-like burst rather than as part of a larger field walk.

Working interpretation:

- `1,11` does not look like a general-purpose digit cell.
- It also does not look like a broad mode register in the same sense as `MODE_STATE_B`, because it is usually touched only briefly:
  - test one bit
  - optionally set or clear one bit
  - branch immediately into dispatch or scan-related logic
- The safest current reading is that `1,11` is a compact selector or pending-state latch closely tied to input/dispatch flow.
- It may hold one or two latched conditions such as:
  - current pending-key condition
  - dispatch qualifier
  - current scan/entry substate

Practical consequence:

- The `1,11` through `1,15` region now looks internally structured rather than flat:
  - `1,11` = short-lived selector/latch
  - `1,12` = scan-related state
  - `1,13` = control bitfield latch
  - `1,14` / `1,15` = mixed control/state cells, with `1,15` the strongest candidate for top-level mode bits
- That is a better fit for the observed code than treating all five cells as interchangeable status nibbles.

## Page 23

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1259)

- Page 23 is the clearest short block yet for the relationship between `SELECT_STATE` (`1,11`) and `SCAN_STATE` (`1,12`).
- It contains two parallel-looking entry patterns:
  - `LB 1,11`, `TM 8`, branch, then `LB 1,12`, `TM 4`
  - later `LB 1,11`, `TM 8`, branch, then `LB 1,12`, `TM 2`
- Those bit tests are immediately followed by short dispatch/helper calls:
  - `CALL 072`
  - `CALL 040`
  - `CALL 025`
  - `CALL 045`
  - `CALL 003`
  - `CALL 014`
- The page also briefly touches `STATE_17` (`1,7`) via `CALL 066`, but it does not look like a field-processing page.
- The tail:
  - `LB 0,15`
  - `CALL 000`
  - `RET`
  suggests a final simple predicate test rather than a long arithmetic path.

Working interpretation:

- Page 23 looks very much like a key-decode or dispatch-boundary page.
- The control flow shape is:
  - first consult `SELECT_STATE` to decide which pending input/dispatch case applies
  - then consult specific bits in `SCAN_STATE`
  - then jump into a small helper/dispatch family
- That makes page 23 a strong candidate for the boundary between:
  - raw scan/key-state bookkeeping
  - functional decode into calculator actions
- It is probably one layer above the physical row scan in page 2, but still below higher-level arithmetic or program-state handling.

Practical consequence:

- The current front-end model now has a usable shape:
  - page 2 = physical display/keypad scan loop
  - `SELECT_STATE` = short-lived pending selector qualifying the next action
  - `SCAN_STATE` = per-scan or per-key-state bits
  - page 23 = early decode/dispatch boundary from scan state into handler families

## Page 24

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1318)

- Page 24 follows page 23 and looks less like decode and more like state update after one handler family has been selected.
- The page touches `SCAN_STATE` (`1,12`) repeatedly:
  - it sets bit `4` early with `SM 4`
  - later it tests `TM 4`
  - later still it clears bit `4` with `RSM 4`
- It also touches:
  - `MODE_STATE_B` (`1,15`) with `SM 8`
  - `WORK_2_14` via `LB 2,14`, `MTA`, `ADX 1`
  - `ANNUNCIATOR` (`1,5`) via `LB 1,5`, `MTA`, `ADX 15`
  - `FLAG_A` through `CALL 020`
  - the bit-clear helper `CALL 045`
- The helper mix is:
  - `CALL 052`
  - `CALL 055`
  - `CALL 064`
  - `CALL 072`
  - `CALL 071`
  - `CALL 025`
- That looks like compact state mutation and bookkeeping, not direct scan-row decoding.

Working interpretation:

- Page 24 is a strong candidate for one concrete post-decode handler path.
- Relative to the current model:
  - page 23 decides which dispatch family applies
  - page 24 performs the immediate bookkeeping for one such family
- The repeated `SCAN_STATE` updates suggest this page acknowledges or advances the current scan/input condition rather than merely inspecting it.
- The simultaneous touch of `MODE_STATE_B` and `WORK_2_14` suggests it also records a higher-level consequence of that input, not just a transient scan bit.

Practical consequence:

- The front-end model now has a clearer pipeline:
  - page 2 = physical scan loop
  - page 23 = early decode boundary
  - page 24 = selected handler bookkeeping / state update
- That makes the page-2 `WORK_2_x` cluster more interesting than before: it is now a plausible short working register family attached to input handling, entry state, or display-side bookkeeping rather than random auxiliary cells.

## Page 25

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1388)

- Page 25 looks like the heavier continuation of the page-24 handler family rather than a separate top-level mode page.
- It opens by loading a fixed `2,7` value through `LBL 2,7`, then immediately writes a fixed pattern of `LM` digits before entering a dense helper sequence.
- The page repeatedly gates its work with `LB 0,13` followed by `TM 8`.
- More importantly, it walks a compact `2,x` block explicitly:
  - `WORK_2_11`
  - `WORK_2_12`, `MTA 2`, `TAM`
  - `WORK_2_13`, `CALL 001`
- That pattern is much stronger evidence than before that the `2,11` through `2,13` cells form a coordinated short working register cluster.
- With `CALL 001` now resolved as a bare `RET` entry, the important part of the `WORK_2_13` sequence is the direct `LB 2,13` itself.
- So page 25 is not calling a hidden helper on `WORK_2_13`; it is selecting that nibble explicitly and then continuing control flow with almost no helper-side work.
- `WORK_2_14` is not touched directly on this page, but page 24 and page 37 still tie `2,14` closely to the same neighborhood.
- The helper mix remains in the same family:
  - `CALL 051`
  - `CALL 052`
  - `CALL 054`
  - `CALL 055`
  - `CALL 025`
  - `CALL 031`
  - `CALL 062`
  - `CALL 045`

Working interpretation:

- Page 25 looks like a substantive working-state update page for the handler family introduced in pages 23 and 24.
- It does not read like display refresh code or pure mode switching.
- The strongest current reading is:
  - page 24 performs immediate scan/control bookkeeping
  - page 25 manipulates a small working register block in page-2 RAM to reflect the decoded input
- Within that block, `WORK_2_13` now looks slightly more latch-like than `WORK_2_12`, because the code selects it directly without relying on a substantive helper body.
- That block could still be:
  - entry-state scratch
  - short display-side working state
  - program/input operand staging
- But it now looks much less likely to be arbitrary one-off scratch RAM.

Practical consequence:

- The `2,11` through `2,14` region should now be treated as a candidate mini-field family rather than isolated cells.
- Page 37 strengthens that reading, because it exposes direct helper entries for `2,12` and `2,14` in the same shared-helper page that already services other fixed RAM families.
- The exact role of each nibble is still unresolved, but the family itself now looks real enough to name provisionally.

## Page 26

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1451)

- Page 26 looks like a cleanup or normalization page sitting immediately after the heavier page-25 working-state update.
- It opens with repeated zero tests on fixed flag cells:
  - `LB 0,12`, `CALL 000`
  - `LB 0,11`, `CALL 000`
- It then repeatedly uses `CALL 074`, the likely field-zeroing wrapper.
- Inside the same page it directly touches `WORK_2_13`:
  - `LB 2,13`
  - `EXC- 2`
  - `EXC-`
- With `CALL 012` and `CALL 014` now narrowed to short page-037 wrappers rather than long routines, the surrounding flow looks even more like local normalization than hidden heavy processing.
- Later it consults `MODE_STATE_B`:
  - `LB 1,15`
  - `TM 8`
- It also uses the same small helper family seen in the surrounding handler pages:
  - `CALL 012`
  - `CALL 014`
  - `CALL 016`
  - `CALL 020`
  - `CALL 031`
  - `CALL 051`
  - `CALL 072`
  - `CALL 074`

Working interpretation:

- Page 26 does not look like primary key decode or primary working-register update.
- It looks more like a finalization step for the same handler family:
  - inspect fixed flags
  - clear or normalize selected state
  - adjust at least one nibble in the `WORK_2_x` family
  - then branch according to a higher-level mode bit in `MODE_STATE_B`
- In that reading, `WORK_2_13` is a plausible "cleanup-sensitive" staging nibble:
  - page 25 selects it directly during working-state update
  - page 26 immediately revisits it during cleanup/finalization
- That makes page 26 a good fit for "commit/reset/normalize after handling one decoded input."

Practical consequence:

- The current front-end/handler pipeline is now:
  - page 23 = decode boundary
  - page 24 = immediate handler bookkeeping
  - page 25 = working-register update
  - page 26 = cleanup/finalization gated by top-level mode state
- This leans the `WORK_2_x` family slightly more toward entry/program-input staging than display refresh, because it is surrounded by mode-gated cleanup logic rather than ongoing scan-loop timing.

## Page-37 hooks for `WORK_2_x`

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L2058)

- Page 37 now gives direct supporting evidence that the `WORK_2_x` family is intentional:
  - one helper path explicitly lands on `LB 2,14`
  - another helper path explicitly lands on `LB 2,12`
- More specifically, the currently traced short calls split this way:
  - `CALL 052` and `CALL 054` are both tiny wrappers that select `WORK_2_14` and branch onward through the overlapped helper fabric
  - `CALL 055` is a short wrapper that routes into the `WORK_2_12` side of the same fabric
  - `CALL 025` is now resolved more tightly: raw operand `025` lands on the page-37 `LB 2,5` entry, then falls through the shared branch chain to an immediate `RET`
  - `CALL 072` is likewise now resolved more tightly: raw operand `072` lands on the page-37 `LB 0,12` entry, then returns immediately through the same short branch chain
- Those entries sit alongside the already-resolved fixed-cell helpers for `ANNUNCIATOR`, `STATE_17`, `FLAG_A`, `FLAG_B`, and `FLAG_C`.
- So the page-037 micro-library is not only servicing the `0,x` and `1,x` control cells; it also exposes fixed-entry support for the `WORK_2_x` family.

Working interpretation:

- That strongly supports treating `WORK_2_11` through `WORK_2_14` as a real serviceable register family in the ROM's design, not just incidental scratch locations hit by a few pages.
- The remaining uncertainty is semantic, not structural:
  - the family is real
  - but we still do not know whether it is best thought of as entry staging, display-side staging, or program-input staging.
- There is now a useful internal split inside the family:
  - `WORK_2_12` is repeatedly used in compare/test style sequences such as `MTA 2` plus `TAM`
  - `WORK_2_14` is repeatedly used in update/progression style sequences such as `LM 7` and `MTA` plus `ADX 1`
  - the short helper calls follow the same split, with `CALL 055` on the `WORK_2_12` side and `CALL 052` / `CALL 054` on the `WORK_2_14` side
  - so `WORK_2_12` currently looks more predicate-like, while `WORK_2_14` looks more update-state-like
  - `CALL 025` reinforces the same pattern, because it explicitly selects `LB 2,5` then `LB 2,14` before returning
  - `CALL 072` reinforces the control-side split, because it explicitly selects `LB 0,12` before returning

Practical consequence:

- `CALL 025` and `CALL 072` are not heavy workers.
- They are tiny fixed-selector entries in page 37:
  - `CALL 025` = select the `2,5` / `2,14` side and return
  - `CALL 072` = select `FLAG_A` (`0,12`) and return
- That makes the surrounding pages easier to read:
  - when page 24, 25, 32, 34, or 35 call `CALL 025`, the important semantic action is usually the fixed RAM selection, not hidden computation in the callee
  - when they call `CALL 072`, they are most likely refreshing or consulting the `FLAG_A` side of the shared state fabric before continuing local logic

## Small transcendental-side implication

- This does not identify `ln`, `exp`, or trig routines directly.
- It does remove one misleading possibility: the dense `CALL 025` / `CALL 072` traffic in pages 20, 24, 25, 32, 34, and 35 is not evidence of deep transcendental subroutines.
- Instead, those pages are repeatedly binding fixed working cells or fixed flag cells and then doing most of the real work inline or through nearby tiny helpers.
- For the transcendental investigation, that shifts the search target away from "mystery helper bodies" and toward:
  - inline digit loops
  - staged literal/template loads
  - pages that combine page-36 arithmetic kernels with those fixed-cell selectors

Follow-up helper collapse:

- A few more apparently important calls also turn out to be tiny:
  - `CALL 035` lands directly on a page-37 `RET`
  - `CALL 053` lands on a page-37 `GO 075`, which immediately reaches `RET`
  - `CALL 076` lands on a short page-37 sequence equivalent to `LG 0`, then the `CALL 072` / `FLAG_A` selection path
- So several pages that initially looked "call-heavy" are even more inline than they first appeared.
- This is especially relevant for page 32 and page 35:
  - their visible `LM` templates and inline arithmetic are now better evidence than their helper-call counts
  - the transcendental search should therefore stay focused on visible constant/template stamping plus inline digit kernels

## Page 32 as a stronger numeric candidate

Reference: [analysis/sinclaircambridgeprogrammable.disasm.txt](/Users/dan/Sinclair/analysis/sinclaircambridgeprogrammable.disasm.txt#L1725)

- Page 32 now looks more promising as a real numeric worker page than the surrounding entry/scan pages.
- The helper collapse matters here because several of its calls are now known not to hide substantial logic:
  - `CALL 053` is effectively a structural return path
  - `CALL 076` is only a tiny `LG 0` plus `FLAG_A` selector
  - `CALL 025` is only fixed `2,5` / `2,14` selection
- That leaves the visible inline body carrying more of the semantic weight.

Visible page-32 structure:

- It stamps a conspicuous literal pattern:
  - `LM 5`
  - `LM 7`
  - `LM 8`
  - `LM 9`
  - `LM 9`
  - `LM 9`
  - later another `LM 8`
- It also contains the strongest inline subtract kernel currently identified:
  - `SC`
  - `MTA 2`
  - `SUB`
  - `ADX 10`
  - `EXC+ 2`
  - branch/return
- That kernel is not just incidental straight-line code.
- Page 32 also contains a local `CALL 032` entry that lands directly on this subtract/compare step, so the page appears to package it as a small internal worker rather than only using it once inline.
- Important addressing caution:
  - `CALL 032` in some other page is not a call into page 32
  - it is just that page's own raw-word-`032` local entry
  - so the evidence here is about page 32's internal modularity, not about broad cross-page reuse of its worker
- And it gates that arithmetic with control checks on `MODE_STATE_C` (`1,13`) and `0,11`.

Working interpretation:

- Page 32 still does not look like a complete user-visible transcendental routine by itself.
- But it now looks more like a compact numeric sub-worker that:
  - stamps a fixed decimal template
  - then runs a digit-wise subtract/compare step over it
  - with that compare step callable as its own tiny local worker inside the page
- That is a better fit for:
  - range checking
  - constant comparison
  - decimal normalization against a fixed threshold
than for plain input bookkeeping.

Practical consequence:

- If `ln` / `exp` really do use fast paths around powers of ten or decimal normalization, page 32 is one of the better current places to look for that support logic.
- The template-heavy pages now separate roughly this way:
  - page 20 = still biased toward format/packing or staged normalization
  - page 25 / 26 = still biased toward handler-state staging
  - page 32 = strongest current candidate for compact numeric compare/normalize support

Further constraint from the visible template:

- The page-32 stamped digits do not look like an obvious direct transcendental constant in the raw visible order.
- The sequence is dominated by `8` and `9`:
  - `5, 7, 8, 9, 9, 9, 9`
  - then a later `8`
- So, at least in the visible write order, it does not read cleanly as:
  - `ln(10)`
  - `pi`
  - `pi/2`
  - `pi/4`
  - or another familiar short scientific constant
- That weakens the case that page 32 is directly embedding a named transcendental constant for final evaluation.
- It strengthens a different reading:
  - page 32 may be stamping a near-boundary decimal threshold or normalization template
  - then subtracting against it as part of a compare/range-reduction step
- In other words, page 32 currently looks more like support for decimal thresholding than like the final approximation kernel itself.

Practical consequence:

- The current best transcendental split is:
  - page 32 = compare/threshold or normalization support
  - some other page still has to perform the actual approximation or repeated refinement
- That remains consistent with the behavioral clue from the real calculator:
  - `ln(1)`, `ln(10)`, and `ln(0.01)` are fast
  - so there is likely a quick exponent/threshold path before any slower approximation loop

Additional real-machine square-root clue:

- The square-root function now shows a similarly revealing timing split:
  - `sqrt(4)` is fast
  - `sqrt(9)` is fast
  - `sqrt(0.25)` is fast
  - `sqrt(2.56)` is pretty fast
  - `sqrt(0.26)` is much slower
- That matters because it does not fit a purely exponent-based shortcut alone.
- The stronger pattern now is that the fast cases include exact decimal squares across more than one magnitude:
  - `4`
  - `9`
  - `0.25`
  - `2.56`
- A better reading than "hard-coded perfect-square special cases" is:
  - the routine probably normalizes the argument very cheaply
  - then applies a tiny decimal iteration or refinement step
  - inputs with especially simple normalized mantissas converge almost immediately
- On that reading:
  - `0.25` and `2.56` are fast because they normalize to especially simple exact-square mantissas
  - `0.26` is slower because it does not
- Safest current reading:
  - square root likely has a quick decimal normalization stage
  - then a tiny refinement method whose exact-square or near-trivial cases terminate very early
  - with slower iterative work only for harder residual mantissas
- This makes the emerging transcendental strategy look less uniform:
  - `ln` / perhaps `exp` exploit decimal-order shortcuts around powers of ten
  - `sqrt` appears to exploit very fast convergence on simple normalized mantissas
  - slower approximation or refinement is reserved for the harder residual cases
- That strengthens the case that the compact compare/template machinery around page 32 may support more than one scientific fast path, not just `ln` / `exp`.

Implication for page 32:

- This square-root timing split makes page 32's current profile look even more useful:
  - stamp a fixed decimal template
  - run a compact digit-wise subtract/compare kernel
  - expose that kernel through a tiny local `CALL 032` entry
  - return quickly if the threshold test succeeds
- That is still not enough to identify page 32 as "the sqrt routine."
- But it is a good fit for the kind of reusable scientific fast-path worker that could answer questions such as:
  - is the mantissa at or exactly on a special boundary?
  - is the input one of a small set of trivial or near-trivial cases?
  - can the ROM bypass the slower refinement loop?
- So the current best reading of page 32 is now broader:
  - not just `ln` / `exp` support
  - but compact threshold/compare support for multiple scientific fast paths.

Arithmetic-density constraint:

- A broader pass over the ROM now suggests that visible digit arithmetic is surprisingly sparse outside page 36.
- The main inline hits are:
  - page 32: the strong subtract/borrow loop
  - page 20: the weaker `MTA` / `ADX 6` decimal-adjust-looking fragment
  - page 2: several arithmetic-looking instructions, but embedded in confirmed display/scan logic
- That matters because it argues against there being many large, obvious inline approximation kernels spread around the ROM.
- Instead, the current best reading is:
  - page 36 concentrates the real digit-arithmetic primitives
  - page 32 provides at least one visible threshold/compare worker on top of them
  - many other pages are mostly state selection, field binding, and staging rather than exposed numeric iteration

Practical consequence:

- The eventual `ln` / `exp` / trig approximation loops may be structurally small and heavily interleaved with:
  - field-walk helpers such as `CALL 057`
  - fixed-cell selectors in page 37
  - template stamping and normalization checks
- So the next useful search criterion is not just "find ADD or SUB."
- It is:
  - find pages with repeated revisits to the same numeric field
  - little or no `SELECT_STATE` / `SCAN_STATE` traffic
  - and nearby threshold/template setup like page 32

Low-control-page pass:

- A quick page-level pass over pages 20 through 35 suggests the lowest-control-traffic candidates are:
  - page 27
  - page 32
  - page 33
  - page 34
- But page 33 is immediately disqualified as a transcendental worker candidate because it contains `TKB` and clearly remains tied to scan/input flow.
- That leaves:
  - page 27
  - page 32
  - page 34
as the most interesting numeric-adjacent pages outside page 36 itself.

Current split among those pages:

- Page 32 remains the strongest compare/threshold page:
  - visible template stamping
  - the clearest inline subtract/borrow kernel
  - limited direct scan-state traffic
- Page 27 now looks more like a control-heavy normalization coordinator:
  - many fixed-flag touches on `0,11`, `0,12`, `0,13`, `0,14`
  - small data movement through `MTA`, `ATB`, `MTA 1`, `TC`
  - but no equally clear inline subtract/add kernel
- Page 34 looks like a mixed bridge page:
  - small arithmetic/comparison fragments such as `AD`, `COMP`, `EXC-`
  - but still substantial interaction with `MODE_STATE_B`, `SELECT_STATE`, and the flag cells
  - so it currently looks more like a mode-gated numeric/control bridge than a pure approximation loop
  - it also contains the cleanest non-reset annunciator write currently identified:
    - after local setup and a direct `MODE_STATE_C bit 8` test
    - it reaches `LB 1,5 ; LM 4 ; RET`
    - the nearby `CALL 034` in the same page should not be read as "call page 34"; it is a raw page-037 helper entry
  - so at least one page-34 path is best read as "enter a specific annunciator state" rather than as ordinary numeric work

Practical consequence:

- The best current numeric-worker chain is:
  - page 32 = threshold/compare support
  - page 27 and/or page 34 = surrounding normalization / control bridge
  - page 36 = digit-arithmetic primitives
- That is compatible with a tiny-ROM transcendental design where:
  - a fast path first normalizes or thresholds the decimal argument
  - then a very small refinement loop runs through shared page-36 primitives
  - without ever exposing a long, clean, self-contained "transcendental page"

Concrete path check:

- A closer read of the page-32 neighborhood does not show a clean handoff into a large numeric-field refinement loop.
- Page 32 itself does contain a real local loop:
  - it reaches the inline subtract sequence
  - then `GO 076` returns control to the top-side setup path in the same page
- But the nearby candidate bridge pages still mostly revisit flag cells rather than a long numeric field:
  - page 27 repeatedly revisits `0,11`, `0,12`, `0,13`, `0,14`, and `0,15`
  - page 34 likewise keeps circling through `0,11`, `0,12`, `0,14`, `0,15` and mode cells such as `1,15`
- So the current evidence does not support:
  - page 32 feeding directly into a long mantissa-iteration page on 27 or 34
- It supports a narrower reading:
  - page 32 performs a compact threshold/compare step locally
  - pages 27 and 34 coordinate flags and mode/state consequences around that step

Practical consequence:

- If there is a true approximation loop for `ln` / `exp` / trig, it is probably even smaller and more distributed than expected.
- The best remaining hypothesis is:
  - page 32 provides a decimal thresholding primitive
  - page 36 provides the digit-arithmetic primitive
  - higher functions compose those with field-walk helpers rather than branching into one obvious long numeric page

Rare `3,x`-field clue:

- One other small clue now stands out: the ROM almost never touches `3,x` RAM at all.
- The only clear `3,x` accesses currently visible are:
  - page 6: `LB 3,15`, `MTA 3`, `EXC- 3`
  - page 30 tail: `LB 3,15`, `EXC 3`, `EXC 3`
- That rarity argues that `EXP_STATE` (`3,15`) is not an ordinary working digit in the same sense as the repeatedly serviced `0,x`, `1,x`, and `2,x` clusters.
- Safest current reading:
  - `EXP_STATE` (`3,15`) is a special-purpose cell or very short field
  - likely tied to a rarely used formatting/state role rather than the main scan or entry bookkeeping
- Given the user-visible `EE` key and the importance of decimal-order handling to the observed fast `ln(10^n)` behavior, `EXP_STATE` is now a plausible candidate for:
  - exponent-sign or order-of-magnitude staging
  - or some adjacent display-format state serving the same purpose
- That is still conjectural, but it is a better use of the evidence than treating the `3,x` bank as ordinary scratch RAM.

Practical consequence:

- The exponent or scientific-notation fast path may not live entirely inside the already named `WORK_2_x` family.
- A small special-purpose cell such as `EXP_STATE` may participate when the machine switches into `EE`-style or decimal-order-sensitive behavior.

Backward reachability of the `EXP_STATE` paths:

- The two visible `EXP_STATE` paths are not generic utility code. Both are gated by control-state logic before they are reached.

- Page 6 path:
  - page 6 first checks `MODE_STATE_C` (`1,13`) bit 8
  - then manipulates `FLAG_A` (`0,12`) bit 2
  - then passes through tests on `ANNUNCIATOR` (`1,5`) and `SELECT_STATE` (`1,11`)
  - only after that does it reach:
    - `LB 0,15`
    - `LB 3,15` (`EXP_STATE`)
    - `MTA 3`
    - `EXC- 3`
- Safest reading:
  - the page-6 `EXP_STATE` access is part of a mode-qualified special case, not general arithmetic housekeeping
  - and of the two visible `EXP_STATE` paths, page 6 looks more like the "read or update the special state itself" side, because it actually transfers through `MTA 3`

- Page 30 tail:
  - page 30 is wrapped around `SELECT_STATE` (`1,11`) and `SCAN_STATE` (`1,12`) tests
  - it also consults `MODE_STATE_C` (`1,13`) and a small `LBL 7,5` template site
  - earlier in the same page it also touches:
    - `LB 0,5` with `ATB` / `MTA` / `ADX 15`
    - `LB 1,5` (`ANNUNCIATOR`) with `TAM`
  - only at the tail does it reach:
    - `LB 3,15` (`EXP_STATE`)
    - `EXC 3`
    - `EXC 3`
- Safest reading:
  - the page-30 `EXP_STATE` path is also a branch-selected special case
  - and page 30 as a whole now looks more like a special formatting or display-state path than like ordinary numeric processing
  - because it couples the main `0,5` field, `ANNUNCIATOR`, and `EXP_STATE` in one compact branch-selected region
  - of the two visible `EXP_STATE` paths, page 30 looks more like the "integrate special state into display/format state" side, because it couples `EXP_STATE` with the live number field and annunciator rather than just touching it in isolation

Practical consequence:

- This strengthens the earlier conjecture:
  - `EXP_STATE` is likely associated with a rare user-visible state such as `EE`-style exponent entry, decimal-order formatting, or a comparable scientific-mode special case
  - not with the calculator's ordinary mantissa field

Where the `EXP_STATE` gating bits are set:

- The two gating conditions followed here were:
  - `MODE_STATE_C` (`1,13`) bit 8
  - `SELECT_STATE` (`1,11`) bit 1

`SELECT_STATE` bit 1:

- The visible `SM 1` sites for `1,11` are sparse:
  - reset/page 0 sets bit 8 in `1,11`, not bit 1
  - page 3 sets `SM 1` after a `CALL 011` / `TM 2` path
  - page 6 sets `SM 1` immediately after the `LB 3,15` / `MTA 3` / `EXC- 3` sequence
  - page 27 sets `SM 1` in its flag-normalization path
  - page 30 sets `SM 1` very early
- Safest reading:
  - `SELECT_STATE` bit 1 currently looks like a latched consequence of entering a special path, not the primary root cause of that path
  - so it is probably not, by itself, the direct "EE key pressed" marker

`MODE_STATE_C` bit 8:

- `SM 8` on `1,13` appears in several places, but they are not all equally informative:
  - reset/startup logic touches the wider control area very early
  - page 21 and page 22 explicitly toggle bit 8 in compact staging-heavy paths
  - page 35 gates heavily on `TM 8`
- Of these, page 22 is the most interesting for the current hypothesis:
  - it toggles `MODE_STATE_C` bit 8 repeatedly
  - it is tied to `SCAN_STATE` and the `WORK_2_12` side of the staging family
  - it already looked more like entry/edit-state movement than like generic numeric work
- Safest current reading:
  - `MODE_STATE_C` bit 8 is a real special-entry or special-edit latch
  - and page 22 is one of the stronger candidates for where that latch is asserted/cleared in response to a decoded key path

Practical consequence:

- The evidence is still short of proving an `EE` mapping.
- But the current best structural hypothesis is:
  - page 22 helps establish or clear a special entry latch in `MODE_STATE_C`
  - page 6 and page 30 then consume that special-entry state and touch `EXP_STATE`
  - which is consistent with `EXP_STATE` participating in exponent/order-of-magnitude entry rather than ordinary mantissa handling

Likely page-23 decode split feeding page 22 versus page 24:

- The decode boundary on page 23 still does not expose a simple symbolic key map.
- But its two main `SCAN_STATE` tests are asymmetrical in a useful way:
  - one branch family is built around `LB 1,12 ; TM 4`
  - the other is built around `LB 1,12 ; TM 2`

- The surrounding caller pages now line up with that asymmetry:
  - page 24 is strongly organized around `SCAN_STATE` bit 4 bookkeeping
    - it sets bit 4
    - tests bit 4
    - later clears bit 4
    - and updates `WORK_2_14` plus `MODE_STATE_B`
  - page 22, by contrast, opens on `TM 2` and repeatedly toggles `MODE_STATE_C` bit 8
    - it looks like special entry/edit-state handling rather than generic post-key bookkeeping

- So the safest current decode-side reading is:
  - page 23's `TM 4` side most likely feeds the page-24 handler family
  - page 23's `TM 2` side is the better current candidate for feeding the page-22 special-latch path

Practical consequence:

- This does not yet identify the physical key.
- But it does narrow the hunt:
  - the rare `EXP_STATE` / possible exponent-order path is more likely to originate from the `SCAN_STATE bit 2` decode family than from the `SCAN_STATE bit 4` family
  - the `TM 4` family now looks more like ordinary post-decode bookkeeping, while the `TM 2` family looks more like the path that establishes special entry state

Page-2 keypad-column clue:

- The page-2 scan loop now suggests a more concrete interpretation of `SCAN_STATE` bits.
- After `TKB`, page 2 runs a tight bit-decode ladder:
  - `TM 1`
  - `TM 2`
  - `TM 4`
  - `TM 8`
  with `ADX 1` steps between them
- Given the hardware note that the keyboard matrix has exactly four input columns:
  - `K1`
  - `K2`
  - `K3`
  - `K4`
- the simplest and strongest current reading is:
  - `SCAN_STATE` bit `1` = `K1`
  - `SCAN_STATE` bit `2` = `K2`
  - `SCAN_STATE` bit `4` = `K3`
  - `SCAN_STATE` bit `8` = `K4`
- That is a better fit than treating the four bits as unrelated software states, because the page-2 loop is visibly doing a one-of-four post-`TKB` decode.

Consequence for the key hypothesis:

- If `SCAN_STATE bit 2` really is the `K2` column, then the page-23 `TM 2` family is not a single key.
- It is the whole `K2` column:
  - `6`
  - `7`
  - `8`
  - `9`
  - `EE`
- That still materially helps:
  - `EE` lives in `K2`
  - while the competing page-24 / `TM 4` family would correspond to `K3`, which holds `=`, `-`, `/`, `+`, `x`
- So the currently favored special-entry path lines up with the only column that actually contains the `EE` key.

Practical consequence:

- This is not yet a unique `EE` identification, because `K2` also contains ordinary digits.
- But it is the strongest hardware-consistent evidence so far in favor of the exponent-entry hypothesis:
  - the special-latch path now points to the correct keypad column for `EE`
  - while the competing `TM 4` path points to the arithmetic-operator column instead

Row-resolution status:

- I do not yet have a clean row mapping for the same path.
- The page-2 code clearly contains row/scan progression, but it is mixed together with:
  - display-driver sequencing
  - `LG`-selected branch targets
  - and the `ADX` ladder that appears to walk the post-`TKB` decode
- So unlike the column side, the row side is not yet exposed as a simple one-of-five symbolic test in the visible code.

What can be said safely:

- The special path is now narrowed to the `K2` column.
- In the hardware matrix, the `K2` column contains:
  - `6`
  - `7`
  - `8`
  - `9`
  - `EE`
- So the current evidence does not isolate `EE` specifically.
- But it does rule out the competing operator-heavy `K3` column for this special-latch path.

Practical consequence:

- The exponent-entry hypothesis is now stronger at the column level but still unresolved at the row level.
- The next likely way to break the tie is not more static page-2 reading by itself.
- It is to correlate the special-latch path against a row-sensitive downstream effect, for example:
  - which `K2` key family reaches `EXP_STATE`
  - or which `K2` key family bypasses ordinary digit-entry handling

Downstream split: ordinary `K2` digit handling versus the rare `EXP_STATE` path

- That comparison now points in a useful direction.

- The ordinary decoded-input family on pages 24 through 26 is heavily built around the `WORK_2_x` staging block:
  - `LB 2,11`
  - `LB 2,12`, `MTA 2`, `TAM`
  - `LB 2,13`
  - `LB 2,14`
  - `CALL 052`, `CALL 054`, `CALL 055`, `CALL 064`, `CALL 025`
- That is exactly the family already suspected to represent ordinary entry/update staging.

- By contrast, the rare `EXP_STATE` paths on page 6 and page 30:
  - do not visibly walk the `WORK_2_11` through `WORK_2_14` family
  - do not use the dense `MTA 2` / `TAM` compare-consume pattern seen in pages 24 to 26
  - instead use short special-case operations around `EXP_STATE` plus control/flag gating

Safest reading:

- The `EXP_STATE` path is structurally different from ordinary digit-entry handling.
- That means the special `K2`-column path is less likely to be one of the ordinary numeric keys `6`, `7`, `8`, or `9`, because those would be expected to feed into the same `WORK_2_x` staging machinery as other normal entry operations.
- It therefore makes `EE` the strongest remaining candidate inside the `K2` column.

Practical consequence:

- This is still an inference, not a proof.
- But the current evidence stack is now coherent:
  - column-level mapping points to `K2`
  - the rare path bypasses the normal digit-entry staging family
  - `EE` is the only non-digit special-entry key in that column
- So `EE` is now the best working identification for the special-latch / `EXP_STATE` path.

## `EE` / exponent-entry path

This is the current best focused hypothesis for scientific-entry handling. It is still provisional, but it is now supported by several independent pieces of evidence.

Observed user behavior:

- On the real machine, `ln(1)`, `ln(10)`, and `ln(0.01)` are fast.
- That strongly suggests a decimal-order fast path rather than one uniformly slow transcendental approximation path.

Rare state cell:

- `EXP_STATE` (`3,15`) is almost the only visibly used `3,x` RAM cell in the ROM.
- Its two clear access sites are rare, gated, and special-case shaped:
  - page 6: `LB 3,15`, `MTA 3`, `EXC- 3`
  - page 30 tail: `LB 3,15`, `EXC 3`, `EXC 3`
- That makes `EXP_STATE` a plausible exponent/order-of-magnitude or scientific-entry state cell rather than ordinary scratch RAM.

Latch and control path:

- `MODE_STATE_C` (`1,13`) bit 8 is currently the best candidate for the special-entry latch.
- Page 22 is the strongest current candidate for setting or clearing that latch:
  - it opens on a `TM 2`-driven path
  - repeatedly toggles `MODE_STATE_C` bit 8
  - and looks more like entry/edit-state handling than generic numeric processing
- Page 6 and page 30 then appear to consume that special-entry state and touch `EXP_STATE`.

Keypad correlation:

- The page-2 post-`TKB` `TM 1/2/4/8` ladder is best read as a keypad-column decode:
  - bit 1 = `K1`
  - bit 2 = `K2`
  - bit 4 = `K3`
  - bit 8 = `K4`
- The special-latch path is currently associated with the `TM 2` family, which points to `K2`.
- The hardware matrix puts these keys on `K2`:
  - `6`
  - `7`
  - `8`
  - `9`
  - `EE`

Why `EE` is currently favored:

- Ordinary decoded entry on pages 24 through 26 is routed through the dense `WORK_2_x` staging family.
- The rare `EXP_STATE` path on pages 6 and 30 bypasses that ordinary digit-entry machinery.
- That makes the path much less likely to correspond to ordinary numeric keys `6`, `7`, `8`, or `9`.
- Inside the `K2` column, `EE` is therefore the strongest remaining candidate.

Current best working model:

- page 23 `TM 2` decode family
- page 22 special-entry latch handling
- `MODE_STATE_C` bit 8 as the special-entry latch
- page 6 / page 30 rare `EXP_STATE` handling
- likely user-visible meaning: `EE` or a very closely related exponent/order-entry mode

Caution:

- This is still not a proof-level decode.
- The row part of the key mapping is not yet isolated statically from page 2 alone.
- So `EE` should still be treated as the best working identification, not a final confirmed label.

## Provisional RAM Labels

These labels are working names only. They are meant to reduce ambiguity in the notes, not to claim fully verified semantics.

- `FLAG_A` = `0,12`
  - Basis:
    - `CALL 020` appears to load this cell.
    - It is used by several short page-037 status helpers.
  - Working use:
    - general status/flag nibble, exact bit meanings unknown.
- `FLAG_B` = `0,14`
  - Basis:
    - `CALL 016` appears to load this cell, clear carry, and continue through shared status logic.
  - Working use:
    - status/flag nibble involved in branch/control decisions.
- `FLAG_C` = `0,15`
  - Basis:
    - `CALL 045` appears to end up clearing bit 2 in a fixed cell selected through this path.
  - Working use:
    - status/flag nibble with at least one frequently cleared control bit.
- `ANNUNCIATOR` = `1,5`
  - Basis:
    - `CALL 011` loads this cell.
    - `CALL 041` begins by loading `1,5` into `A` and branching into shared status logic.
    - reset/startup writes `LM 11` to this cell, and page 34 writes `LM 4`, which fits a symbol-code register much better than an ordinary mantissa digit.
  - Working use:
    - leftmost display-annunciator code or closely related overlay-state cell.
- `STATE_17` = `1,7`
  - Basis:
    - `CALL 066` loads this cell.
  - Working use:
    - another fixed state cell, probably paired with the same control family as `ANNUNCIATOR`.
- `SELECT_STATE` = `1,11`
  - Basis:
    - reset touches `1,11` immediately and sets bit `8`
    - pages 4, 7, 23, 30, and 34 load `1,11`, test or modify a bit, and branch immediately
    - page 6 sets bit `1` in `1,11`
  - Working use:
    - compact selector or pending-state latch associated with scan/input dispatch rather than numeric storage.
  - Stronger current reading:
    - this cell looks more transient than `MODE_STATE_C`, `MODE_STATE_A`, or `MODE_STATE_B`
    - it is likely used to qualify dispatch or entry flow rather than to store a full calculator mode by itself.
- `STEP_LO` = `1,8`
- `STEP_HI` = `1,9`
  - Basis:
    - page 5 repeatedly alternates between `1,8` and `1,9`
    - the manual exposes program step numbers `00` through `35`
    - the page-5 control flow looks much more like bookkeeping than arithmetic
  - Working use:
    - likely the low/high decimal digits of the current program step, or very closely related program-control counters.
- `MODE_STATE_A` = `1,14`
  - Basis:
    - page 1 uses `1,14` in early guard/setup logic before field normalization
    - page 5 compares `1,14` directly against `STEP_LO`
    - later pages use `1,14` in branch-heavy, non-numeric control contexts
  - Working use:
    - mixed control/state nibble, likely paired with `MODE_STATE_B`.
    - may temporarily carry digit-like entry state in some program-control paths.
- `MODE_STATE_B` = `1,15`
  - Basis:
    - page 1 uses `1,15` in the same opening guard logic as `1,14`
    - page 5 compares `1,15` directly against `STEP_HI`
    - many later pages use `1,15` around `TM 4`, `TM 8`, `SM 8`, `CALL 045`, and `CALL 000`
  - Working use:
    - mixed control/state nibble with several directly tested or manipulated status bits.
  - Stronger current reading:
    - bit `8` is especially important, because it is repeatedly tested with `TM 8` and explicitly changed with `SM 8` / `RSM 8`
    - bit `4` is also tested repeatedly with `TM 4`
    - so `MODE_STATE_B` is likely not a general data cell but a compact control register whose upper bits encode major mode or submode state
    - however, page 5 shows that the cell also participates in direct value comparison against `STEP_HI`, so it is probably not a pure bitfield-only register.
- `MODE_STATE_C` = `1,13`
  - Basis:
    - page 0 touches `1,13` immediately during reset/setup
    - page 3 tests `1,13` with `TM 8` and `TM 4`
    - page 21 sets bit `8` in `1,13`
    - page 31 sets and later tests bit `4` in `1,13`
    - page 35 opens by testing bit `8` in `1,13`
  - Working use:
    - compact control-state latch in the same cluster as `MODE_STATE_A` and `MODE_STATE_B`.
  - Stronger current reading:
    - this cell currently looks more like a pure bitfield register than `MODE_STATE_A` or `MODE_STATE_B`
    - its most obvious role is gating control flow by tested bits rather than holding decimal-like temporary state.
- `SCAN_STATE` = `1,12`
  - Basis:
    - page 2 loads `1,12` immediately before `TKB` and a `TM 1/2/4/8` bit-test cascade
    - many later pages also load `1,12` in branch-heavy scan/state contexts
  - Working use:
    - likely a scan-related or key/debounce-related state nibble rather than a numeric data digit.
- `EXP_STATE` = `3,15`
  - Basis:
    - `3,x` RAM is almost untouched elsewhere in the ROM
    - the only clear visible accesses are the rare gated paths on page 6 and page 30
    - those paths are currently the best candidates for `EE` / exponent-entry-related handling
  - Working use:
    - likely a small special-purpose exponent/order-of-magnitude or scientific-entry state cell.
  - Caution:
    - this is still a stronger-than-neutral label and should be treated as a working hypothesis, not a proven semantic name.
- `WORK_2_11` = `2,11`
- `WORK_2_12` = `2,12`
- `WORK_2_13` = `2,13`
- `WORK_2_14` = `2,14`
  - Basis:
    - pages 24 and 25 treat `2,11` through `2,14` as a coordinated working cluster rather than isolated cells
    - page 25 explicitly walks `2,11`, `2,12`, and `2,13`
    - page 24 touches `2,14` inside the same post-decode state-update path
    - page 37 exposes direct helper entries involving `2,12` and `2,14`
  - Working use:
    - compact page-2 working-register family associated with post-decode input handling.
  - Stronger current reading:
    - this family is likely tied to entry/display/program-input staging
    - but the evidence is not yet strong enough to split those four cells into semantic labels beyond neutral `WORK_2_x`.
  - Useful local distinction:
    - `WORK_2_13` currently looks slightly more latch-like or cleanup-sensitive than the rest of the family
    - it is touched directly in page 25 and then revisited directly in page 26 during finalization
    - unlike `WORK_2_12` and `WORK_2_14`, it is not yet associated with a substantive dedicated page-037 helper entry.
    - `WORK_2_12` currently looks more compare/predicate-oriented, because page 24 and page 25 both use it with `MTA 2` and `TAM`
    - `WORK_2_14` currently looks more update/progression-oriented, because page 1 and page 24 use it with `LM 7` or `MTA` plus `ADX 1`, and page 37 gives it multiple direct helper entries.
- `FIELD_5_15` = `5,15`
- `FIELD_7_4` = `7,4`
- `FIELD_6_4` = `6,4`
- `FIELD_5_4` = `5,4`
  - Basis:
    - page 1 loads each of these with `LBL` and then immediately applies `CALL 057`, the field-walk helper.
  - Working use:
    - four standard working fields normalized together during early setup.

These names are intentionally neutral. The next stage is to replace them, where possible, with behavior-level labels such as "program counter field", "shift flags", "display buffer field", or "entry scratch field".

## Shared helper entry points

These are page-037 targets that already look central:

- `CALL 000`: now specifically looks like a zero-test on the current RAM digit.
- `CALL 011`: now looks like a fixed RAM-pointer loader rather than a full helper routine.
- `CALL 020`: now also looks like a fixed RAM-pointer loader, probably for field `0,12`.
- `CALL 024`: now looks like an alias entry into `CALL 045`.
- `CALL 045`: now looks like a shared bit-clear helper on a fixed status cell.
- `CALL 057`: now looks like a repeated field-walk helper over consecutive digits, not a one-shot operation.
- `CALL 064`, `CALL 066`, `CALL 074`: common utility calls used by several later pages.

Several of these now also have direct semantic labels in the generated named
listing, including:

- `TEST_CURRENT_DIGIT_ZERO`
- `LOAD_FLAG_A_PTR`
- `WALK_MAIN_FIELD`
- `ZERO_MAIN_FIELD`
- `RIPPLE_INCREMENT_FROM_CURRENT_PTR`
- `ZERO_FROM_CURRENT_PTR`
- `SUBTRACT_WITH_BORROW`

These names are still provisional. They should become labels only after tracing the corresponding page-037 code.

## Priority next steps

- Trace page-037 entry points `000`, `011`, `020`, `024`, `057`, `064`, `066`, and `074`.
- Name the RAM cells referenced by the page-1 `LBL` table.
- Confirm page-2 digit/key scan behavior against the keypad matrix and DS8874 wiring.
- Distinguish startup-only code from the steady-state calculator scan loop.
