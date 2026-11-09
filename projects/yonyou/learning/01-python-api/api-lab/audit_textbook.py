from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, re, subprocess, sys, tempfile, shutil, os, contextlib, io
R=Path(__file__).resolve().parents[3]
D=R/'docs/01-python-api'
L=R/'learning/01-python-api'
S=R/'site'
PYTHON=L/'.venv-api/bin/python'
class Page(HTMLParser):
    def __init__(self, content):
        super().__init__();self.ids=set();self.links=[];self.article=0;self.details=0
        self.feed(content)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        if tag=='article':self.article+=1
        if tag=='details':self.details+=1
        if tag=='a' and self.article and 'href' in a:self.links.append(a['href'])
    def handle_endtag(self,tag):
        if tag=='article':self.article-=1
pages={p.resolve():Page(p.read_text()) for p in S.rglob('*.html')}
broken=[];count=0
for p in sorted((S/'01-python-api').glob('*.html')):
    page=pages[p.resolve()]
    for href in page.links:
        u=urlsplit(href)
        if u.scheme or u.netloc:continue
        target=(S/u.path.lstrip('/') if u.path.startswith('/') else p.parent/unquote(u.path)).resolve() if u.path else p.resolve()
        count+=1
        if not target.exists():broken.append([p.name,href,'missing file'])
        elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:
            broken.append([p.name,href,'missing anchor'])
print(json.dumps({'content_links_checked':count,'broken':broken},ensure_ascii=False,indent=2))
if broken:sys.exit(1)
checks=[]
def check(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(name)
# 01 的原始示例直接来自正文。
s=(D/'01-reading-python.md').read_text()
blocks=re.findall(r'```python\n(.*?)\n```',s,re.S)
source=next(b for b in blocks if 'def query_receivable(customer_id):' in b and 'balances = ' in b)
ns={}
with contextlib.redirect_stdout(io.StringIO()):exec(source,ns)
check('01 原例成功与零金额',ns['query_receivable']('C001')['amount']==12800 and ns['query_receivable']('C002')['amount']==0)
try:ns['query_receivable']('C999')
except ValueError:check('01 未知客户异常',True)
else:raise AssertionError('01 failed path')
for file,expected in [
    ('02-types-and-contracts.py',"{'customer_id': 'C001', 'amount': 12800}\n{'customer_id': 'C002', 'amount': 0}\nNone\n"),
    ('03-errors-and-debugging.py','C001 12800\nC999 查询失败： 客户不存在\nC002 0\n本批查询结束\n'),
    ('05-async-and-tasks.py','顺序结果： [12800, 0]\n并发结果： [12800, 0]\n查询超时\n查询已取消\n'),
    ('builtin-exceptions-usage.py','无效参数： ValueError\n无效参数： ValueError\n无效参数： TypeError\n查询条数： 5\n'),
]:
    result=subprocess.run([str(PYTHON),str(L/file)],capture_output=True,text=True,check=True)
    check(file+' 输出',result.stdout==expected)
result=subprocess.run([str(PYTHON),str(L/'06-json-roundtrip.py')],capture_output=True,text=True,check=True)
check('06 JSON 往返与错误格式',result.stdout.startswith('dict str bytes\n') and '\nTrue\nTrue\n' in result.stdout and 'JSON 格式不合法' in result.stdout)
with tempfile.TemporaryDirectory() as tmp:
    t=Path(tmp)
    for f in (L/'04-mini-project').glob('*.py'):shutil.copy(f,t/f.name)
    for cid,expected in [('C001',"{'customer_id': 'C001', 'amount': 12800}"),('C002',"{'customer_id': 'C002', 'amount': 0}"),('C999','查询失败： 客户不存在')]:
        result=subprocess.run([str(PYTHON),str(t/'main.py')],env={**os.environ,'CUSTOMER_ID':cid},capture_output=True,text=True,check=True)
        check('04 入口 '+cid,result.stdout.strip()==expected)
    log=(t/'query.log').read_text()
    subprocess.run([str(PYTHON),'-c','import main'],cwd=t,check=True)
    check('04 导入不触发查询或新增日志',(t/'query.log').read_text()==log)
# 新教材的主示例代码须与运行文件一致。
for doc,files in [
    ('07-fastapi-and-pydantic.md',['domain.py','models.py','app_api.py']),
    ('08-httpx-and-upstream.md',['erp_client.py','app_gateway.py']),
]:
    text=(D/doc).read_text()
    for f in files:check(doc+' 与 '+f+' 一致',(L/'api-lab'/f).read_text().strip() in text)
for doc,f in [('09-streaming-and-sse.md','app_stream.py'),('10-websocket-and-selection.md','app_ws.py')]:
    server=(L/'api-lab'/f).read_text().split('@app.get("/", response_class=HTMLResponse)')[0].strip()
    check(doc+' 服务端示例与文件一致',server in (D/doc).read_text())
for p in sorted(D.glob('*.md')):
    check(p.name+' 无占位标记','[[' not in p.read_text())
for p in sorted(D.glob('[0-9][0-9]-*.md')):
    page=pages[(S/'01-python-api'/p.with_suffix('.html').name).resolve()]
    check(p.name+' 折叠参考内容可渲染',page.details>0)
report={'date':'2026-10-22','content_links_checked':count,'broken_links':broken,'checks_passed':len(checks),'checks':checks}
(L/'TEXTBOOK-VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(f'PASS {len(checks)} 项教材检查；正文链接及锚点 {count} 条')
