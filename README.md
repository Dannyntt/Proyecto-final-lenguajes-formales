# Formal Languages — Group Assignment

## Group members
- Laura Santamaria Espinosa
- Daniela Giraldo Salas

## Environment
- Operating system: [completar, p. ej. Ubuntu 22.04 / Windows 11 / macOS 14]
- Programming language: Python 3.10 (no external libraries required)
- Tools: [completar, p. ej. pdflatex, GNU Make]
- No parser generators, parsing libraries, or libraries that compute
  FIRST/FOLLOW sets, LR automata, or parsing tables were used
  (no yacc, bison, ANTLR, Lark, NLTK, etc.).

## Project structure
```
lenguajes-trabajo/
├── README.md
├── parser.py          # Items 1 and 2: FIRST/FOLLOW, LL(1) and SLR(1)
├── sdd.py             # Item 3: SDD evaluator
├── report.tex         # Item 4: report (compiled to report.pdf)
├── Makefile
└── tests/
    ├── ex1_slr.txt
    ├── ex2_both.txt
    ├── ex3_neither.txt
    ├── own_grammar.txt
    ├── own_strings.txt
    └── sdd_strings.txt
```

## Input format for Items 1 and 2
As specified in §2.2 of the assignment:
- The first line contains `n > 0`, the number of nonterminals.
- The next `n` lines have the form `Nonterminal -> alt1 alt2 ...`
- Each alternative is a nonempty sequence of symbols with no blank spaces.
- The empty string ε is written as the single letter `e`.
- `S` is always the initial symbol.
- Nonterminals are capital letters; terminals are single non-blank characters.
- The symbol `$` (end marker) must not appear in the input.
- Every nonterminal appears on the left side of exactly one line.

## Item 1 — FIRST and FOLLOW
Implemented in `parser.py` following Section 4.4.2 of the Dragon Book
(Algorithm 4.4.2). The computation iterates the rules to a fixpoint so that
ε-productions are handled correctly.

Run with `--sets` to print, for each nonterminal in alphabetical order, one
line for `First(A)` and one for `Follow(A)`, in the exact format required:

```bash
python3 parser.py --sets < grammar.txt
```

Example output:

```text
First(A) = {0, 1, 2, e}
Follow(A) = {$}
First(B) = {0, 1, 2}
Follow(B) = {0, 1, 2, $}
First(S) = {0, 1, 2, e}
Follow(S) = {$}
```

## Item 2 — LL(1) and SLR(1) parsers
Both parsers are implemented in `parser.py`.

### LL(1) parser
- The predictive parsing table is built with Algorithm 4.31
  (Section 4.4.3).
- The LL(1) condition is the one at the beginning of Section 4.4.3:
  no cell of the table may contain more than one production.
- The parser is the table-driven, non-recursive predictive parser of
  Algorithm 4.34 (Section 4.4.4), with an explicit stack.
- The grammar is **not** transformed (no left recursion removal, no left
  factoring) before the LL(1) test, as required.

### SLR(1) parser
- The grammar is augmented with a new start symbol `S'`.
- The canonical collection of LR(0) items is built with `CLOSURE` and
  `GOTO` (Section 4.6.2).
- The ACTION and GOTO tables are built as described in Section 4.6.4,
  using FOLLOW sets for reductions.
- The SLR(1) condition is: no cell of ACTION has more than one entry.
- The parser is the LR parsing algorithm of Section 4.6.3.

### Usage
Default behavior (as in §2.2.2 of the assignment):

```bash
python3 parser.py < grammar.txt
```

The program decides whether the grammar is LL(1) and/or SLR(1) and behaves
accordingly:

1. Both LL(1) and SLR(1): prints
   `Select a parser (T: for LL(1), B: for SLR(1), Q: quit):`
   and reads strings until an empty line. Repeats until `Q`.
