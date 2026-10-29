import base64, csv, hashlib, io, json, os, secrets, uuid
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from argon2 import PasswordHasher
import jwt
from .core.config import DISCLAIMER, SCORE_NOTE, GRADCAM_NOTE, MAX_UPLOAD_BYTES, LABELS
from .inference.preprocess import load_image
from PIL import Image
from .inference.registry import MODELS, card, sha256
from .inference.predict import predict, gradcam
from .db import connect, audit, audit_valid

app=FastAPI(title="ChestX-ray AI Assist",version="0.1.0",description=DISCLAIMER)
ph=PasswordHasher()
_jwt_secret = os.getenv("JWT_SECRET")
SECRET = _jwt_secret.encode("utf-8") if _jwt_secret else secrets.token_bytes(32)
ALGS=["HS256"]
IMAGE_CACHE=OrderedDict(); IMAGE_CACHE_LIMIT=100

class CompareRequest(BaseModel):
    models:list[str]

def remember_image(analysis_id,image):
    preview=io.BytesIO(); image.convert("L").resize((224,224),Image.Resampling.BILINEAR).save(preview,format="PNG")
    IMAGE_CACHE[analysis_id]={"png":preview.getvalue(),"size":image.size}; IMAGE_CACHE.move_to_end(analysis_id)
    while len(IMAGE_CACHE)>IMAGE_CACHE_LIMIT: IMAGE_CACHE.popitem(last=False)

def retrieve_image(analysis_id):
    cached=IMAGE_CACHE.get(analysis_id)
    if cached is None: raise HTTPException(410,"The in-memory image is no longer available. Upload the study again to generate this view.")
    IMAGE_CACHE.move_to_end(analysis_id)
    return Image.open(io.BytesIO(cached["png"])).convert("L")

def retrieve_image_size(analysis_id):
    cached=IMAGE_CACHE.get(analysis_id)
    if cached is None: raise HTTPException(410,"The in-memory image is no longer available. Upload the study again to generate this view.")
    return tuple(cached["size"])

def get_saved_analysis(c,analysis_id):
    row=c.execute("SELECT result_json,feedback_json,input_hash FROM analyses WHERE id=?",(analysis_id,)).fetchone()
    if not row: raise HTTPException(404,"Analysis not found.")
    return json.loads(row[0]),json.loads(row[1]),row[2]

async def analyze_bytes(content,filename,model,case_id,user):
    if len(content)>MAX_UPLOAD_BYTES: raise HTTPException(413,"File exceeds the configured upload limit.")
    try:image,warnings=load_image(content,filename)
    except ValueError as e:raise HTTPException(400,str(e))
    digest=hashlib.sha256(content).hexdigest()
    try:result=predict(image,model)
    except (RuntimeError,ValueError) as e:raise HTTPException(503,str(e))
    analysis_id=str(uuid.uuid4()); remember_image(analysis_id,image)
    preview=io.BytesIO(); image.convert("L").resize((224,224),Image.Resampling.BILINEAR).save(preview,format="PNG")
    result.update({"id":analysis_id,"created_at":datetime.now(timezone.utc).isoformat(),"case_id":case_id,"quality_warnings":warnings,"model_input_preview":"data:image/png;base64,"+base64.b64encode(preview.getvalue()).decode("ascii"),"disclaimer":DISCLAIMER,"score_note":SCORE_NOTE,"gradcam_note":GRADCAM_NOTE,"review_status":"needs_review"})
    persisted={k:v for k,v in result.items() if k!="model_input_preview"}
    c=connect(); c.execute("INSERT INTO analyses(id,created_at,model,result_json,input_hash,case_id,feedback_json) VALUES(?,?,?,?,?,?,?)",(analysis_id,result["created_at"],model,json.dumps(persisted),digest,case_id,"{}")); c.commit(); audit(c,user["sub"],"analysis_created",result["model_sha256"],case_id,digest)
    return result

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def headers(request,call_next):
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["Content-Security-Policy"]="default-src 'self' *; img-src 'self' data: blob: *; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src *"
    return response

def current_user(authorization: str|None=Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401,"Sign in required.")
    try: return jwt.decode(authorization[7:],SECRET,algorithms=ALGS)
    except Exception: raise HTTPException(401,"Session expired; sign in again.")

