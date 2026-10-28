"""PhishLens: Message Risk Dashboard with Drift Curve (Streamlit)."""
import json, html, math
from datetime import datetime
import pandas as pd, streamlit as st
import phishlens as ps

st.set_page_config(page_title="PhishLens Message Risk Dashboard", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# ---- palette (taken from the reference slide) ----
CYAN, CYAN_L, LAV_L = "#35bff2", "#d9f2fc", "#ddd6f0"
PUR, PUR_M, PUR_L, NAVY = "#4b3bb5", "#8d7de0", "#b8aeea", "#231a5e"
TXT, MUTE, LINE = "#26243a", "#6f7186", "#cfd9ee"

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap');
html,body,[class*="st-"],.stApp{{font-family:'Poppins','Century Gothic','Segoe UI',sans-serif}}
.stApp{{background:#fff;color:{TXT}}}
header[data-testid="stHeader"],footer,#MainMenu,section[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{{display:none!important}}
.block-container{{padding:1.1rem 1.6rem 1.4rem;max-width:1320px}}
[data-testid="stHorizontalBlock"]{{gap:14px}}
[data-testid="stVerticalBlock"]{{gap:.6rem}}
h1.ttl{{font-weight:300;font-size:2.1rem;line-height:1.15;margin:0;padding:0;color:{TXT}}}
p.sub{{font-size:11px;color:{MUTE};margin:2px 0 6px;max-width:980px;line-height:1.45}}
/* KPI strip */
.kpis{{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:12px;margin:6px 0 2px}}
.kpi{{text-align:center}}
.kpi .ic{{width:30px;height:30px;border-radius:50%;margin:0 auto 5px;background:linear-gradient(160deg,#3aa8ee,#2a63d0);display:flex;align-items:center;justify-content:center}}
.kpi .ic svg{{width:16px;height:16px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
.kpi .kl{{font-size:12.5px;font-weight:500;padding:5px 4px;color:{TXT}}}
.kpi .kv{{font-size:19px;font-weight:600;padding:5px 4px;background:#fff;border:1px solid {LINE};margin-top:7px}}
.kpi .kv small{{font-size:12px;font-weight:500}}
.kpi .a.kl{{background:{CYAN_L}}}.kpi .b.kl{{background:{LAV_L}}}
.kpi .a.kv{{color:#3aa8e6}}.kpi .b.kv{{color:{PUR}}}
.kpi .kv.txt{{font-size:14px;padding:8px 4px}}
/* panels */
[class*="st-key-p_"]{{background:#fff;border:1px solid {LINE};padding:0 14px 12px;gap:.45rem}}
.st-key-p_side{{background:#efeff3;border:0;padding:12px 16px}}
.st-key-p_health,.st-key-p_campaign,.st-key-p_model,.st-key-p_drift{{min-height:268px}}
.st-key-p_side{{min-height:560px}}
.pt{{width:58%;margin:0 auto 6px;background:{CYAN};color:#fff;font-weight:600;font-size:12px;text-align:center;padding:3px 6px}}
.st-key-p_side .pt{{background:none;color:{TXT};width:100%;text-align:left;font-size:14px;padding:0 0 4px}}
.mute{{color:{MUTE};font-size:11px}}
.chip{{display:inline-block;background:{LAV_L};color:{PUR};padding:1px 9px;font-size:11px;font-weight:600}}
/* donuts */
.dn{{display:flex;align-items:center;justify-content:space-around;gap:6px;padding-top:6px}}
.dn .col{{text-align:center;width:128px}}
.dn .rb{{background:{PUR};color:#fff;font-size:11px;font-weight:500;padding:3px 4px;margin-top:6px}}
.dn .mid{{text-align:center}}.dn .mid b{{display:block;font-size:13px;font-weight:600}}.dn .mid span{{font-size:24px;font-weight:600;color:{PUR}}}
/* horizontal bars */
.hb{{display:grid;grid-template-columns:118px 1fr;gap:8px;align-items:center;margin:9px 0;font-size:12px}}
.hb .l{{text-align:right;color:{TXT}}}
.hb .t{{height:17px;background:#e9e9ef}}
.hb .t i{{display:block;height:100%;min-width:38px;color:#fff;font-style:normal;font-weight:600;font-size:11px;text-align:right;padding-right:6px;line-height:17px;box-sizing:border-box}}
.lg{{display:flex;gap:14px;flex-wrap:wrap;font-size:10.5px;color:{MUTE};margin-top:8px;justify-content:center}}
.lg s{{display:inline-block;width:9px;height:9px;margin-right:4px;text-decoration:none}}
/* recent scans */
.rs{{position:relative;margin-top:8px}}
.rs:before{{content:"";position:absolute;left:19px;top:20px;bottom:20px;width:2px;background:#c9d4ec}}
.rs .it{{position:relative;display:flex;align-items:center;gap:14px;margin-bottom:22px}}
.rs .av{{width:40px;height:40px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;border:3px solid #efeff3;box-sizing:border-box}}
.rs .av svg{{width:18px;height:18px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
.rs b{{display:block;font-size:13px;font-weight:600}}.rs span.d{{font-size:10.5px;color:{MUTE}}}
.rs .sk{{height:9px;background:#e0e0e8;margin:4px 0;width:110px}}.rs .sk.s{{width:80px;height:7px}}
/* result */
.res{{display:flex;gap:14px;align-items:center}}
.res .dec{{font-size:16px;font-weight:600;line-height:1.25}}
.why{{font-size:12px;line-height:1.5}}
/* acceptance strip uses .kpi */
.foot{{text-align:center;font-size:10.5px;font-style:italic;color:{MUTE};margin-top:10px}}
/* widgets */
.stButton>button{{background:{PUR};color:#fff;border:0;border-radius:0;font-weight:600;font-size:13px;padding:.35rem 1rem}}
.stButton>button:hover{{background:{NAVY};color:#fff}}.stButton>button:focus-visible{{outline:3px solid {CYAN}}}
[data-baseweb="select"]>div,[data-baseweb="textarea"],textarea{{border-radius:0!important}}
[data-testid="stAlert"]{{border-radius:0}}
@media (max-width:900px){{.kpis{{grid-template-columns:repeat(2,1fr)}}}}
</style>""", unsafe_allow_html=True)

# ---- data / models ----
@st.cache_resource
def get_models(): return ps.load_models()
@st.cache_data
def get_results():
    p = ps.ROOT / "outputs/results.json"
    if not p.exists(): ps.run_pipeline(log=False)
    return json.loads(p.read_text())
models, R = get_models(), get_results()

@st.cache_data
def campaign_risk(model_name):
    df = pd.read_csv(ps.ROOT / "data/clean_messages.csv"); df = df[df.campaign_group.isin(ps.HOLDOUT)].copy()
    df["p"] = models[model_name].predict_proba(df.apply(ps.make_text, axis=1).tolist())[:, 1]
    return [(c, float(g.p.mean()), int(g.label.iloc[0])) for c, g in df.groupby("campaign_group")]

SAMPLES = {"Choose a test case": "",
 "AT-01 · Legitimate password reset": "Hello, we received a request to reset your password. If you did not request this, ignore this message. Visit the portal directly from your bookmarks. No action is needed otherwise.",
 "AT-02 · Phishing, unfamiliar wording": "Hi, the finance side flagged a hiccup with your pay details; please tidy it up here: hxxp://bit[.]ly/58 Thanks, really appreciate it.",
 "Obvious phishing": "URGENT!!! Your account will be suspended within 24 hours. Verify your password immediately at hxxp://192[.]0[.]2[.]9/login. Dear customer, final notice!",
 "Legitimate urgent payroll notice": "Reminder: payroll closes Friday. Confirm any bank detail changes in the HR system; do not click links in email."}
SHORT = {1: "High risk", 0: "Low risk", -1: "Needs review"}
DCOL = {1: NAVY, 0: CYAN, -1: PUR_M}
DTXT = {1: NAVY, 0: "#1b87bd", -1: PUR}

for k, v in dict(log=[], last=None, msg="", rob=None, flash=None, model="TF-IDF + LogReg", chan="email").items(): st.session_state.setdefault(k, v)
model_name = st.session_state.model

def wrap(t, ch): return f"{t}. urlfeat_none sender_unknown chan_{ch}"
def stamp():
    n = datetime.now(); s = "th" if 11 <= n.day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n.day % 10, "th")
    return f"{n.day}{s} {n.strftime('%b %Y')} {n.strftime('%I:%M %p').lstrip('0')}"

def load_sample(): st.session_state.msg = SAMPLES[st.session_state.sample]
def do_scan():
    t = st.session_state.msg.strip()
    if not t: st.session_state.flash = "Paste or load a message first."; return
    ch, mn = st.session_state.chan, st.session_state.model
    p, d = ps.score_message(t, ch, models[mn]); cues, terms = ps.explain(t, models["TF-IDF + LogReg"])
    st.session_state.last = dict(text=t, ch=ch, p=p, d=d, cues=cues, terms=terms, model=mn)
    st.session_state.log.insert(0, dict(id=f"M-{len(st.session_state.log)+1:03d}", ch=ch, p=p, d=d, model=mn, ts=stamp()))
    st.session_state.rob = None; st.session_state.flash = None
def do_robust():
    L = st.session_state.last
    if not L: return
    m = models[L["model"]]; base = float(m.predict_proba([wrap(L["text"], L["ch"])])[0, 1])
    st.session_state.rob = [("Original", base)] + [(k, float(m.predict_proba([wrap(f(L["text"]), L["ch"])])[0, 1])) for k, f in ps.PERTURB.items()]

# ---- svg helpers ----
ICONS = {
 "msg": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
 "dup": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
 "camp": '<path d="M5 21V4"/><path d="M5 4h13l-2.5 4.5L18 13H5"/>',
 "hold": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
 "mod": '<circle cx="6" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="12" cy="18" r="2"/><path d="M7.6 7.6l3.4 8.8M16.4 7.6L13 16.4M8 6h8"/>',
 "abs": '<circle cx="12" cy="12" r="9"/><path d="M10 9v6M14 9v6"/>',
 "scan": '<circle cx="11" cy="11" r="6"/><path d="M16 16l4 4"/>',
 "sms": '<path d="M4 5h16v11H9l-5 4z"/>'}
def ico(k): return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[k]}</svg>'
def pt(t): return f'<div class="pt">{html.escape(t)}</div>'
def pct(x): return f"{x*100:.0f}%"

def donut(v, c=PUR, label=""):
    r, C = 44, 2 * math.pi * 44
    return (f'<svg width="118" height="118" viewBox="0 0 120 120" role="img" aria-label="{label} {pct(v)}"><defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="2.5" flood-opacity=".18"/></filter></defs>'
            f'<circle cx="60" cy="60" r="55" fill="#fff" filter="url(#sh)"/><circle cx="60" cy="60" r="{r}" fill="none" stroke="{LAV_L}" stroke-width="11"/>'
            f'<circle cx="60" cy="60" r="{r}" fill="none" stroke="{c}" stroke-width="11" stroke-dasharray="{v*C:.1f} {C:.1f}" transform="rotate(-90 60 60)"/>'
            f'<text x="60" y="67" text-anchor="middle" font-size="21" font-weight="600" fill="{TXT}">{pct(v)}</text></svg>')

def grouped_bars(cats, a, b, na, nb):
    W, H, L, B, T = 380, 215, 36, 30, 28; pw, ph = W - L - 8, H - B - T; s = ""
    for t in (0, .25, .5, .75, 1):
        y = T + ph * (1 - t); s += f'<line x1="{L}" x2="{W-8}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e3e6f0"/><text x="{L-6}" y="{y+3:.1f}" text-anchor="end" font-size="9" fill="{MUTE}">{int(t*100)}%</text>'
    gw = pw / len(cats); bw = gw * .24
    for i, c in enumerate(cats):
        cx = L + gw * (i + .5)
        for off, v, col in ((-bw - 1, a[i], PUR), (1, b[i], PUR_L)):
            h = ph * v; s += f'<rect x="{cx+off:.1f}" y="{T+ph-h:.1f}" width="{bw:.1f}" height="{max(h,1):.1f}" fill="{col}"/><text x="{cx+off+bw/2:.1f}" y="{T+ph-h-4:.1f}" text-anchor="middle" font-size="9" fill="{TXT}">{v*100:.0f}</text>'
        s += f'<text x="{cx:.1f}" y="{H-10}" text-anchor="middle" font-size="10" fill="{TXT}">{html.escape(c)}</text>'
    lg = f'<rect x="{L}" y="7" width="8" height="8" fill="{PUR}"/><text x="{L+12}" y="14.5" font-size="10" fill="{TXT}">{na}</text><rect x="{L+86}" y="7" width="8" height="8" fill="{PUR_L}"/><text x="{L+98}" y="14.5" font-size="10" fill="{TXT}">{nb}</text>'
    return f'<svg width="100%" viewBox="0 0 {W} {H}" role="img" aria-label="Grouped bars: {na} and {nb} per model">{s}{lg}</svg>'

def curve(cats, series, sel):
    W, H, L, B, T = 380, 215, 36, 34, 28; pw, ph = W - L - 10, H - B - T
    mx = max(max(v) for _, v, _ in series) * 100; ymax = max(5, math.ceil(mx / 5) * 5); s = ""
    for k in range(5):
        t = k / 4; y = T + ph * (1 - t); s += f'<line x1="{L}" x2="{W-10}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e3e6f0"/><text x="{L-6}" y="{y+3:.1f}" text-anchor="end" font-size="9" fill="{MUTE}">{ymax*t:.0f}</text>'
    xs = [L + pw * (i + .5) / len(cats) for i in range(len(cats))]
    for x, c in zip(xs, cats): s += f'<text x="{x:.1f}" y="{H-14}" text-anchor="middle" font-size="9" fill="{TXT}">{html.escape(c)}</text>'
    pts = lambda v: [(x, T + ph * (1 - min(val * 100 / ymax, 1))) for x, val in zip(xs, v)]
    order = [t for t in series if t[0] != sel] + [t for t in series if t[0] == sel]
    for name, v, col in order:
        P = pts(v); on = name == sel; line = " ".join(f"{x:.1f},{y:.1f}" for x, y in P)
        if on: s += f'<defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".35"/><stop offset="1" stop-color="{col}" stop-opacity=".03"/></linearGradient></defs><polygon points="{xs[0]:.1f},{T+ph} {line} {xs[-1]:.1f},{T+ph}" fill="url(#ga)"/>'
        s += f'<polyline points="{line}" fill="none" stroke="{col}" stroke-width="{2.4 if on else 1.4}" opacity="{1 if on else .75}"/>' + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{3 if on else 2.2}" fill="{col}"/>' for x, y in P)
    lx, lg = L, ""
    for name, _, col in series: lg += f'<line x1="{lx}" x2="{lx+16}" y1="11" y2="11" stroke="{col}" stroke-width="2"/><circle cx="{lx+8}" cy="11" r="2.4" fill="{col}"/><text x="{lx+21}" y="14.5" font-size="10" fill="{TXT}">{html.escape(name.replace("TF-IDF + ",""))}</text>'; lx += 21 + 7 * len(name.replace("TF-IDF + ", "")) + 14
    return f'<svg width="100%" viewBox="0 0 {W} {H}" role="img" aria-label="Mean probability shift in points per text perturbation, per model"><text x="{L}" y="{T-6}" font-size="9" fill="{MUTE}">pts</text>{s}{lg}</svg>'

def hbars(rows, band=True):  # rows: (label, value, colour)
    tr = f'background:linear-gradient(90deg,#e9e9ef 35%,{LAV_L} 35% 65%,#e9e9ef 65%)' if band else ""
    return "".join(f'<div class="hb"><span class="l">{html.escape(l)}</span><span class="t" style="{tr}"><i style="width:{v*100:.1f}%;background:{c}">{pct(v)}</i></span></div>' for l, v, c in rows)

def kpis(items, n):
    return f'<div class="kpis" style="--n:{n}">' + "".join(f'<div class="kpi">' + (f'<div class="ic">{ico(i)}</div>' if i else "") + f'<div class="kl {"a" if k % 2 == 0 else "b"}">{html.escape(l)}</div><div class="kv {"a" if k % 2 == 0 else "b"}{" txt" if not i else ""}">{v}</div></div>' for k, (i, l, v) in enumerate(items)) + "</div>"

# ---- header ----
st.markdown('<h1 class="ttl">PhishLens: Message Risk Dashboard with Drift Curve</h1><p class="sub">Triage view for simulated emails and SMS. Messages are scored from text only, so no link is ever opened. The dashboard shows how each model holds up on phishing campaigns it never saw, when it abstains for human review, and how far its score drifts when the wording is lightly changed.</p>', unsafe_allow_html=True)

M = R["models"][model_name]
st.markdown(kpis([("msg", "Messages", f"{R['dedup']['before']}"), ("dup", "Duplicates", f"{R['dedup']['removed']}"), ("camp", "Campaigns", f"{len(R['split']['train_campaigns'])+len(R['split']['holdout_campaigns'])}"),
    ("hold", "Holdout", f"{len(R['split']['holdout_campaigns'])}"), ("mod", "Models", f"{len(R['models'])}"), ("abs", "Abstained", f"{M['confusion']['abstain']}"), ("scan", "Scans", f"{len(st.session_state.log)}")], 7), unsafe_allow_html=True)

# ---- main grid ----
main, side = st.columns([3.15, 1])
with main:
    a1, a2 = st.columns(2)
    with a1, st.container(key="p_health"):
        lr = R["models"]["TF-IDF + LogReg"]["macro_f1"]; rs = R["random_split_contrast"]["macro_f1"]
        st.markdown(pt("Generalisation Health") + f'<div class="dn"><div class="col">{donut(rs, PUR, "Random split macro-F1")}<div class="rb">Random split</div></div><div class="mid"><b>Leakage gap</b><span>{(rs-lr)*100:.0f} pts</span></div><div class="col">{donut(lr, PUR_M, "Campaign holdout macro-F1")}<div class="rb">Campaign holdout</div></div></div><div class="mute" style="text-align:center;margin-top:10px">Macro-F1, TF-IDF + LogReg. Shared templates inflate the random split.</div>', unsafe_allow_html=True)
    with a2, st.container(key="p_campaign"):
        nm = lambda c: c.split("_", 1)[1].replace("_", " ").capitalize()
        rows = [(nm(c), v, NAVY if y == 1 else PUR_M) for c, v, y in campaign_risk(model_name)]
        st.markdown(pt("Campaign Risk, Unseen") + hbars(rows) + f'<div class="lg"><span><s style="background:{NAVY}"></s>Phishing</span><span><s style="background:{PUR_M}"></s>Legitimate</span><span><s style="background:{LAV_L}"></s>Abstain band 35-65%</span></div><div class="mute" style="text-align:center;margin-top:6px">Mean risk per holdout campaign, {html.escape(model_name)}</div>', unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    names = list(R["models"])
    with b1, st.container(key="p_model"):
        st.markdown(pt("Model Comparison") + grouped_bars([n.replace("TF-IDF + ", "") for n in names], [R["models"][n]["macro_f1"] for n in names], [R["models"][n]["abstain_rate"] for n in names], "Macro-F1", "Abstain rate"), unsafe_allow_html=True)
    with b2, st.container(key="p_drift"):
        cats = ["Defang", "No punct.", "Exclaim", "UPPER", "Leet", "Padding"]
        cols = {"Rules": NAVY, "TF-IDF + LogReg": PUR_M, "TF-IDF + RandomForest": CYAN}
        ser = [(n, [d["mean_abs_shift"] for d in R["models"][n]["drift"].values()], cols[n]) for n in names]
        st.markdown(pt("Drift Curve") + curve(cats, ser, model_name), unsafe_allow_html=True)
with side, st.container(key="p_side"):
    items = ""
    for e in st.session_state.log[:6]:
        items += f'<div class="it"><div class="av" style="background:{DCOL[e["d"]]}">{ico("sms" if e["ch"]=="sms" else "msg")}</div><div><b>{e["id"]} · {SHORT[e["d"]]}</b><span class="d">{e["ch"].upper()} · {pct(e["p"])} risk · {e["ts"]}</span></div></div>'
    if not items: items = '<div class="it"><div class="av" style="background:#d6d8e4"></div><div><div class="sk"></div><div class="sk s"></div></div></div>' * 6
    st.markdown(pt("Recent Scans") + f'<div class="rs">{items}</div>' + ('' if st.session_state.log else '<div class="mute" style="margin-top:6px">No scans yet. Scan a message below and it appears here.</div>'), unsafe_allow_html=True)

# ---- scanner row ----
c1, c2, c3 = st.columns([1.5, 1.15, 1.15])
with c1, st.container(key="p_scan"):
    st.markdown(pt("Scan a Message") + '<span class="chip">Offline: links never opened</span>', unsafe_allow_html=True)
    st.selectbox("Test case", list(SAMPLES), key="sample", on_change=load_sample, label_visibility="collapsed")
    st.text_area("Message", key="msg", height=110, placeholder="Paste a simulated email or SMS. Use defanged links (hxxp://example[.]com).", label_visibility="collapsed")
    x, y, z = st.columns([1, 1.6, 1.2])
    x.selectbox("Channel", ["email", "sms"], key="chan", label_visibility="collapsed")
    y.selectbox("Model", names, key="model", label_visibility="collapsed")
    z.button("Scan message", on_click=do_scan, use_container_width=True)
    if st.session_state.flash: st.warning(st.session_state.flash)
L = st.session_state.last
with c2, st.container(key="p_result"):
    st.markdown(pt("Risk Result"), unsafe_allow_html=True)
    if not L: st.caption("Scan a message to see its risk, decision and a safe explanation.")
    else:
        st.markdown(f'<div class="res">{donut(L["p"], DCOL[L["d"]], "Risk")}<div class="dec" style="color:{DTXT[L["d"]]}">{ps.LABEL[L["d"]]}<div class="mute">{html.escape(L["model"])}</div></div></div><div class="why"><b>Why:</b> ' + ("; ".join(html.escape(c) for c in L["cues"]) or "no rule cues matched") + (f". Model terms: {html.escape(', '.join(L['terms']))}" if L["terms"] else "") + '</div>', unsafe_allow_html=True)
with c3, st.container(key="p_robust"):
    st.markdown(pt("Message Robustness"), unsafe_allow_html=True)
    st.button("Run perturbations", on_click=do_robust, disabled=not L)
    if st.session_state.rob:
        base = st.session_state.rob[0][1]
        st.markdown(hbars([(k if k == "Original" else k.split(" (")[0], p, NAVY if p >= .65 else CYAN if p <= .35 else PUR_M) for k, p in st.session_state.rob]) + f'<div class="mute" style="text-align:center">Largest shift: {max(abs(p-base) for _, p in st.session_state.rob)*100:.0f} pts. Large shifts expose model limits (AT-03).</div>', unsafe_allow_html=True)
    else: st.caption("Scan a message, then apply controlled wording changes to see how its risk score moves.")

# ---- acceptance strip ----
at = R["acceptance"]; shifts = max(abs(v - at["AT-03"]["base_risk"]) for v in at["AT-03"]["shifts"].values()) * 100
st.markdown(kpis([("", "AT-01 Legitimate reset", f'{at["AT-01"]["decision"]} · {pct(at["AT-01"]["risk"])}'), ("", "AT-02 Unseen phishing", f'{at["AT-02"]["decision"].split(":")[0]} · {pct(at["AT-02"]["risk"])}'),
    ("", "AT-03 Defang and punctuation", f"Max shift {shifts:.0f} pts"), ("", f"False alarms, legit urgent", f'{M["fpr_legit_urgent"]*100:.0f}% · {html.escape(model_name.replace("TF-IDF + ",""))}')], 4), unsafe_allow_html=True)
st.markdown(f'<div class="foot">{ps.DISCLAIMER} Acceptance results are logged in outputs/results.json.</div>', unsafe_allow_html=True)
