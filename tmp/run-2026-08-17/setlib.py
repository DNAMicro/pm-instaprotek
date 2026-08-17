"""Description-driven executor for the SETTINGS tabs on nullnet.

Each scenario row's Test Description tells us what to do ("Input ISO code",
"Click date format field", "Check bypass product review", ...). We match the
phrase to a control in the open modal by its label text, act, and record the
real outcome. Grid 10-14 (open/edit/save/delete/confirm) are always run against
the record THIS run created, so the destructive steps never touch live data.
"""
import re
import nlib as N

TESTVAL = "RegressionTest0817"

# ---------- form introspection ----------
def controls(pg):
    """Every visible control in the sub-modal with its best-guess label."""
    return pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return[];
      const out=[];
      d.querySelectorAll('input,textarea').forEach(e=>{{
        if(e.type==='hidden')return;
        if(e.offsetParent===null && e.type!=='file')return;
        const sel=e.closest('.Select');
        const wrap=e.closest('.md-text-field-container,.md-cell,.md-select-field__toggle,.Select')||e.parentElement;
        let lbl='';
        if(e.id){{const l=d.querySelector('label[for="'+e.id+'"]');if(l)lbl=l.textContent.trim();}}
        if(!lbl&&wrap)lbl=(wrap.innerText||'').split('\\n')[0].trim();
        out.push({{id:e.id||null,type:e.type,tag:e.tagName,label:lbl.slice(0,50),
                  isSelect:!!sel,checked:e.checked,val:(e.value||'').slice(0,24)}});
      }});
      d.querySelectorAll('[id$="-toggle"]').forEach(t=>{{
        out.push({{id:t.id,type:'md-select',tag:'MD',label:(t.closest('.md-cell,div')||{{}}).innerText?.split('\\n')[0]?.trim().slice(0,50)||'',
                  isSelect:false,checked:null,val:t.textContent.trim().slice(0,24)}});
      }});
      return out;}}""")

def _score(label, phrase):
    l=re.sub(r'[^a-z0-9 ]','',(label or '').lower())
    p=re.sub(r'[^a-z0-9 ]','',(phrase or '').lower())
    if not l or not p: return 0
    if p in l or l in p: return 100
    lw=set(l.split()); pw=set(p.split())
    return len(lw & pw)*10

def find_control(pg, phrase, types=None):
    cs=controls(pg)
    best=None; bs=0
    for c in cs:
        if types and c["type"] not in types and c["tag"] not in types: continue
        s=_score(c["label"], phrase)
        if c["id"]: s+=_score(c["id"].replace('_',' '), phrase)
        if s>bs: bs=s; best=c
    return best if bs>0 else None

# ---------- actions ----------
def act_input(pg, phrase, value=None):
    c=find_control(pg, phrase, types=["text","email","tel","number","textarea","TEXTAREA"])
    if not c or c["isSelect"]:
        c2=find_control(pg, phrase)
        if not c2 or c2["isSelect"]: return (False, f"no text field matched '{phrase}' (controls: {[x['label'] or x['id'] for x in controls(pg)][:8]})")
        c=c2
    val=value or TESTVAL
    sel=f".md-dialog:not(.md-dialog--full-page) #{c['id']}" if c["id"] else None
    try:
        if sel and pg.locator(sel).count():
            L=pg.locator(sel).first
        else:
            L=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=text]").first
        L.scroll_into_view_if_needed(); L.fill(val); pg.wait_for_timeout(600)
        got=L.input_value()
        return (val in got or got==val, f"field '{c['label'] or c['id']}' now reads '{got}'")
    except Exception as e:
        return (False, f"could not type into '{c['label'] or c['id']}': {str(e)[:70]}")

def act_open_select(pg, phrase):
    c=find_control(pg, phrase)
    if not c: return (False, f"no field matched '{phrase}'", [])
    try:
        if c["type"]=="md-select":
            o=N.md_open(pg, c["id"]); return (bool(o), f"'{c['label'] or c['id']}' opened", o)
        if c["id"]:
            o=N.rs_open(pg, c["id"], ".md-dialog:not(.md-dialog--full-page)")
            return (bool(o), f"'{c['label'] or c['id']}' opened", o)
        # positional react-select fallback
        pg.evaluate(f"""()=>{{const d={N.SUB};const s=[...d.querySelectorAll('.Select')][0];
          if(s){{s.scrollIntoView({{block:'center'}});s.querySelector('.Select-control').click();}}}}""")
        pg.wait_for_timeout(1500)
        return (True, "opened first select", N.opts(pg))
    except Exception as e:
        return (False, f"could not open '{c.get('label') or c.get('id')}': {str(e)[:70]}", [])

def act_pick(pg, md=False, text=None):
    try:
        if md: t=N.md_pick(pg, text)
        else:  t=N.rs_pick(pg, text)
        return (True, t)
    except Exception as e:
        return (False, str(e)[:70])

def act_check(pg, phrase):
    r=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const want=%s;
      const cbs=[...d.querySelectorAll('input[type=checkbox]')];
      let best=null,bs=-1;
      cbs.forEach(cb=>{{const w=cb.closest('.md-selection-control-container,.md-cell,div');
        const t=((w?w.innerText:'')||'').toLowerCase();
        let s=0; want.forEach(k=>{{if(t.includes(k))s++;}});
        if(s>bs){{bs=s;best=cb;}}}});
      if(!best)return null;
      const before=best.checked;
      (best.closest('label')||best).click();
      return {{before, after:best.checked, label:(best.closest('.md-selection-control-container,.md-cell,div')||{{}}).innerText?.slice(0,40)}};}}"""
      % (repr([w for w in re.sub(r'[^a-z ]','',phrase.lower()).split() if len(w)>3])))
    pg.wait_for_timeout(1200)
    if not r: return (False, f"no checkbox matched '{phrase}'")
    return (r["after"]!=r["before"], f"checkbox '{(r.get('label') or '').strip()[:34]}' toggled {r['before']} -> {r['after']}")

def act_radio(pg, phrase):
    r=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const rs=[...d.querySelectorAll('input[type=radio]')];
      if(!rs.length)return null;
      const t=rs[0]; (t.closest('label')||t).click();
      return {{n:rs.length, checked:t.checked,
               label:(t.closest('.md-selection-control-container,.md-cell,div')||{{}}).innerText?.slice(0,40)}};}}""")
    pg.wait_for_timeout(1000)
    if not r: return (False, f"no radio group found for '{phrase}'")
    return (bool(r["checked"]), f"radio '{(r.get('label') or '').strip()[:34]}' selected ({r['n']} option(s) in the group)")

def act_upload(pg, which=0):
    try:
        fi=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=file]")
        if fi.count()<=which: return (False, f"only {fi.count()} file input(s) present")
        fi.nth(which).set_input_files(N.IMG); pg.wait_for_timeout(2500)
        shown=pg.evaluate(f"""()=>{{const d={N.SUB};return !!d&&(!!d.querySelector('img[src^="data:"],img[src*="blob"]')||/background-image/.test(d.innerHTML));}}""")
        return (True, f"image accepted and preview rendered={shown}")
    except Exception as e:
        return (False, str(e)[:70])

def file_inputs(pg):
    return pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=file]").count()

def save(pg, rx="Save & Close|Save and Close|Save & Continue|Save"):
    r=N.sub_click(pg, rx)
    pg.wait_for_timeout(7000)
    open_still=N.has_sub(pg)
    errs=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}}""")
    return r, open_still, errs
