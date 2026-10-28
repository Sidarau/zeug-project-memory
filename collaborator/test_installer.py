import json, os, pathlib, socket, subprocess, sys, tempfile, time, unittest, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
class InstallerTest(unittest.TestCase):
 def test_one_command_creates_project_and_refreshes_without_changing_global_home(self):
  with tempfile.TemporaryDirectory() as d:
   tmp=pathlib.Path(d)
   with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
   server=subprocess.Popen([sys.executable,str(ROOT/'tests/mock_cmd.py'),str(ROOT),str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:
    api='http://127.0.0.1:'+str(port)
    for _ in range(40):
     try:urllib.request.urlopen(api+'/repo/SKILL.md',timeout=1).close();break
     except OSError:time.sleep(.1)
    (tmp/'home/.claude/skills/zeug-project-memory').mkdir(parents=True);(tmp/'home/.claude/skills/zeug-project-memory/SKILL.md').write_text('Existing customized global skill')
    (tmp/'conf').mkdir();(tmp/'conf/zz-ci.env').write_text('Existing private key record')
    env=dict(os.environ,ZEUG_INSTALL_HOME=str(tmp/'home'),ZEUG_CONFIG_DIR=str(tmp/'conf'),ZEUG_API=api,ZEUG_REPO_RAW=api+'/repo',ZEUG_PROJECT='zz-ci',ZEUG_KEY='zlm_'+'T'*43,ZEUG_PROJECT_SETUP='1',ZEUG_PROJECT_DIR=str(tmp/'project'))
    result=subprocess.run(['sh',str(ROOT/'install.sh')],env=env,cwd=tmp,capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
    self.assertTrue((tmp/'project/AGENTS.md').exists());self.assertTrue((tmp/'project/CLAUDE.md').exists())
    self.assertEqual((tmp/'conf/zz-ci.env').read_text(),'Existing private key record');self.assertEqual((tmp/'home/.claude/skills/zeug-project-memory/SKILL.md').read_text(),'Existing customized global skill')
    for p in (tmp/'project').rglob('*'):
     if p.is_file():self.assertNotIn('zlm_'+'T'*43,p.read_text())
    result=subprocess.run([sys.executable,str(tmp/'project/.zeug/setup.py'),'refresh','--target',str(tmp/'project'),'--kit',str(ROOT/'collaborator/kit.json')],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
   finally:server.terminate();server.wait(timeout=5)
if __name__=='__main__':unittest.main()
