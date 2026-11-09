"""作者复现检查：只在本模块的临时目录运行，结束时清理自己的服务与副本。"""
from pathlib import Path
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time

MODULE = Path(__file__).resolve().parent
ROOT = MODULE.parents[1]
DOCS = ROOT / 'docs/02-deployment'
results = []
transcripts = {}
env = os.environ.copy()
for key in ['QUERY_CURRENCY', 'HOST', 'PORT', 'HOST_PORT']:
    env.pop(key, None)
env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')


def run(args, cwd, check=True, extra=None):
    result = subprocess.run(args, cwd=cwd, env={**env, **(extra or {})}, text=True,
                            capture_output=True, timeout=60)
    if check and result.returncode:
        raise AssertionError((args, result.stdout, result.stderr))
    return result


def passed(name):
    results.append(name)
    print('PASS', name, flush=True)


with tempfile.TemporaryDirectory(prefix='author-check.', dir=MODULE) as temporary:
    temp = Path(temporary)
    for filename, prefix in [('02-files-and-logs.md', 'practice'),
                             ('03-git-changes.md', 'git-practice'),
                             ('04-git-collaboration.md', 'git-collab'),
                             ('05-environment-and-permissions.md', 'practice')]:
        area = temp / filename[:2]
        area.mkdir()
        blocks = re.findall(r'```sh\n(.*?)```', (DOCS / filename).read_text(), re.S)
        script = '\n'.join(blocks)
        script = script.replace('mktemp -d "$PWD/', f'mktemp -d "{area}/')
        out = run(['/bin/zsh', '-f', '-c', script], MODULE)
        transcripts[filename] = {'stdout': out.stdout, 'stderr': out.stderr}
        work = next(area.glob(prefix + '.*'))
        if filename.startswith('02'):
            assert (work/'errors-only.txt').read_text().count('\n') == 2
            lines = (work/'issues-time-order.txt').read_text().splitlines()
            assert 'r003' in lines[0] and 'r004' in lines[1]
            assert not (work/'normal.txt').read_text()
            assert 'No such file' in (work/'errors.txt').read_text()
            assert out.stdout.rstrip().endswith('2')
        elif filename.startswith('03'):
            assert (work/'query.txt').read_text() == 'customer=C001\ncurrency=CNY\ntimeout=3\n'
            assert not run(['git', 'status', '--short'], work).stdout
            assert run(['git', 'rev-list', '--count', 'HEAD'], work).stdout.strip() == '3'
            assert 'MM query.txt' in out.stdout
        elif filename.startswith('04'):
            bob = work/'bob'
            assert (bob/'query.conf').read_text() == 'mode=balanced\ncurrency=CNY\n'
            assert 'scratch.txt' in run(['git', 'status', '--short'], bob).stdout
            assert not (bob/'experiment.txt').exists()
            assert run(['git', 'rev-list', '--count', 'HEAD'], bob).stdout.strip() == '7'
            assert 'Not possible to fast-forward' in out.stderr
            assert 'CONFLICT' in out.stdout
            assert not run(['git', 'stash', 'list'], bob).stdout
            # 收尾补查 Alice 可以快进到 Bob 推送的合并提交。
            run(['git', 'pull', '--ff-only'], work/'alice')
            assert 'mode=balanced' in (work/'alice/query.conf').read_text()
        else:
            assert out.stdout.count('读取结果：12800 CNY') == 4
            assert 'PermissionError' in out.stderr
            assert out.stderr.count('配置错误') == 3
            assert (work/'.venv/bin/activate').exists()
            assert 'No broken requirements found.' in out.stdout
        passed(filename + ' 全部 sh 块按顺序重放')

    source = (MODULE/'service-lab/server.py').read_text()
    blocks = re.findall(r'```python\n(.*?)```', (DOCS/'08-delivery-lab.md').read_text(), re.S)
    assert source in blocks
    for language, filename in [('dockerfile', 'Dockerfile'), ('yaml', 'compose.yaml'), ('text', '.dockerignore')]:
        blocks = re.findall('```'+language+r'\n(.*?)```', (DOCS/'09-docker-compose.md').read_text(), re.S)
        assert (MODULE/'service-lab'/filename).read_text() in blocks
    passed('正文完整源码与三个容器配置文件一致')

    service = temp/'delivery'
    shutil.copytree(MODULE/'service-lab', service)
    run(['git', 'init', '-b', 'main'], service)
    for key, value in [('user.name', 'Author Check'), ('user.email', 'author@example.invalid'), ('commit.gpgsign', 'false')]:
        run(['git', 'config', '--local', key, value], service)
    run(['git', 'add', '.'], service)
    run(['git', 'commit', '-m', 'Initial sample'], service)
    (service/'data/balances.json').write_text('{"C001": 12800, "C002": 0, "C003": 500}\n')
    run([sys.executable, '-m', 'json.tool', 'data/balances.json'], service)
    run(['git', 'add', 'data/balances.json'], service)
    run(['git', 'commit', '-m', 'Add C003'], service)
    run([str(ROOT/'.venv-docs/bin/python'), '-m', 'venv', '.venv'], service)
    run([str(service/'.venv/bin/python'), '-m', 'pip', 'check'], service)
    passed('综合练习独立仓库修改提交、JSON 和 Python 3.12 venv')

    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    service_env = {**env, 'QUERY_CURRENCY': 'CNY', 'HOST': '127.0.0.1', 'PORT': str(port)}
    (service/'logs').mkdir(exist_ok=True)
    process = None
    try:
        with (service/'logs/service.log').open('w') as log:
            process = subprocess.Popen([str(service/'.venv/bin/python'), 'server.py'], cwd=service,
                                       env=service_env, stdout=log, stderr=subprocess.STDOUT)
            for _ in range(100):
                if process.poll() is not None:
                    raise AssertionError('服务启动后退出')
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=0.1):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                raise AssertionError('启动超时')
            def request(path, status, field, value):
                response = run(['curl', '-sS', '--max-time', '3', '-w', '\n%{http_code}',
                                f'http://127.0.0.1:{port}{path}'], service)
                body, code = response.stdout.rsplit('\n', 1)
                assert int(code) == status and json.loads(body)[field] == value
            request('/health', 200, 'status', 'ok')
            for customer, amount in [('C001', 12800), ('C002', 0), ('C003', 500)]:
                request('/receivables/'+customer, 200, 'amount', amount)
            request('/receivables/C999', 404, 'error', 'customer_not_found')
            request('/absent', 404, 'error', 'route_not_found')
            passed('HTTP health、三个余额、未知客户和未知路由')
            listener = run(['lsof', '-nP', f'-iTCP:{port}', '-sTCP:LISTEN'], service)
            assert str(process.pid) in listener.stdout
            run(['ps', '-p', str(process.pid), '-o', 'pid,ppid,%cpu,%mem,command'], service)
            duplicate = run([sys.executable, 'server.py'], service, check=False, extra=service_env)
            assert duplicate.returncode and 'Address already in use' in duplicate.stderr
            missing = run([sys.executable, 'server.py'], service, check=False, extra={'PORT': str(port)})
            assert missing.returncode and 'QUERY_CURRENCY=CNY' in missing.stderr
            invalid = run([sys.executable, 'server.py'], service, check=False,
                          extra={'QUERY_CURRENCY': 'CNY', 'PORT': 'bad'})
            assert invalid.returncode and 'PORT' in invalid.stderr
            passed('PID/端口对应、占用、缺配置、非法端口')
            data = service/'data/balances.json'
            saved = data.with_suffix('.json.saved')
            data.rename(saved)
            request('/health', 200, 'status', 'ok')
            request('/receivables/C003', 500, 'error', 'data_unavailable')
            saved.rename(data)
            request('/receivables/C003', 200, 'amount', 500)
            assert not run(['git', 'status', '--short'], service).stdout
            passed('缺数据500、health仍200、恢复后200、工作区干净')
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)
        stopped = run(['curl', '-sS', '--max-time', '3', f'http://127.0.0.1:{port}/health'], service, check=False)
        assert stopped.returncode == 7
        log_text = (service/'logs/service.log').read_text()
        assert 'data_read_failed' in log_text and 'FileNotFoundError' in log_text
        transcripts['service'] = {'port': port, 'log': log_text, 'stopped_returncode': stopped.returncode}
        passed('只终止本次 PID、端口连接失败与错误日志')
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

config = json.loads(run(['docker', 'compose', '-p', 'receivable-demo', 'config', '--format', 'json'], MODULE/'service-lab').stdout)
assert config['services']['query']['ports'][0]['published'] == '8029'
changed = json.loads(run(['docker', 'compose', '-p', 'receivable-demo', 'config', '--format', 'json'], MODULE/'service-lab', extra={'HOST_PORT': '8039'}).stdout)
assert changed['services']['query']['ports'][0]['published'] == '8039'
assert changed['services']['query']['environment']['PORT'] == '8028'
assert changed['services']['query']['volumes'][0]['read_only']
passed('Compose 默认端口、插值覆盖、内部环境与只读挂载解析')
report = {'checks': results, 'transcripts': transcripts,
          'not_executed': ['远程 SSH/scp/隧道', 'Linux ss/systemd/journalctl', 'tmux', 'Docker build/up/exec/down']}
(MODULE/'VERIFICATION-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print('全部作者检查通过；临时副本及本次服务已清理。')