@app.get("/api/v1/health")
def health(): return {"status":"ok","models_ready":{n: p[0].exists() for n,p in MODELS.items()},"disclaimer":DISCLAIMER}

@app.get("/api/v1/version")
def version(): return {"name":"ChestX-ray AI Assist","version":app.version,"disclaimer":DISCLAIMER}

@app.post("/api/v1/setup")
def setup(username:str=Form(...),password:str=Form(...)):
    c=connect()
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0]: raise HTTPException(409,"Initial setup is already complete.")
    if len(password)<12: raise HTTPException(400,"Use a password with at least 12 characters.")
    c.execute("INSERT INTO users VALUES(?,?,?)",(username,ph.hash(password),"admin")); c.commit()
    audit(c,username,"first_run_admin_created")
    return {"created":True,"message":"Local administrator created. Sign in to continue."}

@app.post("/api/v1/session")
def session(username:str=Form(...),password:str=Form(...)):
    c=connect(); user=c.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
    if not user:
        audit(c,"anonymous","login_failed"); raise HTTPException(401,"Invalid username or password.")
    try: ph.verify(user["password_hash"],password)
    except Exception:
        audit(c,username,"login_failed"); raise HTTPException(401,"Invalid username or password.")
    token=jwt.encode({"sub":username,"role":user["role"],"exp":datetime.now(timezone.utc)+timedelta(hours=8)},SECRET,algorithm="HS256")
    audit(c,username,"login")
    return {"access_token":token,"token_type":"bearer","role":user["role"]}

@app.get("/api/v1/models")
def models(user=Depends(current_user)):
    return {"models":[{"name":n,"ready":p[0].exists(),"sha256":None} for n,p in MODELS.items()],"default":"D"}

@app.get("/api/v1/models/{name}/card")
def model_card(name:str,user=Depends(current_user)):
    try:return card(name)
    except ValueError:raise HTTPException(404,"Unknown model.")

@app.post("/api/v1/analyses")
async def analyze(file:UploadFile=File(...),model:str=Form("D"),case_id:str=Form(""),user=Depends(current_user)):
    content=await file.read(MAX_UPLOAD_BYTES+1)
    return await analyze_bytes(content,file.filename or "",model,case_id,user)

@app.post("/api/v1/analyses/{analysis_id}/compare")
def compare_models(analysis_id:str,request:CompareRequest,user=Depends(current_user)):
    selected=list(dict.fromkeys(request.models))
    if not selected or len(selected)>5 or any(name not in MODELS for name in selected):raise HTTPException(400,"Select between one and five available models.")
    image=retrieve_image(analysis_id); compared=[]
    for name in selected:
        try:compared.append(predict(image,name))
        except (RuntimeError,ValueError) as e:raise HTTPException(503,str(e))
    c=connect(); base,_,_=get_saved_analysis(c,analysis_id)
    base["comparison"]=[{"model":r["model"],"model_sha256":r["model_sha256"],"findings":r["findings"]} for r in compared]
    c.execute("UPDATE analyses SET result_json=? WHERE id=?",(json.dumps(base),analysis_id)); c.commit(); audit(c,user["sub"],"models_compared",case_id=analysis_id)
    return {"analysis_id":analysis_id,"models":compared,"disclaimer":DISCLAIMER,"score_note":SCORE_NOTE}

@app.get("/api/v1/analyses/{analysis_id}/gradcam")
def analysis_gradcam(analysis_id:str,finding:str=Query(...),model:str=Query("D"),user=Depends(current_user)):
    if model not in MODELS:raise HTTPException(400,"Unknown model.")
    image=retrieve_image(analysis_id)
    try:content=gradcam(image,model,finding,output_size=retrieve_image_size(analysis_id))
    except ValueError as e:raise HTTPException(400,str(e))
    except RuntimeError as e:raise HTTPException(503,str(e))
    c=connect(); saved,_,_=get_saved_analysis(c,analysis_id); audit(c,user["sub"],"gradcam_requested",sha256(MODELS[model][0]),saved.get("case_id",""))
    return {"finding":finding,"model":model,"image":"data:image/png;base64,"+base64.b64encode(content).decode("ascii"),"caption":GRADCAM_NOTE}

