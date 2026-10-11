"""Bounded direct-set oracle and immutable r1/r2 component audit. Stdlib only."""
from __future__ import annotations
import argparse
import ast
import copy
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TOTAL_CHECKS = ('reference_validation_pass','finite_replication_pass','original_evaluator_contract_pass','named_case_budget_pass')
ENUM_CHECKS = ('candidate_count','nonempty_count','nonempty_union_count','empty_containing_count',
               'integer_half_all','minimum_half','r2_exact_corpus_match','r2_empty_containing_minimum_half')


def direct(family, universe):
    # Reject duplicates before changing representation. No float inequalities.
    members = tuple(frozenset(s) for s in family)
    unique = len(members) == len(set(members))
    domain = all(s <= universe for s in members)
    closed = all(a.union(b) in members for a in members for b in members)
    union = frozenset().union(*members)
    maximum = max((sum(e in s for s in members) for e in union), default=0)
    half = 2 * maximum >= len(members)
    eligible = unique and domain and closed and bool(union)
    return {'unique': unique, 'in_domain': domain, 'union_closed': closed,
            'nonempty_union': bool(union), 'size': len(members), 'maximum_frequency': maximum,
            'integer_half': half, 'eligible': eligible, 'accepted': eligible and half}


def complete(checks, expected):
    return bool(expected) and set(checks) == set(expected) and all(checks[k] is True for k in expected)


