"""Check exact raw bytes against acquisition provenance before extraction."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def verify():
    manifest=ROOT/'data/external/bushland/acquisition_manifest.json'
    entries=json.loads(manifest.read_text())['files'];checked=[]
    for r in entries:
        if not r.get('local_path'):continue
        p=ROOT/r['local_path']
        if not p.resolve().is_relative_to((ROOT/'data/external/bushland').resolve()):raise ValueError('Invalid raw path')
        data=p.read_bytes()
        if len(data)!=r['bytes'] or hashlib.sha256(data).hexdigest()!=r['sha256']:
            raise ValueError(f'SHA-256 or size mismatch: {p.name}')
        if r.get('official_md5') and hashlib.md5(data).hexdigest()!=r['official_md5']:
            raise ValueError(f'Official MD5 mismatch: {p.name}')
        checked.append(r['local_path'])
    if not checked:raise ValueError('No acquired raw research files')
    return checked


if __name__=='__main__':print(f'Verified {len(verify())} original public research files')
