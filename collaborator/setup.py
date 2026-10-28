#!/usr/bin/env python3
"""Project-only installer/updater. Python 3.9+, standard library; no credentials."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import urllib.request

KIT_URL = 'https://raw.githubusercontent.com/Sidarau/zeug-project-memory/main/collaborator/kit.json'
BEGIN = '<!-- zeug-collaborate:start -->'
END = '<!-- zeug-collaborate:end -->'
TBEGIN = '# zeug-collaborate:start'
TEND = '# zeug-collaborate:end'
SLUG = re.compile(r'^[a-z0-9][a-z0-9-]{1,40}$')
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


class SetupError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode()


def text(value, label):
    if not isinstance(value, str) or not value or len(value) > 200 or any(ord(c) < 32 for c in value) or any(c in value for c in '<>`'):
        raise SetupError('Invalid ' + label)
    return value


def profile_of(p):
    if not isinstance(p, dict) or set(p) != {'schemaVersion', 'project', 'name', 'memoryUrl', 'linear'} or p['schemaVersion'] != 1:
        raise SetupError('Unsupported project profile; download it again from CMD.')
    if not isinstance(p['project'], str) or not SLUG.fullmatch(p['project']):
        raise SetupError('Invalid project ID')
    text(p['name'], 'project name')
    if p['memoryUrl'] != 'https://mcp.zeuglab.com/w/' + p['project']:
        raise SetupError('Memory endpoint does not match the project')
    l = p['linear']
    if not isinstance(l, dict) or set(l) != {'workspaceSlug', 'organizationId', 'teamId', 'teamKey', 'projects'}:
        raise SetupError('Invalid Linear configuration')
    if not isinstance(l['workspaceSlug'], str) or not SLUG.fullmatch(l['workspaceSlug']):
        raise SetupError('Invalid Linear workspace')
    if not all(isinstance(l[k], str) and UUID.fullmatch(l[k]) for k in ('organizationId', 'teamId')):
        raise SetupError('Invalid Linear organization/team ID')
    if not isinstance(l['teamKey'], str) or not re.fullmatch(r'[A-Z][A-Z0-9]{0,15}', l['teamKey']):
        raise SetupError('Invalid Linear team key')
    if not isinstance(l['projects'], list) or not 1 <= len(l['projects']) <= 30:
        raise SetupError('Configure at least one permitted Linear project')
    ids = set()
    for item in l['projects']:
        if not isinstance(item, dict) or set(item) != {'id', 'name'} or not isinstance(item['id'], str) or not UUID.fullmatch(item['id']):
            raise SetupError('Invalid Linear project')
        text(item['name'], 'Linear project name')
        if item['id'] in ids:
            raise SetupError('Duplicate Linear project ID')
        ids.add(item['id'])
    return p


def kit_of(raw):
    if len(raw) > 2_000_000:
        raise SetupError('Kit is too large')
    k = json.loads(raw)
    if k.get('schemaVersion') != 1 or not isinstance(k.get('files'), dict) or len(k['files']) > 40:
        raise SetupError('Unsupported kit format')
    if not isinstance(k.get('sha256'), dict) or set(k['files']) != set(k['sha256']):
        raise SetupError('Incomplete kit checksums')
    required = {'setup.py', 'skill/SKILL.md', 'skill/references/linear.md', 'skill/references/memory.md', 'skill/references/documents.md', 'skill/references/updates.md'}
    if not required.issubset(k['files']):
        raise SetupError('Incomplete kit')
    for name, value in k['files'].items():
        if name not in required and name != 'skill/agents/openai.yaml':
            raise SetupError('Unexpected kit path: ' + name)
        if not isinstance(value, str) or digest(value.encode()) != k['sha256'][name]:
            raise SetupError('Kit checksum mismatch: ' + name)
    return k, digest(encode(k))


def fetch_kit(local=None):
    if local:
        return kit_of(Path(local).read_bytes())
    # No cookies, authorization headers, profile data or tokens are sent to GitHub.
    with urllib.request.urlopen(KIT_URL, timeout=20) as r:
        if r.geturl() != KIT_URL:
            raise SetupError('Unexpected kit redirect')
        return kit_of(r.read(2_000_001))


def guarded(root, rel):
    path = PurePosixPath(rel)
    if path.is_absolute() or '..' in path.parts or '\\' in rel:
        raise SetupError('Unsafe output path')
    dest = root.joinpath(*path.parts)
    cur = dest
    while cur != root:
        if cur.is_symlink():
            raise SetupError('Symlink in managed path: ' + rel)
        cur = cur.parent
    if dest.exists() and not dest.is_file():
        raise SetupError('Expected a file: ' + rel)
    return dest


def write_atomic(dest, data, mode=0o600):
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.zeug-write-', dir=dest.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def recovery_path(rel):
    fixed = {'AGENTS.md', 'CLAUDE.md', '.mcp.json', '.codex/config.toml', '.zeug/setup.py', '.zeug/project.json', '.zeug/PROJECT.md', '.zeug/LINEAR_SOP.md', '.zeug/installed.json'}
    suffixes = {'SKILL.md', 'agents/openai.yaml', 'references/linear.md', 'references/memory.md', 'references/documents.md', 'references/updates.md'}
    return rel in fixed or any(rel == p + s for p in ('.agents/skills/zeug-collaborate/', '.claude/skills/zeug-collaborate/') for s in suffixes)


def recover(root):
    journal = guarded(root, '.zeug/update-journal.json')
    if not journal.exists():
        return
    entries = json.loads(journal.read_text(encoding='utf-8'))
    if not isinstance(entries, dict) or not all(recovery_path(r) for r in entries):
        raise SetupError('Invalid update recovery journal; inspect it before continuing')
    # Restore an interrupted transaction before trusting the previous state receipt.
    for rel, old in entries.items():
        dest = guarded(root, rel)
        if old is None:
            if dest.exists():
                dest.unlink()
        else:
            write_atomic(dest, base64.b64decode(old['data'], validate=True), old['mode'])
    journal.unlink()


def block_merge(current, new, begin, end, expected):
    if current.count(begin) != current.count(end) or current.count(begin) > 1:
        raise SetupError('Malformed managed instruction block')
    if begin in current:
        before, rest = current.split(begin, 1)
        old, after = rest.split(end, 1)
        if expected is None or digest((begin + old + end).encode()) != expected:
            raise SetupError('Managed instructions changed locally')
        return before + new + after
    if expected is not None:
        raise SetupError('Managed instructions were removed locally')
    return current + ('\n\n' if current else '') + new + '\n'


def install(root, profile, kit, revision, dry_run=False):
    root = Path(root).expanduser().absolute()
    if root.is_symlink():
        raise SetupError('Choose a real project directory, not a symlink')
    root = root.resolve()
    recover(root)
    state_path = guarded(root, '.zeug/installed.json')
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    if state and state.get('schemaVersion') != 1:
        raise SetupError('Unsupported installed state')
    old_files, old_blocks = state.get('files', {}), state.get('blocks', {})
    existing_profile = guarded(root, '.zeug/project.json')
    if existing_profile.exists() and json.loads(existing_profile.read_text(encoding='utf-8')).get('project') != profile['project']:
        raise SetupError('This directory belongs to another project')
    planned, hashes, blocks = {}, {}, {}

    def plain(rel, data):
        dest = guarded(root, rel)
        if dest.exists():
            old = dest.read_bytes()
            if old != data and old_files.get(rel) != digest(old):
                raise SetupError('Local file conflict: ' + rel)
        planned[rel] = data
        hashes[rel] = digest(data)

    for rel, body in kit['files'].items():
        if rel == 'setup.py':
            plain('.zeug/setup.py', body.encode())
        else:
            for prefix in ('.agents/skills/zeug-collaborate/', '.claude/skills/zeug-collaborate/'):
                plain(prefix + rel.removeprefix('skill/'), body.encode())
    l = profile['linear']
    project_text = ('# ' + profile['name'] + '\n\nCMD project: ' + profile['project'] +
                    '\nMemory: ' + profile['memoryUrl'] + '\nLinear workspace: https://linear.app/' + l['workspaceSlug'] +
                    '\nOrganization ID: ' + l['organizationId'] + '\nTeam: ' + l['teamKey'] + ' (' + l['teamId'] + ')\n\nPermitted Linear projects:\n' +
                    ''.join('- ' + p['name'] + ': ' + p['id'] + '\n' for p in l['projects']) +
                    '\nAuthenticate with your own accounts. Verify these IDs live before writing. If several projects fit, ask which one.\n')
    plain('.zeug/project.json', encode(profile))
    plain('.zeug/PROJECT.md', project_text.encode())
    plain('.zeug/LINEAR_SOP.md', ('# Project Linear scope\n\n' + project_text + '\nFollow the current workflow in .agents/skills/zeug-collaborate/references/linear.md.\n').encode())
    for rel in ('AGENTS.md', 'CLAUDE.md'):
        instruction = (BEGIN + '\n## Zeug project collaboration\n\nAt each new session run `python3 .zeug/setup.py refresh --target .` (Windows: `python`).\n'
                       'Read `.zeug/PROJECT.md`, `.zeug/LINEAR_SOP.md` and the updated '\
                       + ('.agents' if rel == 'AGENTS.md' else '.claude') + '/skills/zeug-collaborate/SKILL.md.\n'
                       'Use only the configured project and your own accounts. Report refresh failures; hold external writes until current SOPs are verified.\n' + END)
        dest = guarded(root, rel)
        planned[rel] = block_merge(dest.read_text(encoding='utf-8') if dest.exists() else '', instruction, BEGIN, END, old_blocks.get(rel)).encode()
        blocks[rel] = digest(instruction.encode())
    servers = {'linear-' + profile['project']: 'https://mcp.linear.app/mcp', 'zeug-' + profile['project']: profile['memoryUrl']}
    toml_rel = '.codex/config.toml'
    dest = guarded(root, toml_rel)
    current = dest.read_text(encoding='utf-8') if dest.exists() else ''
    outside = re.sub(re.escape(TBEGIN) + r'.*?' + re.escape(TEND), '', current, flags=re.S)
    for name in servers:
        if re.search(r'\[\s*mcp_servers\s*\.\s*["\']?' + re.escape(name) + r'["\']?\s*\]', outside):
            raise SetupError('Existing Codex server conflict: ' + name)
    toml = TBEGIN + '\n' + '\n'.join('[mcp_servers.' + json.dumps(n) + ']\nurl = ' + json.dumps(u) + '\n' for n, u in servers.items()) + TEND
    planned[toml_rel] = block_merge(current, toml, TBEGIN, TEND, old_blocks.get(toml_rel)).encode()
    blocks[toml_rel] = digest(toml.encode())
    dest = guarded(root, '.mcp.json')
    config = json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else {}
    if not isinstance(config, dict) or not isinstance(config.get('mcpServers', {}), dict):
        raise SetupError('Invalid existing .mcp.json')
    existing = config.setdefault('mcpServers', {})
    managed = {n: {'type': 'http', 'url': u} for n, u in servers.items()}
    for name, val in managed.items():
        if name in existing and existing[name] != val and state.get('servers', {}).get(name) != existing[name]:
            raise SetupError('Existing Claude server conflict: ' + name)
        existing[name] = val
    planned['.mcp.json'] = encode(config)
    new_state = {'schemaVersion': 1, 'revision': revision, 'files': hashes, 'blocks': blocks, 'servers': managed}
    planned['.zeug/installed.json'] = encode(new_state)
    # Validate every destination before writing any file.
    destinations = {rel: guarded(root, rel) for rel in planned}
    if not dry_run:
        changes = {rel: data for rel, data in planned.items() if not destinations[rel].exists() or destinations[rel].read_bytes() != data}
        if changes:
            journal = guarded(root, '.zeug/update-journal.json')
            backups = {rel: {'data': base64.b64encode(destinations[rel].read_bytes()).decode(), 'mode': destinations[rel].stat().st_mode & 0o777} if destinations[rel].exists() else None for rel in changes}
            write_atomic(journal, encode(backups))
            try:
                for rel, data in changes.items():
                    old = backups[rel]
                    write_atomic(destinations[rel], data, old['mode'] if old else 0o600)
                journal.unlink()
            except BaseException:
                recover(root)
                raise
    return {'project': profile['project'], 'revision': revision, 'files': len(planned), 'dryRun': dry_run}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'refresh'])
    parser.add_argument('--target', default='.')
    parser.add_argument('--profile')
    parser.add_argument('--kit', help='Use a reviewed local kit instead of fetching GitHub')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        root = Path(args.target).expanduser().absolute()
        if root.is_symlink():
            raise SetupError('Choose a real project directory, not a symlink')
        recover(root.resolve())
        source = Path(args.profile) if args.profile else Path(args.target) / '.zeug/project.json'
        profile = profile_of(json.loads(source.read_text(encoding='utf-8')))
        kit, revision = fetch_kit(args.kit)
        print(json.dumps(install(args.target, profile, kit, revision, args.dry_run)))
        if args.action == 'init':
            print('Project files ready. Open this directory in Codex or Claude Code and approve your own connector sign-ins.')
            print('Codex: codex mcp login linear-' + profile['project'] + '; codex mcp login zeug-' + profile['project'])
            print('Claude Code: /mcp. Select Linear workspace ' + profile['linear']['workspaceSlug'] + '.')
    except (OSError, ValueError, KeyError, TypeError, SetupError) as e:
        print('Setup/refresh failed; installation not certified current: ' + str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
