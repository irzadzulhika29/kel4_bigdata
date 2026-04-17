#!/bin/sh
set -eu

echo "Menunggu PostgreSQL siap..."
until pg_isready -h postgres -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
  sleep 2
done

psql -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'SQL'
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    created_at DATE,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    email_opt_in INTEGER,
    sms_opt_in INTEGER,
    call_opt_in INTEGER
);
SQL

row_count="$(psql -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM customers;")"

if [ "$row_count" = "0" ]; then
  echo "Memuat customers.csv ke PostgreSQL..."
  psql -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\copy customers (customer_id, created_at, first_name, last_name, email, phone, email_opt_in, sms_opt_in, call_opt_in) FROM '/seed-data/customers.csv' WITH (FORMAT csv, HEADER true)"
  echo "Seed customers selesai."
else
  echo "Tabel customers sudah berisi $row_count baris. Seed dilewati."
fi
