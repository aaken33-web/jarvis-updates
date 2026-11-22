
import os, json, time, sqlite3, logging, ast, re, sys
from pathlib import Path
from datetime import datetime, timedelta
import requests

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; LOGS=ROOT/"logs"; WORK=ROOT/"workspace"
SKILLS=DATA/"skills"; BACKUPS=ROOT/"backups"
for p in (DATA,LOGS,WORK,SKILLS,BACKUPS): p.mkdir(exist_ok=True)
DB=DATA/"jarvis13_autonomy.db"
OLLAMA="http://127.0.0.1:11434"
MODEL="gemma3:4b"
logging.basicConfig(filename=LOGS/"jarvis13_autonomy.log",level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",encoding="utf-8")
log=logging.getLogger("jarvis13")

def conn():
    c=sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY, created TEXT, kind TEXT, status TEXT, detail TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value TEXT)""")
    c.commit()
    return c

def event(kind,status,detail):
    with conn() as c:
        c.execute("INSERT INTO events(created,kind,status,detail) VALUES(?,?,?,?)",
                  (datetime.now().isoformat(timespec="seconds"),kind,status,str(detail)[:4000]))

def get_state(key,default=""):
    with conn() as c:
        row=c.execute("SELECT value FROM state WHERE key=?",(key,)).fetchone()
    return row[0] if row else default

def set_state(key,value):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO state(key,value) VALUES(?,?)",(key,str(value)))

def ask_local(prompt,timeout=180):
    r=requests.post(OLLAMA+"/api/chat",json={
        "model":MODEL,"stream":False,
        "messages":[
            {"role":"system","content":"Je bent Jarvis, een lokale persoonlijke AI. Wees eerlijk, praktisch en voorzichtig. Geef geen instructies om beveiliging te omzeilen."},
            {"role":"user","content":prompt}],
        "options":{"temperature":0.2}},timeout=timeout)
    r.raise_for_status()
    return r.json()["message"]["content"]

def health_check():
    try:
        r=requests.get(OLLAMA+"/api/tags",timeout=8); r.raise_for_status()
        models=[x.get("name","") for x in r.json().get("models",[])]
        if not models:
            event("health","warning","Ollama reageert, maar er zijn geen modellen geïnstalleerd.")
        else:
            event("health","ok","Ollama bereikbaar. Modellen: "+", ".join(models))
    except Exception as e:
        event("health","error","Ollama niet bereikbaar: "+str(e))

def backup_core():
    # Keep rolling dated backups; never overwrite a previous backup.
    import shutil
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    target=BACKUPS/("core_"+stamp)
    target.mkdir(exist_ok=False)
    for name in ("jarvis12.py","jarvis13_agent.py","requirements.txt"):
        f=ROOT/name
        if f.exists(): shutil.copy2(f,target/name)
    # Retain the latest 10 backups.
    folders=sorted([p for p in BACKUPS.glob("core_*") if p.is_dir()],key=lambda p:p.name,reverse=True)
    for old in folders[10:]:
        shutil.rmtree(old,ignore_errors=True)
    event("backup","ok",f"Core-back-up gemaakt: {target.name}")

def improve_skills():
    """Create/update declarative prompt skills; never generate or execute arbitrary Python."""
    skill_files=list(SKILLS.glob("*.json"))
    existing=[]
    for f in skill_files[:30]:
        try: existing.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception: pass
    with sqlite3.connect(ROOT/"data"/"jarvis12.db") as c:
        try:
            rows=c.execute("SELECT goal,status FROM tasks ORDER BY id DESC LIMIT 20").fetchall()
        except Exception: rows=[]
    task_history="\n".join(f"- [{status}] {goal}" for goal,status in rows)
    current=json.dumps(existing,ensure_ascii=False)[:6000]
    prompt=f"""
