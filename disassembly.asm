
; PAGE 0 

; Special characters: F, G, E, -.
; Don't know which is which yet.
; Last bit of M[0x1c] determines leftmost display

; 0x15    seems to be location of decimal point??? (see 0220)
; 0x15.1  seems to determine that we're entering goto target (see 0346)
; 0x15.2  ?
; 0x17.2  program entry mode
; 0x17.4  ?
; 0x17.8  setting high digit of goto target SETTING_GOTO_HI_8
; 0x1c.4  is keypad ready flag
; 0x5*, 0x6*, 0x7*
          36 step program
; 0x74    current instruction
;
  0000 @0000  245  CALL           CLEAR_REGISTER_2 ; Clear 2:0 to 2:f
P00_W040:
  0001 @0040  035  LB MEM_1D
  0002 @0020  271  CALL           ZERO_FROM_CURRENT_PTR ; Clear 1:0 to 1:d
  0003 @0010  237  CALL           LOAD_B_4C           ; Clear 4:0 to 4:c
  0004 @0004  271  CALL           ZERO_FROM_CURRENT_PTR
P00_W002:
  0005 @0002  256  CALL           COPY_REGISTER_2_TO_0
P00_W041:
  0006 @0041  033  LB MEM_1B
  0007 @0060  112  SM 8            ; M[MEM_1B] |= 8
P00_W030:
  0010 @0030  017  LB MEM_0F     
  0011 @0014  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  0012 @0006  367  GO             P00_W067; jump if M[0x0f] != 0
  0013 @0043  016  LB MEM_0E     
  0014 @0021  107  TM 8          
  0015 @0050  367  GO             P00_W067 ; jump if (M[0x1e] & 8) != 0
  0016 @0024  015  LB FLAG_013   
  0017 @0012  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  0020 @0045  361  GO             P00_W061 ; jump M[0x13] != 0
LOOP1:
  ; This block stores 11 - M[0x0e] in M[0x15] when result is >= 0
  ; also zeros out M[0x0e]
  ; Places decimal point
  0021 @0062  060  0TA           
  0022 @0071  016  LB MEM_0E     
  0023 @0074  007  EXC           ; M[0x0e] = 0
  0024 @0036  040  COMP          ; A = old -M[0x0e] - 1
  0025 @0057  134  ADX 12        ; 11 - old M[0x0e] ; This is where fateful 0x0b comes from!
  0026 @0027  032  LB MEM_15     ; skip if old M[0x0e] >= 12
  0027 @0013  007  EXC           ; M[0x15] <- 11 - old M[0x0e] when old M[0x0e] <= 11
  0030 @0005  143  LG             LGGO   P30_W060
  0031 @0042  160  DATA    1,60
P00_W061:
  0032 @0061  016  LB MEM_0E     
  0033 @0070  106  TM 4          
  0034 @0034  367  GO             P00_W067 ; jump if (M[0x1e] & 4) != 0
  0035 @0016  104  TM 1          
  0036 @0047  210  CALL           SHIFT_LEFT_MEM_0B ; call if (M[0x1e] & 1) != 0
  0037 @0023  016  LB MEM_0E   
  0040 @0011  105  TM 2          
  0041 @0044  351  GO             IF_MEM_0E_AND_2 ; if (M[0x1e] & 2) != 0
  0042 @0022  332  GO             IF_NOT_MEM_0E_AND_2 ; if (M[0x1e] & 2) == 0
IF_MEM_0E_AND_2:
  0043 @0051  210  CALL           SHIFT_LEFT_MEM_0B
  0044 @0064  210  CALL           SHIFT_LEFT_MEM_0B
IF_NOT_MEM_0E_AND_2:
  0045 @0032  015  LB FLAG_013
  0046 @0055  160  LM 0           M[0x13] <- 0
  0047 @0066  160  LM 0           M[0x14] <- 0
  0050 @0073  362  GO             LOOP1
P00_W035:
  ; A == current instruction
  0051 @0035  013  LB MEM_0B   
  0052 @0056  007  EXC            ; M[0x11] <- current instruction
P00_W067:
  0053 @0067  211  CALL           LOAD_MEM_15
  0054 @0033  116  SM 2          
  0055 @0015  147  LG             LGCALL WEIRD_SHUFFLE
  0056 @0046  200  DATA    2,00
  0057 @0063  032  LB MEM_15 ; reset writes the default MEM_15 code; likely blank or neutral
  0060 @0031  173  LM 11         
  0061 @0054  143  LG             LGGO   SUB_P30_W057
  0062 @0026  157  DATA    1,57
P00_W053:
  0063 @0053  116  SM 2          
  0064 @0025  000  NOP           
  0065 @0052  212  CALL           CLEAR_MEM_1C
  0066 @0065  302  GO             P00_W002
CLEAR_DIGIT_SET_FLAG:
  0067 @0072  014  LB MEM_0C     ; B <- MEM_0C
  0070 @0075  107  TM 8          ; check M[0x0c] & 8
  0071 @0076  337  GO             P00_W037 ; jump if M[0x0c] & 8
  0072 @0077  100  RET           
P00_W037:
  0073 @0037  160  LM 0          ; M[Bd++] = 0
SET_4C_BIT_4:
  0074 @0017  023  LBL            ; B <- 4:12
  0075 @0007  114  DATA    4,12
  0076 @0003  117  SM 4           ; M[4:12] |= 4
  0077 @0001  100  RET           

; PAGE 1 
NEXT_PROGRAM_STEP:
; Increment program counter (PC)
  0100 @0100  036  LB PROGRAM_COUNTER_1E ; short routine: LB PROGRAM_COUNTER_1E ; CALL ADD_ONE_ALT
  0101 @0140  224  CALL           ADD_ONE_ALT
; Check if PC == 36
  0102 @0120  060  0TA           
  0103 @0110  126  ADX 6         
  0104 @0104  036  LB PROGRAM_COUNTER_1E
  0105 @0102  062  TAM           
  0106 @0141  324  GO             ROTATE_PROGRAM ; if PC[0] != 6
  0107 @0160  135  ADX 13        ; 6 + 13 = 3
  0110 @0130  037  LB MODE_STATE_B
  0111 @0114  062  TAM           
  0112 @0106  324  GO             ROTATE_PROGRAM ; if PC[1] != 3
  0113 @0143  036  LB PROGRAM_COUNTER_1E
; Wrap PC back to zero
  0114 @0121  160  LM 0           ; M[B] <- 0, ++Bd
  0115 @0150  160  LM 0           ; M[B] <- 0, ++Bd
; Rotate program to bring in new instruction
; Long chain 5f -> 74 -> .. -> 7f -> 64 -> ... -> 54 -> 55 -> ... -> 5f
; Rows 54..., 64..., 74... are probably the program.
ROTATE_PROGRAM:
  0116 @0124  023  LBL
  0117 @0112  137  DATA    5,15
  0120 @0145  006  MTA            ; A <- M[5f]
  0121 @0162  023  LBL           
  0122 @0171  164  DATA    7,4    ; B <- 7:4
  0123 @0174  257  CALL           SHIFT_ROW_RIGHT ; Manissa and exponent
  0124 @0136  257  CALL           SHIFT_ROW_RIGHT
  0125 @0157  023  LBL           
  0126 @0127  144  DATA    6,4    ; B <- 6:4
  0127 @0113  257  CALL           SHIFT_ROW_RIGHT ; Mantissa and exponent
  0130 @0105  257  CALL           SHIFT_ROW_RIGHT
  0131 @0142  023  LBL           
  0132 @0161  124  DATA    5,4
  0133 @0170  257  CALL           SHIFT_ROW_RIGHT ; Mantissa and exponent
  0134 @0134  257  CALL           SHIFT_ROW_RIGHT
  0135 @0116  100  RET           
P01_W047:
  0136 @0147  212  CALL           CLEAR_MEM_1C
  0137 @0123  054  LB MEM_2C  
  0140 @0111  205  CALL           SKIP_IF_ROW_NZ_ALT
  0141 @0144  326  GO             P01_W026
  0142 @0122  056  LB MEM_2E  
  0143 @0151  167  LM 7           ; M[0x14] = 7
P01_W064:
  0144 @0164  032  LB MEM_15 ; MEM_15 is consulted in the same normalization region
  0145 @0132  060  0TA           
  0146 @0155  257  CALL           SHIFT_ROW_RIGHT
P01_W066:
  0147 @0166  231  CALL           SUB_REGISTER_2_5
  0150 @0173  115  TC            
  0151 @0135  375  GO             P01_W075 ; jump if C
  0152 @0156  225  CALL           ADD_MANTISSA_ROW0_ROW2
  0153 @0167  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  0154 @0133  056  LB MEM_2E  
  0155 @0115  006  MTA           
  0156 @0146  121  ADX 1         
  0157 @0163  325  GO             P01_W025
  0160 @0131  007  EXC           
  0161 @0154  364  GO             P01_W064
P01_W026:
  0162 @0126  157  LG             LGCALL SET_4C_BIT_4
  0163 @0153  017  DATA    0,17
P01_W025:
  0164 @0125  272  CALL           SWAP_MEM_0C_FIELD1
  0165 @0152  220  CALL           SHIFT_LEFT_ROW_0
  0166 @0165  144  LG             LGGO   SUB_P26_W000
  0167 @0172  100  DATA    1,00
P01_W075:
  0170 @0175  241  CALL           MOVE_DECIMAL_POINT_LEFT
  0171 @0176  366  GO             P01_W066

SKIP_IF_ROW_NZ:
  0172 @0177  060  0TA           
  0173 @0137  062  TAM           
  0174 @0117  101  RETS           
  0175 @0107  010  EXC-          
  0176 @0103  377  GO             SKIP_IF_ROW_NZ
  0177 @0101  100  RET           

; PAGE 2 
; Special handling when A == 2
; Get digit for display.
; This is digit from row 0
; unless A = 2 in whih case it comes from
; the last bit set in the digit
; First time here A = 7
DISPLAY_TOP:
  0200 @0200  211  CALL           LOAD_MEM_15
  0201 @0240  135  ADX 13        
  0202 @0220  000  NOP           
  0203 @0210  121  ADX 1         
  0204 @0204  315  GO             P02_W015
; Looks like display loop
; remember ~x = -x - 1
; First time here we fall through with A = 5
DISPLAY:
  0205 @0202  126  ADX 6          ; Now A == 11
  0206 @0241  012  LB MEM_05
  0207 @0260  120  ATB            ; Bd <- A. So A controls digit in register.
; First time fetches 0 from 0x0b, presumably lowest digit
  0210 @0230  006  MTA            ; Fetch digit for display
DISPLAY_LOOP:
  ; Stash display digit
  0211 @0214  061  HXA            ; H <- display digit
  0212 @0206  060  0TA           
  0213 @0243  040  COMP           ; A <- 0xf
  0214 @0221  003  SC             ; C <- 1
  ; blank digit so we don't get ghosting when D changes
  0215 @0250  021  DSPS           ; Sa...Sg <- A, Sp <- ~C (Sp == decimal point)
  0216 @0224  103  BTA            ; A <- Bd (A is digit index)
  0217 @0212  043  RSC            ; C <- 0
  0220 @0245  032  LB MEM_15 ; MEM_15 (0x15) participates directly in the display loop
  0221 @0262  062  TAM
; First time through we skip because M[0x15] == 11 == A, so C == 0
  0222 @0271  003  SC             ; C == 1 if different
  0223 @0274  040  COMP           ; A <- -Bd - 1
  0224 @0236  134  ADX 12         ; A <- 11 - Bd
; First time through, A == 0
  0225 @0257  000  NOP           
  0226 @0227  120  ATB            ; Bd <- A
; Select digit for output
  0227 @0213  045  BTD            ; D <- Bd and BLK set low (D is key scan)
  0230 @0205  034  LB MEM_1C  ; MEM_1C / TKB front-end of the keypad scan path
  0231 @0242  025  TKB            ; Check key pressed!
  0232 @0261  323  GO             P02_W023 ; loop if no key active
  0233 @0270  112  SM 8          
  0234 @0234  106  TM 4           ; are we ready for key?
  0235 @0216  142  LG             LGGO   P33_W000 ; Handle key?
  0236 @0247  300  DATA    3,00
P02_W023:
; Not ready for key
; A must still be equal to Bd
  0237 @0223  040  COMP          ; A <- ~A = -A-1
  0240 @0211  134  ADX 12        ; 12 - Bd - 1?
  0241 @0244  000  NOP           
  0242 @0222  061  HXA           ; H <-> A, bring back stashed digit
  0243 @0251  021  DSPS          ; output A to whatever Bd was at BTD above
  0244 @0264  061  HXA           ; H <-> A
  0245 @0232  133  ADX 11        
  0246 @0255  300  GO             DISPLAY_TOP
  0247 @0266  125  ADX 5         
  0250 @0273  107  TM 8          
P02_W035:
  0251 @0235  060  0TA           
  0252 @0256  034  LB MEM_1C 
  0253 @0267  027  EXC 1         
  0254 @0233  326  GO             FIND_LAST_BIT
P02_W015:
  0255 @0215  105  TM 2          
  0256 @0246  331  GO             P02_W031
  0257 @0263  302  GO             DISPLAY
; Why are we finding last bit of M[0x06]?
P02_W031:
  0260 @0231  023  LBL           
  0261 @0254  006  DATA    0,6
; Find last set bit of M[B]
;                      8421
;                      BCDE with F for no bit set
; That E that ends up displayed at D == 5 comes from digit F
FIND_LAST_BIT:
  0262 @0226  060  0TA           
  0263 @0253  132  ADX 10        ; A <- 10
  0264 @0225  000  NOP           
  0265 @0252  104  TM 1          
  0266 @0265  121  ADX 1         
  0267 @0272  105  TM 2          
  0270 @0275  121  ADX 1         
  0271 @0276  106  TM 4          
  0272 @0277  121  ADX 1         
  0273 @0237  107  TM 8          
  0274 @0217  121  ADX 1         
  0275 @0207  125  ADX 5         
  0276 @0203  000  NOP           
  0277 @0201  314  GO             DISPLAY_LOOP

; PAGE 3 
; Surely (mostly) inset digit
SUB_P03_W000:
  0300 @0300  007  EXC           
