create table events (
  id bigint generated always as identity primary key,
  gmail_message_id text not null unique,
  status text not null default 'processing'
    check (status in ('processing', 'processed', 'skipped', 'failed')),
  attempts int not null default 1,
  error text,
  result jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table tickets (
  id bigint generated always as identity primary key,
  gmail_thread_id text not null unique,
  customer_email text not null,
  subject text not null default '',
  category text,
  status text not null default 'open'
    check (status in ('open', 'answered', 'escalated')),
  proposed_action text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table messages (
  id bigint generated always as identity primary key,
  ticket_id bigint not null references tickets (id) on delete cascade,
  gmail_message_id text not null unique,
  direction text not null check (direction in ('in', 'out')),
  from_address text not null,
  body text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index messages_ticket_id_idx on messages (ticket_id);

create table knowledge_base (
  id bigint generated always as identity primary key,
  section text not null,
  title text not null,
  content text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (section, title)
);

create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger update_events_updated_at
    before update on events
    for each row
    execute function update_updated_at_column();

create trigger update_tickets_updated_at
    before update on tickets
    for each row
    execute function update_updated_at_column();

create trigger update_messages_updated_at
    before update on messages
    for each row
    execute function update_updated_at_column();

create trigger update_knowledge_base_updated_at
    before update on knowledge_base
    for each row
    execute function update_updated_at_column();

alter table events enable row level security;
alter table tickets enable row level security;
alter table messages enable row level security;
alter table knowledge_base enable row level security;