#!/bin/bash
set -euo pipefail

TERRAFORM_DIR="./terraform"
ANSIBLE_INVENTORY_FILE="./ansible/hosts.tmp"
ANSIBLE_PLAYBOOK_FILE="./ansible/playbook.yml"
PRIVATE_KEY="${HOME}/.ssh/id_rsa"

DOMAIN="familytreeapp.duckdns.org"
EMAIL="your_real_email@gmail.com"
CONTAINER_NAME="familytreeapp"
NGINX_SITE="/etc/nginx/sites-available/familytreeapp"

export ANSIBLE_HOST_KEY_CHECKING=False

cleanup() {
  [[ -f "$ANSIBLE_INVENTORY_FILE" ]] && rm -f "$ANSIBLE_INVENTORY_FILE"
}
trap cleanup EXIT

echo "--- Terraform Apply ---"
terraform -chdir="$TERRAFORM_DIR" init
terraform -chdir="$TERRAFORM_DIR" apply -auto-approve

echo "--- Fetching EC2 IP ---"
INSTANCE_IP=$(terraform -chdir="$TERRAFORM_DIR" output -json instance_public_ip | jq -r)
[[ -z "$INSTANCE_IP" || "$INSTANCE_IP" == "null" ]] && exit 1

ssh-keygen -R "$INSTANCE_IP" || true
ssh -o StrictHostKeyChecking=no -i "$PRIVATE_KEY" ubuntu@"$INSTANCE_IP" "exit" || true

cat > "$ANSIBLE_INVENTORY_FILE" <<EOF
[web]
${INSTANCE_IP} ansible_user=ubuntu ansible_ssh_private_key_file=${PRIVATE_KEY}
EOF

echo "--- Running Ansible ---"
ansible-playbook -i "$ANSIBLE_INVENTORY_FILE" "$ANSIBLE_PLAYBOOK_FILE" --private-key "$PRIVATE_KEY"

echo "--- Nginx + HTTPS automation ---"
ssh -i "$PRIVATE_KEY" ubuntu@"$INSTANCE_IP" <<'EOF'
set -euo pipefail

DOMAIN="familytreeapp.duckdns.org"
EMAIL="your_real_email@gmail.com"
CONTAINER_NAME="familytreeapp"
NGINX_SITE="/etc/nginx/sites-available/familytreeapp"

# Ensure HTTP config exists (do not overwrite)
if [ ! -f "$NGINX_SITE" ]; then
  sudo tee "$NGINX_SITE" > /dev/null <<'NGINX'
server {
    listen 80;
    server_name familytreeapp.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
NGINX

  sudo ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/familytreeapp
fi

sudo nginx -t
sudo systemctl reload nginx

# Obtain cert if missing
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  sudo certbot --nginx \
    -d "$DOMAIN" \
    -m "$EMAIL" \
    --agree-tos \
    --non-interactive
fi

sudo systemctl reload nginx
sudo docker restart "$CONTAINER_NAME"
EOF

echo "--- DONE ---"
echo "App available at: https://${DOMAIN}"