; Get here if K == 1 or K == 2
; K == 2 => 6 7 8 9 EE
; K == 1 => 0 1 2 3 4 5
P03_W040:
  0301 @0340  006  MTA           
  0302 @0320  266  CALL           LOAD_MEM_17
  0303 @0310  105  TM PROGRAM_ENTRY_MODE_2
  ; Maybe insert instruction
  0304 @0304  371  GO             INSERT_INSTRUCTION ; if program entry mode
  0305 @0302  014  LB MEM_0C     
  0306 @0341  105  TM 2          
  0307 @0360  367  GO             P03_W067 ; if M[0x0c] & 2
  0310 @0330  035  LB MEM_1D
  0311 @0314  107  TM 8          
  0312 @0306  344  GO             P03_W044 ; if M[0x1d] & 8
  0313 @0343  014  LB MEM_0C     
  0314 @0321  106  TM 4          
  0315 @0350  373  GO             P03_W073
P03_W024:
  0316 @0324  155  LG             LGGO   P04_W000
  0317 @0312  100  DATA    1,00
P03_W045:
  0320 @0345  133  ADX 11        
  0321 @0362  000  NOP           
INSERT_INSTRUCTION:
; Read or store current instruction
; Gets here from 0262 when M[0x17] & 2
  0322 @0371  023  LBL           
  0323 @0374  164  DATA    7,4
  0324 @0336  007  EXC           
NEXT_PROGRAM_STEP_ALT:
  0325 @0357  157  LG             LGCALL NEXT_PROGRAM_STEP
  0326 @0327  200  DATA    2,00
; Enter program mode?
PROGRAM_MODE:
  0327 @0313  262  CALL           CLEAR_MEM_0F
  0330 @0305  036  LB PROGRAM_COUNTER_1E
COPY_BANK1_TO_BASE_LOOP:
  0331 @0342  026  MTA 1         
  0332 @0361  031  EXC+ 1        
  0333 @0370  342  GO             COPY_BANK1_TO_BASE_LOOP
; Fetch instruction?
  0334 @0334  023  LBL           
  0335 @0316  164  DATA    7,4
  0336 @0347  006  MTA            A <- M[0x74]
  0337 @0323  157  LG             LGGO   P00_W035
  0340 @0311  135  DATA    1,35
P03_W044:
  0341 @0344  266  CALL           LOAD_MEM_17
  0342 @0322  106  TM 4          
  0343 @0351  324  GO             P03_W024A ; if M[0x17] & 4
  0344 @0364  211  CALL           LOAD_MEM_15
  0345 @0332  104  TM 1          
  0346 @0355  155  LG             LGGO   DO_GOTO ; if M[0x15] & 1
  0347 @0366  300  DATA    3,00
P03_W073:
  ; B = 0x0c
  0350 @0373  113  RSM 4          ; M[0x0c] &= ~4
  0351 @0335  154  LG             LGGO   P06_W000
  0352 @0356  100  DATA    1,00
P03_W067:
  ; Come out off program entry mode?
  0353 @0367  114  RSM PROGRAM_ENTRY_MODE_2
; A = 3 => P20_W000
; A = 2 => SUB_P03_W017
; A = 1 => P03_W052
; A = 0 => SET_MEM_0C_BIT8 then P03_W003
  0354 @0333  135  ADX 13        
  0355 @0315  147  LG             LGGO   P20_W000
  0356 @0346  100  DATA    1,00
  0357 @0363  121  ADX 1         
  0360 @0331  317  GO             SUB_P03_W017
  0361 @0354  121  ADX 1         
  0362 @0326  352  GO             P03_W052
  0363 @0353  203  CALL           SET_MEM_0C_BIT8
  0364 @0325  303  GO             P03_W003
P03_W052:
  0365 @0352  107  TM 8          
  0366 @0365  317  GO             SUB_P03_W017
; Two program steps!
; Could this be go if neg?
  0367 @0372  157  LG             LGCALL NEXT_PROGRAM_STEP
  0370 @0375  200  DATA    2,00
  0371 @0376  157  LG             LGCALL NEXT_PROGRAM_STEP
  0372 @0377  200  DATA    2,00
  0373 @0337  303  GO             P03_W003
SUB_P03_W017:
  0374 @0317  211  CALL           LOAD_MEM_15
  0375 @0307  111  SM 1           ; M[0x15] |= 1
P03_W003:
  0376 @0303  143  LG             LGGO   SUB_P30_W061
  0377 @0301  161  DATA    1,61

; PAGE 4 
; Insert digit?????
P04_W000:
  0400 @0400  123  ADX 3         
  0401 @0440  000  NOP           
  0402 @0420  123  ADX 3         
  0403 @0410  316  GO             P04_W016
  0404 @0404  211  CALL           LOAD_MEM_15
  0405 @0402  104  TM 1          
  0406 @0441  155  LG             LGGO   DO_GOTO ; if M[0x15] & 1
  0407 @0460  300  DATA    3,00
  0410 @0430  033  LB MEM_1B
  0411 @0414  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  0412 @0406  337  GO             P04_W037
  0413 @0443  211  CALL           LOAD_MEM_15
  0414 @0421  106  TM 4          
  0415 @0450  332  GO             INSERT_MEM_1C_INTO_MEM_05
P04_W024:
  0416 @0424  023  LBL           
  0417 @0412  026  DATA    1,6
  0420 @0445  006  MTA           
  0421 @0462  121  ADX 1         
  0422 @0471  326  GO             P04_W026
  0423 @0474  007  EXC           
  0424 @0436  211  CALL           LOAD_MEM_15
  0425 @0457  107  TM 8          
  0426 @0427  241  CALL           MOVE_DECIMAL_POINT_LEFT
  0427 @0413  034  LB MEM_1C 
  0430 @0405  006  MTA           
  0431 @0442  236  CALL           SHIFT_ROW_RIGHT_ROW0
  0432 @0461  014  LB MEM_0C     
  0433 @0470  007  EXC           
  0434 @0434  326  GO             P04_W026
P04_W016:
  0435 @0416  211  CALL           LOAD_MEM_15
  0436 @0447  107  TM 8          
  0437 @0423  367  GO             P04_W067
  0440 @0411  112  SM 8          
  0441 @0444  033  LB MEM_1B
  0442 @0422  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  0443 @0451  325  GO             P04_W025
P04_W064:
  0444 @0464  326  GO             P04_W026
INSERT_MEM_1C_INTO_MEM_05:
  0445 @0432  034  LB MEM_1C  ; MEM_1C is inserted into MEM_05 with an EXC+ / EXC shuttle pair
  0446 @0455  006  MTA           
  0447 @0466  012  LB MEM_05 
  0450 @0473  011  EXC+          
  0451 @0435  007  EXC           
  0452 @0456  326  GO             P04_W026
P04_W067:
  0453 @0467  106  TM 4          
  0454 @0433  363  GO             P04_W063
  0455 @0415  142  LG             LGGO   P33_W035
  0456 @0446  335  DATA    3,35
P04_W063:
  0457 @0463  023  LBL           
  0460 @0431  006  DATA    0,6
  0461 @0454  112  SM 8          
P04_W026:
  0462 @0426  143  LG             LGGO   SUB_P30_W061
  0463 @0453  161  DATA    1,61
P04_W025:
  0464 @0425  141  LG             LGCALL P34_W015
  0465 @0452  015  DATA    0,15
  0466 @0465  170  LM 8           ; M[0x15] <- 8
  0467 @0472  170  LM 8           ; M[0x16] <- 8
  0470 @0475  012  LB MEM_05 
  0471 @0476  160  LM 0           ; M[0x05] <- 0
  0472 @0477  364  GO             P04_W064
P04_W037:
  0473 @0437  141  LG             LGCALL P34_W015
  0474 @0417  015  DATA    0,15
  0475 @0407  160  LM 0          
  0476 @0403  167  LM 7          
  0477 @0401  324  GO             P04_W024

; PAGE 5 
DO_GOTO:
  0500 @0500  034  LB MEM_1C
  0501 @0540  006  MTA            ; A <- M[0x1c]
  0502 @0520  266  CALL           LOAD_MEM_17 ; B <- 0x17
; M[0x17].8 tells us we're setting top digit of goto target
; rather than low digit.
  0503 @0510  107  TM SETTING_GOTO_HI_8          
  0504 @0504  306  GO             SET_TARGET_TOP_DIGIT ; if M[0x17] & 8
  0505 @0502  112  SM 8           ; M[0x17] |= 8
  0506 @0541  023  LBL           
  0507 @0560  031  DATA    1,9
; This is GOTO
; it's setting top digit of GOTO target
  0510 @0530  007  EXC            ; M[0x19] <- M[0x1c]
  0511 @0514  347  GO             P05_W047
SET_TARGET_TOP_DIGIT:
  0512 @0506  102  RSM 8         
  0513 @0543  211  CALL           LOAD_MEM_15
  0514 @0521  110  RSM 1         
  0515 @0550  023  LBL           
  0516 @0524  030  DATA    1,8
; Set low digit of GOTO target
  0517 @0512  007  EXC           ; M[0x18] <- A
; Part of GOTO support?
; 0x1e:0x1f PC
; 0x18:0x19 GOTO target
; This is GOTO I think
PROGRAM_STEP_COMPARE:
  0520 @0545  036  LB PROGRAM_COUNTER_1E
  0521 @0562  006  MTA           ; A <- M[0x1e] ; PC low
  0522 @0571  023  LBL           ; PC low
  0523 @0574  030  DATA    1,8
  0524 @0536  062  TAM           ; compare PC low with 0x18
  0525 @0557  322  GO             PROGRAM_STEP_REINIT ; if unequal
  0526 @0527  037  LB MODE_STATE_B ; A <- M[0x1f] ; PC hi
  0527 @0513  006  MTA           
  0530 @0505  023  LBL           
  0531 @0542  031  DATA    1,9    ; compare PC hi with 01x9
  0532 @0561  062  TAM           
  0533 @0570  322  GO             PROGRAM_STEP_REINIT ; unequal
  0534 @0534  035  LB MEM_1D
  0535 @0516  107  TM 8          
P05_W047:
  0536 @0547  143  LG             LGGO   SUB_P30_W061 ; 1D.8 set
  0537 @0523  161  DATA    1,61
  0540 @0511  156  LG             LGGO   PROGRAM_MODE ; 1D.8 zero
  0541 @0544  313  DATA    3,13
PROGRAM_STEP_REINIT:
  0542 @0522  157  LG             LGCALL NEXT_PROGRAM_STEP
  0543 @0551  200  DATA    2,00
  0544 @0564  345  GO             PROGRAM_STEP_COMPARE
SUBTRACT_ONE_1_9:
  0545 @0532  023  LBL           
  0546 @0555  031  DATA    1,9    ; PC hi
  0547 @0566  247  CALL           SUBTRACT_WITH_BORROW
  0550 @0573  354  GO             LINEAR_OP2
; swap ROW0, ROW2
; ROW0, ROW2 = ROW2, ROW0 + ROW2 / 100
LINEAR_OP1:
  0551 @0535  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  0552 @0556  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  0553 @0567  225  CALL           ADD_MANTISSA_ROW0_ROW2
  0554 @0533  220  CALL           SHIFT_LEFT_ROW_0
  0555 @0515  202  CALL           INCREMENT_MANTISSA_ROW0_ENTRY
  0556 @0546  220  CALL           SHIFT_LEFT_ROW_0
  0557 @0563  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  0560 @0531  100  RET           
LINEAR_OP2:
  0561 @0554  023  LBL            ; Add one to register 1,9
  0562 @0526  031  DATA    1,9
  0563 @0553  224  CALL           ADD_ONE_ALT
  0564 @0525  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  0565 @0552  220  CALL           SHIFT_LEFT_ROW_0
  0566 @0565  220  CALL           SHIFT_LEFT_ROW_0
  0567 @0572  220  CALL           SHIFT_LEFT_ROW_0
  0570 @0575  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  0571 @0576  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
LINEAR_OP2_LOOP:
  0572 @0577  266  CALL           LOAD_MEM_17
  0573 @0537  247  CALL           SUBTRACT_WITH_BORROW
  0574 @0517  101  RETS          
  0575 @0507  225  CALL           ADD_MANTISSA_ROW0_ROW2
  0576 @0503  377  GO             LINEAR_OP2_LOOP
  0577 @0501  000  NOP           

; PAGE 6 
; A corresponds to key
; In F-shift state
; Dispatch table on A:
; 10        → P06_W005
; 7–9       → COMPUTE_TRIG
; 6         → P22_W000
; 5         → DO_RCL
; 4         → P35_W050
; 3         → P06_W034
; 2         → P06_W056
; 1         → P06_W075
; 0         → clear MEM_1D bit 3 → P06_W061
P06_W000:
  0600 @0600  125  ADX 5         
  0601 @0640  000  NOP           
  0602 @0620  121  ADX 1         
  0603 @0610  305  GO             P06_W005
  0604 @0604  123  ADX 3         
  0605 @0602  142  LG             LGGO   COMPUTE_TRIG ; trig???
  0606 @0641  100  DATA    1,00
  0607 @0660  121  ADX 1         
  0610 @0630  146  LG             LGGO   P22_W000 ; parens
  0611 @0614  100  DATA    1,00
  0612 @0606  121  ADX 1         
  0613 @0643  363  GO             DO_RCL ; rcl
  0614 @0621  121  ADX 1         
  0615 @0650  141  LG             LGGO   P35_W050 ; ln
  0616 @0624  350  DATA    3,50
  0617 @0612  121  ADX 1         
  0620 @0645  334  GO             P06_W034 ; #
  0621 @0662  121  ADX 1         
  0622 @0671  356  GO             P06_W056 ; sto?
  0623 @0674  121  ADX 1         
  0624 @0636  375  GO             P06_W075 ; sqrt
  0625 @0657  035  LB MEM_1D
  0626 @0627  102  RSM 8         
  0627 @0613  361  GO             P06_W061
P06_W005:
  0630 @0605  014  LB MEM_0C     
P06_W042:
  0631 @0642  116  SM 2          ; M[0x15] |= 2
; After stop?
P06_W061:
  0632 @0661  143  LG             LGGO   SUB_P30_W061
  0633 @0670  161  DATA    1,61
; Start enter digit?
P06_W034:
  0634 @0634  035  LB MEM_1D
  0635 @0616  107  TM 8          
  0636 @0647  366  GO             P06_W066; jump if bit 3 set
  0637 @0623  147  LG             LGCALL WEIRD_SHUFFLE
  0640 @0611  200  DATA    2,00
  0641 @0644  211  CALL           LOAD_MEM_15
  0642 @0622  105  TM 2          
  0643 @0651  332  GO             P06_W032
  0644 @0664  342  GO             P06_W042
P06_W032:
  0645 @0632  114  RSM 2         
  0646 @0655  361  GO             P06_W061
P06_W066:
  0647 @0666  266  CALL           LOAD_MEM_17
  0650 @0673  117  SM 4          
  0651 @0635  361  GO             P06_W061
