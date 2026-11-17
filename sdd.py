import sys

EPS = 'e'
END = '$'

nonterms = {'S', 'A', 'B'}
start = 'S'
terminals = {'0', '1', '2'}

LL = {
    'S': {'0': ('S', ('A',)), '1': ('S', ('A',)),
          '2': ('S', ('A',)), '$': ('S', ('A',))},
    'A': {'0': ('A', ('B', 'A')), '1': ('A', ('B', 'A')),
          '2': ('A', ('B', 'A')), '$': ('A', ())},
    'B': {'0': ('B', ('0',)), '1': ('B', ('1',)), '2': ('B', ('2',))},
}


class Node:
    _counter = 0
    def __init__(self, symbol):
        self.symbol = symbol
        self.children = []
        self.prod = None
        self.attrs = {}
        self.id = Node._counter
        Node._counter += 1


def parse_tree(s):
    inp = list('' if s == 'e' else s) + [END]
    root = Node(start)
    stack = [root]
    p = 0
    while stack:
        node = stack[-1]
        X = node.symbol
        a = inp[p] if p < len(inp) else END
        if X in nonterms:
            prod = LL.get(X, {}).get(a)
            if prod is None:
                return None
            node.prod = prod
            _, rhs = prod
            node.children = [Node(sym) for sym in rhs]
            stack.pop()
            for ch in reversed(node.children):
                stack.append(ch)
        else:
            if X == a:
                node.attrs['lexval'] = X
                stack.pop()
                p += 1
            else:
                return None
    return root if p == len(inp) - 1 and inp[p] == END else None


# Reglas: (atributo definido, atributos usados, función)
# 'head' es la cabeza de la producción; entero i es el i-ésimo hijo.
RULES = {
    ('S', ('A',)): [
        ((0, 'pos'), [], lambda get: 0),
        (('head', 'len'), [(0, 'len')], lambda get: get((0, 'len'))),
        (('head', 'sum'), [(0, 'sum')], lambda get: get((0, 'sum'))),
    ],
    ('A', ('B', 'A')): [
        ((0, 'pos'), [('head', 'pos')], lambda get: get(('head', 'pos'))),
        ((1, 'pos'), [('head', 'pos')],
         lambda get: get(('head', 'pos')) + 1),
        (('head', 'len'), [(1, 'len')], lambda get: 1 + get((1, 'len'))),
        (('head', 'sum'),
         [(0, 'val'), (0, 'pos'), (1, 'sum')],
         lambda get: get((0, 'val')) * (get((0, 'pos')) + 1) + get((1, 'sum'))),
    ],
    ('A', ()): [
        (('head', 'len'), [], lambda get: 0),
        (('head', 'sum'), [], lambda get: 0),
    ],
    ('B', ('0',)): [ (('head', 'val'), [(0, 'lexval')],
                      lambda get: int(get((0, 'lexval')))) ],
    ('B', ('1',)): [ (('head', 'val'), [(0, 'lexval')],
                      lambda get: int(get((0, 'lexval')))) ],
    ('B', ('2',)): [ (('head', 'val'), [(0, 'lexval')],
                      lambda get: int(get((0, 'lexval')))) ],
}


def build_graph(root):
    vertices, edges, defined_by = set(), set(), {}

    def traverse(node):
        if node.symbol in nonterms:
            for defines, uses, func in RULES[node.prod]:
                tgt, tattr = defines
                tnode = node if tgt == 'head' else node.children[tgt]
                tv = (tnode, tattr)
                vertices.add(tv)
                defined_by[tv] = (node, uses, func)
                for utgt, uattr in uses:
                    unode = node if utgt == 'head' else node.children[utgt]
                    uv = (unode, uattr)
                    vertices.add(uv)
                    edges.add((uv, tv))
        else:
            vertices.add((node, 'lexval'))
        for ch in node.children:
            traverse(ch)

    traverse(root)
    return vertices, edges, defined_by


def topo(vertices, edges):
    indeg = {v: 0 for v in vertices}
    adj = {v: [] for v in vertices}
    for u, v in edges:
        adj[u].append(v)
        indeg[v] += 1
    q = [v for v in vertices if indeg[v] == 0]
    order = []
    while q:
        u = q.pop(0)
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order if len(order) == len(vertices) else None


def evaluate(root):
    vertices, edges, defined_by = build_graph(root)
    order = topo(vertices, edges)
    if order is None:
        return None
    values = {}

    def collect(node):
        if node.symbol not in nonterms:
            values[(node, 'lexval')] = node.attrs.get('lexval', node.symbol)
        for ch in node.children:
            collect(ch)

    collect(root)
    for v in order:
        if v in values:
            continue
        node, attr = v
        owner, uses, func = defined_by[v]

        def getter(key, owner=owner):
            utgt, uattr = key
            un = owner if utgt == 'head' else owner.children[utgt]
            return values[(un, uattr)]

        val = func(getter)
        values[v] = val
        node.attrs[attr] = val

    return order, values


def print_tree(node, depth=0):
    attrs = ', '.join(f"{k}={node.attrs[k]}" for k in sorted(node.attrs))
    line = '  ' * depth + f"{node.symbol}#{node.id}"
    if attrs:
        line += f" [{attrs}]"
    print(line)
    for ch in node.children:
        print_tree(ch, depth + 1)


def print_order(order, values):
    for v in order:
        node, attr = v
        print(f"{node.symbol}#{node.id}.{attr} = {values[v]}")


def main():
    while True:
        line = sys.stdin.readline()
        if line == '':
            break
        s = line.rstrip('\n')
        s = ''.join(ch for ch in s if not ch.isspace())
        if s == '':
            break
        root = parse_tree(s)
        if root is None:
            print('no')
            continue
        res = evaluate(root)
        if res is None:
            print('circular')
            continue
        order, values = res
        print_tree(root)
        print("Evaluation order:")
        print_order(order, values)
        print(f"S.sum = {root.attrs.get('sum')}")


if __name__ == '__main__':
    main()