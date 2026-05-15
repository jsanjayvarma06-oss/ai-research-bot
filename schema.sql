-- ============================================================
-- AI Research Brain — Supabase Schema
-- Run this entire file in your Supabase SQL Editor
-- ============================================================


-- STEP 1: Enable pgvector extension for semantic search
create extension if not exists vector;


-- STEP 2: Create the main research notes table
create table research_notes (
  id               uuid        default gen_random_uuid() primary key,
  author_name      text        not null,
  author_slack_id  text        not null,
  filename         text,
  raw_content      text        not null,
  summary          text,
  topics           text[],
  embedding        vector(768),
  created_at       timestamptz default now()
);


-- STEP 3: Create index for faster vector search
create index on research_notes using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);


-- STEP 4: Create the semantic search function
create or replace function match_notes(
  query_embedding  vector(768),
  match_threshold  float   default 0.4,
  match_count      int     default 5
)
returns table (
  id              uuid,
  author_name     text,
  filename        text,
  summary         text,
  topics          text[],
  raw_content     text,
  created_at      timestamptz,
  similarity      float
)
language sql stable
as $$
  select
    id,
    author_name,
    filename,
    summary,
    topics,
    raw_content,
    created_at,
    1 - (embedding <=> query_embedding) as similarity
  from research_notes
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;