; Hypothesis: this is STO = MEx, RCL
; But doesn't fit ?????
P06_W056:
  0652 @0656  147  LG             LGCALL P21_W037
  0653 @0667  237  DATA    2,37
  0654 @0633  154  LG             LGCALL SUB_P07_W000
  0655 @0615  200  DATA    2,00
  0656 @0646  017  LB MEM_0F     
; Hypothesis: this is RCL
; Then row 3 is memory
DO_RCL:
  0657 @0663  077  LB EXP_STATE  
COPY_EXP_STATE_TO_BASE:
  0660 @0631  066  MTA 3
  0661 @0654  070  EXC- 3        
  0662 @0626  331  GO             COPY_EXP_STATE_TO_BASE
P06_W053:
  0663 @0653  212  CALL           CLEAR_MEM_1C
  0664 @0625  033  LB MEM_1B
  0665 @0652  111  SM 1           ; M[MEM_1B] |= 1
  0666 @0665  157  LG             LGGO   P00_W030
  0667 @0672  130  DATA    1,30
; Could be sqrt
P06_W075:
  0670 @0675  147  LG             LGCALL P21_W037
  0671 @0676  237  DATA    2,37
  0672 @0677  154  LG             LGCALL SUB_P07_W000
  0673 @0637  200  DATA    2,00
  0674 @0617  144  LG             LGCALL MODE_STATE_NORMALIZATION
  0675 @0607  200  DATA    2,00
  0676 @0603  146  LG             LGGO   P22_W044
  0677 @0601  144  DATA    1,44

; PAGE 7 
SUB_P07_W000:
  0700 @0700  033  LB MEM_1B
  0701 @0740  107  TM 8          
P07_W020:
  0702 @0720  317  GO             P07_W017
SUB_P07_W010:
  0703 @0710  032  LB MEM_15
  0704 @0704  006  MTA           
  0705 @0702  134  ADX 12        
  0706 @0741  007  EXC           
P07_W060:
  0707 @0760  013  LB MEM_0B   
  0710 @0730  205  CALL           SKIP_IF_ROW_NZ_ALT
  0711 @0714  371  GO             P07_W071
  0712 @0706  013  LB MEM_0B   
  0713 @0743  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  0714 @0721  342  GO             P07_W042
P07_W050:
  0715 @0750  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  0716 @0724  014  LB MEM_0C     
  0717 @0712  007  EXC           
  0720 @0745  241  CALL           MOVE_DECIMAL_POINT_LEFT
  0721 @0762  360  GO             P07_W060
P07_W071:
  0722 @0771  262  CALL           CLEAR_MEM_0F
P07_W074:
  0723 @0774  014  LB MEM_0C     
  0724 @0736  110  RSM 1         
  0725 @0757  033  LB MEM_1B
  0726 @0727  271  CALL           ZERO_FROM_CURRENT_PTR
  0727 @0713  034  LB MEM_1C 
  0730 @0705  100  RET           
P07_W042:
  0731 @0742  040  COMP          
  0732 @0761  062  TAM           
  0733 @0770  316  GO             P07_W016
  0734 @0734  350  GO             P07_W050
P07_W016:
  0735 @0716  032  LB MEM_15
  0736 @0747  006  MTA           
  0737 @0723  131  ADX 9         
  0740 @0711  373  GO             P07_W073
  0741 @0744  007  EXC           
P07_W022:
  0742 @0722  214  CALL           SUB_P37_W014
  0743 @0751  000  NOP           
  0744 @0764  241  CALL           MOVE_DECIMAL_POINT_LEFT
  0745 @0732  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  0746 @0755  322  GO             P07_W022
  0747 @0766  374  GO             P07_W074
P07_W073:
  0750 @0773  007  EXC           
P07_W035:
  0751 @0735  032  LB MEM_15
  0752 @0756  006  MTA           
  0753 @0767  137  ADX 15        
  0754 @0733  346  GO             P07_W046
  0755 @0715  374  GO             P07_W074
P07_W046:
  0756 @0746  007  EXC           
  0757 @0763  261  CALL           SUB_P37_W061
  0760 @0731  000  NOP           
  0761 @0754  335  GO             P07_W035
; Store 0000058520320000 in row 2
STORE_LOG_10:
  0762 @0726  245  CALL           CLEAR_REGISTER_2
  0763 @0753  052  LB MEM_25   
  0764 @0725  165  LM 5           ; log(10) = 2.302585
  0765 @0752  170  LM 8          
  0766 @0765  165  LM 5          
  0767 @0772  162  LM 2          
  0770 @0775  160  LM 0          
  0771 @0776  163  LM 3          
  0772 @0777  162  LM 2          
  0773 @0737  100  RET           
P07_W017:
  0774 @0717  032  LB MEM_15
  0775 @0707  173  LM 11         
  0776 @0703  256  CALL           COPY_REGISTER_2_TO_0
  0777 @0701  310  GO             SUB_P07_W010

; PAGE 10 
  1000 @1000  000  NOP           
  1001 @1040  000  NOP           
  1002 @1020  000  NOP           
  1003 @1010  000  NOP           
  1004 @1004  000  NOP           
  1005 @1002  000  NOP           
  1006 @1041  000  NOP           
  1007 @1060  000  NOP           
  1010 @1030  000  NOP           
  1011 @1014  000  NOP           
  1012 @1006  000  NOP           
  1013 @1043  000  NOP           
  1014 @1021  000  NOP           
  1015 @1050  000  NOP           
  1016 @1024  000  NOP           
  1017 @1012  000  NOP           
  1020 @1045  000  NOP           
  1021 @1062  000  NOP           
  1022 @1071  000  NOP           
  1023 @1074  000  NOP           
  1024 @1036  000  NOP           
  1025 @1057  000  NOP           
  1026 @1027  000  NOP           
  1027 @1013  000  NOP           
  1030 @1005  000  NOP           
  1031 @1042  000  NOP           
  1032 @1061  000  NOP           
  1033 @1070  000  NOP           
  1034 @1034  000  NOP           
  1035 @1016  000  NOP           
  1036 @1047  000  NOP           
  1037 @1023  000  NOP           
  1040 @1011  000  NOP           
  1041 @1044  000  NOP           
  1042 @1022  000  NOP           
  1043 @1051  000  NOP           
  1044 @1064  000  NOP           
  1045 @1032  000  NOP           
  1046 @1055  000  NOP           
  1047 @1066  000  NOP           
  1050 @1073  000  NOP           
  1051 @1035  000  NOP           
  1052 @1056  000  NOP           
  1053 @1067  000  NOP           
  1054 @1033  000  NOP           
  1055 @1015  000  NOP           
  1056 @1046  000  NOP           
  1057 @1063  000  NOP           
  1060 @1031  000  NOP           
  1061 @1054  000  NOP           
  1062 @1026  000  NOP           
  1063 @1053  000  NOP           
  1064 @1025  000  NOP           
  1065 @1052  000  NOP           
  1066 @1065  000  NOP           
  1067 @1072  000  NOP           
  1070 @1075  000  NOP           
  1071 @1076  000  NOP           
  1072 @1077  000  NOP           
  1073 @1037  000  NOP           
  1074 @1017  000  NOP           
  1075 @1007  000  NOP           
  1076 @1003  000  NOP           
  1077 @1001  000  NOP           

; PAGE 11 
  1100 @1100  000  NOP           
  1101 @1140  000  NOP           
  1102 @1120  000  NOP           
  1103 @1110  000  NOP           
  1104 @1104  000  NOP           
  1105 @1102  000  NOP           
  1106 @1141  000  NOP           
  1107 @1160  000  NOP           
  1110 @1130  000  NOP           
  1111 @1114  000  NOP           
  1112 @1106  000  NOP           
  1113 @1143  000  NOP           
  1114 @1121  000  NOP           
  1115 @1150  000  NOP           
  1116 @1124  000  NOP           
  1117 @1112  000  NOP           
  1120 @1145  000  NOP           
  1121 @1162  000  NOP           
  1122 @1171  000  NOP           
  1123 @1174  000  NOP           
  1124 @1136  000  NOP           
  1125 @1157  000  NOP           
  1126 @1127  000  NOP           
  1127 @1113  000  NOP           
  1130 @1105  000  NOP           
  1131 @1142  000  NOP           
  1132 @1161  000  NOP           
  1133 @1170  000  NOP           
  1134 @1134  000  NOP           
  1135 @1116  000  NOP           
  1136 @1147  000  NOP           
  1137 @1123  000  NOP           
  1140 @1111  000  NOP           
  1141 @1144  000  NOP           
  1142 @1122  000  NOP           
  1143 @1151  000  NOP           
  1144 @1164  000  NOP           
  1145 @1132  000  NOP           
  1146 @1155  000  NOP           
  1147 @1166  000  NOP           
  1150 @1173  000  NOP           
  1151 @1135  000  NOP           
  1152 @1156  000  NOP           
  1153 @1167  000  NOP           
  1154 @1133  000  NOP           
  1155 @1115  000  NOP           
  1156 @1146  000  NOP           
  1157 @1163  000  NOP           
  1160 @1131  000  NOP           
  1161 @1154  000  NOP           
  1162 @1126  000  NOP           
  1163 @1153  000  NOP           
  1164 @1125  000  NOP           
  1165 @1152  000  NOP           
  1166 @1165  000  NOP           
  1167 @1172  000  NOP           
  1170 @1175  000  NOP           
  1171 @1176  000  NOP           
  1172 @1177  000  NOP           
  1173 @1137  000  NOP           
  1174 @1117  000  NOP           
  1175 @1107  000  NOP           
  1176 @1103  000  NOP           
  1177 @1101  000  NOP           

; PAGE 12 
  1200 @1200  000  NOP           
  1201 @1240  000  NOP           
  1202 @1220  000  NOP           
  1203 @1210  000  NOP           
  1204 @1204  000  NOP           
  1205 @1202  000  NOP           
  1206 @1241  000  NOP           
  1207 @1260  000  NOP           
  1210 @1230  000  NOP           
  1211 @1214  000  NOP           
  1212 @1206  000  NOP           
  1213 @1243  000  NOP           
  1214 @1221  000  NOP           
  1215 @1250  000  NOP           
  1216 @1224  000  NOP           
  1217 @1212  000  NOP           
  1220 @1245  000  NOP           
  1221 @1262  000  NOP           
  1222 @1271  000  NOP           
  1223 @1274  000  NOP           
  1224 @1236  000  NOP           
  1225 @1257  000  NOP           
  1226 @1227  000  NOP           
  1227 @1213  000  NOP           
  1230 @1205  000  NOP           
  1231 @1242  000  NOP           
  1232 @1261  000  NOP           
  1233 @1270  000  NOP           
  1234 @1234  000  NOP           
  1235 @1216  000  NOP           
  1236 @1247  000  NOP           
  1237 @1223  000  NOP           
  1240 @1211  000  NOP           
  1241 @1244  000  NOP           
  1242 @1222  000  NOP           
  1243 @1251  000  NOP           
  1244 @1264  000  NOP           
  1245 @1232  000  NOP           
  1246 @1255  000  NOP           
  1247 @1266  000  NOP           
  1250 @1273  000  NOP           
  1251 @1235  000  NOP           
  1252 @1256  000  NOP           
  1253 @1267  000  NOP           
  1254 @1233  000  NOP           
  1255 @1215  000  NOP           
  1256 @1246  000  NOP           
  1257 @1263  000  NOP           
  1260 @1231  000  NOP           
  1261 @1254  000  NOP           
  1262 @1226  000  NOP           
  1263 @1253  000  NOP           
  1264 @1225  000  NOP           
  1265 @1252  000  NOP           
  1266 @1265  000  NOP           
  1267 @1272  000  NOP           
  1270 @1275  000  NOP           
  1271 @1276  000  NOP           
  1272 @1277  000  NOP           
  1273 @1237  000  NOP           
  1274 @1217  000  NOP           
  1275 @1207  000  NOP           
  1276 @1203  000  NOP           
  1277 @1201  000  NOP           

; PAGE 13 
  1300 @1300  000  NOP           
  1301 @1340  000  NOP           
  1302 @1320  000  NOP           
  1303 @1310  000  NOP           
  1304 @1304  000  NOP           
  1305 @1302  000  NOP           
  1306 @1341  000  NOP           
  1307 @1360  000  NOP           
  1310 @1330  000  NOP           
  1311 @1314  000  NOP           
  1312 @1306  000  NOP           
  1313 @1343  000  NOP           
  1314 @1321  000  NOP           
  1315 @1350  000  NOP           
  1316 @1324  000  NOP           
  1317 @1312  000  NOP           
  1320 @1345  000  NOP           
  1321 @1362  000  NOP           
  1322 @1371  000  NOP           
  1323 @1374  000  NOP           
  1324 @1336  000  NOP           
  1325 @1357  000  NOP           
  1326 @1327  000  NOP           
  1327 @1313  000  NOP           
  1330 @1305  000  NOP           
  1331 @1342  000  NOP           
  1332 @1361  000  NOP           
  1333 @1370  000  NOP           
  1334 @1334  000  NOP           
  1335 @1316  000  NOP           
  1336 @1347  000  NOP           
  1337 @1323  000  NOP           
  1340 @1311  000  NOP           
  1341 @1344  000  NOP           
  1342 @1322  000  NOP           
  1343 @1351  000  NOP           
  1344 @1364  000  NOP           
  1345 @1332  000  NOP           
  1346 @1355  000  NOP           
  1347 @1366  000  NOP           
  1350 @1373  000  NOP           
  1351 @1335  000  NOP           
  1352 @1356  000  NOP           
  1353 @1367  000  NOP           
  1354 @1333  000  NOP           
  1355 @1315  000  NOP           
  1356 @1346  000  NOP           
  1357 @1363  000  NOP           
  1360 @1331  000  NOP           
  1361 @1354  000  NOP           
  1362 @1326  000  NOP           
  1363 @1353  000  NOP           
  1364 @1325  000  NOP           
  1365 @1352  000  NOP           
  1366 @1365  000  NOP           
  1367 @1372  000  NOP           
  1370 @1375  000  NOP           
  1371 @1376  000  NOP           
  1372 @1377  000  NOP           
  1373 @1337  000  NOP           
  1374 @1317  000  NOP           
  1375 @1307  000  NOP           
  1376 @1303  000  NOP           
  1377 @1301  000  NOP           

