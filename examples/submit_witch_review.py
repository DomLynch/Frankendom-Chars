"""Manually submit one bounded HF CPU render of an existing Witch GLB.

Requires huggingface_hub==1.31.0 and an authenticated account with job access.
This submits paid compute only when explicitly executed, never from CI.
"""
import argparse
import json
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dataset', required=True)
    parser.add_argument('--input-revision', required=True, help='Immutable Hub commit SHA')
    parser.add_argument('--model-file', required=True, help='GLB path inside that dataset')
    parser.add_argument('--output-dataset', required=True, help='Existing private writable dataset')
    parser.add_argument('--code-revision', required=True, help='Frankendom-Chars Git commit SHA')
    parser.add_argument('--rank', type=int, choices=range(2, 11), default=10)
    args = parser.parse_args()
    if any(len(value) != 40 or any(c not in '0123456789abcdef' for c in value.lower())
           for value in [args.input_revision, args.code_revision]):
        parser.error('Both revisions must be full 40-character commit SHAs')
    from huggingface_hub import HfApi, get_token
    token = get_token()
    if not token:
        parser.error('Authenticate with hf auth login; do not put tokens in command arguments')
    api = HfApi()
    if not api.repo_info(args.output_dataset, repo_type='dataset').private:
        parser.error('Use a private output dataset for this example')
    config = vars(args) | {'run': 'review-' + uuid.uuid4().hex[:12]}
    worker = '''import os,json,hashlib,urllib.request
from pathlib import Path
from huggingface_hub import HfApi,hf_hub_download
c=json.loads(os.environ['RENDER_CONFIG']);api=HfApi()
prefix=c['run'];probe=prefix+'/preflight.txt'
commit=api.upload_file(path_or_fileobj=b'roundtrip',path_in_repo=probe,repo_id=c['output_dataset'],repo_type='dataset')
p=hf_hub_download(c['output_dataset'],probe,repo_type='dataset',revision=commit.oid)
assert Path(p).read_bytes()==b'roundtrip'
os.makedirs('/tmp/witch/models',exist_ok=True);os.chdir('/tmp/witch')
model=hf_hub_download(c['input_dataset'],c['model_file'],repo_type='dataset',revision=c['input_revision'])
Path('models/witch-L'+str(c['rank'])+'.glb').write_bytes(Path(model).read_bytes())
url='https://raw.githubusercontent.com/DomLynch/Frankendom-Chars/'+c['code_revision']+'/characters/witch/case/source/render_candidate.py'
with urllib.request.urlopen(url,timeout=60) as response:Path('render_candidate.py').write_bytes(response.read())
import subprocess,sys
subprocess.run([sys.executable,'render_candidate.py','--','L'+str(c['rank'])],check=True)
api.upload_folder(folder_path='review',path_in_repo=prefix+'/review',repo_id=c['output_dataset'],repo_type='dataset')
print('SAVED',c['output_dataset'],prefix)
'''
    setup = 'apt-get update -qq && apt-get install -y -qq libxrender1 libxi6 libxfixes3 libxkbcommon0 libsm6 libgl1 >/dev/null && exec "$@"'
    job = api.run_job(
        image='ghcr.io/astral-sh/uv:python3.13-bookworm',
        command=['bash', '-c', setup, 'witch', 'uv', 'run', '--with', 'bpy==5.2.2',
                 '--with', 'huggingface-hub==1.31.0', 'python', '-c', worker],
        flavor='cpu-upgrade', timeout='30m', secrets={'HF_TOKEN': token},
        env={'RENDER_CONFIG': json.dumps(config)}, labels={'name': config['run']},
    )
    print(json.dumps({'id': job.id, 'url': job.url, 'output': config['run'],
                      'timeout': '30m', 'flavor': 'cpu-upgrade'}))


if __name__ == '__main__':
    main()
