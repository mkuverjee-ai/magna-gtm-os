-- Magna GTM OS: database schema (Supabase / Postgres).
--
-- Optional. Without a database the OS still works: keys live in each person's
-- ~/.magna-gtm-config and logs go to log/*.jsonl in the repo (shared by /save).
-- With one, a key is set once for the whole team and logs are queryable.
--
-- Setup: create a Supabase project, open the SQL editor, paste this file, run it.
-- Then give each teammate the project URL and the service_role key; ./onboard
-- stores them in ~/.magna-gtm-config (chmod 600). Nothing else is configured locally.
--
-- RLS is ON with no policies, so only the service_role key can read or write.
-- The anon/publishable key sees nothing, which is the point: api_keys holds secrets.

create table if not exists team (
  name        text primary key,
  email       text,
  role        text,
  active      boolean not null default true,
  created_at  timestamptz not null default now()
);

create table if not exists api_keys (
  name        text primary key,          -- INSTANTLY_API_KEY, LEMLIST_API_KEY, AI_ARK_API_KEY, ...
  value       text not null,
  updated_by  text,
  updated_at  timestamptz not null default now()
);

create table if not exists sessions (
  id          bigint generated always as identity primary key,
  at          timestamptz not null default now(),
  who         text,
  play        text,                       -- plays/<slug>, or null for company-wide work
  summary     text not null,
  files       text[],
  skills      text[]
);

create table if not exists intelligence (
  id              bigint generated always as identity primary key,
  at              timestamptz not null default now(),
  who             text,
  play            text,
  category        text not null,          -- copy_angle, subject_line, segment, persona, offer, cta, ...
  label           text not null,
  insight         text not null,
  recommendation  text,
  sample_size     integer,
  reply_rate      numeric,
  confidence      text,                   -- low / medium / high
  status          text not null default 'observed'   -- observed / testing / proven / retired
);

-- Call transcripts. Optional: only useful if the team records calls (Fireflies,
-- Granola). Confidential calls can be stored summary-only.
create table if not exists meetings (
  id            text primary key,         -- recorder's id, or anything unique
  at            timestamptz not null,
  title         text,
  participants  text[],
  summary       text,
  action_items  jsonb,
  transcript    text
);

create index if not exists sessions_at_idx      on sessions (at desc);
create index if not exists intelligence_play_idx on intelligence (play, at desc);
create index if not exists meetings_at_idx      on meetings (at desc);

alter table team         enable row level security;
alter table api_keys     enable row level security;
alter table sessions     enable row level security;
alter table intelligence enable row level security;
alter table meetings     enable row level security;