; PAGE 14 
  1400 @1400  000  NOP           
  1401 @1440  000  NOP           
  1402 @1420  000  NOP           
  1403 @1410  000  NOP           
  1404 @1404  000  NOP           
  1405 @1402  000  NOP           
  1406 @1441  000  NOP           
  1407 @1460  000  NOP           
  1410 @1430  000  NOP           
  1411 @1414  000  NOP           
  1412 @1406  000  NOP           
  1413 @1443  000  NOP           
  1414 @1421  000  NOP           
  1415 @1450  000  NOP           
  1416 @1424  000  NOP           
  1417 @1412  000  NOP           
  1420 @1445  000  NOP           
  1421 @1462  000  NOP           
  1422 @1471  000  NOP           
  1423 @1474  000  NOP           
  1424 @1436  000  NOP           
  1425 @1457  000  NOP           
  1426 @1427  000  NOP           
  1427 @1413  000  NOP           
  1430 @1405  000  NOP           
  1431 @1442  000  NOP           
  1432 @1461  000  NOP           
  1433 @1470  000  NOP           
  1434 @1434  000  NOP           
  1435 @1416  000  NOP           
  1436 @1447  000  NOP           
  1437 @1423  000  NOP           
  1440 @1411  000  NOP           
  1441 @1444  000  NOP           
  1442 @1422  000  NOP           
  1443 @1451  000  NOP           
  1444 @1464  000  NOP           
  1445 @1432  000  NOP           
  1446 @1455  000  NOP           
  1447 @1466  000  NOP           
  1450 @1473  000  NOP           
  1451 @1435  000  NOP           
  1452 @1456  000  NOP           
  1453 @1467  000  NOP           
  1454 @1433  000  NOP           
  1455 @1415  000  NOP           
  1456 @1446  000  NOP           
  1457 @1463  000  NOP           
  1460 @1431  000  NOP           
  1461 @1454  000  NOP           
  1462 @1426  000  NOP           
  1463 @1453  000  NOP           
  1464 @1425  000  NOP           
  1465 @1452  000  NOP           
  1466 @1465  000  NOP           
  1467 @1472  000  NOP           
  1470 @1475  000  NOP           
  1471 @1476  000  NOP           
  1472 @1477  000  NOP           
  1473 @1437  000  NOP           
  1474 @1417  000  NOP           
  1475 @1407  000  NOP           
  1476 @1403  000  NOP           
  1477 @1401  000  NOP           

; PAGE 15 
  1500 @1500  000  NOP           
  1501 @1540  000  NOP           
  1502 @1520  000  NOP           
  1503 @1510  000  NOP           
  1504 @1504  000  NOP           
  1505 @1502  000  NOP           
  1506 @1541  000  NOP           
  1507 @1560  000  NOP           
  1510 @1530  000  NOP           
  1511 @1514  000  NOP           
  1512 @1506  000  NOP           
  1513 @1543  000  NOP           
  1514 @1521  000  NOP           
  1515 @1550  000  NOP           
  1516 @1524  000  NOP           
  1517 @1512  000  NOP           
  1520 @1545  000  NOP           
  1521 @1562  000  NOP           
  1522 @1571  000  NOP           
  1523 @1574  000  NOP           
  1524 @1536  000  NOP           
  1525 @1557  000  NOP           
  1526 @1527  000  NOP           
  1527 @1513  000  NOP           
  1530 @1505  000  NOP           
  1531 @1542  000  NOP           
  1532 @1561  000  NOP           
  1533 @1570  000  NOP           
  1534 @1534  000  NOP           
  1535 @1516  000  NOP           
  1536 @1547  000  NOP           
  1537 @1523  000  NOP           
  1540 @1511  000  NOP           
  1541 @1544  000  NOP           
  1542 @1522  000  NOP           
  1543 @1551  000  NOP           
  1544 @1564  000  NOP           
  1545 @1532  000  NOP           
  1546 @1555  000  NOP           
  1547 @1566  000  NOP           
  1550 @1573  000  NOP           
  1551 @1535  000  NOP           
  1552 @1556  000  NOP           
  1553 @1567  000  NOP           
  1554 @1533  000  NOP           
  1555 @1515  000  NOP           
  1556 @1546  000  NOP           
  1557 @1563  000  NOP           
  1560 @1531  000  NOP           
  1561 @1554  000  NOP           
  1562 @1526  000  NOP           
  1563 @1553  000  NOP           
  1564 @1525  000  NOP           
  1565 @1552  000  NOP           
  1566 @1565  000  NOP           
  1567 @1572  000  NOP           
  1570 @1575  000  NOP           
  1571 @1576  000  NOP           
  1572 @1577  000  NOP           
  1573 @1537  000  NOP           
  1574 @1517  000  NOP           
  1575 @1507  000  NOP           
  1576 @1503  000  NOP           
  1577 @1501  000  NOP           

; PAGE 16 
  1600 @1600  000  NOP           
  1601 @1640  000  NOP           
  1602 @1620  000  NOP           
  1603 @1610  000  NOP           
  1604 @1604  000  NOP           
  1605 @1602  000  NOP           
  1606 @1641  000  NOP           
  1607 @1660  000  NOP           
  1610 @1630  000  NOP           
  1611 @1614  000  NOP           
  1612 @1606  000  NOP           
  1613 @1643  000  NOP           
  1614 @1621  000  NOP           
  1615 @1650  000  NOP           
  1616 @1624  000  NOP           
  1617 @1612  000  NOP           
  1620 @1645  000  NOP           
  1621 @1662  000  NOP           
  1622 @1671  000  NOP           
  1623 @1674  000  NOP           
  1624 @1636  000  NOP           
  1625 @1657  000  NOP           
  1626 @1627  000  NOP           
  1627 @1613  000  NOP           
  1630 @1605  000  NOP           
  1631 @1642  000  NOP           
  1632 @1661  000  NOP           
  1633 @1670  000  NOP           
  1634 @1634  000  NOP           
  1635 @1616  000  NOP           
  1636 @1647  000  NOP           
  1637 @1623  000  NOP           
  1640 @1611  000  NOP           
  1641 @1644  000  NOP           
  1642 @1622  000  NOP           
  1643 @1651  000  NOP           
  1644 @1664  000  NOP           
  1645 @1632  000  NOP           
  1646 @1655  000  NOP           
  1647 @1666  000  NOP           
  1650 @1673  000  NOP           
  1651 @1635  000  NOP           
  1652 @1656  000  NOP           
  1653 @1667  000  NOP           
  1654 @1633  000  NOP           
  1655 @1615  000  NOP           
  1656 @1646  000  NOP           
  1657 @1663  000  NOP           
  1660 @1631  000  NOP           
  1661 @1654  000  NOP           
  1662 @1626  000  NOP           
  1663 @1653  000  NOP           
  1664 @1625  000  NOP           
  1665 @1652  000  NOP           
  1666 @1665  000  NOP           
  1667 @1672  000  NOP           
  1670 @1675  000  NOP           
  1671 @1676  000  NOP           
  1672 @1677  000  NOP           
  1673 @1637  000  NOP           
  1674 @1617  000  NOP           
  1675 @1607  000  NOP           
  1676 @1603  000  NOP           
  1677 @1601  000  NOP           

; PAGE 17 
  1700 @1700  000  NOP           
  1701 @1740  000  NOP           
  1702 @1720  000  NOP           
  1703 @1710  000  NOP           
  1704 @1704  000  NOP           
  1705 @1702  000  NOP           
  1706 @1741  000  NOP           
  1707 @1760  000  NOP           
  1710 @1730  000  NOP           
  1711 @1714  000  NOP           
  1712 @1706  000  NOP           
  1713 @1743  000  NOP           
  1714 @1721  000  NOP           
  1715 @1750  000  NOP           
  1716 @1724  000  NOP           
  1717 @1712  000  NOP           
  1720 @1745  000  NOP           
  1721 @1762  000  NOP           
  1722 @1771  000  NOP           
  1723 @1774  000  NOP           
  1724 @1736  000  NOP           
  1725 @1757  000  NOP           
  1726 @1727  000  NOP           
  1727 @1713  000  NOP           
  1730 @1705  000  NOP           
  1731 @1742  000  NOP           
  1732 @1761  000  NOP           
  1733 @1770  000  NOP           
  1734 @1734  000  NOP           
  1735 @1716  000  NOP           
  1736 @1747  000  NOP           
  1737 @1723  000  NOP           
  1740 @1711  000  NOP           
  1741 @1744  000  NOP           
  1742 @1722  000  NOP           
  1743 @1751  000  NOP           
  1744 @1764  000  NOP           
  1745 @1732  000  NOP           
  1746 @1755  000  NOP           
  1747 @1766  000  NOP           
  1750 @1773  000  NOP           
  1751 @1735  000  NOP           
  1752 @1756  000  NOP           
  1753 @1767  000  NOP           
  1754 @1733  000  NOP           
  1755 @1715  000  NOP           
  1756 @1746  000  NOP           
  1757 @1763  000  NOP           
  1760 @1731  000  NOP           
  1761 @1754  000  NOP           
  1762 @1726  000  NOP           
  1763 @1753  000  NOP           
  1764 @1725  000  NOP           
  1765 @1752  000  NOP           
  1766 @1765  000  NOP           
  1767 @1772  000  NOP           
  1770 @1775  000  NOP           
  1771 @1776  000  NOP           
  1772 @1777  000  NOP           
  1773 @1737  000  NOP           
  1774 @1717  000  NOP           
  1775 @1707  000  NOP           
  1776 @1703  000  NOP           
  1777 @1701  000  NOP           

; PAGE 20 
P20_W000:
  2000 @2000  147  LG             LGCALL P21_W037 ; page 20 looks like template stamping plus inline decimal adjustment
  2001 @2040  237  DATA    2,37
  
; 1B = MEM_1B
; MEM_1B:
;  0 => fall through
;  1 => P34_W000
;  2 => MAYBE_MEX ; MEx?
;  3 => DEG_RAD
;  4..15 => P20_W034
  2002 @2020  033  LB MEM_1B
  2003 @2010  134  ADX 12        
  2004 @2004  334  GO             P20_W034
  2005 @2002  121  ADX 1         
  2006 @2041  350  GO             DEG_RAD
  2007 @2060  121  ADX 1         
  2010 @2030  143  LG             LGGO   MAYBE_MEX ; MEx?
  2011 @2014  172  DATA    1,72
  2012 @2006  121  ADX 1         
  2013 @2043  141  LG             LGGO   P34_W000
  2014 @2021  100  DATA    1,00
DEG_RAD:
  2015 @2050  154  LG             LGCALL SUB_P07_W000
  2016 @2024  200  DATA    2,00
  2017 @2012  245  CALL           CLEAR_REGISTER_2
; Store .......69275..1. in row 2
  2020 @2045  023  LBL            ; template site 2,7 used by the page-20 staging family
  2021 @2062  047  DATA    2,7    ; 180/pi = 57.296
  2022 @2071  166  LM 6          
  2023 @2074  171  LM 9          
  2024 @2036  162  LM 2          
  2025 @2057  167  LM 7          
  2026 @2027  165  LM 5          
  2027 @2013  056  LB MEM_2E  
  2030 @2005  161  LM 1          
; Swap the whole thing into register 0
  2031 @2042  251  CALL           SWAP_2_15_2
  2032 @2061  146  LG             LGCALL P23_W030
  2033 @2070  230  DATA    2,30
P20_W034:
  2034 @2034  141  LG             LGCALL STEP_HI_MODE_PATH
  2035 @2016  200  DATA    2,00
  2036 @2047  035  LB MEM_1D
  2037 @2023  105  TM 2          
  2040 @2011  365  GO             SUB_P20_W065
  2041 @2044  145  LG             LGCALL POST_DECODE_BOOKKEEPING
  2042 @2022  000  DATA    0,00
  2043 @2051  145  LG             LGCALL P24_W025
  2044 @2064  025  DATA    0,25
  2045 @2032  146  LG             LGCALL SUB_P23_W026
  2046 @2055  226  DATA    2,26
  2047 @2066  144  LG             LGCALL MODE_STATE_NORMALIZATION
  2050 @2073  200  DATA    2,00
  2051 @2035  035  LB MEM_1D
  2052 @2056  104  TM 1          
  2053 @2067  143  LG             LGGO   MODE_TRANSITION_PREP
  2054 @2033  300  DATA    3,00
  2055 @2015  237  CALL           LOAD_B_4C
  2056 @2046  106  TM 4          
  2057 @2063  307  GO             P20_W007
  2060 @2031  145  LG             LGCALL P24_W025
  2061 @2054  025  DATA    0,25
  2062 @2026  237  CALL           LOAD_B_4C
  2063 @2053  106  TM 4          
  2064 @2025  143  LG             LGGO   SUB_P31_W037
  2065 @2052  337  DATA    3,37
SUB_P20_W065:
  2066 @2065  143  LG             LGGO   P31_W002
  2067 @2072  302  DATA    3,02
; Get here if K == 2
; K == 2 => P20_W075 ; 6 7 8 9 EE
P20_W075:
  2070 @2075  006  MTA	  ; read scan state
  2071 @2076  126  ADX 6  ; A <- M[0x1C] + 6
  2072 @2077  000  NOP           
  2073 @2037  156  LG             LGGO   SUB_P03_W000
  2074 @2017  300  DATA    3,00
P20_W007:
  2075 @2007  113  RSM 4         
  2076 @2003  262  CALL           CLEAR_MEM_0F
  2077 @2001  365  GO             SUB_P20_W065

; PAGE 21 
; Weird. It does permutation:
; (0x0F -> 0x0e -> 0x05 ->) (0x0d -> 0x06 ->)
; Could be exponent entry
WEIRD_SHUFFLE:
  2100 @2100  017  LB MEM_0F
  2101 @2140  007  EXC           ; A <-> M[0:15]
  2102 @2120  023  LBL           
  2103 @2110  005  DATA    0,5
  2104 @2104  007  EXC           ; A <-> M[0:5]
  2105 @2102  017  LB MEM_0F     
  2106 @2141  010  EXC-          ; A <-> M[0:15]
  2107 @2160  007  EXC           ; A <-> M[0:14]
  2110 @2130  012  LB MEM_05
  2111 @2114  007  EXC           ; A <-> M[0:5]
  2112 @2106  016  LB MEM_0E     
  2113 @2143  010  EXC-          ; A <-> M[0:14]
  2114 @2121  007  EXC           ; A <-> M[0:13]
  2115 @2150  023  LBL           ;
  2116 @2124  006  DATA    0,6
  2117 @2112  007  EXC           ; A <-> M[0:6]
  2120 @2145  015  LB FLAG_013   ; B <- FLAG_013
  2121 @2162  007  EXC           ; A <-> M[0:13]
  2122 @2171  100  RET           
