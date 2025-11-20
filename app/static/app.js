const API_BASE = 'https://api-para-ig-igbot.cp6q0w.easypanel.host'

const api = {
  login: async (payload) => fetch(API_BASE + '/accounts/login', {method:'POST',headers:{'Content-Type':'application/json','X-App-Session':`Bearer ${appSession}`},body:JSON.stringify(payload)}).then(r=>r.json()),
  logout: async (username) => fetch(API_BASE + '/accounts/logout', {method:'POST',headers:{'Content-Type':'application/json','X-App-Session':`Bearer ${appSession}`},body:JSON.stringify({username})}).then(r=>r.json()),
  sessLogin: async (username, password) => fetch(API_BASE + '/api/login', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})}).then(r=>r.json()),
  accounts: async () => fetch(API_BASE + '/accounts', {headers:{'X-App-Session':`Bearer ${appSession}`}}).then(r=>r.json()),
  setWebhook: async (username, url, enabled) => fetch(API_BASE + `/accounts/${encodeURIComponent(username)}/webhook`, {method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${tokenValue}`,'X-App-Session':`Bearer ${appSession}`},body:JSON.stringify({webhook_url:url, enabled})}).then(r=>r.json()),
  testWebhook: async (username, text) => fetch(API_BASE + '/test_webhook', {method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${tokenValue}`},body:JSON.stringify({username, text})}).then(r=>r.json()),
  reset: async (username) => fetch(API_BASE + `/accounts/${encodeURIComponent(username)}/reset`, {method:'POST',headers:{'Authorization':`Bearer ${tokenValue}`,'X-App-Session':`Bearer ${appSession}`}}).then(r=>r.json()),
  getOptions: async (username) => fetch(API_BASE + `/accounts/${encodeURIComponent(username)}/options`, {headers:{'Authorization':`Bearer ${tokenValue}`,'X-App-Session':`Bearer ${appSession}`}}).then(r=>r.json()),
  setOptions: async (username, opts) => fetch(API_BASE + `/accounts/${encodeURIComponent(username)}/options`, {method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${tokenValue}`,'X-App-Session':`Bearer ${appSession}`},body:JSON.stringify(opts)}).then(r=>r.json()),
  resetToken: async (username) => fetch(API_BASE + `/accounts/${encodeURIComponent(username)}/token/reset`, {method:'POST',headers:{'Authorization':`Bearer ${tokenValue}`,'X-App-Session':`Bearer ${appSession}`}}).then(r=>r.json()),
}

const el = (q) => document.querySelector(q)

let uiState = { logged: false, username: null }
let tokenValue = ''
let tokenShown = false
let appSession = localStorage.getItem('appSession')||''
let appRefresh = localStorage.getItem('appRefresh')||''
 
// monitor removido

function show(section){
  document.querySelectorAll('.section').forEach(s=>s.style.display='none')
  el(section).style.display='block'
}

async function loadAccounts(){
  const res = await api.accounts()
  const list = res.accounts || []
  const container = el('#accounts')
  container.innerHTML = ''
  list.forEach(a => {
    const div = document.createElement('div')
    div.className = 'panel'
    const webhook = a.webhook_url || ''
    const enabled = !!a.webhook_enabled
    div.innerHTML = `
      <div class="stack">
        <div>
          <div class="label">Usuario</div>
          <div>${a.username}</div>
        </div>
        <div>
          <div class="label">Contraseña</div>
          <div>******</div>
        </div>
      </div>
      <div style="margin-top:12px"></div>
      <div>
        <div class="label">Webhook URL</div>
        <div class="row">
          <input style="flex:1" value="${webhook}" placeholder="https://tu-n8n/webhook/ig-gateway" />
          <button class="secondary" data-set="${a.username}">Guardar</button>
          <button class="secondary" data-test="${a.username}">Probar</button>
        </div>
        <div style="margin-top:8px">
          <div class="label">Estado del webhook</div>
          <div class="mono webhook-state" data-user="${a.username}"></div>
        </div>
      </div>
    `
    container.appendChild(div)
    uiState.logged = true
    uiState.username = a.username
    const ws = div.querySelector('.webhook-state')
    if(ws){
      let txt = ''
      if(!webhook){ txt = 'Listo para usar: falta webhook' }
      else { txt = 'Webhook configurado' }
      ws.textContent = txt
    }
    const inp = div.querySelector('input')
  })
  if(uiState.logged){
    // fetch token for display
    try{
      const t = await fetch(API_BASE + `/accounts/${encodeURIComponent(uiState.username)}/token`, {headers:{'X-App-Session':`Bearer ${appSession}`}}).then(r=>r.json())
      tokenValue = t.token || ''
      el('#token-value').textContent = tokenValue
      el('#token-masked').textContent = '••••••••••••••••'
    }catch{}
    const topUser = el('#top-username'); if(topUser){ topUser.textContent = uiState.username }
    show('#dashboard')
    const base = API_BASE
    const sendUrlInit = el('#send-url'); if(sendUrlInit){ sendUrlInit.textContent = base + '/send_message' }
    const confUrl = el('#conf-url'); if(confUrl){ confUrl.textContent = base + '/send_message' }
    // load options
    let options = null
    try{
      const res = await api.getOptions(uiState.username)
      options = res.options || null
    }catch{}
    const set = (id, v) => { const s = el(id); if(s){ s.classList.toggle('active', !!v) } }
    if(options){
      set('#sw-typing', options.delay_typing)
      set('#sw-seen', options.mark_seen_previous)
      set('#sw-profile', options.view_profile)
      set('#sw-stories', options.view_stories)
      set('#sw-safe', options.safe_mode)
    }
    const updateSendUrl = () => {
      const parts = []
      if(el('#sw-typing')?.classList.contains('active')) parts.push('typing=1')
      if(el('#sw-seen')?.classList.contains('active')) parts.push('seen=1')
      if(el('#sw-profile')?.classList.contains('active')) parts.push('profile=1')
      if(el('#sw-stories')?.classList.contains('active')) parts.push('stories=1')
      if(el('#sw-safe')?.classList.contains('active')) parts.push('safe=1')
      const q = parts.length ? ('?' + parts.join('&')) : ''
      const path = el('#sw-file')?.classList.contains('active') ? '/send_file' : '/send_message'
      const url = base + path + q
      const su = el('#send-url'); if(su){ su.textContent = url }
      const cu = el('#conf-url'); if(cu){ cu.textContent = url }
      // cuerpo de n8n removido según solicitud
    }
    updateSendUrl()
    const bind = (id, key) => { const s = el(id); if(!s) return; s.onclick = async () => { const active = s.classList.toggle('active'); await api.setOptions(uiState.username, {[key]: active}); updateSendUrl() } }
    bind('#sw-typing','delay_typing')
    bind('#sw-seen','mark_seen_previous')
    bind('#sw-profile','view_profile')
    bind('#sw-stories','view_stories')
    bind('#sw-safe','safe_mode')
    const swFile = el('#sw-file'); if(swFile){ swFile.onclick = () => { swFile.classList.toggle('active'); const nameEl = el('#bp-content-name'); if(nameEl){ nameEl.textContent = swFile.classList.contains('active') ? 'file_url' : 'text' } const cont = el('#bp-content'); if(cont){ cont.placeholder = swFile.classList.contains('active') ? 'https://ejemplo.com/archivo.jpg' : 'Hola' } updateSendUrl(); rebuildBody() } }

    const swBody = el('#sw-body'); if(swBody){ swBody.classList.add('active'); const bc = el('#body-config'); if(bc){ bc.style.display = 'block' } swBody.onclick = () => { const on = swBody.classList.toggle('active'); if(bc){ bc.style.display = on ? 'block' : 'none' } rebuildBody() } }

    const bpUser = el('#bp-username'); if(bpUser){ bpUser.value = ''; bpUser.placeholder = '@usuario'; bpUser.oninput = () => rebuildBody() }
    const bpRec = el('#bp-recipient'); if(bpRec){ bpRec.value = ''; bpRec.placeholder = '@destino o id'; bpRec.oninput = () => rebuildBody() }
    const bpCont = el('#bp-content'); if(bpCont){ bpCont.value = ''; bpCont.placeholder = 'Hola'; bpCont.oninput = () => rebuildBody() }

    function rebuildBody(){
      const on = el('#sw-body')?.classList.contains('active')
      const u = el('#bp-username')?.value || ''
      const r = el('#bp-recipient')?.value || ''
      const c = el('#bp-content')?.value || ''
      const isFile = el('#sw-file')?.classList.contains('active')
      const body = isFile ? {username:u, recipient:r, file_url:c} : {username:u, recipient:r, text:c}
      
    }
    rebuildBody()
    const n8nAuth = el('#n8n-auth-value'); if(n8nAuth){ n8nAuth.textContent = `Bearer ${tokenValue || '<token>'}` }
    updateSendUrl()

    // monitor removido
    
  } else {
    show('#landing')
  }
  // logout control se mantiene solo en la barra superior
  container.querySelectorAll('button[data-set]').forEach(b=>{
    b.onclick = async () => {
      const inp = b.parentElement.querySelector('input')
      await api.setWebhook(b.dataset.set, inp.value, undefined)
      await loadAccounts()
    }
  })
  container.querySelectorAll('button[data-test]').forEach(b=>{
    b.onclick = async () => {
      await api.testWebhook(b.dataset.test, 'prueba')
    }
  })
  return list.length
}

async function onLogin(){
  const username = el('#in-username').value.trim()
  const password = el('#in-password').value.trim()
  const verification_code = el('#in-code').value.trim() || null
  const webhook_url = null
  if(!username||!password){ alert('Completa usuario y contraseña de Instagram'); return }
  let res = null
  try{
    res = await api.login({username,password,verification_code,webhook_url})
  }catch(e){ alert('Error de red al iniciar sesión en Instagram'); return }
  if(res && res.ok){
    el('#login-modal').classList.remove('active')
  }
  else {
    const msg = res?.detail || 'No se pudo iniciar sesión en Instagram'
    alert(msg)
  }
  await loadAccounts()
}

window.addEventListener('DOMContentLoaded', async () => {
  // header logo detection
  const logoImg = el('#site-logo')
  const tryPath = async (p) => fetch(API_BASE + p, {method:'HEAD'}).then(r=>r.ok).catch(()=>false)
  const candidates = [
    '/imagenes/logo.webp',
    '/imagenes/logo.png',
    '/imagenes/logo.jpg',
    '/imagenes/logo.jpeg',
    '/static/imagenes/logo.png',
    '/static/imagenes/logo.jpg',
    '/static/imagenes/logo.jpeg',
    '/static/imagenes/logo.webp',
    '/static/imagenes/logo.svg',
    '/static/imagenes/logo.ico',
    '/static/images/logo.png',
    '/static/images/logo.webp',
    '/static/images/logo.svg',
    '/static/logo.png',
    '/static/logo.svg'
  ]
  let found = null
  for(const p of candidates){ if(await tryPath(p)){ found = p; break } }
  if(found){
    logoImg.src = API_BASE + found
    logoImg.style.display = 'block'
    const fav = el('#favicon'); if(fav){ fav.href = API_BASE + found }
    const fav2 = el('#favicon2'); if(fav2){ fav2.href = API_BASE + found }
  } else {
    logoImg.style.display = 'none'
  }
  
  const openIgLogin = () => {
    const u = el('#in-username'); const p = el('#in-password'); const c = el('#in-code')
    if(u){ u.value = '' }
    if(p){ p.value = ''; p.type = 'password' }
    if(c){ c.value = '' }
    const ep = el('#btn-eye-pass'); if(ep){ ep.textContent = '👁' }
    el('#login-modal').classList.add('active');
    startLogoAnimation()
  }
  const btnOpenIg = el('#btn-open-ig'); if(btnOpenIg){ btnOpenIg.onclick = () => { if(appSession){ openIgLogin() } else { const m = el('#session-login'); if(m){ m.classList.add('active') } } } }
  const sessLoginBtn = el('#btn-sess-login'); if(sessLoginBtn){ sessLoginBtn.onclick = async () => { const uEl = el('#sess-user'); const pEl = el('#sess-pass'); const u = uEl?.value||''; const p = pEl?.value||''; if(!u||!p){ alert('Completa usuario y contraseña'); return } const prevText = sessLoginBtn.textContent; sessLoginBtn.textContent = 'Iniciando...'; sessLoginBtn.disabled = true; try{ const res = await api.sessLogin(u,p); if(res && res.ok && res.token){ appSession = res.token; try{ localStorage.setItem('appSession', appSession) }catch{}; if(res.refresh){ appRefresh = res.refresh; try{ localStorage.setItem('appRefresh', appRefresh) }catch{} } el('#session-login')?.classList.remove('active'); const count = await loadAccounts(); if(!count){ openIgLogin(); } } else { alert('Usuario o contraseña incorrectos'); window.open('https://wa.me/5491140696611?text=Quiero%20acceso%20al%20bot%20de%20IG','_blank'); if(uEl) uEl.value=''; if(pEl) pEl.value=''; } }catch(e){ alert('Usuario o contraseña incorrectos'); window.open('https://wa.me/5491140696611?text=Quiero%20acceso%20al%20bot%20de%20IG','_blank'); if(uEl) uEl.value=''; if(pEl) pEl.value=''; } finally { sessLoginBtn.textContent = prevText; sessLoginBtn.disabled = false } } }
  const btnEyeSess = el('#btn-eye-sess'); if(btnEyeSess){ btnEyeSess.onclick = () => { const f = el('#sess-pass'); if(!f) return; const t = f.getAttribute('type')==='password'?'text':'password'; f.setAttribute('type', t) } }
  
  
  // abrir IG directamente
  
  el('#btn-do-login').onclick = onLogin
  
  const step1 = el('#login-step1')
  const eyePass = el('#btn-eye-pass'); if(eyePass){ eyePass.onclick = () => { const inp = el('#in-password'); if(!inp) return; const is = inp.type==='password'; inp.type = is?'text':'password'; eyePass.textContent = is?'🙈':'👁' } }
  const eye = el('#btn-eye')
  if(eye){
    eye.onclick = () => {
      tokenShown = !tokenShown
      el('#token-masked').textContent = tokenShown ? tokenValue : '••••••••••••••••'
      const pill = el('#token-masked')?.closest('.pill')
      if(pill){ pill.classList.toggle('expanded', tokenShown) }
    }
  }
  const btnResetToken = el('#btn-reset-token')
  if(btnResetToken){
    btnResetToken.onclick = async () => {
      if(!uiState.username) return
      try{
        const {token} = await api.resetToken(uiState.username)
        tokenValue = token || ''
        el('#token-value').textContent = tokenValue
        el('#token-masked').textContent = tokenShown ? tokenValue : '••••••••••••••••'
        const base = API_BASE
        const authHeader = el('#auth-header'); if(authHeader){ authHeader.textContent = `Authorization: Bearer ${tokenValue || '<token>'}` }
        
      }catch{}
    }
  }
  const copyToken = el('#copy-token')
  if(copyToken){
    copyToken.onclick = () => navigator.clipboard.writeText(tokenValue)
  }
  const btnLogoutTop = el('#btn-logout-top')
  if(btnLogoutTop){
    btnLogoutTop.onclick = async () => {
      if(uiState.username){ await api.logout(uiState.username) }
      uiState = {logged:false, username:null}
      appSession = ''
      try{ localStorage.removeItem('appSession') }catch{}
      appRefresh = ''
      try{ localStorage.removeItem('appRefresh') }catch{}
      show('#landing')
    }
  }
  const btnResetTop = el('#btn-reset-top')
  if(btnResetTop){
    btnResetTop.onclick = async () => {
      if(uiState.username){ await api.reset(uiState.username); await loadAccounts() }
    }
  }
  // copia de body n8n removida
  const igLottie = el('#ig-lottie')
  function startLogoAnimation(){
    if(!igLottie) return
    igLottie.loop = false
    try{ igLottie.stop() }catch{}
    if(window._logoCompleteHandler){ igLottie.removeEventListener('complete', window._logoCompleteHandler) }
    window._logoCompleteHandler = () => { try{ igLottie.pause() }catch{} }
    igLottie.addEventListener('complete', window._logoCompleteHandler)
    try{ igLottie.play() }catch{}
  }
  
  if(appSession){
    try{
      const v = await fetch(API_BASE + '/api/verify-session', {headers:{'X-App-Session':`Bearer ${appSession}`}}).then(r=>r.json())
      if(v && v.ok){
        const r = await fetch(API_BASE + '/api/refresh-session', {method:'POST', headers:{'X-App-Session':`Bearer ${appSession}`}}).then(r=>r.json())
        if(r && r.ok && r.token){ appSession = r.token; localStorage.setItem('appSession', appSession) }
        el('#session-login')?.classList.remove('active')
      } else {
        appSession = ''
        localStorage.removeItem('appSession')
      }
    }catch(e){ appSession=''; localStorage.removeItem('appSession') }
  } else if(appRefresh){
    try{
      const r = await fetch(API_BASE + '/api/refresh-from-token', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({refresh: appRefresh})}).then(r=>r.json())
      if(r && r.ok && r.token){ appSession = r.token; localStorage.setItem('appSession', appSession); el('#session-login')?.classList.remove('active') }
    }catch{}
  }
  await loadAccounts()
})

function copyText(id){
  const t = el(id).textContent
  navigator.clipboard.writeText(t)
}
