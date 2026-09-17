"""Studio MCP stdio endpoint. Calls the running local server; no Hermes config writes."""
import json, os, sys, urllib.request, urllib.error
URL=os.environ.get('STUDIO_URL','http://127.0.0.1:8787').rstrip('/')
TOKEN=os.environ.get('STUDIO_TOKEN','')
TOOLS=[
 {'name':'studio_workspace','description':'Read the Studio brand, active creative, source materials, and saved creatives.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}},
 {'name':'studio_generate','description':'Generate one campaign background with an authorised Hermes image provider. Costs model usage. Returns a job ID; poll studio_job. Use studio_catalog to find providers and models.','inputSchema':{'type':'object','properties':{'prompt':{'type':'string'},'profile':{'type':'string','default':'default'},'provider':{'type':'string'},'model':{'type':'string'},'aspect':{'type':'string','enum':['portrait','square','landscape']},'references':{'type':'array','items':{'type':'string'},'description':'Local /media/ or /references/ image URLs from Studio.'}},'required':['prompt','provider','model'],'additionalProperties':False}},
 {'name':'studio_catalog','description':'Discover Hermes profiles, available authorised image providers/models, and skills. Returns a job ID.','inputSchema':{'type':'object','properties':{'profile':{'type':'string','default':'default'}},'additionalProperties':False}},
 {'name':'studio_job','description':'Get the status/result of a Studio job. Generated results contain a local image URL.','inputSchema':{'type':'object','properties':{'job':{'type':'string'}},'required':['job'],'additionalProperties':False}}
]
def request(path,data=None):
    req=urllib.request.Request(URL+'/api/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+TOKEN} if TOKEN else {})})
    with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
def handle(msg):
    method=msg.get('method');params=msg.get('params',{})
    if method=='initialize':return {'protocolVersion':params.get('protocolVersion','2025-03-26'),'capabilities':{'tools':{}},'serverInfo':{'name':'stillroom-studio','version':'1.0.0'}}
    if method=='ping':return {}
    if method=='tools/list':return {'tools':TOOLS}
    if method=='tools/call':
        try:
            name=params['name'];args=params.get('arguments',{})
            if name=='studio_workspace':result=request('state')
            elif name=='studio_catalog':result=request('jobs',{'op':'catalog','profile':args.get('profile','default')})
            elif name=='studio_generate':result=request('jobs',{**args,'op':'generate'})
            elif name=='studio_job':
                import re
                if not re.fullmatch('[a-f0-9]{32}',args['job']):raise ValueError('Invalid job ID')
                result=request('jobs/'+args['job'])
            else:raise ValueError('Unknown tool')
            return {'content':[{'type':'text','text':json.dumps(result)}]}
        except Exception as e:return {'isError':True,'content':[{'type':'text','text':str(e)}]}
    if method and method.startswith('notifications/'):return None
    raise ValueError('Method not found')
if __name__=='__main__':
    for line in sys.stdin:
        try:
            msg=json.loads(line);result=handle(msg)
            if 'id' in msg:print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':result}),flush=True)
        except Exception as e:
            print(json.dumps({'jsonrpc':'2.0','id':None,'error':{'code':-32603,'message':str(e)}}),flush=True)
