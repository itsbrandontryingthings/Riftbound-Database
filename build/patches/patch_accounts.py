#!/usr/bin/env python3
"""Add optional accounts (Supabase email + password) to the public website version.
Signed in: card counts and decks save to the visitor's own account (row-level security: only they can read it).
Signed out: everything keeps working and saves in the browser, as before.
Run after patch_web.py. Usage: patch_accounts.py in.html out.html"""
import sys

SUPABASE_URL = "https://unemhzpqaygxpdjmtvuh.supabase.co"
SUPABASE_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVuZW1oenBxYXlneHBkam10dnVoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE5MTU3NDUsImV4cCI6MjEwNzQ5MTc0NX0.ue0S-o1fLj2ZoP1v7zHmpwIXVbFPJlBI5eRT3njWpWo"

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f"expected {count} of {old[:70]!r}, found {n}"
    h = h.replace(old, new)

# ---------- styles
rep(".localnote b{color:var(--fg)}", """.localnote b{color:var(--fg)}
.acct{display:flex;gap:8px 12px;align-items:center;flex-wrap:wrap}
.acct .who{font-size:14px;color:var(--muted);overflow-wrap:anywhere}
.acct .who b{color:var(--fg);font-weight:600}
#auth{border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--fg);padding:18px;max-width:min(400px,calc(100vw - 32px));width:100%}
#auth::backdrop{background:rgb(5 6 10 / .78)}
#auth form{display:grid;gap:12px}
#auth h2{font-family:var(--display);font-size:19px;margin:0}
#auth label{display:grid;gap:4px;font-size:14px;color:var(--muted)}
#auth input{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font:inherit;color:var(--fg)}
#auth .msg{font-size:13.5px;min-height:1.2em}
#auth .msg.err{color:var(--fury)} #auth .msg.ok{color:var(--ok)}
#auth .switch{background:none;border:0;padding:0;color:var(--accent);text-decoration:underline;text-underline-offset:2px;font-size:14px;justify-self:start}
#auth .row{display:flex;gap:8px;justify-content:space-between;align-items:center;flex-wrap:wrap}""")

# ---------- account bar under the title, and the sign-in dialog
rep('    <h1>Riftbound - Complete Database</h1>',
    '    <h1>Riftbound - Complete Database</h1>\n    <div class="acct" id="acct"><button class="btn primary" id="acct-in">Sign in or create an account</button><span class="who" id="acct-who"></span><button class="btn" id="acct-out" hidden>Sign out</button></div>')
rep('<p class="localnote"><b>Your collection is private.</b> Cards and decks you enter save in this browser on this device, and nobody else who opens this site can see them. To move them to another phone or computer, use <b>Back up or move your collection</b> at the bottom of the page.</p>',
    '<p class="localnote" id="acct-note"><b>Your collection is private.</b> Create a free account to save your cards and decks to it and use them on any phone or computer. Without an account they save in this browser only. Either way, nobody else who opens this site can see them.</p>\n'
    '  <dialog id="auth" aria-labelledby="auth-title"><form id="auth-form" novalidate>\n'
    '    <div class="row"><h2 id="auth-title">Sign in</h2><button type="button" class="btn" id="auth-x" aria-label="Close">×</button></div>\n'
    '    <label>Email <input id="auth-email" type="email" autocomplete="email" required></label>\n'
    '    <label>Password <input id="auth-pass" type="password" autocomplete="current-password" minlength="6" required></label>\n'
    '    <p class="msg" id="auth-msg" aria-live="polite"></p>\n'
    '    <div class="row"><button type="submit" class="btn primary" id="auth-go">Sign in</button><button type="button" class="switch" id="auth-switch">New here? Create an account</button></div>\n'
    '  </form></dialog>')

# ---------- Supabase library (UMD build, global "supabase") before the page script
rep('<script src="cards.js"></script>',
    '<script src="cards.js"></script>\n<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"></script>')

# ---------- every save also goes to the account when signed in
rep('function queueSave(){\n  LS.set("rb-counts", counts);', 'function queueSave(){\n  LS.set("rb-counts", counts); cloudSave();')
rep('function saveDecks(){\n  LS.set("rb-decks", customDecks); LS.set("rb-deck", curDeck);', 'function saveDecks(){\n  LS.set("rb-decks", customDecks); LS.set("rb-deck", curDeck); cloudSave();')