; Get here if K == 8
P21_W074:
  2123 @2174  266  CALL           LOAD_MEM_17
; Maybe comes out of program mode
  2124 @2136  114  RSM PROGRAM_ENTRY_MODE_2
  2125 @2157  034  LB MEM_1C 
  2126 @2127  027  EXC 1          A <-> MEM_1C, B <- 0C
  2127 @2113  136  ADX 14        
  2130 @2105  352  GO             P21_W052 ; jump if old M[0x1c] >= 2
  2131 @2142  121  ADX 1         
  2132 @2161  315  GO             P21_W015 ; jump if old M[0x1c] == 1
  2133 @2170  105  TM 2          
  2134 @2134  351  GO             CLEAR_MEM_0C_BIT_2 ; jump if M[0x0c] & 2
  2135 @2116  106  TM 4          
  2136 @2147  344  GO             SET_MEM_0C_BIT_2_CLEAR_BIT_4 ; jump if M[0x0c] & 4
  2137 @2123  117  SM 4           ; M[0x0c] |= 4
  2140 @2111  376  GO             P21_W076
SET_MEM_0C_BIT_2_CLEAR_BIT_4:
  2141 @2144  116  SM 2           ; M[0x0c] |= 2
  2142 @2122  364  GO             CLEAR_MEM_0C_BIT_4
CLEAR_MEM_0C_BIT_2:
  2143 @2151  114  RSM 2          ; M[0x0c] &= ~2
CLEAR_MEM_0C_BIT_4:
  2144 @2164  113  RSM 4          ; M[0x0c] &= ~4
  2145 @2132  376  GO             P21_W076
P21_W055:
  2146 @2155  113  RSM 4         
  2147 @2166  035  LB MEM_1D
  2150 @2173  271  CALL           ZERO_FROM_CURRENT_PTR
; Maybe enters program mode
  2151 @2135  266  CALL           LOAD_MEM_17
  2152 @2156  116  SM 2          
  2153 @2167  156  LG             LGGO   PROGRAM_MODE
  2154 @2133  313  DATA    3,13
P21_W015:
  2155 @2115  106  TM 4          
  2156 @2146  156  LG             LGGO   NEXT_PROGRAM_STEP_ALT
  2157 @2163  357  DATA    3,57
  2160 @2131  033  LB MEM_1B
  2161 @2154  107  TM 8          
  2162 @2126  245  CALL           CLEAR_REGISTER_2
  2163 @2153  157  LG             LGGO   P00_W040
  2164 @2125  140  DATA    1,40
P21_W052:
  2165 @2152  106  TM 4          
  2166 @2165  355  GO             P21_W055
  2167 @2172  035  LB MEM_1D
  2170 @2175  112  SM 8          
P21_W076:
  2171 @2176  143  LG             LGGO   SUB_P30_W061
  2172 @2177  161  DATA    1,61
P21_W037:
  2173 @2137  211  CALL           LOAD_MEM_15
  2174 @2117  105  TM 2          
  2175 @2107  300  GO             WEIRD_SHUFFLE
  2176 @2103  100  RET           
  2177 @2101  000  NOP           

; PAGE 22 
; What is 4C?
P22_W000:
  2200 @2200  237  CALL           LOAD_B_4C
  2201 @2240  105  TM 2          
  2202 @2220  306  GO             P22_W006
  2203 @2210  146  LG             LGCALL COPY_ROW_4_FROM_ROW_2
  2204 @2204  052  DATA    0,52
  2205 @2202  146  LG             LGCALL SUB_P22_W051
  2206 @2241  051  DATA    0,51
  2207 @2260  237  CALL           LOAD_B_4C
  2210 @2230  157  LG             LGGO   P00_W053
  2211 @2214  153  DATA    1,53
P22_W006:
  2212 @2206  111  SM 1          
  2213 @2243  034  LB MEM_1C 
SHIFT_MEM_1C_TO_SPECIAL_LATCH:
  2214 @2221  160  LM 0          
  2215 @2250  147  LG             LGCALL P21_W037
  2216 @2224  237  DATA    2,37
  2217 @2212  034  LB MEM_1C 
  2220 @2245  011  EXC+           ; EXC+ here is part of a staging shuffle between MEM_1C and the neighboring special latch
  2221 @2262  000  NOP           
  2222 @2271  007  EXC           
  2223 @2274  130  ADX 8         
  2224 @2236  112  SM 8          
  2225 @2257  034  LB MEM_1C 
  2226 @2227  007  EXC           
  2227 @2213  102  RSM 8         
  2230 @2205  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  2231 @2242  146  LG             LGGO   P23_W000
  2232 @2261  300  DATA    3,00
  2233 @2270  154  LG             LGCALL SUB_P07_W000
  2234 @2234  200  DATA    2,00
  2235 @2216  245  CALL           CLEAR_REGISTER_2
  2236 @2247  255  CALL           STAGE_MEM_0C_IN_WORK2_ENTRY
P22_W023:
  2237 @2223  144  LG             LGCALL SUB_P26_W000
  2240 @2211  000  DATA    0,00
P22_W044:
  2241 @2244  142  LG             LGGO   P33_W055
  2242 @2222  355  DATA    3,55
SUB_P22_W051:
  2243 @2251  035  LB MEM_1D ; MEM_1D bit-8 toggling is explicit here
  2244 @2264  006  MTA           
  2245 @2232  023  LBL           
  2246 @2255  115  DATA    4,13
  2247 @2266  007  EXC           
  2250 @2273  102  RSM 8         ; M[B] &= ~8
  2251 @2235  130  ADX 8         ; A += 8
  2252 @2256  112  SM 8          ; if overflow M[B] |= 8
  2253 @2267  035  LB MEM_1D
  2254 @2233  007  EXC           
  2255 @2215  102  RSM 8         ; 
  2256 @2246  130  ADX 8         ;
  2257 @2263  112  SM 8          
  2260 @2231  100  RET           
COPY_ROW_2_FROM_ROW_4:
  2261 @2254  057  LB MEM_2F  
  2262 @2226  103  BTA           ; A <- Bd
  2263 @2253  125  ADX 5         
  2264 @2225  376  GO             COPY_ROW_BR_FROM_ROW_A
COPY_ROW_4_FROM_ROW_2:
  2265 @2252  023  LBL           
  2266 @2265  117  DATA    4,15
  2267 @2272  103  BTA           ; A <- Bd
  2270 @2275  123  ADX 3         
COPY_ROW_BR_FROM_ROW_A:
  2271 @2276  061  HXA           ; H <-> A
COPY_LOOP:			 ; M[*:Br] <- M[*:H]
  2272 @2277  001  HXBR          ; H <-> Br
  2273 @2237  006  MTA           ; A <- M[B]
  2274 @2217  001  HXBR          ; H <-> Br
  2275 @2207  010  EXC-          ;
  2276 @2203  377  GO             COPY_LOOP
  2277 @2201  100  RET           

; PAGE 23 
P23_W000:
  2300 @2300  104  TM 1          
  2301 @2340  361  GO             P23_W061
  2302 @2320  033  LB MEM_1B ; page 23 is the clearest early decode boundary after scan state is tested
  2303 @2310  107  TM 8          
  2304 @2304  146  LG             LGGO   P23_W067
  2305 @2302  367  DATA    3,67
  2306 @2341  154  LG             LGCALL SUB_P07_W010
  2307 @2360  210  DATA    2,10
P23_W030:
  2310 @2330  034  LB MEM_1C 
  2311 @2314  106  TM 4          
  2312 @2306  324  GO             SUB_P23_W024    ; Divide?
  2313 @2343  145  LG             LGCALL P24_W072 ; Multiply?
  2314 @2321  072  DATA    0,72
  2315 @2350  345  GO             P23_W045
SUB_P23_W024:
  2316 @2324  145  LG             LGCALL P24_W040
  2317 @2312  040  DATA    0,40
P23_W045:
  2320 @2345  142  LG             LGGO   P33_W055
  2321 @2362  355  DATA    3,55
P23_W071:
  2322 @2371  007  EXC           
; Get here if K == 4
P23_W074:
  2323 @2374  006  MTA           
  2324 @2336  266  CALL           LOAD_MEM_17
  2325 @2357  105  TM PROGRAM_ENTRY_MODE_2
  2326 @2327  156  LG             LGGO   P03_W045 ; Jump if program mode
  2327 @2313  345  DATA    3,45
  2330 @2305  146  LG             LGGO   SHIFT_MEM_1C_TO_SPECIAL_LATCH
  2331 @2342  121  DATA    1,21
P23_W061:
  2332 @2361  033  LB MEM_1B
  2333 @2370  107  TM 8          
  2334 @2334  322  GO             P23_W022
  2335 @2316  154  LG             LGCALL SUB_P07_W010
  2336 @2347  210  DATA    2,10
  2337 @2323  105  TM 2          
  2340 @2311  373  GO             P23_W073
  2341 @2344  366  GO             P23_W066
P23_W022:
  2342 @2322  256  CALL           COPY_REGISTER_2_TO_0
  2343 @2351  034  LB MEM_1C 
  2344 @2364  105  TM 2          
  2345 @2332  373  GO             P23_W073
  2346 @2355  245  CALL           CLEAR_REGISTER_2
P23_W066:
  2347 @2366  203  CALL           SET_MEM_0C_BIT8
P23_W073:
  2350 @2373  145  LG             LGCALL P25_W014
  2351 @2335  214  DATA    2,14
  2352 @2356  345  GO             P23_W045
P23_W067:
  2353 @2367  154  LG             LGCALL P07_W020
  2354 @2333  220  DATA    2,20
  2355 @2315  106  TM 4          
  2356 @2346  324  GO             SUB_P23_W024
P23_W063:
  2357 @2363  145  LG             LGCALL P24_W025
  2360 @2331  025  DATA    0,25
  2361 @2354  345  GO             P23_W045
SUB_P23_W026:
  2362 @2326  245  CALL           CLEAR_REGISTER_2
  2363 @2353  053  LB WORK_2_11  
  2364 @2325  161  LM 1          
  2365 @2352  170  LM 8          
  2366 @2365  145  LG             LGGO   P25_W014
  2367 @2372  314  DATA    3,14
SUB_P23_W075:
  2370 @2375  017  LB MEM_0F      ; short routine: LB MEM_0F ; CALL SKIP_IF_MEM_B_IS_ZERO
  2371 @2376  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  2372 @2377  100  RET           
; We end up here if M[0x0f] == 0
  2373 @2337  214  CALL           SUB_P37_W014
  2374 @2317  000  NOP           
  2375 @2307  261  CALL           SUB_P37_W061
  2376 @2303  000  NOP           
  2377 @2301  100  RET           

; PAGE 24 
POST_DECODE_BOOKKEEPING:
  2400 @2400  267  CALL           COPY_MEM_0F_2 ; page 24 looks like immediate post-decode bookkeeping
P24_W040:
; Mystery! What sets this flag
  2401 @2440  034  LB MEM_1C 
  2402 @2420  117  SM 4          
P24_W010:
  2403 @2410  015  LB FLAG_013   
  2404 @2404  046  MTA 2         
  2405 @2402  062  TAM           
  2406 @2441  357  GO             SUB_P24_W057
  2407 @2460  252  CALL           ADD_EXPONENT_ROW0_ROW2
  2410 @2430  237  CALL           LOAD_B_4C
  2411 @2414  115  TC            
  2412 @2406  117  SM 4          
UPDATE_WORK2_12_STAGE:
  2413 @2443  054  LB MEM_2C  
  2414 @2421  046  MTA 2         
  2415 @2450  022  AD            
  2416 @2424  007  EXC           
  2417 @2412  255  CALL           STAGE_MEM_0C_IN_WORK2_ENTRY
  2420 @2445  034  LB MEM_1C 
  2421 @2462  106  TM 4          
  2422 @2471  334  GO             FINALIZE_POST_DECODE_STATE
  2423 @2474  157  LG             LGGO   P01_W047
  2424 @2436  347  DATA    3,47
SUB_P24_W057:
  2425 @2457  254  CALL           INCREMENT_2_14_ALT
  2426 @2427  115  TC            
  2427 @2413  343  GO             UPDATE_WORK2_12_STAGE
  2430 @2405  252  CALL           ADD_EXPONENT_ROW0_ROW2
  2431 @2442  251  CALL           SWAP_2_15_2
  2432 @2461  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  2433 @2470  357  GO             SUB_P24_W057
FINALIZE_POST_DECODE_STATE:
  2434 @2434  272  CALL           SWAP_MEM_0C_FIELD1
  2435 @2416  014  LB MEM_0C     
  2436 @2447  271  CALL           ZERO_FROM_CURRENT_PTR
  2437 @2423  056  LB MEM_2E  
  2440 @2411  170  LM 8          
P24_W044:
  2441 @2444  032  LB MEM_15
  2442 @2422  006  MTA           
  2443 @2451  137  ADX 15        
  2444 @2464  363  GO             P24_W063
  2445 @2432  056  LB MEM_2E  
  2446 @2455  006  MTA           
  2447 @2466  121  ADX 1         
  2450 @2473  144  LG             LGGO   SUB_P26_W000
  2451 @2435  100  DATA    1,00
  2452 @2456  007  EXC           
  2453 @2467  034  LB MEM_1C 
  2454 @2433  204  CALL           SHIFT_LEFT_ALT
  2455 @2415  220  CALL           SHIFT_LEFT_ROW_0
  2456 @2446  344  GO             P24_W044
P24_W063:
  2457 @2463  007  EXC           
  2460 @2431  225  CALL           ADD_MANTISSA_ROW0_ROW2
  2461 @2454  344  GO             P24_W044
LATCH_MODE_STATE_B_FROM_POST_DECODE:
  2462 @2426  037  LB MODE_STATE_B
  2463 @2453  112  SM 8          
P24_W025:
  2464 @2425  245  CALL           CLEAR_REGISTER_2
  2465 @2452  053  LB WORK_2_11  
  2466 @2465  161  LM 1          
P24_W072:
  2467 @2472  034  LB MEM_1C 
  2470 @2475  113  RSM 4         
  2471 @2476  015  LB FLAG_013   
  2472 @2477  201  CALL           SET_MEM_0C_BIT8_ENTRY
  2473 @2437  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  2474 @2417  310  GO             P24_W010
  2475 @2407  000  NOP           
  2476 @2403  000  NOP           
  2477 @2401  000  NOP           

