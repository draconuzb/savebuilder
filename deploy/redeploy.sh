#!/usr/bin/env bash
# Lokal mashinadan serverga tez redeploy.
# Ishlatish: bash deploy/redeploy.sh
set -e

KEY="${SB_KEY:-$HOME/Downloads/bekpro.pem}"
HOST="${SB_HOST:-ec2-user@54.221.147.244}"

echo "==> git archive"
git archive --format=tar.gz -o /tmp/savebuilder.tar.gz HEAD

echo "==> scp -> $HOST"
scp -i "$KEY" /tmp/savebuilder.tar.gz "$HOST":/tmp/savebuilder.tar.gz

echo "==> extract + deps + restart"
ssh -i "$KEY" "$HOST" bash -s <<'REMOTE'
set -e
cd ~/savebuilder
tar -xzf /tmp/savebuilder.tar.gz -C ~/savebuilder
./.venv/bin/pip install -q --disable-pip-version-check -r requirements.txt
sudo systemctl restart savebuilder
sleep 5
echo "status: $(systemctl is-active savebuilder)"
curl -s --max-time 8 http://127.0.0.1:8080/health; echo
REMOTE

echo "==> tayyor: https://bot.wecreate.uz"