Ontwerp maximaal twee nuttige nieuwe vaardigheden voor Jarvis op basis van zijn taakgeschiedenis.
Geef uitsluitend JSON met vorm {{"skills":[{{"name":"...","description":"...","instructions":"...","triggers":["..."]}}]}}.
Vaardigheden zijn alleen instructies/prompts voor de taalassistent, geen Python-code, geen commando's,
geen downloads, geen systeemwijzigingen, geen netwerkacties en geen toegang tot accounts.
Schrijf concrete, veilige instructies in het Nederlands. Geef alleen nieuwe vaardigheden die nog niet bestaan.
Bestaande vaardigheden: {current}
Recente taakgeschiedenis: {task_history}
"""
    try:
        raw=ask_local(prompt,180)
        match=re.search(r"\{.*\}",raw,re.S)
        if not match: raise ValueError("Geen JSON ontvangen")
        data=json.loads(match.group(0))
        added=0
        for item in data.get("skills",[])[:2]:
            name=re.sub(r"[^a-z0-9_-]","_",str(item.get("name","")).lower())[:40].strip("_")
            instructions=str(item.get("instructions","")).strip()
            if not name or len(instructions)<40 or len(instructions)>1800: continue
            # Reject any attempt to turn a prompt-skill into an executable action.
            low=instructions.lower()
            if any(x in low for x in ("voer powershell uit","schakel antivirus uit","verwijder beveiliging","stuur geld","wachtwoord opslaan")):
                continue
            payload={"name":name,"description":str(item.get("description",""))[:240],
                     "instructions":instructions,"triggers":[str(x)[:60] for x in item.get("triggers",[])[:8]],
                     "created":datetime.now().isoformat(timespec="seconds"),"type":"prompt_skill"}
            path=SKILLS/(name+".json")
            if path.exists(): continue
            path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
            added+=1
        event("self_development","ok",f"Zelfontwikkelronde voltooid. {added} nieuwe promptvaardigheden toegevoegd.")
        set_state("last_skill_cycle",datetime.now().isoformat(timespec="seconds"))
    except Exception as e:
        event("self_development","error","Vaardigheden ontwikkelen mislukt: "+str(e))

def weekly_review():
    try:
        logs=(LOGS/"jarvis12.log").read_text(encoding="utf-8",errors="ignore")[-12000:] if (LOGS/"jarvis12.log").exists() else ""
        prompt=("Analyseer deze Jarvis-logregels. Geef maximaal vijf concrete verbeterpunten, "
                "prioriteer fouten die vaak terugkomen, en maak geen wijzigingen. "
                "Antwoord in het Nederlands met acties en risico's.\n\n"+logs)
        report=ask_local(prompt,180)
        path=WORK/("Jarvis_zelfevaluatie_"+datetime.now().strftime("%Y%m%d")+".md")
        if not path.exists():
            path.write_text("# Jarvis zelfevaluatie\n\nGemaakt: "+datetime.now().isoformat(timespec="minutes")+"\n\n"+report,encoding="utf-8")
        event("self_review","ok",f"Zelfevaluatie opgeslagen: {path.name}")
        set_state("last_review",datetime.now().isoformat(timespec="seconds"))
    except Exception as e:
        event("self_review","error",str(e))

def run_cycle():
    event("agent","running","Jarvis 13 autonome onderhoudsronde gestart.")
    health_check()
    last_backup=get_state("last_backup")
    if not last_backup or datetime.now()-datetime.fromisoformat(last_backup)>timedelta(days=1):
        backup_core(); set_state("last_backup",datetime.now().isoformat(timespec="seconds"))
    last_skill=get_state("last_skill_cycle")
    if not last_skill or datetime.now()-datetime.fromisoformat(last_skill)>timedelta(days=7):
        improve_skills()
    last_review=get_state("last_review")
    if not last_review or datetime.now()-datetime.fromisoformat(last_review)>timedelta(days=7):
        weekly_review()
    event("agent","ok","Autonome onderhoudsronde afgerond.")

def main():
    event("agent","started","Jarvis 13 autonome achtergrondagent gestart.")
    while True:
        try: run_cycle()
        except Exception as e:
            log.exception("Autonomy cycle failed"); event("agent","error",str(e))
        time.sleep(6*60*60)

if __name__=="__main__":
    if "--once" in sys.argv:
        run_cycle()
    else:
        main()