; PAGE 25 
SOMETHING_WITH_PI_BY_2:
  2500 @2500  245  CALL           CLEAR_REGISTER_2 ; page 25 looks like heavier working-register update after decode
  2501 @2540  023  LBL           ; store pi/2 in M[2:7]
  2502 @2520  047  DATA    2,7
  2503 @2510  170  LM 8          ; pi/2
  2504 @2504  160  LM 0          
P25_W002:
  2505 @2502  167  LM 7          
  2506 @2541  165  LM 5          
P25_W060:
  2507 @2560  161  LM 1          
  2510 @2530  203  CALL           SET_MEM_0C_BIT8
P25_W014:
  2511 @2514  015  LB FLAG_013   
  2512 @2506  046  MTA 2         
  2513 @2543  062  TAM           
  2514 @2521  347  GO             P25_W047
  2515 @2550  254  CALL           INCREMENT_2_14_ALT
  2516 @2524  252  CALL           ADD_EXPONENT_ROW0_ROW2
  2517 @2512  115  TC            
  2520 @2545  251  CALL           SWAP_2_15_2
  2521 @2562  254  CALL           INCREMENT_2_14_ALT
  2522 @2571  015  LB FLAG_013   
  2523 @2574  107  TM 8          
  2524 @2536  361  GO             P25_W061
  2525 @2557  251  CALL           SWAP_2_15_2
  2526 @2527  252  CALL           ADD_EXPONENT_ROW0_ROW2
  2527 @2513  015  LB FLAG_013   
  2530 @2505  232  CALL           SWAP_FIELD2_ALT
  2531 @2542  251  CALL           SWAP_2_15_2
P25_W061:
  2532 @2561  216  CALL           DECREMENT_MEM_0E
  2533 @2570  366  GO             P25_W066
  2534 @2534  210  CALL           SHIFT_LEFT_MEM_0B
  2535 @2516  361  GO             P25_W061
P25_W047:
  2536 @2547  107  TM 8          
  2537 @2523  251  CALL           SWAP_2_15_2
  2540 @2511  252  CALL           ADD_EXPONENT_ROW0_ROW2
  2541 @2544  115  TC            
  2542 @2522  262  CALL           CLEAR_MEM_0F
  2543 @2551  053  LB WORK_2_11  
  2544 @2564  205  CALL           SKIP_IF_ROW_NZ_ALT
  2545 @2532  356  GO             CHECK_WORK2_12_MATCH
  2546 @2555  361  GO             P25_W061
P25_W066:
  2547 @2566  015  LB FLAG_013   
  2550 @2573  160  LM 0          
  2551 @2535  251  CALL           SWAP_2_15_2
CHECK_WORK2_12_MATCH:
  2552 @2556  054  LB MEM_2C  
  2553 @2567  046  MTA 2         
  2554 @2533  062  TAM           
  2555 @2515  326  GO             P25_W026
  2556 @2546  255  CALL           STAGE_MEM_0C_IN_WORK2_ENTRY
  2557 @2563  225  CALL           ADD_MANTISSA_ROW0_ROW2
P25_W031:
  2560 @2531  144  LG             LGGO   SUB_P26_W000
  2561 @2554  100  DATA    1,00
P25_W026:
  2562 @2526  255  CALL           STAGE_MEM_0C_IN_WORK2_ENTRY
P25_W053:
  2563 @2553  231  CALL           SUB_REGISTER_2_5
  2564 @2525  115  TC            
  2565 @2552  331  GO             P25_W031
  2566 @2565  225  CALL           ADD_MANTISSA_ROW0_ROW2
  2567 @2572  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  2570 @2575  055  LB WORK_2_13  
  2571 @2576  201  CALL           SET_MEM_0C_BIT8_ENTRY
  2572 @2577  353  GO             P25_W053
SUB_P25_W037:
  2573 @2537  245  CALL           CLEAR_REGISTER_2
  2574 @2517  023  LBL           
  2575 @2507  051  DATA    2,9
  2576 @2503  302  GO             P25_W002
  2577 @2501  000  NOP           

; PAGE 26 
SUB_P26_W000:
  2600 @2600  212  CALL           CLEAR_MEM_1C ; page 26 looks like cleanup / finalize for the same handler family
  2601 @2640  037  LB MODE_STATE_B
  2602 @2620  106  TM 4          
  2603 @2610  361  GO             P26_W061
  2604 @2604  014  LB MEM_0C     
  2605 @2602  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  2606 @2641  345  GO             P26_W045
  2607 @2660  205  CALL           SKIP_IF_ROW_NZ_ALT
  2610 @2630  374  GO             P26_W074
P26_W014:
  2611 @2614  013  LB MEM_0B    ; short routine: LB MEM_0B ; CALL SKIP_IF_MEM_B_IS_ZERO
  2612 @2606  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  2613 @2643  374  GO             P26_W074
  2614 @2621  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  2615 @2650  261  CALL           SUB_P37_W061
  2616 @2624  000  NOP           
  2617 @2612  314  GO             P26_W014
P26_W045:
  2620 @2645  220  CALL           SHIFT_LEFT_ROW_0
  2621 @2662  214  CALL           SUB_P37_W014
  2622 @2671  000  NOP           
P26_W074:
  2623 @2674  055  LB WORK_2_13  
  2624 @2636  050  EXC- 2        
  2625 @2657  010  EXC-          
  2626 @2627  205  CALL           SKIP_IF_ROW_NZ_ALT
  2627 @2613  262  CALL           CLEAR_MEM_0F
  2630 @2605  267  CALL           COPY_MEM_0F_2
  2631 @2642  100  RET           
P26_W061:
  2632 @2661  113  RSM 4         
  2633 @2670  272  CALL           SWAP_MEM_0C_FIELD1
  2634 @2634  023  LBL           
  2635 @2616  012  DATA    0,10
  2636 @2647  161  LM 1          
  2637 @2623  267  CALL           COPY_MEM_0F_2
  2640 @2611  023  LBL           
  2641 @2644  047  DATA    2,7
  2642 @2622  165  LM 5          
  2643 @2651  355  GO             P26_W055
P26_W064:
  2644 @2664  155  LG             LGCALL LINEAR_OP1
  2645 @2632  235  DATA    2,35
P26_W055:
  2646 @2655  155  LG             LGCALL SUBTRACT_ONE_1_9
  2647 @2666  232  DATA    2,32
  2650 @2673  364  GO             P26_W064
  2651 @2635  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  2652 @2656  251  CALL           SWAP_2_15_2
  2653 @2667  037  LB MODE_STATE_B
  2654 @2633  107  TM 8          
  2655 @2615  331  GO             P26_W031
  2656 @2646  146  LG             LGGO   P22_W023
  2657 @2663  123  DATA    1,23
P26_W031:
  2660 @2631  102  RSM 8         
  2661 @2654  146  LG             LGGO   P23_W063
  2662 @2626  363  DATA    3,63
SUB_P26_W053:
  2663 @2653  216  CALL           DECREMENT_MEM_0E
  2664 @2625  372  GO             P26_W072
  2665 @2652  220  CALL           SHIFT_LEFT_ROW_0
  2666 @2665  353  GO             SUB_P26_W053
P26_W072:
  2667 @2672  212  CALL           CLEAR_MEM_1C
  2670 @2675  100  RET           
SUB_P26_W076:
  2671 @2676  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  2672 @2677  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  2673 @2637  231  CALL           SUB_REGISTER_2_5
  2674 @2617  220  CALL           SHIFT_LEFT_ROW_0
  2675 @2607  202  CALL           INCREMENT_MANTISSA_ROW0_ENTRY
  2676 @2603  220  CALL           SHIFT_LEFT_ROW_0
  2677 @2601  100  RET           

; PAGE 27 
MODE_STATE_NORMALIZATION:
  2700 @2700  245  CALL           CLEAR_REGISTER_2
  2701 @2740  013  LB MEM_0B   
  2702 @2720  205  CALL           SKIP_IF_ROW_NZ_ALT
  2703 @2710  326  GO             P27_W026
  2704 @2704  212  CALL           CLEAR_MEM_1C
  2705 @2702  276  CALL           SUB_P37_W076
  2706 @2741  220  CALL           SHIFT_LEFT_ROW_0
P27_W060:
  2707 @2760  216  CALL           DECREMENT_MEM_0E
  2710 @2730  371  GO             P27_W071
  2711 @2714  216  CALL           DECREMENT_MEM_0E
  2712 @2706  350  GO             P27_W050
  2713 @2743  250  CALL           INCREMENT_2_14
  2714 @2721  360  GO             P27_W060
P27_W050:
  2715 @2750  015  LB FLAG_013   
  2716 @2724  107  TM 8          
  2717 @2712  362  GO             P27_W062
  2720 @2745  250  CALL           INCREMENT_2_14
P27_W062:
  2721 @2762  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
P27_W071:
  2722 @2771  216  CALL           DECREMENT_MEM_0E
  2723 @2774  000  NOP           
  2724 @2736  015  LB FLAG_013   
  2725 @2757  047  EXC 2         
  2726 @2727  130  ADX 8         
  2727 @2713  000  NOP           
  2730 @2705  007  EXC           
  2731 @2742  015  LB FLAG_013   
  2732 @2761  172  LM 10         
NORMALIZATION_UPDATE_LOOP:
  2733 @2770  272  CALL           SWAP_MEM_0C_FIELD1
  2734 @2734  014  LB MEM_0C     
  2735 @2716  233  CALL           COPY_CURRENT_TO_FIELD2
  2736 @2747  225  CALL           ADD_MANTISSA_ROW0_ROW2
  2737 @2723  015  LB FLAG_013   
  2740 @2711  006  MTA           
  2741 @2744  120  ATB           
  2742 @2722  111  SM 1          
  2743 @2751  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  2744 @2764  272  CALL           SWAP_MEM_0C_FIELD1
  2745 @2732  231  CALL           SUB_REGISTER_2_5
  2746 @2755  015  LB FLAG_013   
  2747 @2766  026  MTA 1         
  2750 @2773  115  TC            
  2751 @2735  376  GO             SET_PTR_AND_RIPPLE_INCREMENT
  2752 @2756  137  ADX 15        
  2753 @2767  325  GO             P27_W025
  2754 @2733  251  CALL           SWAP_2_15_2
  2755 @2715  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  2756 @2746  272  CALL           SWAP_MEM_0C_FIELD1
  2757 @2763  245  CALL           CLEAR_REGISTER_2
  2760 @2731  214  CALL           SUB_P37_W014
  2761 @2754  000  NOP           
P27_W026:
  2762 @2726  144  LG             LGGO   SUB_P26_W000
  2763 @2753  100  DATA    1,00
P27_W025:
  2764 @2725  015  LB FLAG_013   
  2765 @2752  007  EXC           
  2766 @2765  225  CALL           ADD_MANTISSA_ROW0_ROW2
  2767 @2772  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  2770 @2775  370  GO             NORMALIZATION_UPDATE_LOOP
SET_PTR_AND_RIPPLE_INCREMENT:
  2771 @2776  120  ATB           
  2772 @2777  224  CALL           ADD_ONE_ALT
  2773 @2737  370  GO             NORMALIZATION_UPDATE_LOOP
SKIP_IF_MEM_B_IS_ZERO:
  2774 @2717  060  0TA           
  2775 @2707  062  TAM            ; compare M[B] == 0
  2776 @2703  100  RET            ; if M[B] != 0
  2777 @2701  101  RETS           ; if M[B] == 0

; PAGE 30 
P30_W000:			  ; set digit A in MEM_05 to 15
  3000 @3000  012  LB MEM_05
  3001 @3040  120  ATB            ; Bd <- A
  3002 @3020  177  LM 15          ; MEM_05[A] <- 15
  3003 @3010  324  GO             P30_W024
P30_W004:
  3004 @3004  014  LB MEM_0C     
  3005 @3002  111  SM 1          
  3006 @3041  361  GO             SUB_P30_W061
P30_W060:
  3007 @3060  033  LB MEM_1B
  3010 @3030  104  TM 1          
  3011 @3014  357  GO             SUB_P30_W057 ; if MEM_1B & 1
  3012 @3006  237  CALL           LOAD_B_4C
  3013 @3043  104  TM 1          
  3014 @3021  357  GO             SUB_P30_W057 ; if M[4:12] & 1
  3015 @3050  012  LB MEM_05 
P30_W024:
  3016 @3024  006  MTA           
  3017 @3012  137  ADX 15        
  3020 @3045  357  GO             SUB_P30_W057
  3021 @3062  103  BTA           
  3022 @3071  032  LB MEM_15
  3023 @3074  062  TAM           
  3024 @3036  300  GO             P30_W000
SUB_P30_W057:
  3025 @3057  237  CALL           LOAD_B_4C
  3026 @3027  104  TM 1          
  3027 @3013  346  GO             P30_W046 ; jump if M[4:12] & 1
  3030 @3005  106  TM 4          
  3031 @3042  304  GO             P30_W004 ; jump if M[4:12] & 4
; Call at least 9 times
SUB_P30_W061:
  ; test if program running ???
  3032 @3061  035  LB MEM_1D ; 0x1d
  3033 @3070  107  TM 8          
  3034 @3034  323  GO             P30_W023 ; jmp if M[MEM_1D] & 8
P30_W016:
  ; TF 2 skip takes us here
  ; Heads towards find last bit
  3035 @3016  156  LG             LGGO   P02_W035
  3036 @3047  135  DATA    1,35
; What is TF2 doing here?
; Is TF2 really K3?
P30_W023:
  3037 @3023  024  TF 2          
  3040 @3011  322  GO             P30_W022
  3041 @3044  316  GO             P30_W016
; TF 2 not skip takes us here
P30_W022:
  3042 @3022  157  LG             LGCALL NEXT_PROGRAM_STEP
  3043 @3051  200  DATA    2,00
  3044 @3064  023  LBL           
  3045 @3032  165  DATA    7,5
  3046 @3055  006  MTA           
  3047 @3066  034  LB MEM_1C 
  3050 @3073  125  ADX 5         
  3051 @3035  146  LG             LGGO   P23_W071
  3052 @3056  371  DATA    3,71
  3053 @3067  133  ADX 11        
  3054 @3033  156  LG             LGGO   SUB_P03_W000
  3055 @3015  300  DATA    3,00
P30_W046:
  3056 @3046  110  RSM 1         
  3057 @3063  114  RSM 2         
  3060 @3031  146  LG             LGCALL SUB_P22_W051
  3061 @3054  051  DATA    0,51
  3062 @3026  033  LB MEM_1B
  3063 @3053  102  RSM 8         
  3064 @3025  146  LG             LGCALL COPY_ROW_2_FROM_ROW_4
  3065 @3052  054  DATA    0,54
  3066 @3065  361  GO             SUB_P30_W061
