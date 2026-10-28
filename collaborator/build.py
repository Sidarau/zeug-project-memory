"""Publish a reviewed canonical skill as the self-contained distribution kit."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--skill');args=p.parse_args()
out=Path(__file__).parent
source=Path(args.skill) if args.skill else out/'skill'
if args.skill:
 import shutil
 shutil.copytree(source, out/'skill', dirs_exist_ok=True, ignore=shutil.ignore_patterns('scripts','__pycache__'))
files={'setup.py':(source/'scripts/setup.py' if args.skill else out/'setup.py').read_text(encoding='utf-8')}
for path in [source/'SKILL.md',*(source/'references').glob('*.md'),source/'agents/openai.yaml']:
 files['skill/'+path.relative_to(source).as_posix()]=path.read_text(encoding='utf-8')
kit={'schemaVersion':1,'files':files,'sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in files.items()}}
(out/'kit.json').write_text(json.dumps(kit,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(out/'setup.py').write_text(files['setup.py'],encoding='utf-8')
print('Built kit with',len(files),'files')
