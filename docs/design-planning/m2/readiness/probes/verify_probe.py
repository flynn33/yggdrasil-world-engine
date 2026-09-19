"""Verify diagnostic-tool integrity and repeatability; not a product gate."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, help='New output path; existing evidence is never overwritten.')
    args = parser.parse_args()
    out = args.report or base / 'evidence/probe-verification-final.json'
    if out.exists():
        parser.error('Output already exists; choose a new --report path.')
    if not out.parent.is_dir():
        parser.error('Output parent directory must already exist.')
    source = base / 'inspection/ash_generation_packet_schema.json'
    script = base / 'probes/schema_readiness_probe.py'
    report = base / 'evidence/schema-readiness-final.json'
    result = json.loads(report.read_text())
    checks = {'source_sha256_unchanged': hashlib.sha256(source.read_bytes()).hexdigest() == result['source']['sha256']}
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        bad = temporary / 'bad.json'
        bad.write_text('{}\n')
        p = subprocess.run([sys.executable, str(script), '--source', str(bad), '--report', str(temporary/'bad-report.json')], capture_output=True, text=True)
        checks['mismatched_source_rejected'] = p.returncode == 1 and not (temporary/'bad-report.json').exists()
        p = subprocess.run([sys.executable, str(script), '--source', str(source), '--report', str(report)], capture_output=True, text=True)
        checks['existing_evidence_overwrite_rejected'] = p.returncode == 1
        for seed in ('1', '2', '3'):
            destination = temporary / f'repeat-{seed}.json'
            p = subprocess.run([sys.executable, str(script), '--source', str(source), '--report', str(destination)], capture_output=True, text=True, env={**os.environ, 'PYTHONHASHSEED': seed})
            checks[f'hashseed_{seed}_blocked_exit'] = p.returncode == 2
            repeated = json.loads(destination.read_text())
            # Run timestamp differs intentionally; semantic evidence and diagnostics must repeat.
            checks[f'hashseed_{seed}_same_results'] = all(result[k] == repeated[k] for k in ('source', 'summary', 'root_results', 'record_results', 'exchange_probes', 'limits'))
    checks['source_sha256_still_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == result['source']['sha256']
    verification = {'scope': 'Diagnostic tool only; not YWE product acceptance', 'checks': checks, 'all_checks_passed': all(checks.values())}
    with out.open('x', encoding='utf-8') as stream:
        json.dump(verification, stream, indent=2)
        stream.write('\n')
    print(json.dumps(verification, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