; MEx?
MAYBE_MEX:
  3067 @3072  154  LG             LGCALL SUB_P07_W000
  3070 @3075  200  DATA    2,00
  3071 @3076  077  LB EXP_STATE   ; rare EXP_STATE access; likely scientific-entry/display-state related
; Swap memory with main register
SWAP_EXP_STATE:
  3072 @3077  067  EXC 3          ; reverse swap loop between EXP_STATE and the paired base-bank field
  3073 @3037  067  EXC 3         
  3074 @3017  010  EXC-          
  3075 @3007  377  GO             SWAP_EXP_STATE
  3076 @3003  154  LG             LGGO   P06_W053
  3077 @3001  153  DATA    1,53

; PAGE 31 
MODE_TRANSITION_PREP:
  3100 @3100  037  LB MODE_STATE_B
  3101 @3140  102  RSM 8         
  3102 @3120  237  CALL           LOAD_B_4C
  3103 @3110  106  TM 4          
  3104 @3104  337  GO             SUB_P31_W037
P31_W002:
  3105 @3102  146  LG             LGCALL SUB_P23_W075
  3106 @3141  275  DATA    2,75
  3107 @3160  013  LB MEM_0B   
  3110 @3130  205  CALL           SKIP_IF_ROW_NZ_ALT
  3111 @3114  362  GO             MODE_TRANSITION_STAGE
  3112 @3106  015  LB FLAG_013   
  3113 @3143  107  TM 8          
  3114 @3121  362  GO             MODE_TRANSITION_STAGE
  3115 @3150  145  LG             LGCALL P24_W025
  3116 @3124  025  DATA    0,25
  3117 @3112  035  LB MEM_1D
  3120 @3145  117  SM 4          
MODE_TRANSITION_STAGE:
  3121 @3162  144  LG             LGCALL SUB_P26_W053
  3122 @3171  053  DATA    0,53
  3123 @3174  220  CALL           SHIFT_LEFT_ROW_0
  3124 @3136  245  CALL           CLEAR_REGISTER_2
  3125 @3157  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  3126 @3127  256  CALL           COPY_REGISTER_2_TO_0
  3127 @3113  225  CALL           ADD_MANTISSA_ROW0_ROW2
  3130 @3105  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  3131 @3142  220  CALL           SHIFT_LEFT_ROW_0
  3132 @3161  220  CALL           SHIFT_LEFT_ROW_0
  3133 @3170  023  LBL           
  3134 @3134  012  DATA    0,10
  3135 @3116  116  SM 2          
  3136 @3147  251  CALL           SWAP_2_15_2
P31_W023:
  3137 @3123  144  LG             LGCALL SUB_P26_W076
  3140 @3111  076  DATA    0,76
  3141 @3144  023  LBL           
  3142 @3122  012  DATA    0,10
  3143 @3151  107  TM 8          
  3144 @3164  367  GO             P31_W067
  3145 @3132  251  CALL           SWAP_2_15_2
  3146 @3155  155  LG             LGCALL LINEAR_OP1
  3147 @3166  235  DATA    2,35
  3150 @3173  032  LB MEM_15
  3151 @3135  224  CALL           ADD_ONE_ALT
  3152 @3156  323  GO             P31_W023
P31_W067:
  3153 @3167  155  LG             LGCALL LINEAR_OP1
  3154 @3133  235  DATA    2,35
  3155 @3115  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  3156 @3146  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  3157 @3163  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  3160 @3131  056  LB MEM_2E  
  3161 @3154  171  LM 9          
  3162 @3126  157  LG             LGCALL P01_W066
  3163 @3153  266  DATA    2,66
  3164 @3125  267  CALL           COPY_MEM_0F_2
  3165 @3152  035  LB MEM_1D
  3166 @3165  106  TM 4          
P31_W072:
  3167 @3172  145  LG             LGCALL SOMETHING_WITH_PI_BY_2
  3170 @3175  200  DATA    2,00
  3171 @3176  142  LG             LGGO   P33_W047
  3172 @3177  347  DATA    3,47
SUB_P31_W037:
  3173 @3137  113  RSM 4         
  3174 @3117  262  CALL           CLEAR_MEM_0F
  3175 @3107  372  GO             P31_W072
  3176 @3103  000  NOP           
  3177 @3101  000  NOP           

; PAGE 32 
; Must be trig functions
COMPUTE_TRIG:
  3200 @3200  147  LG             LGCALL P21_W037 ; page 32 is the strongest current compact compare/threshold worker
  3201 @3240  237  DATA    2,37
  3202 @3220  141  LG             LGCALL STEP_HI_MODE_PATH
  3203 @3210  200  DATA    2,00
  3204 @3204  145  LG             LGCALL SUB_P25_W037
  3205 @3202  237  DATA    2,37
  3206 @3241  276  CALL           SUB_P37_W076
  3207 @3260  145  LG             LGCALL SUB_P25_W037
  3210 @3230  237  DATA    2,37
  3211 @3214  144  LG             LGCALL SUB_P26_W053
  3212 @3206  053  DATA    0,53
  3213 @3243  272  CALL           SWAP_MEM_0C_FIELD1
  3214 @3221  262  CALL           CLEAR_MEM_0F
  3215 @3250  245  CALL           CLEAR_REGISTER_2
  3216 @3224  012  LB MEM_05  ; MEM_05 <- cos(0.005)
  3217 @3212  000  NOP           
  3220 @3245  165  LM 5           ; cos(0.005)
  3221 @3262  167  LM 7          
  3222 @3271  170  LM 8          
  3223 @3274  171  LM 9          
  3224 @3236  171  LM 9          
  3225 @3257  171  LM 9          
  3226 @3227  171  LM 9          
P32_W013:
  3227 @3213  144  LG             LGCALL SUB_P26_W076
  3230 @3205  076  DATA    0,76
  3231 @3242  251  CALL           SWAP_2_15_2
  3232 @3261  155  LG             LGCALL SUBTRACT_ONE_1_9
  3233 @3270  232  DATA    2,32
  3234 @3234  313  GO             P32_W013
  3235 @3216  015  LB FLAG_013   
  3236 @3247  170  LM 8          
  3237 @3223  035  LB MEM_1D
  3240 @3211  105  TM 2          
  3241 @3244  373  GO             P32_W073
  3242 @3222  104  TM 1          
  3243 @3251  142  LG             LGGO   P33_W074
  3244 @3264  374  DATA    3,74
P32_W032:
  3245 @3232  144  LG             LGCALL SUB_P26_W000
  3246 @3255  000  DATA    0,00
  3247 @3266  365  GO             P32_W065
P32_W073:
  3250 @3273  013  LB MEM_0B    ; short routine: LB MEM_0B ; CALL SKIP_IF_ROW_NZ_ALT
  3251 @3235  205  CALL           SKIP_IF_ROW_NZ_ALT
  3252 @3256  365  GO             P32_W065
  3253 @3267  267  CALL           COPY_MEM_0F_2
  3254 @3233  145  LG             LGCALL P24_W040
  3255 @3215  040  DATA    0,40
  3256 @3246  145  LG             LGCALL P24_W025
  3257 @3263  025  DATA    0,25
  3260 @3231  146  LG             LGCALL SUB_P23_W026
  3261 @3254  226  DATA    2,26
  3262 @3226  144  LG             LGCALL MODE_STATE_NORMALIZATION
  3263 @3253  200  DATA    2,00
  3264 @3225  145  LG             LGCALL P24_W025
  3265 @3252  025  DATA    0,25
P32_W065:
  3266 @3265  142  LG             LGGO   P33_W047
  3267 @3272  347  DATA    3,47
SUBTRACT_2:
  3270 @3275  003  SC             ; compact subtract/compare worker: SC, MTA 2, SUB, ADX 10, EXC+ 2
SUBTRACT_2_LOOP:
  3271 @3276  046  MTA 2         A <- M[Bd:Br], Bd ^= 2
  3272 @3277  042  SUB           
  3273 @3237  132  ADX 10        
  3274 @3217  051  EXC+ 2        
  3275 @3207  376  GO             SUBTRACT_2_LOOP
  3276 @3203  100  RET           
  3277 @3201  000  NOP           

; PAGE 33 
P33_W000:
; This appears to store the key
  3300 @3300  137  ADX 15        
  3301 @3340  007  EXC           
IS_KEY_HELD:
  3302 @3320  025  TKB           
  3303 @3310  156  LG             LGGO   P02_W035
  3304 @3304  135  DATA    1,35
  3305 @3302  137  ADX 15        
  3306 @3341  320  GO             IS_KEY_HELD
  3307 @3360  064  READ          
; Dispatch by column!
; K == 8 => P21_W074 ; ^/v  C/CE RUN
; K == 4 => P23_W074 ; = - / + x
; K == 2 => P20_W075 ; 6 7 8 9 EE
; K == 1 => P21_W040 ; 0 1 2 3 4 5
  3310 @3330  130  ADX 8         
  3311 @3314  147  LG             LGGO   P21_W074
  3312 @3306  374  DATA    3,74
  3313 @3343  124  ADX 4         
  3314 @3321  146  LG             LGGO   P23_W074
  3315 @3350  374  DATA    3,74
  3316 @3324  122  ADX 2         
  3317 @3312  147  LG             LGGO   P20_W075
  3320 @3345  175  DATA    1,75
  3321 @3362  156  LG             LGGO   P03_W040
  3322 @3371  340  DATA    3,40
P33_W074:
  3323 @3374  267  CALL           COPY_MEM_0F_2
  3324 @3336  145  LG             LGCALL P24_W040
  3325 @3357  040  DATA    0,40
  3326 @3327  245  CALL           CLEAR_REGISTER_2
  3327 @3313  053  LB WORK_2_11  
  3330 @3305  145  LG             LGCALL P25_W060
  3331 @3342  260  DATA    2,60
  3332 @3361  144  LG             LGCALL MODE_STATE_NORMALIZATION
  3333 @3370  200  DATA    2,00
  3334 @3334  037  LB MODE_STATE_B
  3335 @3316  102  RSM 8         
P33_W047:
  3336 @3347  037  LB MODE_STATE_B
  3337 @3323  107  TM 8          
  3340 @3311  317  GO             P33_W017
P33_W044:
  3341 @3344  267  CALL           COPY_MEM_0F_2
  3342 @3322  035  LB MEM_1D
  3343 @3351  113  RSM 4         
  3344 @3364  114  RSM 2         
  3345 @3332  110  RSM 1         
P33_W055:
  3346 @3355  212  CALL           CLEAR_MEM_1C
  3347 @3366  157  LG             LGGO   P00_W041
  3350 @3373  141  DATA    1,41
P33_W035:
  3351 @3335  116  SM 2          
  3352 @3356  117  SM 4          
P33_W067:
  3353 @3367  013  LB MEM_0B   
  3354 @3333  006  MTA           
  3355 @3315  121  ADX 1         
  3356 @3346  353  GO             P33_W053 ; if M[0x0b] == 0xf
P33_W063:
  3357 @3363  147  LG             LGCALL WEIRD_SHUFFLE
  3360 @3331  200  DATA    2,00
  3361 @3354  143  LG             LGGO   SUB_P30_W061
  3362 @3326  161  DATA    1,61
; Digit entry
P33_W053:
  3363 @3353  032  LB MEM_15
  3364 @3325  006  MTA           
  3365 @3352  125  ADX 5         
  3366 @3365  363  GO             P33_W063
  3367 @3372  241  CALL           MOVE_DECIMAL_POINT_LEFT
  3370 @3375  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  3371 @3376  014  LB MEM_0C     
  3372 @3377  007  EXC            ; Emplace new digit
  3373 @3337  367  GO             P33_W067
P33_W017:
  3374 @3317  102  RSM 8         
  3375 @3307  014  LB MEM_0C     
  3376 @3303  170  LM 8          
  3377 @3301  344  GO             P33_W044

; PAGE 34 
; Guessing exp related
P34_W000:
  3400 @3400  154  LG             LGCALL SUB_P07_W000 ; page 34 is a mixed control/numeric bridge with annunciator-side behavior
  3401 @3440  200  DATA    2,00
  3402 @3420  154  LG             LGCALL STORE_LOG_10
  3403 @3410  226  DATA    2,26
  3404 @3404  060  0TA           
  3405 @3402  014  LB MEM_0C     
  3406 @3441  007  EXC           
  3407 @3460  037  LB MODE_STATE_B
  3410 @3430  022  AD            
  3411 @3414  007  EXC           
  3412 @3406  220  CALL           SHIFT_LEFT_ROW_0
  3413 @3443  251  CALL           SWAP_2_15_2
  3414 @3421  145  LG             LGCALL P24_W072
  3415 @3450  072  DATA    0,72
  3416 @3424  015  LB FLAG_013   
  3417 @3412  107  TM 8          
  3420 @3445  305  GO             P34_W005
  3421 @3462  216  CALL           DECREMENT_MEM_0E
  3422 @3471  361  GO             P34_W061
  3423 @3474  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  3424 @3436  216  CALL           DECREMENT_MEM_0E
  3425 @3457  361  GO             P34_W061
  3426 @3427  157  LG             LGCALL SET_4C_BIT_4
  3427 @3413  017  DATA    0,17
P34_W005:
  3430 @3405  144  LG             LGCALL SUB_P26_W053
  3431 @3442  053  DATA    0,53
P34_W061:
  3432 @3461  060  0TA           
  3433 @3470  013  LB MEM_0B   
  3434 @3434  007  EXC           
  3435 @3416  016  LB MEM_0E     
  3436 @3447  010  EXC-          
  3437 @3423  160  LM 0          
  3440 @3411  060  0TA           
  3441 @3444  014  LB MEM_0C     
  3442 @3422  007  EXC           
  3443 @3451  017  LB MEM_0F     
  3444 @3464  007  EXC           
  3445 @3432  274  CALL           ARITHMETIC_SHIFT_RIGHT_ROW0
  3446 @3455  154  LG             LGCALL STORE_LOG_10
  3447 @3466  226  DATA    2,26
  3450 @3473  037  LB MODE_STATE_B
  3451 @3435  117  SM 4          
  3452 @3456  264  CALL           SWAP_MANTISSA_ROW0_ROW2
  3453 @3467  145  LG             LGCALL FINALIZE_POST_DECODE_STATE
  3454 @3433  034  DATA    0,34
P34_W015:
  3455 @3415  033  LB MEM_1B
  3456 @3446  271  CALL           ZERO_FROM_CURRENT_PTR
  3457 @3463  035  LB MEM_1D
  3460 @3431  107  TM 8          
  3461 @3454  337  GO             P34_W037