def source_module(name):
    path = HERE / 'reference' / (name + '.py')
    names = {'is_union_closed', 'closure', 'frankl_ok'} if name == 'r1' else {'closure', 'bfs_all'}
    nodes = [node for node in ast.parse(path.read_text(encoding='utf-8')).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names:
        raise RuntimeError('FAIL_CLOSED: missing reviewed function')
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return SimpleNamespace(**{name: namespace[name] for name in names})


def v1_projection(r1, forced):
    tree = ast.parse((HERE / 'reference/r1.py').read_text(encoding='utf-8'))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    prefix = []
    for node in main.body:
        if isinstance(node, ast.For):
            break  # original V2 and V4 are explicitly not executed
        prefix.append(copy.deepcopy(node))
    verdict = next(n for n in main.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
                           and t.slice.value == 'verdict' for t in n.targets))
    ret = ast.parse("return {'checks': checks, 'verdict': out['verdict'], 'exit_code': 0 if ok else 1}").body[0]
    original_return = next(node for node in main.body if isinstance(node, ast.Return))
    ret.value.values[-1] = copy.deepcopy(original_return.value)
    probe = ast.FunctionDef(name='probe', args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[],
                           kw_defaults=[], defaults=[]), body=prefix + [copy.deepcopy(verdict), ret], decorator_list=[])
    executable = ast.fix_missing_locations(ast.Module(body=[probe], type_ignores=[]))
    namespace = {'closure': r1.closure, 'is_union_closed': lambda family: forced}
    exec(compile(executable, str(HERE / 'reference/r1.py') + ':V1-projection', 'exec'), namespace)
    result = namespace['probe']()
    result['projection_source'] = ast.unparse(executable)
    result['assumption'] = 'all other stages pass; original enumeration/exploration/output I/O NOT_RUN'
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--round', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    record = json.loads(args.round.read_text(encoding='utf-8'))
    protocol = json.loads((HERE / 'PROTOCOL.json').read_text(encoding='utf-8'))
    protocol_hash = hashlib.sha256((HERE / 'PROTOCOL.json').read_bytes()).hexdigest()
    if record.get('state') not in ('ADMITTED','ROUND_FINISHED') or not record.get('admitted_at') or record.get('protocol_sha256') != protocol_hash:
        raise RuntimeError('FAIL_CLOSED: missing admission or changed frozen protocol')
    for entry in json.loads((HERE / 'SOURCE_MANIFEST.json').read_text(encoding='utf-8')):
        if hashlib.sha256((HERE / entry['snapshot']).read_bytes()).hexdigest() != entry['sha256']:
            raise RuntimeError('FAIL_CLOSED: source snapshot hash mismatch')
    started = time.perf_counter()
    cpu_started = time.process_time()
    args.output.mkdir(parents=True, exist_ok=False)  # never overwrite an earlier attempt
    r1, r2 = source_module('r1'), source_module('r2')
    named = []
    def case(name, passed, **details):
        named.append({'name': name, 'passed': bool(passed), **details})
        print(json.dumps(named[-1], sort_keys=True), flush=True)
    for control in protocol['control_table']:
        name, family, expected = control['name'], control['family'], control['expected_accepted']
        universe = frozenset(control['universe'])
        observed = direct(family, universe)
        case(name, observed['accepted'] is expected, expected_acceptance=expected, observed=observed,
             input=[sorted(s) for s in family])
    controls_pass = all(c['passed'] for c in named)
    boundary_defects = []
    for name, family in [('r1_duplicate_singleton_probe', [{1},{1}]),
                         ('r1_duplicate_closed_probe', [{1},{1},{2},{1,2}])]:
        f = [frozenset(s) for s in family]
        closure, half = r1.is_union_closed(f), r1.frankl_ok(f)
        passed = not (closure and half)
        case(name, passed, expected='duplicate input must be rejected by full evaluator',
             observed_closure=closure, observed_half=half, input=[sorted(s) for s in family])
        if not passed:
            boundary_defects.append(name)
    case('r1_empty_family_closure_probe', r1.is_union_closed([]) is True,
         note='vacuous closure is legal as a predicate; full evaluator must exclude empty union')
    case('r1_empty_union_frequency_probe', r1.frankl_ok([frozenset()]) is False,
         observed=r1.frankl_ok([frozenset()]))
    verdict_defects = []
    for forced, name in [(False,'r1_V1_forced_false'), (True,'r1_V1_forced_true')]:
        observed = v1_projection(r1, forced)
        passed = all(observed['checks'].values()) or (observed['exit_code'] != 0 and observed['verdict'] != 'EVALUATOR_ROUND_COMPLETE')
        case(name, passed, observed=observed)
        if not passed:
            verdict_defects.append(name)
    for name, flags, expected in [('audit_summary_failed_control', {'a':True,'b':False}, ['a','b']),
                                  ('audit_summary_missing_control', {'a':True}, ['a','b']),
                                  ('audit_summary_empty_controls', {}, [])]:
        case(name, complete(flags, expected) is False)
    enumeration = []
    mismatches = []
    with (args.output / 'direct_union_closed_corpus.jsonl').open('w', encoding='utf-8', newline='\n') as corpus:
        for m in protocol['budget']['exhaustive_exception']['m']:
            U = frozenset(range(1,m+1))
            subsets = tuple(frozenset(s) for n in range(m+1) for s in itertools.combinations(range(1,m+1), n))
            containing = set()
            count = nontrivial = passed = 0
            minimum = Fraction(1,1)
            witness = None
            min_empty = Fraction(1,1)
            compared = 0
            for choices in itertools.product((False, True), repeat=len(subsets)):
                family = tuple(s for s, included in zip(subsets, choices) if included)
                closed = all(a.union(b) in family for a in family for b in family)
                original_closed = r1.is_union_closed(family)
                if closed != original_closed:
                    mismatches.append({'m':m, 'family':[sorted(s) for s in family], 'r1_closure':original_closed, 'direct_closure':closed})
                compared += 1
                if not family or not closed:
                    continue
                count += 1
                serialized = tuple(tuple(sorted(s)) for s in family)
                corpus.write(json.dumps({'m':m, 'family':serialized}, sort_keys=True) + '\n')
                if frozenset() in family:
                    containing.add(frozenset(family))
                result = direct(family, U)
                if not result['nonempty_union']:
                    continue
                nontrivial += 1
                passed += result['integer_half']
                original_half = r1.frankl_ok(family)
                if original_half != result['integer_half']:
                    mismatches.append({'m':m, 'family':serialized, 'direct_half':result['integer_half'], 'r1_half':original_half})
                ratio = Fraction(result['maximum_frequency'], result['size'])
                if ratio < minimum:
                    minimum, witness = ratio, serialized
                if frozenset() in family:
                    min_empty = min(min_empty, ratio)
            original_bfs = r2.bfs_all(m)
            converted = {frozenset(frozenset(e+1 for e in range(m) if subset >> e & 1)
                                  for subset in range(1 << m) if bits >> subset & 1) for bits in original_bfs}
            symmetric = converted.symmetric_difference(containing)
            for family in symmetric:
                mismatches.append({'m':m, 'r2_symmetric_difference':sorted([sorted(s) for s in family], key=lambda x:(len(x),x))})
            expected = protocol['enumeration']
            checks = {'candidate_count':compared == 2**(2**m),
                      'nonempty_count':count == expected['expected_nonempty_union_closed'][m-1],
                      'nonempty_union_count':nontrivial == expected['expected_nonempty_union'][m-1],
                      'empty_containing_count':len(containing) == expected['expected_empty_set_containing'][m-1],
                      'integer_half_all':passed == nontrivial,
                      'minimum_half':minimum == Fraction(1,2),
                      'r2_exact_corpus_match':not symmetric and len(original_bfs) == len(containing),
                      'r2_empty_containing_minimum_half':min_empty == Fraction(1,2)}
            entry = {'m':m, 'candidate_count':compared, 'nonempty_union_closed':count,
                     'nonempty_union':nontrivial, 'empty_containing':len(containing),
                     'empty_containing_nontrivial':len(containing)-1, 'integer_half_pass':passed,
                     'minimum_ratio':[minimum.numerator,minimum.denominator], 'minimum_witness':witness,
                     'empty_containing_minimum_ratio':[min_empty.numerator,min_empty.denominator], 'checks':checks}
            enumeration.append(entry)
            print(json.dumps({'enumeration':entry}, sort_keys=True), flush=True)
    expected_names = protocol['controls']
    flags = {c['name']:c['passed'] for c in named}
    coverage = [e['m'] for e in enumeration] == [1,2,3,4] and sum(e['candidate_count'] for e in enumeration) == 65812
    finite_pass = coverage and all(complete(e['checks'], ENUM_CHECKS) for e in enumeration) and not mismatches
    reference_pass = controls_pass and all(flags.get(n) is True for n in expected_names if not n.startswith('r1_duplicate') and not n.startswith('r1_V1'))
    original_pass = not boundary_defects and not verdict_defects
    checks = {'reference_validation_pass':reference_pass, 'finite_replication_pass':finite_pass,
              'original_evaluator_contract_pass':original_pass,
              'named_case_budget_pass':len(named) <= 100 and set(flags) == set(expected_names)}
    total = complete(checks, TOTAL_CHECKS)
    result = {'protocol_sha256':protocol_hash, 'checks':checks, 'all_criteria_passed':total,
              'verdict':'AUDIT_PASS' if total else 'AUDIT_FAIL_EVALUATOR_DEFECTS' if finite_pass else 'AUDIT_FAIL',
              'exit_code':0 if total else 1, 'named_cases':named, 'enumeration':enumeration,
              'mismatches':mismatches, 'confirmed_boundary_defects':boundary_defects,
              'confirmed_verdict_defects':verdict_defects,
              'wall_seconds':time.perf_counter()-started, 'cpu_seconds':time.process_time()-cpu_started,
              'not_run':protocol['not_run'], 'conjecture_counterexample_found':False,
              'claim_scope':'finite exact replication and evaluator-contract audit only'}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps({'summary':checks,'verdict':result['verdict'],'exit_code':result['exit_code']},sort_keys=True), flush=True)
    return result['exit_code']

if __name__ == '__main__':
    raise SystemExit(main())