# ---------- account logic
rep('syncControls(); render(); showTab(["collection","packs","decks"].includes(st.tab) ? st.tab : "collection"); connect();',
    r'''// ---- accounts (Supabase). Table "collections": one row per person, readable and writable only by its owner.
const SB_URL = "''' + SUPABASE_URL + r'''", SB_KEY = "''' + SUPABASE_ANON + r'''";
let sb = null, cloudUser = null, cloudReady = false, cloudTimer = null, cloudDirty = false;
function cloudSave(){
  if (!sb || !cloudUser || !cloudReady) return;
  cloudDirty = true; setSync("Saving…");
  clearTimeout(cloudTimer);
  cloudTimer = setTimeout(async () => {
    cloudTimer = null; const me = cloudUser; if (!me) return;
    cloudDirty = false;
    const { error } = await sb.from("collections").upsert({ id: me.id, counts, decks: customDecks, updated_at: new Date().toISOString() });
    if (error){ cloudDirty = true; setSync("Couldn't save to your account. Saved in this browser; it will retry on your next change.", "warn"); }
    else if (!cloudDirty) setSync("✓ Saved to your account", "ok");
  }, 800);
}
// send any change still waiting (used right before signing out)
async function cloudFlush(){
  if (!cloudTimer || !cloudUser || !cloudReady) return;
  clearTimeout(cloudTimer); cloudTimer = null; cloudDirty = false;
  await sb.from("collections").upsert({ id: cloudUser.id, counts, decks: customDecks, updated_at: new Date().toISOString() });
}
async function cloudLoad(){
  if (!sb || !cloudUser) return;
  setSync("Loading your collection…");
  const { data, error } = await sb.from("collections").select("counts, decks").eq("id", cloudUser.id).maybeSingle();
  if (error){ cloudReady = false; setSync("Couldn't reach your account. Saving in this browser for now.", "warn"); return; }
  if (data){
    counts = data.counts || {}; customDecks = Array.isArray(data.decks) ? data.decks : [];
    LS.set("rb-counts", counts); LS.set("rb-decks", customDecks);
    cloudReady = true; render(); setSync("✓ Saved to your account", "ok");
  } else {
    // first sign-in: whatever was entered in this browser becomes the start of the account
    cloudReady = true; cloudSave(); render();
  }
}
function showAcct(){
  $("acct-in").hidden = !!cloudUser; $("acct-out").hidden = !cloudUser;
  $("acct-who").innerHTML = cloudUser ? `Signed in as <b>${esc(cloudUser.email || "")}</b>` : "";
  $("acct-note").hidden = !!cloudUser;
}
let authMode = "in";
function setAuthMode(m){
  authMode = m;
  $("auth-title").textContent = m === "in" ? "Sign in" : "Create an account";
  $("auth-go").textContent = m === "in" ? "Sign in" : "Create account";
  $("auth-switch").textContent = m === "in" ? "New here? Create an account" : "Already have an account? Sign in";
  $("auth-pass").autocomplete = m === "in" ? "current-password" : "new-password";
  $("auth-msg").textContent = ""; $("auth-msg").className = "msg";
}
function authMsg(t, cls){ $("auth-msg").textContent = t; $("auth-msg").className = "msg " + (cls || ""); }
$("acct-in").addEventListener("click", () => { setAuthMode("in"); try { $("auth").showModal(); } catch(e){ $("auth").setAttribute("open", ""); } $("auth-email").focus(); });
$("auth-x").addEventListener("click", () => $("auth").close());
$("auth-switch").addEventListener("click", () => setAuthMode(authMode === "in" ? "up" : "in"));
$("auth-form").addEventListener("submit", async e => {
  e.preventDefault();
  if (!sb){ authMsg("Accounts aren't available right now. Check your connection and reload the page.", "err"); return; }
  const email = $("auth-email").value.trim(), password = $("auth-pass").value;
  if (!/^\S+@\S+\.\S+$/.test(email)){ authMsg("Enter your email address.", "err"); return; }
  if (password.length < 6){ authMsg("Use a password of at least 6 characters.", "err"); return; }
  $("auth-go").disabled = true; authMsg(authMode === "in" ? "Signing in…" : "Creating your account…");
  try {
    if (authMode === "in"){
      const { error } = await sb.auth.signInWithPassword({ email, password });
      if (error) authMsg(/invalid/i.test(error.message) ? "That email and password don't match an account. Check them, or create an account." : /confirm/i.test(error.message) ? "Confirm your email first: open the link we sent you, then sign in." : error.message, "err");
      else { $("auth").close(); $("auth-pass").value = ""; }
    } else {
      const { data, error } = await sb.auth.signUp({ email, password, options: { emailRedirectTo: location.origin + location.pathname } });
      if (error) authMsg(/registered|exists/i.test(error.message) ? "There's already an account with that email. Sign in instead." : error.message, "err");
      else if (data.session){ $("auth").close(); $("auth-pass").value = ""; }
      else authMsg("Almost done: open the confirmation link we emailed you, then sign in here.", "ok");
    }
  } catch(err){ authMsg("Couldn't reach the account service. Check your connection and try again.", "err"); }
  $("auth-go").disabled = false;
});
$("acct-out").addEventListener("click", async () => {
  if (sb){ try { await cloudFlush(); } catch(e){} await sb.auth.signOut(); }
  // clear this browser so the next person on a shared device starts empty
  counts = {}; customDecks = []; LS.set("rb-counts", counts); LS.set("rb-decks", customDecks);
  render(); setSync("Signed out. Nothing is saved in this browser.", "ok");
});
document.addEventListener("visibilitychange", () => { if (!document.hidden && cloudUser && cloudReady && !cloudDirty) cloudLoad(); });
function cloudInit(){
  if (!window.supabase || !window.supabase.createClient){ return; }
  sb = window.supabase.createClient(SB_URL, SB_KEY, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } });
  sb.auth.onAuthStateChange((event, session) => {
    const u = session ? session.user : null, changed = (u && u.id) !== (cloudUser && cloudUser.id);
    cloudUser = u; showAcct();
    if (u && changed){ cloudReady = false; cloudLoad(); }
    if (!u){ cloudReady = false; }
  });
}
syncControls(); render(); showTab(["collection","packs","decks"].includes(st.tab) ? st.tab : "collection"); connect(); cloudInit(); showAcct();''')

# the backup note no longer the only way to move devices
rep("your counts save in this browser, so use the backup code to move them to another device.",
    "your counts save to your account when you're signed in, or in this browser when you're not.")

open(out, "w", encoding="utf-8").write(h)
print("ok", len(h))
