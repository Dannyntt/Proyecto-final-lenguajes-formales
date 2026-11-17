import sys

EPS = 'e'
END = '$'


class Grammar:
    def __init__(self, nonterms, prods):
        self.nonterms = set(nonterms)
        self.prods = prods
        self.start = 'S'
        self.terminals = set()
        for _, rhs in prods:
            for X in rhs:
                if X not in self.nonterms:
                    self.terminals.add(X)


def read_grammar(f):
    line = f.readline()
    while line and line.strip() == '':
        line = f.readline()
    if not line:
        return None
    n = int(line.strip())
    nonterms, prods = [], []
    for _ in range(n):
        line = f.readline()
        while line and line.strip() == '':
            line = f.readline()
        if not line:
            break
        left, right = line.split('->')
        A = left.strip()
        nonterms.append(A)
        for alt in right.strip().split():
            rhs = () if alt == 'e' else tuple(alt)
            prods.append((A, rhs))
    return Grammar(nonterms, prods)


def add_all(dst, src):
    before = len(dst)
    dst |= src
    return len(dst) != before


def compute_first(g):
    first = {A: set() for A in g.nonterms}
    for t in g.terminals:
        first[t] = {t}

    changed = True
    while changed:
        changed = False
        for A, rhs in g.prods:
            if not rhs:
                if EPS not in first[A]:
                    first[A].add(EPS)
                    changed = True
            else:
                all_eps = True
                for X in rhs:
                    if X in g.nonterms:
                        if add_all(first[A], first[X] - {EPS}):
                            changed = True
                        if EPS not in first[X]:
                            all_eps = False
                            break
                    else:
                        if X not in first[A]:
                            first[A].add(X)
                            changed = True
                        all_eps = False
                        break
                if all_eps and EPS not in first[A]:
                    first[A].add(EPS)
                    changed = True
    return first


def first_seq(seq, first, nonterms):
    res = set()
    if not seq:
        return {EPS}
    for X in seq:
        if X in nonterms:
            res |= first[X] - {EPS}
            if EPS not in first[X]:
                return res
        else:
            res.add(X)
            return res
    res.add(EPS)
    return res


def compute_follow(g, first):
    follow = {A: set() for A in g.nonterms}
    follow[g.start].add(END)

    changed = True
    while changed:
        changed = False
        for A, rhs in g.prods:
            for i, B in enumerate(rhs):
                if B not in g.nonterms:
                    continue
                beta = rhs[i + 1:]
                fb = first_seq(beta, first, g.nonterms)
                if add_all(follow[B], fb - {EPS}):
                    changed = True
                if EPS in fb:
                    if add_all(follow[B], follow[A]):
                        changed = True
    return follow


def build_ll_table(g, first, follow):
    table = {A: {} for A in g.nonterms}
    conflicts = []

    for A, rhs in g.prods:
        f = first_seq(rhs, first, g.nonterms)
        for a in f - {EPS}:
            table[A].setdefault(a, []).append((A, rhs))
        if EPS in f:
            for b in follow[A]:
                table[A].setdefault(b, []).append((A, rhs))

    ok = True
    for A in table:
        for a, lst in table[A].items():
            if len(set(lst)) > 1:
                ok = False
                conflicts.append((A, a, lst))
    return table, ok, conflicts


def ll_parse(g, table, s):
    inp = list('' if s == 'e' else s) + [END]
    stack = [END, g.start]
    p = 0

    while True:
        X = stack[-1]
        a = inp[p] if p < len(inp) else END
        if X == END and a == END:
            return True
        if X == END:
            return False
        if X in g.nonterms:
            choices = list(dict.fromkeys(table.get(X, {}).get(a, [])))
            if len(choices) != 1:
                return False
            _, rhs = choices[0]
            stack.pop()
            for sym in reversed(rhs):
                stack.append(sym)
        else:
            if X == a:
                stack.pop()
                p += 1
            else:
                return False


def build_slr(g, follow):
    AUG = "S'"
    prods = [(AUG, (g.start,))] + list(g.prods)
    nonterms = set(g.nonterms) | {AUG}
    terminals = set(g.terminals) | {END}

    by_head = {A: [] for A in nonterms}
    for i, (A, _) in enumerate(prods):
        by_head[A].append(i)

    def closure(I):
        J = set(I)
        changed = True
        while changed:
            changed = False
            for p, dot in list(J):
                _, rhs = prods[p]
                if dot < len(rhs) and rhs[dot] in nonterms:
                    for q in by_head.get(rhs[dot], []):
                        if (q, 0) not in J:
                            J.add((q, 0))
                            changed = True
        return frozenset(J)

    def goto(I, X):
        J = set()
        for p, dot in I:
            _, rhs = prods[p]
            if dot < len(rhs) and rhs[dot] == X:
                J.add((p, dot + 1))
        return closure(J)

    C = [closure({(0, 0)})]
    idx = {C[0]: 0}
    trans = {}
    i = 0
    while i < len(C):
        symbols = set()
        for p, dot in C[i]:
            _, rhs = prods[p]
            if dot < len(rhs):
                symbols.add(rhs[dot])
        for X in sorted(symbols):
            J = goto(C[i], X)
            if not J:
                continue
            if J not in idx:
                idx[J] = len(C)
                C.append(J)
            trans[(i, X)] = idx[J]
        i += 1

    action_lists, goto_tab = {}, {}

    def add_act(st, a, act):
        action_lists.setdefault((st, a), []).append(act)

    for i, I in enumerate(C):
        for p, dot in I:
            A, rhs = prods[p]
            if dot < len(rhs):
                X = rhs[dot]
                if X in terminals and (i, X) in trans:
                    add_act(i, X, ('shift', trans[(i, X)]))
            else:
                if p == 0:
                    add_act(i, END, ('accept',))
                else:
                    for a in follow[A]:
                        add_act(i, a, ('reduce', p))
        for X in nonterms:
            if (i, X) in trans:
                goto_tab[(i, X)] = trans[(i, X)]

    ok = True
    action, conflicts = {}, []
    for k, v in action_lists.items():
        u = list(dict.fromkeys(v))
        if len(u) > 1:
            ok = False
            conflicts.append((k, u))
        action[k] = u[0]
    return action, goto_tab, prods, ok, C, conflicts


