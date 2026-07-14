#!/bin/sh

n8n start &
N8N_PID=$!

for i in $(seq 1 30); do
  if wget -q --spider http://localhost:5678/healthz 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "--- Importing n8n workflows (idempotent) ---"
n8n import:workflow --separate --input=/n8n 2>&1

echo "--- Activating all workflows ---"
node -e "
var p='/usr/local/lib/node_modules/n8n/node_modules/.pnpm/pg@8.17.0_pg-native@3.8.0/node_modules/pg';
var pg = require(p);
var c = new pg.Client({
  host: 'postgres',
  database: process.env.DB_POSTGRESDB_DATABASE || 'devpilot',
  user: process.env.DB_POSTGRESDB_USER || 'devpilot',
  password: process.env.DB_POSTGRESDB_PASSWORD || 'changeme'
});
c.connect(function(err) {
  if (err) { console.log('DB connect error:', err.message); c.end(); return; }
  c.query(\"UPDATE workflow_entity SET active=true\", function(e, r) {
    if (e) console.log('Update error:', e.message);
    else console.log('Activated ' + r.rowCount + ' workflows');
    c.end();
  });
});
" 2>&1

wait $N8N_PID