@app.post("/api/v1/batch")
async def analyze_batch(files:list[UploadFile]=File(...),model:str=Form("D"),case_id:str=Form(""),user=Depends(current_user)):
    if not files or len(files)>20:raise HTTPException(400,"Select between 1 and 20 images per batch.")
    results=[]
    for f in files:
        content=await f.read(MAX_UPLOAD_BYTES+1)
        try:r=await analyze_bytes(content,f.filename or "",model,case_id,user); results.append({k:v for k,v in r.items() if k!="model_input_preview"})
        except HTTPException as e:results.append({"filename":f.filename,"error":e.detail})
    return {"count":len(results),"completed":sum("error" not in r for r in results),"results":results}

@app.get("/api/v1/analyses")
def list_analyses(q:str="",case_id:str="",user=Depends(current_user)):
    c=connect(); rows=[json.loads(r[0]) for r in c.execute("SELECT result_json FROM analyses ORDER BY created_at DESC")]
    if q:
        needle=q.casefold(); rows=[r for r in rows if needle in str(r.get("case_id","")).casefold() or needle in r.get("model","").casefold()]
    if case_id:rows=[r for r in rows if r.get("case_id")==case_id]
    return rows

@app.get("/api/v1/analyses/{analysis_id}")
def get_analysis(analysis_id:str,user=Depends(current_user)):
    c=connect(); row=c.execute("SELECT result_json FROM analyses WHERE id=?",(analysis_id,)).fetchone()
    if not row:raise HTTPException(404,"Analysis not found.")
    return json.loads(row[0])

@app.get("/api/v1/analyses/{analysis_id}/input-preview")
def analysis_input_preview(analysis_id:str,user=Depends(current_user)):
    image=retrieve_image(analysis_id);out=io.BytesIO();image.save(out,format="PNG")
    return {"model_input_preview":"data:image/png;base64,"+base64.b64encode(out.getvalue()).decode("ascii")}

@app.get("/api/v1/analyses/{analysis_id}/report.json")
def report_json(analysis_id:str,user=Depends(current_user)):
    c=connect();result,feedbacks,input_hash=get_saved_analysis(c,analysis_id)
    return {"title":"AI-assisted analysis report","analysis":result,"feedback":feedbacks,"input_sha256":input_hash,"disclaimer":DISCLAIMER,"score_note":SCORE_NOTE}

