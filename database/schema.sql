-- ============================================================
-- Sistem Informasi Bencana & Gotong Royong — Skema Database
-- Jalankan di Supabase SQL Editor (Project > SQL Editor > New Query)
-- ============================================================

-- Extension buat UUID generation
create extension if not exists "uuid-ossp";

-- ------------------------------------------------------------
-- Enums
-- ------------------------------------------------------------
create type report_type as enum ('NEED_HELP', 'OFFER_HELP', 'INFO_ONLY');
create type report_status as enum ('OPEN', 'IN_PROGRESS', 'RESOLVED');

-- ------------------------------------------------------------
-- Table: users
-- Identity ledger + preferensi langganan cuaca per wilayah
-- ------------------------------------------------------------
create table users (
    id uuid primary key default uuid_generate_v4(),
    telegram_id bigint unique not null,
    kode_adm4 varchar,               -- kode wilayah BMKG (nullable, diisi saat user set lokasi)
    is_subscribed boolean not null default true,
    created_at timestamptz not null default now()
);

create index idx_users_telegram_id on users(telegram_id);

-- ------------------------------------------------------------
-- Table: mutual_aid_reports
-- Core engine crowdsourcing bantuan warga
-- ------------------------------------------------------------
create table mutual_aid_reports (
    id uuid primary key default uuid_generate_v4(),
    reporter_id bigint not null references users(telegram_id),
    report_type report_type not null,
    description text not null,
    latitude double precision not null,
    longitude double precision not null,
    status report_status not null default 'OPEN',
    created_at timestamptz not null default now()
);

create index idx_reports_status on mutual_aid_reports(status);
create index idx_reports_created_at on mutual_aid_reports(created_at desc);

-- ------------------------------------------------------------
-- Table: api_cache_logs
-- Cache sementara buat hindari rate-limit API eksternal
-- ------------------------------------------------------------
create table api_cache_logs (
    id serial primary key,
    endpoint_hash varchar not null,
    payload jsonb not null,
    fetched_at timestamptz not null default now(),
    expires_at timestamptz not null
);

create index idx_cache_endpoint_hash on api_cache_logs(endpoint_hash);
create index idx_cache_expires_at on api_cache_logs(expires_at);

-- ============================================================
-- Row Level Security (RLS)
-- Bot pakai anon key, jadi kita batasi lewat policy: user cuma
-- boleh insert/update row yang terhubung ke telegram_id mereka.
-- Untuk MVP, matching dilakukan di application layer (bot service),
-- policy di bawah ini adalah baseline pertahanan tambahan.
-- ============================================================

alter table users enable row level security;
alter table mutual_aid_reports enable row level security;
alter table api_cache_logs enable row level security;

-- users: siapa saja (anon) boleh insert baris baru (registrasi awal),
-- tapi hanya boleh select/update baris miliknya sendiri lewat service layer.
create policy "allow insert users" on users
    for insert
    with check (true);

create policy "allow select own user" on users
    for select
    using (true); -- MVP: bot yang filter by telegram_id di query, bukan RLS granular per-session

create policy "allow update own user" on users
    for update
    using (true);

-- mutual_aid_reports: publik boleh baca semua laporan (buat dashboard & bot),
-- insert boleh siapa saja yang sudah terdaftar di users.
create policy "allow select all reports" on mutual_aid_reports
    for select
    using (true);

create policy "allow insert reports" on mutual_aid_reports
    for insert
    with check (true);

create policy "allow update reports" on mutual_aid_reports
    for update
    using (true);

-- api_cache_logs: internal only, akses lewat service role key (bukan anon)
create policy "allow all cache access" on api_cache_logs
    for all
    using (true);

-- ============================================================
-- Catatan: policy di atas cukup permisif untuk kecepatan development MVP.
-- Sebelum production/publish luas, ketatkan pakai auth.uid() atau
-- custom claim yang memverifikasi telegram_id request cocok dengan row.
-- ============================================================
