import json, os, time, threading, subprocess
from datetime import datetime
from flask import Flask, request, redirect, render_template_string
from werkzeug.utils import secure_filename
F = "reminders.json"
S = os.path.abspath("sounds")
os.makedirs(S, exist_ok=True)
app = Flask(__name__)
def load():
    return json.load(open(F)) if os.path.exists(F) else []
def save(d):
    json.dump(d, open(F, "w"))
def fix(t):
    t = t.lower()
    if os.path.exists("respell.txt"):
        for l in open("respell.txt"):
            if "=" in l:
                a, b = l.strip().split("=", 1)
                t = t.replace(a.strip().lower(), b.strip())
    return t
def due(r, n):
    t = n.strftime("%Y-%m-%d")
    if r.get("paused") or r["time"] != n.strftime("%H:%M") or r["done"] or r.get("on") or r.get("ran") == t:
        return False
    dt = r.get("date") or t
    if dt > t:
        return False
    w = datetime.strptime(dt, "%Y-%m-%d")
    f = r.get("freq", "once")
    if f == "daily":
        return True
    if f == "weekly":
        return w.weekday() == n.weekday()
    if f == "monthly":
        return w.day == n.day
    return dt == t
def ring(r):
    sp = os.path.join(S, r["song"]) if r.get("song") else ""
    if sp and os.path.exists(sp):
        subprocess.run(["termux-media-player", "play", sp])
        time.sleep(int(r.get("songsec") or 30))
        subprocess.run(["termux-media-player", "stop"])
    else:
        tn=r.get("tone") or "beep"
        subprocess.run(["termux-media-player", "play", os.path.abspath("tones/"+tn+".wav")])
        time.sleep({"beep":1,"double":1,"siren":3,"chime":2}.get(tn,1))
def speak(r):
    c=0 if not r.get("last") else r.get("cnt",0)
    ls=[l.strip() for l in r["msg"].split("\n") if l.strip()]
    if c<len(ls):
        t=ls[c]
    else:
        try:
            a=[l.strip() for l in open("lines_en.txt" if r.get("lang")=="en" else "lines.txt",encoding="utf-8") if l.strip()]
        except Exception:
            a=["{m}"]
        t=a[(c-len(ls))%len(a)].replace("{m}",ls[0] if ls else "")
    k=max(0,c-len(ls)+1)
    v=str(round(min(2.0,1+0.1*k),1))
    r["cnt"]=c+1
    en=r.get("lang")=="en"
    subprocess.run(["termux-tts-speak","-l","en" if en else "fil","-n","US" if en else "PH","-s","MUSIC","-s","MUSIC","-p",v,"-r",v,t if en else fix(t)])

def loop():
    while True:
        n = datetime.now()
        d = load()
        for r in d:
            if due(r, n):
                r["on"] = True
                r["last"] = 0
                r["ran"] = n.strftime("%Y-%m-%d")
                save(d)
            if r.get("snooze") and time.time() >= r["snooze"]:
                r["snooze"] = 0
                r["on"] = True
                r["last"] = 0
                r["cnt"] = 0
                save(d)
            if r.get("on") and time.time() - r.get("last", 0) >= r.get("gap", 300):
                if r.get("last", 0) == 0:
                    ring(r)
                speak(r)
                d2 = load()
                for x in d2:
                    if x["id"] == r["id"] and x.get("on"):
                        x["last"] = time.time(); x["cnt"] = r.get("cnt",0)
                save(d2)
        time.sleep(1)
def view(r):
    if r.get("on"):
        t = datetime.fromtimestamp(r["last"] + r.get("gap", 300)) if r.get("last") else datetime.now()
        dd = t.strftime("%b %d, %Y")
    else:
        t = datetime.strptime(r["time"], "%H:%M")
        try:
            dd = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%b %d, %Y")
        except Exception:
            dd = ""
    return {"tm": t.strftime("%I:%M").lstrip("0"), "ap": t.strftime("%p"), "dd": dd}
P = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<link rel=icon href=/static/a3.png><link rel=apple-touch-icon href=/static/a3.png><link rel=manifest href=/static/manifest.json>
<title>Totskie Reminder</title>
<style>
*{box-sizing:border-box}
[hidden]{display:none!important}
body{margin:0;background:#e5e7eb;color:#111827;font:16px system-ui,sans-serif}
.w{max-width:480px;margin:0 auto;padding:16px}
.h{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.h img{width:64px;height:64px;border-radius:14px;cursor:pointer;box-shadow:0 2px 8px #0003}
.h h1{margin:0;font-size:22px}.h p{margin:2px 0 0;color:#6b7280;font-size:13px}
.c{background:#fff;border-radius:14px;padding:14px;margin-bottom:12px;box-shadow:0 1px 4px #0002}
form.c{display:grid;gap:10px}
input,select{width:100%;padding:12px;border:1px solid #d1d5db;border-radius:10px;font-size:16px;background:#fff}
.r{display:flex;gap:8px;align-items:center}
button,.b{border:0;border-radius:10px;padding:10px 14px;font-size:15px;color:#fff;text-decoration:none;background:#16a34a}
.t{font-size:28px;font-weight:700}.t small{font-size:14px;margin-left:4px;color:#6b7280}
.m{font-size:17px;margin:2px 0}.s{color:#6b7280;font-size:13px}
.x{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}.e{background:#2563eb}.d{background:#dc2626}
.p{background:#f59e0b}.k{background:#6b7280}
.o{opacity:.55}.n{text-align:center;color:#6b7280;padding:24px}
</style></head><body><div class=w>
<div class=h><img src=/static/a3.png onclick="logo()"><div><h1>Totskie Reminder</h1><p>Tap the logo to add or edit</p></div></div>
<form id=f class=c method=post action=/save enctype=multipart/form-data hidden>
<input type=hidden name=id id=i>
<input type=date name=date id=dt required>
<input type=time name=time id=t required>
<input name=msg id=m placeholder="Message" required>
<select name=freq id=q><option value=once>Once</option><option value=daily>Daily</option><option value=weekly>Weekly (same weekday as the date)</option><option value=monthly>Monthly (same day number as the date)</option></select>
<div class=r><input type=number name=gap id=g value=300 min=3 style=width:100px><span class=s>seconds between repeats</span></div>
<span class=s>Song (optional)</span>
<input type=file name=song id=sf accept="audio/*">
<div class=r><input type=number name=songsec id=ss value=30 min=3 style=width:100px><span class=s>seconds to play the song</span></div>
<div class=r><select name=lang id=lng><option value=fil>Filipino</option><option value=en>English</option></select><span class=s>voice</span></div>
<select name=tone id=tn><option value=beep>Beep</option><option value=double>Duha ka beep</option><option value=siren>Sirena</option><option value=chime>Chime</option></select>
<label class=s><input type=checkbox name=nosong style=width:auto> Remove song (use beep)</label>
<div class=r><button>Save</button><button type=button class=k onclick="cx()">Cancel</button></div></form>
{% for r in d %}<div class="c{% if r.done or r.paused %} o{% endif %}">
<div class=t>{{r.tm}}<small>{{r.ap}}</small></div>
{% if r.dd %}<div class=s>{{r.dd}}</div>{% endif %}
<div class=m>{{r.msg}}</div>
<div class=s>{{(r.freq or 'once')|capitalize}} - repeats every {{r.gap or 300}}s{% if r.song %} - Song: {{r.song.split('_',1)[-1]}}{% endif %}{% if r.on %} - RINGING{% endif %}{% if r.done %} - done{% endif %}{% if r.paused %} - PAUSED{% endif %}</div>
<div class=x><a class="b e" href=# onclick='ed({{r|tojson}});return false'>Edit</a>
{% if not r.done %}<a class=b href=/done/{{r.id}}>Done</a>{% if r.on %}<a class=b href=/snooze/{{r.id}}/5>5m</a><a class=b href=/snooze/{{r.id}}/15>15m</a><a class=b href=/snooze/{{r.id}}/30>30m</a>{% endif %}{% if r.snooze %}<span class=s> Snoozed</span>{% endif %}<a class="b p" href=/pause/{{r.id}}>{% if r.paused %}Resume{% else %}Pause{% endif %}</a>{% endif %}
<a class="b d" href=/del/{{r.id}}>Delete</a></div></div>
{% else %}<div class="c n">No reminders yet</div>{% endfor %}
</div>
<script>
dt.value=new Date().toLocaleDateString('en-CA');
function cx(){f.hidden=true;i.value='';m.value='';g.value=300;q.value='once';ss.value=30;sf.value=''}
function logo(){var h=f.hidden;cx();f.hidden=!h}
function ed(r){f.hidden=false;i.value=r.id;t.value=r.time;m.value=r.msg;g.value=r.gap||300;q.value=r.freq||'once';ss.value=r.songsec||30;lng.value=r.lang||"fil";tn.value=r.tone||"beep";dt.value=r.date||dt.value;scrollTo(0,0)}
</script>
</body></html>"""
@app.route("/")
def home():
    return render_template_string(P, d=[dict(r, **view(r)) for r in load()])
@app.route("/save", methods=["POST"])
def sv():
    i = request.form.get("id")
    d = load()
    old = [r for r in d if r["id"] == i] if i else []
    if i:
        d = [r for r in d if r["id"] != i]
    rid = i or str(int(time.time()*1000))
    song = old[0].get("song", "") if old else ""
    if request.form.get("nosong"):
        song = ""
    up = request.files.get("song")
    if up and up.filename:
        song = rid + "_" + (secure_filename(up.filename) or "song")
        up.save(os.path.join(S, song))
    d.append({"id": rid, "time": request.form["time"], "msg": request.form["msg"], "date": request.form.get("date") or datetime.now().strftime("%Y-%m-%d"), "freq": request.form.get("freq", "once"), "gap": int(request.form.get("gap") or 300), "song": song, "songsec": int(request.form.get("songsec") or 30), "lang": request.form.get("lang","fil"), "tone": request.form.get("tone","beep"), "done": False, "paused": bool(old and old[0].get("paused"))})
    d.sort(key=lambda r: r["time"])
    save(d)
    return redirect("/")
@app.route("/del/<i>")
def dl(i):
    save([r for r in load() if r["id"] != i])
    return redirect("/")
@app.route("/done/<i>")
def dn(i):
    d = load()
    for r in d:
        if r["id"] == i:
            r["on"] = False
            r["snooze"] = 0
            if r.get("freq", "once") == "once":
                r["done"] = True
    save(d)
    return redirect("/")
@app.route("/snooze/<i>/<int:m>")
def sz(i, m):
    d = load()
    for r in d:
        if r["id"] == i:
            r["on"] = False
            r["snooze"] = time.time() + m * 60
            r["last"] = 0
            r["cnt"] = 0
    save(d)
    return redirect("/")
@app.route("/pause/<i>")
def ps(i):
    d = load()
    for r in d:
        if r["id"] == i:
            r["paused"] = not r.get("paused")
            r["snooze"] = 0
            r["on"] = not r["paused"]
            r["last"] = 0
            r["cnt"] = 0
    save(d)
    return redirect("/")
def load():
    for _ in range(5):
        try:
            with open(F) as f:
                return json.load(f) if os.path.exists(F) else []
        except Exception:
            time.sleep(0.1)
    return []

def save(d):
    t = F + ".tmp"
    with open(t, "w") as f:
        json.dump(d, f)
    os.replace(t, F)

threading.Thread(target=loop, daemon=True).start()
app.run(host="127.0.0.1", port=5050)
