#!/usr/bin/env bash
# ============================================================================
# scripts/make-dev-certs.sh — generate a self-signed TLS pair for local nginx
# ----------------------------------------------------------------------------
# DEV / LOCAL USE ONLY. Browsers will warn. For EC2 / production, replace the
# generated files with Let's Encrypt material:
#   sudo certbot certonly --nginx -d <your-ec2-host>
#   then mount /etc/letsencrypt/live/<host>/{fullchain,privkey}.pem into
#   the nginx container's /etc/nginx/certs/ instead.
#
# Output:
#   ./certs/fullchain.pem   (self-signed, RSA-2048, 365-day validity, CN=localhost)
#   ./certs/privkey.pem     (chmod 600)
#
# Both files are gitignored (see .gitignore -> certs/, *.pem, *.key, *.crt).
#
# Usage:
#   ./scripts/make-dev-certs.sh           # idempotent: skips if cert exists
#   ./scripts/make-dev-certs.sh --force   # regenerate even if present
#
# Verify what you generated:
#   openssl x509 -in certs/fullchain.pem -noout -subject -issuer -dates -ext subjectAltName
#
# Test the full nginx config end-to-end (from repo root):
#   docker run --rm --add-host=app:127.0.0.1 \
#     -v "$PWD/nginx.conf:/etc/nginx/nginx.conf:ro" \
#     -v "$PWD/certs:/etc/nginx/certs:ro" \
#     nginx:1.27-alpine nginx -t
# ============================================================================
set -euo pipefail

CERT_DIR="${CERT_DIR:-./certs}"
CERT_FILE="${CERT_DIR}/fullchain.pem"
KEY_FILE="${CERT_DIR}/privkey.pem"
DAYS="${DAYS:-365}"
FORCE=0

for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=1 ;;
        --help|-h)
            sed -n '2,30p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "Unknown arg: $arg" >&2; exit 64 ;;
    esac
done

if ! command -v openssl >/dev/null 2>&1; then
    echo "ERROR: openssl not found on PATH. Install it and retry." >&2
    exit 1
fi

mkdir -p "$CERT_DIR"

if [[ -f "$CERT_FILE" && -f "$KEY_FILE" && $FORCE -eq 0 ]]; then
    echo "Certs already present at $CERT_DIR/ — skipping. Pass --force to regenerate."
    openssl x509 -in "$CERT_FILE" -noout -subject -dates
    exit 0
fi

echo "Generating self-signed RSA-2048 cert into $CERT_DIR/ (valid $DAYS days)..."

openssl req \
    -x509 \
    -newkey rsa:2048 \
    -nodes \
    -days "$DAYS" \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/C=US/ST=Dev/L=Localhost/O=job-tracker/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:job-tracker.local,DNS:app,IP:127.0.0.1,IP:::1" \
    -addext "keyUsage=digitalSignature,keyEncipherment" \
    -addext "extendedKeyUsage=serverAuth"

chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo
echo "Done. Files written:"
ls -la "$CERT_DIR"

echo
echo "WARNING: these are SELF-SIGNED dev certs. Browsers will show a warning."
echo "         For production, swap in Let's Encrypt material (see header comment)."
echo
echo "Sanity check:"
openssl x509 -in "$CERT_FILE" -noout -subject -dates -ext subjectAltName
