#!/usr/bin/env python3
"""Check actual #print axioms output for declared targets; not a statement-equivalence proof."""
import json
from pathlib import Path
import re
import subprocess
import tempfile


def parse_axioms(text, name):
    escaped = re.escape(name)
    if re.search(r"'" + escaped + r"' does not depend on any axioms", text):
        return set()
    match = re.search(r"'" + escaped + r"' depends on axioms:\s*\[([^\]]*)\]", text, re.S)
    if not match:
        raise ValueError('Missing/unrecognized axiom report for ' + name)
    return {x.strip() for x in match.group(1).split(',') if x.strip()}


def main():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / 'claims.json').read_text())
    names = data['declarations']
    allowed = set(data['allow_axioms'])
    if not names or len(set(names)) != len(names):
        raise ValueError('Empty/duplicate theorem audit list')
    for name in [data['module'], *names]:
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9.]*(?:[A-Za-z_0-9])?', name):
            raise ValueError('Unsupported declaration name')
    if not allowed <= {'propext', 'Classical.choice', 'Quot.sound'}:
        raise ValueError('Unexpected axiom allowlist extension')
    # Fail-closed parser negative controls; these do not invoke Lean.
    assert parse_axioms("'T' does not depend on any axioms", 'T') == set()
    assert parse_axioms("'T' depends on axioms: [sorryAx]", 'T') == {'sorryAx'}
    assert parse_axioms("'T' depends on axioms: [Hidden.assumption]", 'T') == {'Hidden.assumption'}
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'Audit.lean'
        path.write_text('import ' + data['module'] + '\n' + '\n'.join('#print axioms ' + name for name in names) + '\n')
        run = subprocess.run(['lake', 'env', 'lean', str(path)], cwd=root, capture_output=True, text=True, timeout=120)
        print(run.stdout); print(run.stderr)
        if run.returncode:
            raise ValueError('Lean audit command failed')
        for name in names:
            extra = parse_axioms(run.stdout, name) - allowed
            if extra:
                raise ValueError(f'{name}: disallowed axioms {sorted(extra)}')
    print(f'PASS: {len(names)} declared targets; original statement and novelty still require review.')

if __name__ == '__main__':
    main()
