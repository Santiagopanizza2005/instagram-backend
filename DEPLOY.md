# Configuración de despliegue

## Variables de entorno (Vercel)
En el panel de tu proyecto Vercel → Settings → Environment Variables, añade:

- `SUPABASE_URL` = `https://taurpcrtobypkbvrzxgs.supabase.co`
- `SUPABASE_SERVICE_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRhdXJwY3J0b2J5cGtidnJ6eGdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzUxNzY2MCwiZXhwIjoyMDc5MDkzNjYwfQ.32LsySTFn6t99Nk0UrwhezDTiOLh7nfyY8ch9sfmmOI`
- `JWT_SECRET` = `k28DHg9273!jd92JHD92h29dHJD92h2@73jkADH9283h#92`
- `JWT_EXPIRES` = `86400`
- `POLL_INTERVAL` = `1`

## Variables de entorno (Heroku)
```bash
heroku config:set SUPABASE_URL=https://taurpcrtobypkbvrzxgs.supabase.co
heroku config:set SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRhdXJwY3J0b2J5cGtidnJ6eGdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzUxNzY2MCwiZXhwIjoyMDc5MDkzNjYwfQ.32LsySTFn6t99Nk0UrwhezDTiOLh7nfyY8ch9sfmmOI
heroku config:set JWT_SECRET=k28DHg9273!jd92JHD92h29dHJD92h2@73jkADH9283h#92
heroku config:set JWT_EXPIRES=86400
heroku config:set POLL_INTERVAL=1
```

## Comandos de despliegue

### Vercel
```bash
vercel --prod
```

### Heroku
```bash
git add .
git commit -m "Ready for production"
git push heroku main
```

## Verificación post-despliegue
- `GET https://<tu-dominio>/health` → `{"status":"ok"}`
- `GET https://<tu-dominio>/db/health` → `{"ok":true,"sb_ok":true,"url":"https://taurpcrtobypkbvrzxgs.supabase.co"}`
- `POST https://<tu-dominio>/api/login` con credenciales de usuario → 200 con token

## Notas de seguridad
- Usa Service Role key solo en backend (ya configurado)
- Las políticas RLS no son necesarias con Service Role
- Asegúrate de que las tablas `app_users` y `user_accounts` existan en Supabase