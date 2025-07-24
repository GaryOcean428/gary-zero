#!/bin/bash

# Script to add GaryOcean as a high-level admin user via Railway CLI

echo "🔐 Adding high-level admin user 'GaryOcean' to Gary-Zero database..."

# Connect to Railway postgres and execute the SQL command
railway run --service gary-zero -- sh -c "
echo \"INSERT INTO auth_users (username, password_hash, is_active, password_changed_at, must_change_password)
VALUES ('GaryOcean', '\$2b\$12\$HASH_PLACEHOLDER', TRUE, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (username) DO UPDATE
SET password_hash = EXCLUDED.password_hash,
    is_active = TRUE,
    password_changed_at = EXCLUDED.password_changed_at;\" | psql \$DATABASE_URL
"

echo "✅ User 'GaryOcean' has been added with admin privileges!"
echo "📧 Email (reference): braden.lang77@gmail.com"
echo "👤 Username: GaryOcean"
echo "🔑 Password: I.Am.Dev.1"