@app.get("/api/v1/analyses/{analysis_id}/report.csv")
def report_csv(analysis_id:str,user=Depends(current_user)):
    c=connect();result,feedbacks,input_hash=get_saved_analysis(c,analysis_id)
    out=io.StringIO();writer=csv.writer(out);writer.writerow(["report disclaimer",DISCLAIMER]);writer.writerow(["score interpretation",SCORE_NOTE]);writer.writerow(["analysis_id","case_id","created_at","model","model_sha256","finding","model_score_not_calibrated_probability","threshold","above_threshold","reliability","reviewer_decision","input_sha256"])
    for f in result.get("findings",[]):writer.writerow([result["id"],result.get("case_id",""),result["created_at"],result["model"],result["model_sha256"],f["finding"],f["score"],f["threshold"],f["above_threshold"],f["reliability"],feedbacks.get(f["finding"],{}).get("decision",""),input_hash])
    return StreamingResponse(iter([out.getvalue()]),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename=analysis-{analysis_id}.csv"})

@app.get("/api/v1/analyses/{analysis_id}/report.pdf")
def report_pdf(analysis_id:str,finding:str|None=None,model:str|None=None,user=Depends(current_user)):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    c=connect();result,feedbacks,input_hash=get_saved_analysis(c,analysis_id)
    out=io.BytesIO();pdf=canvas.Canvas(out,pagesize=letter);width,height=letter;y=height-48
    pdf.setTitle("AI-assisted analysis report");pdf.setFont("Helvetica-Bold",16);pdf.drawString(42,y,"AI-assisted analysis report");y-=25
    pdf.setFont("Helvetica",9)
    for line in [f"Case ID: {result.get('case_id') or 'Not provided'}",f"UTC: {result['created_at']}",f"Model: {result['model']}",f"Model SHA-256: {result['model_sha256']}",f"Input SHA-256: {input_hash}"]:
        pdf.drawString(42,y,line[:120]);y-=14
    y-=8;pdf.setFont("Helvetica-Bold",9);pdf.drawString(42,y,"Finding");pdf.drawString(190,y,"Score");pdf.drawString(260,y,"Threshold");pdf.drawString(350,y,"Signal");pdf.drawString(430,y,"Reliability");y-=14;pdf.setFont("Helvetica",8)
    for f in result.get("findings",[]):
        if y<90:pdf.showPage();y=height-48;pdf.setFont("Helvetica",8)
        pdf.drawString(42,y,f["finding"]);pdf.drawString(190,y,f"{f['score']:.4f}");pdf.drawString(260,y,f"{f['threshold']:.4f}");pdf.drawString(350,y,"Above threshold" if f["above_threshold"] else "Below threshold");pdf.drawString(430,y,f["reliability"]);y-=13
    y=min(y-10,90);pdf.setFont("Helvetica",8)
    for text in [DISCLAIMER,SCORE_NOTE,"Scores are model outputs, not calibrated probabilities."]:
        for j in range(0,len(text),105):
            if y<45:pdf.showPage();y=height-48;pdf.setFont("Helvetica",8)
            pdf.drawString(42,y,text[j:j+105]);y-=11
    if finding and model and finding in LABELS and model in MODELS and analysis_id in IMAGE_CACHE:
        if y<210:pdf.showPage();y=height-48;pdf.setFont("Helvetica",8)
        pdf.setFont("Helvetica-Bold",9);pdf.drawString(42,y,"Selected Grad-CAM influence map");y-=10
        try:
            image=retrieve_image(analysis_id);cam=gradcam(image,model,finding,output_size=retrieve_image_size(analysis_id))
            pdf.drawImage(ImageReader(io.BytesIO(cam)),42,y-150,width=150,height=150,preserveAspectRatio=True,mask="auto")
            pdf.setFont("Helvetica",7);pdf.drawString(42,y-160,GRADCAM_NOTE[:120]);y-=175
        except (ValueError,RuntimeError):pass
    if feedbacks:
        if y<65:pdf.showPage();y=height-48
        pdf.drawString(42,y,"Reviewer feedback:");y-=12
        for finding,value in feedbacks.items():pdf.drawString(48,y,f"{finding}: {value.get('decision','')} · {value.get('reviewer','')}");y-=11
    if y<45:pdf.showPage();y=height-48
    pdf.line(42,y-15,260,y-15);pdf.setFont("Helvetica",8);pdf.drawString(42,y-28,"Reviewer signature / date")
    pdf.save();out.seek(0)
    return StreamingResponse(out,media_type="application/pdf",headers={"Content-Disposition":f"attachment; filename=analysis-{analysis_id}.pdf"})

@app.post("/api/v1/analyses/{analysis_id}/feedback")
def feedback(analysis_id:str, finding:str=Form(...),decision:str=Form(...),note:str=Form(""),user=Depends(current_user)):
    if finding not in LABELS or decision not in {"agree","disagree","unsure"}:raise HTTPException(400,"Invalid feedback values.")
    c=connect(); row=c.execute("SELECT feedback_json,result_json FROM analyses WHERE id=?",(analysis_id,)).fetchone()
    if not row:raise HTTPException(404,"Analysis not found.")
    feedbacks=json.loads(row[0]); feedbacks[finding]={"decision":decision,"note":note[:500],"reviewer":user["sub"],"utc":datetime.now(timezone.utc).isoformat()}
    result=json.loads(row[1]); result["review_status"]="reviewed" if len(feedbacks)==len(LABELS) else "in_review"
    c.execute("UPDATE analyses SET feedback_json=?,result_json=? WHERE id=?",(json.dumps(feedbacks),json.dumps(result),analysis_id)); c.commit(); audit(c,user["sub"],"feedback_saved",case_id=analysis_id); return {"saved":True,"review_status":result["review_status"]}

@app.get("/api/v1/audit")
def get_audit(user=Depends(current_user)):
    if user.get("role")!="admin":raise HTTPException(403,"Admin role required.")
    c=connect(); rows=[dict(r) for r in c.execute("SELECT * FROM audit ORDER BY seq")]
    return {"integrity_valid":audit_valid(c),"entries":rows}

@app.exception_handler(Exception)
async def general_error(request,exc):
    return JSONResponse(status_code=500,content={"error":{"code":"internal_error","message":"Request could not be completed."}})

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .core.config import ROOT

DIST_DIR = ROOT / "frontend" / "dist"
if DIST_DIR.is_dir() and (DIST_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        target = DIST_DIR / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        return FileResponse(DIST_DIR / "index.html")