CLEAR_MEM_0F_SET_MEM_0B:
  3462 @3426  262  CALL           CLEAR_MEM_0F
  3463 @3453  013  LB MEM_0B   
SET_ALL_F:
  3464 @3425  060  0TA           
  3465 @3452  040  COMP           ; A <- 15
  3466 @3465  010  EXC-          
  3467 @3472  325  GO             SET_ALL_F
  3470 @3475  032  LB MEM_15 ; specific MEM_15 state write; reached after MEM_1D bit-8 gating
  3471 @3476  164  LM 4          
  3472 @3477  100  RET           
P34_W037:
  3473 @3437  266  CALL           LOAD_MEM_17
  3474 @3417  117  SM 4           M[1:7] |= 4
  3475 @3407  326  GO             CLEAR_MEM_0F_SET_MEM_0B
  3476 @3403  000  NOP           
  3477 @3401  000  NOP           

; PAGE 35 
STEP_HI_MODE_PATH:
  3500 @3500  035  LB MEM_1D
  3501 @3540  107  TM 8          
  3502 @3520  130  ADX 8         
  3503 @3510  000  NOP           
  3504 @3504  030  EXC- 1        
  3505 @3502  060  0TA           
  3506 @3541  047  EXC 2         
  3507 @3560  160  LM 0          
  3510 @3530  037  LB MODE_STATE_B
  3511 @3514  130  ADX 8         
  3512 @3506  112  SM 8          
  3513 @3543  154  LG             LGGO   SUB_P07_W000
  3514 @3521  300  DATA    3,00
; log?
P35_W050:
  3515 @3550  147  LG             LGCALL P21_W037
  3516 @3524  237  DATA    2,37
  3517 @3512  154  LG             LGCALL SUB_P07_W000
  3520 @3545  200  DATA    2,00
  3521 @3562  160  LM 0          
  3522 @3571  276  CALL           SUB_P37_W076
  3523 @3574  013  LB MEM_0B   
  3524 @3536  205  CALL           SKIP_IF_ROW_NZ_ALT
  3525 @3557  157  LG             LGCALL SET_4C_BIT_4
  3526 @3527  017  DATA    0,17
  3527 @3513  146  LG             LGCALL SUB_P23_W075
  3530 @3505  275  DATA    2,75
  3531 @3542  015  LB FLAG_013   
  3532 @3561  107  TM 8          
  3533 @3570  145  LG             LGCALL LATCH_MODE_STATE_B_FROM_POST_DECODE
  3534 @3534  026  DATA    0,26
  3535 @3516  220  CALL           SHIFT_LEFT_ROW_0
P35_W047:
  3536 @3547  267  CALL           COPY_MEM_0F_2
  3537 @3523  144  LG             LGCALL SUB_P26_W076
  3540 @3511  076  DATA    0,76
  3541 @3544  023  LBL           
  3542 @3522  012  DATA    0,10
  3543 @3551  200  CALL           SKIP_IF_MEM_B_IS_ZERO
  3544 @3564  365  GO             STEP_HI_UPDATE_LOOP
  3545 @3532  256  CALL           COPY_REGISTER_2_TO_0
  3546 @3555  272  CALL           SWAP_MEM_0C_FIELD1
  3547 @3566  220  CALL           SHIFT_LEFT_ROW_0
  3550 @3573  023  LBL           
  3551 @3535  052  DATA    2,10
  3552 @3556  160  LM 0          
  3553 @3567  225  CALL           ADD_MANTISSA_ROW0_ROW2
  3554 @3533  154  LG             LGCALL STORE_LOG_10
  3555 @3515  226  DATA    2,26
P35_W046:
  3556 @3546  216  CALL           DECREMENT_MEM_0E
  3557 @3563  326  GO             P35_W026
  3560 @3531  225  CALL           ADD_MANTISSA_ROW0_ROW2
  3561 @3554  346  GO             P35_W046
P35_W026:
  3562 @3526  015  LB FLAG_013   
  3563 @3553  160  LM 0          
  3564 @3525  142  LG             LGGO   P32_W032
  3565 @3552  132  DATA    1,32
STEP_HI_UPDATE_LOOP:
  3566 @3565  023  LBL           
  3567 @3572  031  DATA    1,9
  3570 @3575  224  CALL           ADD_ONE_ALT
  3571 @3576  023  LBL           
  3572 @3577  031  DATA    1,9
  3573 @3537  104  TM 1          
  3574 @3517  347  GO             P35_W047
  3575 @3507  266  CALL           LOAD_MEM_17
  3576 @3503  224  CALL           ADD_ONE_ALT
  3577 @3501  347  GO             P35_W047

; PAGE 36 
TOGGLE_MEM_BIT8:
  3600 @3600  006  MTA            ; A <- M[B]
  3601 @3640  130  ADX 8          ; A += 8
  3602 @3620  000  NOP           
  3603 @3610  365  GO             DO_EXC
ADD_REGISTER_2:                   ; Add register at Br to register at Br^2.
  3604 @3604  043  RSC            ; page-36 add/carry worker: add one digit with incoming carry
ADD_REGISTER_2_LOOP:
  3605 @3602  046  MTA 2          ; A <- M[B], Br ^= 2
  3606 @3641  002  ADD            ; A += M[B] + C, C <- carry, skip if A < 10
  3607 @3660  126  ADX 6          ; add extra 6 if A >= 10
  3610 @3630  051  EXC+ 2         ; A <-> M[B], Br ^= 2, ++Bd, skip if Bd==0 or Bd==13
  3611 @3614  302  GO             ADD_REGISTER_2_LOOP
  3612 @3606  100  RET           
; Looking like a bug. Maybe intended to round.
INCREMENT_MANTISSA_ROW0:
  3613 @3643  012  LB MEM_05 
  3614 @3621  006  MTA            ; A <- M[B]
  3615 @3650  133  ADX 11         ; skip if M[B] < 5
  3616 @3624  023  LBL            ; B <- 0:5
  3617 @3612  005  DATA    0,5
ADD_ONE:                        ; Add one?
  3620 @3645  003  SC             ; page-36 carry-propagation worker: seed/propagate carry through current digit
ADD_ONE1:
  3621 @3662  060  0TA            ; A <- 0
  3622 @3671  002  ADD            ; A += M[B] + C
  3623 @3674  126  ADX 6          ; BCD correct
  3624 @3636  011  EXC+           ; M[B] <- A, ++Bd, skip if Bd == 13 (or 0)
  3625 @3657  362  GO             ADD_ONE1
  3626 @3627  100  RET           
SUB_DIGIT_COMPARE:
  3627 @3613  060  0TA           
  3630 @3605  042  SUB            ; page-36 subtract/compare worker: one-digit subtract with decimal correction
  3631 @3642  132  ADX 10         ; BCD correction
  3632 @3661  011  EXC+          
  3633 @3670  313  GO             SUB_DIGIT_COMPARE
  3634 @3634  115  TC             ; Skip if C == 0
  3635 @3616  101  RETS          
  3636 @3647  016  LB MEM_0E     
  3637 @3623  161  LM 1          
  3640 @3611  160  LM 0          
  3641 @3644  015  LB FLAG_013   
  3642 @3622  300  GO             TOGGLE_MEM_BIT8
STAGE_MEM_0C_IN_WORK2:
  3643 @3651  060  0TA           
  3644 @3664  014  LB MEM_0C     
  3645 @3632  051  EXC+ 2        
  3646 @3655  000  NOP           
  3647 @3666  010  EXC-          
  3650 @3673  160  LM 0          
  3651 @3635  100  RET           
SWAP_FIELD2:		; Swap by permutation
  3652 @3656  047  EXC 2         
  3653 @3667  047  EXC 2         
  3654 @3633  010  EXC-          
  3655 @3615  356  GO             SWAP_FIELD2
  3656 @3646  100  RET           
SWAP_FIELD1:           ; Swap by permutation: ABC => BAC => CAB => ACB
  3657 @3663  027  EXC 1          ; A <-> M[B], Br ^= 1
  3660 @3631  027  EXC 1          ; A <-> M[B], Br ^= 1
  3661 @3654  010  EXC-           ; A <-> M[B], --Bd, skip if Bd == 15
  3662 @3626  363  GO             SWAP_FIELD1
  3663 @3653  100  RET           
; increment and exchanges into memory
INCREMENT_CURRENT_DIGIT:
  3664 @3625  121  ADX 1         
  3665 @3652  000  NOP           
; This really is nothing but EXC
DO_EXC:
  3666 @3665  007  EXC            A <-> M[B]
  3667 @3672  100  RET           
SHIFT_LEFT:        ; Shift left inserting 0 at end
  3670 @3675  060  0TA           
SHIFT_LEFT1:
  3671 @3676  010  EXC-          
  3672 @3677  376  GO             SHIFT_LEFT1
  3673 @3637  100  RET           
SET_ZERO:
  3674 @3617  060  0TA           
  3675 @3607  010  EXC-          
  3676 @3603  317  GO             SET_ZERO
  3677 @3601  100  RET           

; PAGE 37 
SKIP_IF_MEM_B_IS_ZERO:
  3700 @3700  144  LG             LGGO   SKIP_IF_MEM_B_IS_ZERO
  3701 @3740  317  DATA    3,17
; Shift left 00-0c (divide by 10)
SHIFT_LEFT_ROW_0:
  3702 @3720  014  LB MEM_0C     
; Shift left 10-1b (divide by 10)
SHIFT_LEFT_MEM_0B:
  3703 @3710  013  LB MEM_0B   
SHIFT_LEFT_ALT:
  3704 @3704  375  GO             SHIFT_LEFT
INCREMENT_MANTISSA_ROW0_ENTRY:
  3705 @3702  343  GO             INCREMENT_MANTISSA_ROW0
; Move decimal point left
MOVE_DECIMAL_POINT_LEFT:
  3706 @3741  032  LB MEM_15
  3707 @3760  006  MTA           
  3710 @3730  325  GO             INCREMENT_CURRENT_DIGIT
; Called 4 times
SUB_P37_W014:
  3711 @3714  015  LB FLAG_013   
  3712 @3706  107  TM 8          
  3713 @3743  216  CALL           DECREMENT_MEM_0E
INCREMENT_MEM_0E:
  3714 @3721  016  LB MEM_0E     
INCREMENT_2_14:
  3715 @3750  056  LB MEM_2E  
ADD_ONE_ALT:
  3716 @3724  345  GO             ADD_ONE
CLEAR_MEM_1C:
  3717 @3712  034  LB MEM_1C  ; helper entry selecting MEM_1C
CLEAR_REGISTER_2:
  3720 @3745  057  LB MEM_2F  
CLEAR_MEM_0F:
  3721 @3762  017  LB MEM_0F     
ZERO_FROM_CURRENT_PTR:
  3722 @3771  317  GO             SET_ZERO
ARITHMETIC_SHIFT_RIGHT_ROW0:
  3723 @3774  060  0TA           
SHIFT_ROW_RIGHT_ROW0:              ; shift MEM_05 right
  3724 @3736  012  LB MEM_05  ; helper path selecting MEM_05 before the shift/propagate loop
SHIFT_ROW_RIGHT:		  ; * 10
  3725 @3757  011  EXC+          
  3726 @3727  257  CALL           SHIFT_ROW_RIGHT
  3727 @3713  100  RET           
SKIP_IF_ROW_NZ_ALT:
  3730 @3705  157  LG             LGGO   SKIP_IF_ROW_NZ
  3731 @3742  377  DATA    3,77
SUB_P37_W061:
  3732 @3761  015  LB FLAG_013   
  3733 @3770  107  TM 8          
  3734 @3734  221  CALL           INCREMENT_MEM_0E
DECREMENT_MEM_0E:
  3735 @3716  016  LB MEM_0E     
SUBTRACT_WITH_BORROW:             ; Maybe subtract 1
  3736 @3747  043  RSC            ; helper path that begins with RSC and falls into shared local control
  3737 @3723  313  GO             SUB_DIGIT_COMPARE
LOAD_MEM_15:		  ; B <- 1:5
  3740 @3711  023  LBL           
  3741 @3744  025  DATA    1,5
  3742 @3722  100  RET           
SWAP_2_15_2:
  3743 @3751  057  LB MEM_2F  
SWAP_MANTISSA_ROW0_ROW2:
  3744 @3764  054  LB MEM_2C  
SWAP_FIELD2_ALT:
  3745 @3732  356  GO             SWAP_FIELD2
STAGE_MEM_0C_IN_WORK2_ENTRY:
  3746 @3755  351  GO             STAGE_MEM_0C_IN_WORK2
LOAD_MEM_17:
  3747 @3766  023  LBL           
  3750 @3773  027  DATA    1,7
  3751 @3735  100  RET           
COPY_REGISTER_2_TO_0:
  3752 @3756  057  LB MEM_2F  
COPY_MEM_0F_2:
  3753 @3767  017  LB MEM_0F     
COPY_CURRENT_TO_FIELD2:
  3754 @3733  046  MTA 2          ; reverse copy helper from the current field into field 2
  3755 @3715  050  EXC- 2        
  3756 @3746  233  CALL           COPY_CURRENT_TO_FIELD2
  3757 @3763  100  RET           
SUB_REGISTER_2_5:
  3760 @3731  052  LB MEM_25    ; helper path on the MEM_25 / MEM_2E side of the staging family
INCREMENT_2_14_ALT:
  3761 @3754  056  LB MEM_2E  
  3762 @3726  142  LG             LGGO   SUBTRACT_2
  3763 @3753  175  DATA    1,75
; Add row 2, 25-2c to row0 05-0c (add mantissa)
ADD_MANTISSA_ROW0_ROW2:
  3764 @3725  052  LB MEM_25   
; Add row 2, 2d-2f to row0 0d-0f (add exponent)
ADD_EXPONENT_ROW0_ROW2:
  3765 @3752  056  LB MEM_2E  
  3766 @3765  304  GO             ADD_REGISTER_2
SWAP_MEM_0C_FIELD1:
  3767 @3772  014  LB MEM_0C     
  3770 @3775  363  GO             SWAP_FIELD1
SUB_P37_W076:
  3771 @3776  157  LG             LGGO   CLEAR_DIGIT_SET_FLAG
  3772 @3777  172  DATA    1,72
LOAD_B_4C:
  3773 @3737  023  LBL           
  3774 @3717  114  DATA    4,12  ; B <- 4:12
  3775 @3707  100  RET           
SET_MEM_0C_BIT8:
  3776 @3703  014  LB MEM_0C     
SET_MEM_0C_BIT8_ENTRY:
  3777 @3701  300  GO             TOGGLE_MEM_BIT8