def slr_parse(action, goto_tab, prods, s):
    inp = list('' if s == 'e' else s) + [END]
    states = [0]
    p = 0
    while True:
        st = states[-1]
        a = inp[p] if p < len(inp) else END
        act = action.get((st, a))
        if act is None:
            return False
        if act[0] == 'shift':
            states.append(act[1])
            p += 1
        elif act[0] == 'reduce':
            _, rhs = prods[act[1]]
            if rhs:
                if len(states) <= len(rhs):
                    return False
                states = states[:-len(rhs)]
            A = prods[act[1]][0]
            j = goto_tab.get((states[-1], A))
            if j is None:
                return False
            states.append(j)
        else:
            return True


def fmt_set(s):
    parts = sorted([x for x in s if x not in (EPS, END)])
    if EPS in s:
        parts.append('e')
    if END in s:
        parts.append('$')
    return '{' + ', '.join(parts) + '}'


def print_sets(g, first, follow):
    for A in sorted(g.nonterms):
        print(f"First({A}) = {fmt_set(first[A])}")
        print(f"Follow({A}) = {fmt_set(follow[A])}")


def print_ll_table(g, table):
    print("\nLL(1) parsing table:")
    syms = sorted(set().union(*[set(t.keys()) for t in table.values()]) if table else [])
    header = 'NT'.ljust(6) + ''.join(s.ljust(12) for s in syms)
    print(header)
    for A in sorted(g.nonterms):
        row = A.ljust(6)
        for s in syms:
            cell = table[A].get(s, [])
            uniq = list(dict.fromkeys(cell))
            if len(uniq) == 1:
                _, rhs = uniq[0]
                txt = A + '->' + (''.join(rhs) if rhs else 'e')
            elif len(uniq) > 1:
                txt = 'CONFLICT'
            else:
                txt = ''
            row += txt.ljust(12)
        print(row)


def print_lr0_automaton(C, prods):
    print("\nLR(0) canonical collection:")
    for i, I in enumerate(C):
        print(f"I{i}:")
        for p, dot in sorted(I):
            A, rhs = prods[p]
            s = list(rhs)
            s.insert(dot, '.')
            print(f"  {A} -> {''.join(s)}")


def print_slr_table(action, goto_tab, g):
    print("\nSLR(1) ACTION/GOTO table:")
    cols = sorted(set(k[1] for k in action.keys()) | set(k[1] for k in goto_tab.keys()))
    print('St'.ljust(6) + ''.join(c.ljust(10) for c in cols))
    n_states = max([k[0] for k in action.keys()] + [k[0] for k in goto_tab.keys()]) + 1
    for st in range(n_states):
        row = str(st).ljust(6)
        for c in cols:
            if (st, c) in action:
                act = action[(st, c)]
                if act[0] == 'shift':
                    txt = 's' + str(act[1])
                elif act[0] == 'reduce':
                    txt = 'r' + str(act[1])
                else:
                    txt = 'acc'
            elif (st, c) in goto_tab:
                txt = str(goto_tab[(st, c)])
            else:
                txt = ''
            row += txt.ljust(10)
        print(row)


def parse_strings(fn):
    while True:
        line = sys.stdin.readline()
        if line == '':
            break
        s = line.rstrip('\n')
        s = ''.join(ch for ch in s if not ch.isspace())
        if s == '':
            break
        print('yes' if fn(s) else 'no')


def main():
    flags = set(sys.argv[1:])
    use_sets = '--sets' in flags
    use_tables = '--tables' in flags

    g = read_grammar(sys.stdin)
    if g is None:
        print("Empty grammar")
        return

    first = compute_first(g)
    follow = compute_follow(g, first)
    table, ll_ok, ll_conf = build_ll_table(g, first, follow)
    action, goto_tab, prods, slr_ok, C, slr_conf = build_slr(g, follow)

    if use_sets:
        print_sets(g, first, follow)
    if use_tables:
        print_ll_table(g, table)
        print_lr0_automaton(C, prods)
        print_slr_table(action, goto_tab, g)

    if ll_ok and slr_ok:
        while True:
            print("Select a parser (T: for LL(1), B: for SLR(1), Q: quit):")
            line = sys.stdin.readline()
            if line == '':
                break
            choice = line.strip()
            if choice == 'Q':
                break
            if choice == 'T':
                parse_strings(lambda s: ll_parse(g, table, s))
            elif choice == 'B':
                parse_strings(lambda s: slr_parse(action, goto_tab, prods, s))
    elif ll_ok:
        print("Grammar is LL(1).")
        parse_strings(lambda s: ll_parse(g, table, s))
    elif slr_ok:
        print("Grammar is SLR(1).")
        parse_strings(lambda s: slr_parse(action, goto_tab, prods, s))
    else:
        print("Grammar is neither LL(1) nor SLR(1).")


if __name__ == '__main__':
    main()