import base64, copy, importlib.util, json, pathlib, tempfile, unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('setup',ROOT/'setup.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
PROFILE={'schemaVersion':1,'project':'sample-project','name':'Sample project','memoryUrl':'https://mcp.zeuglab.com/w/sample-project','linear':{'workspaceSlug':'sample-workspace','organizationId':'11111111-1111-4111-8111-111111111111','teamId':'22222222-2222-4222-8222-222222222222','teamKey':'SMP','projects':[{'id':'33333333-3333-4333-8333-333333333333','name':'Project'}]}}
class SetupTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)/'project';self.kit,self.rev=s.kit_of((ROOT/'kit.json').read_bytes())
 def install(self,**kw): return s.install(self.root,s.profile_of(copy.deepcopy(PROFILE)),self.kit,self.rev,**kw)
 def snapshot(self): return {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
 def test_new_and_repeat(self):
  self.install();before=self.snapshot();self.install();self.assertEqual(before,self.snapshot());self.assertIn('SMP',(self.root/'.zeug/LINEAR_SOP.md').read_text())
 def test_existing_files_preserved(self):
  self.root.mkdir();(self.root/'AGENTS.md').write_text('# Existing instructions\n');(self.root/'CLAUDE.md').write_text('User rules\n');(self.root/'.mcp.json').write_text(json.dumps({'other':'keep','mcpServers':{'existing':{'type':'http','url':'https://example.org/mcp'}}}));(self.root/'.codex').mkdir();(self.root/'.codex/config.toml').write_text('model = "user-chosen"\n')
  self.install();self.assertTrue((self.root/'AGENTS.md').read_text().startswith('# Existing instructions'));self.assertIn('user-chosen',(self.root/'.codex/config.toml').read_text());self.assertIn('existing',json.loads((self.root/'.mcp.json').read_text())['mcpServers'])
 def test_outside_instruction_edits_survive_update(self):
  self.install();p=self.root/'AGENTS.md';p.write_text('New local policy\n'+p.read_text());self.install();self.assertTrue(p.read_text().startswith('New local policy'))
 def test_managed_conflict_no_writes(self):
  self.install();p=self.root/'.agents/skills/zeug-collaborate/references/linear.md';p.write_text('Custom local rule');before=self.snapshot()
  with self.assertRaises(s.SetupError): self.install()
  self.assertEqual(before,self.snapshot())
 def test_conflicting_mcp_no_partial_install(self):
  self.root.mkdir();p=self.root/'.mcp.json';p.write_text(json.dumps({'mcpServers':{'linear-sample-project':{'command':'user-command'}}}));before=self.snapshot()
  with self.assertRaises(s.SetupError): self.install()
  self.assertEqual(before,self.snapshot())
 def test_symlink_rejected(self):
  self.root.mkdir();outside=pathlib.Path(self.tmp.name)/'outside';outside.mkdir();(self.root/'.zeug').symlink_to(outside,target_is_directory=True)
  with self.assertRaises(s.SetupError): self.install()
  self.assertEqual([],list(outside.iterdir()))
 def test_other_project_rejected(self):
  self.install();p=copy.deepcopy(PROFILE);p['project']='other-project';p['memoryUrl']='https://mcp.zeuglab.com/w/other-project'
  with self.assertRaises(s.SetupError):s.install(self.root,p,self.kit,self.rev)
 def test_profile_rejects_extra_credentials_or_wrong_endpoint(self):
  for changed in [{**PROFILE,'token':'do-not-save'},{**PROFILE,'project':'../outside'},{**PROFILE,'memoryUrl':'https://example.org/mcp'}]:
   with self.assertRaises(s.SetupError):s.profile_of(changed)
 def test_checksum_and_path_rejected(self):
  k=copy.deepcopy(self.kit);k['files']['setup.py']+='tamper'
  with self.assertRaises(s.SetupError):s.kit_of(s.encode(k))
  k=copy.deepcopy(self.kit);k['files']['../outside']='bad';k['sha256']['../outside']=s.digest(b'bad')
  with self.assertRaises(s.SetupError):s.kit_of(s.encode(k))
 def test_refresh_updates_sop_and_records_digest(self):
  self.install();k=copy.deepcopy(self.kit);k['files']['skill/references/linear.md']+='\nNew approved workflow.\n';k['sha256']['skill/references/linear.md']=s.digest(k['files']['skill/references/linear.md'].encode());k,rev=s.kit_of(s.encode(k));s.install(self.root,PROFILE,k,rev)
  self.assertIn('New approved workflow',(self.root/'.agents/skills/zeug-collaborate/references/linear.md').read_text());self.assertEqual(rev,json.loads((self.root/'.zeug/installed.json').read_text())['revision'])
 def test_failed_write_rolls_back_and_next_refresh_succeeds(self):
  self.install();before=self.snapshot();original=s.write_atomic;count=[0]
  k=copy.deepcopy(self.kit);k['files']['skill/references/linear.md']+='\nUpdated rules.\n';k['sha256']['skill/references/linear.md']=s.digest(k['files']['skill/references/linear.md'].encode());k,rev=s.kit_of(s.encode(k))
  def fail_once(*args,**kwargs):
   count[0]+=1
   if count[0]==3:raise PermissionError('injected write failure')
   return original(*args,**kwargs)
  with mock.patch.object(s,'write_atomic',side_effect=fail_once):
   with self.assertRaises(PermissionError):s.install(self.root,PROFILE,k,rev)
  self.assertEqual(before,self.snapshot());s.install(self.root,PROFILE,k,rev)
 def test_interrupted_update_journal_recovers(self):
  self.install();before=self.snapshot();p=self.root/'AGENTS.md';old=p.read_bytes();p.write_bytes(b'incomplete new version')
  (self.root/'.zeug/update-journal.json').write_bytes(s.encode({'AGENTS.md':{'data':base64.b64encode(old).decode(),'mode':0o600}}))
  self.install();self.assertEqual(before,self.snapshot())
 def test_unicode_in_profile_and_existing_instructions_survives(self):
  p=copy.deepcopy(PROFILE);p['name']='Café 合作';p['linear']['projects'][0]['name']='Révision'
  self.root.mkdir();(self.root/'AGENTS.md').write_text('Local café 中文\n',encoding='utf-8')
  s.install(self.root,p,self.kit,self.rev);s.install(self.root,p,self.kit,self.rev)
  self.assertIn('Local café 中文',(self.root/'AGENTS.md').read_text(encoding='utf-8'));self.assertIn('Café 合作',(self.root/'.zeug/PROJECT.md').read_text(encoding='utf-8'))
 def test_dry_run_creates_nothing(self):self.install(dry_run=True);self.assertFalse(self.root.exists())
 def test_config_is_credential_free(self):
  self.install();alltext='\n'.join(b.decode() for b in self.snapshot().values());self.assertNotIn('Bearer ',alltext);self.assertNotIn('api_key',alltext.lower())
if __name__=='__main__':unittest.main()