2. Only LL(1): prints `Grammar is LL(1).` and parses with the LL(1) parser.
3. Only SLR(1): prints `Grammar is SLR(1).` and parses with the SLR(1) parser.
4. Neither: prints `Grammar is neither LL(1) nor SLR(1).` and exits.

Strings to parse are read one per line until an empty line is given.
The empty string is given as a line containing only `e`. For each string,
the program prints `yes` or `no`.

### Extra flags (for the report)
- `--sets` prints the FIRST and FOLLOW sets (see Item 1).
- `--tables` prints the LL(1) parsing table, the LR(0) canonical collection,
  and the SLR(1) ACTION/GOTO table. These are the tables shown in the PDF
  report.

Both flags can be combined:

```bash
python3 parser.py --sets --tables < tests/own_grammar.txt
```

## Item 3 — SDD
Implemented in `sdd.py`. Grammar (Section 3 of the assignment):

```
3
S -> A
A -> B A e
B -> 0 1 2
```

This grammar satisfies:
- G1: it is LL(1) and SLR(1) (parsed with the parsers from Item 2).
- G2: 3 nonterminals, 6 productions, `A` is recursive.
- G3: it is not one of the grammars/SDDs of the book or of the document.

SDD: for a string over `{0,1,2}`, compute
- `len`: length of the derived substring (synthesized),
- `pos`: starting position of the substring (inherited),
- `val`: value of a digit (synthesized),
- `sum`: weighted sum `Σ digit_i · (pos_i + 1)` (synthesized).

The start symbol `S` has no inherited attributes. The SDD has both
synthesized and inherited attributes and is L-attributed (but not
S-attributed).

### Usage

```bash
python3 sdd.py < strings.txt
```

Strings are read one per line until an empty line. For each string:
- If it is not in the language, the program prints `no`.
- Otherwise it prints:
  - the annotated parse tree, one node per line, indented by depth;
  - the evaluation order (a topological order of the dependency graph);
  - the value of the main attribute `S.sum`.
- If the dependency graph has a cycle, it prints `circular`.

The SDD is stored as data (semantic rules are dictionaries in the source
code), so the evaluator does not know about this particular SDD and works
for any non-circular SDD in the same representation.

## Running the examples

### Example 1 (grammar is SLR(1), not LL(1))
```bash
python3 parser.py < tests/ex1_slr.txt
i + i
(i)
(i+i)*i)

```

Expected output:

```text
Grammar is SLR(1).
yes
yes
no
```

### Example 2 (grammar is both LL(1) and SLR(1))
```bash
python3 parser.py < tests/ex2_both.txt
T
d
adbc
a

Q
```

Expected output:

```text
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
yes
yes
no
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
```

### Example 3 (ambiguous and left-recursive grammar)
```bash
python3 parser.py < tests/ex3_neither.txt
```

Expected output:

```text
Grammar is neither LL(1) nor SLR(1).
```

### Grammar used for the report and for Item 3
```bash
python3 parser.py --sets --tables < tests/own_grammar.txt
```

Then parse the strings in `tests/own_strings.txt`:

```bash
python3 parser.py < tests/own_grammar.txt
e
0
12
0121
4
012012

Q
```

Expected results: `yes, yes, yes, yes, no, yes`.

### Item 3 tests
```bash
python3 sdd.py < tests/sdd_strings.txt
```

Includes:
- the shortest string (`e`, gives `S.sum = 0`);
- a recursive/deeply nested string (`012012`);
- a string not in the language (`4`, prints `no`).

Circular detection: replacing the rule of `S -> A` by
`S.sum = S.sum + A.sum` makes the evaluator print `circular`.

## Building the report
```bash
pdflatex report.tex
pdflatex report.tex
```

or simply:

```bash
make
```

The compiled `report.pdf` must be in the root directory of the submission.

## Generative AI tools
We used ChatGPT (OpenAI) to help structure the implementation, to review
the algorithms against the Dragon Book, and to revise the report text.
Every algorithm and every result was manually checked and tested by both
group members before submission.