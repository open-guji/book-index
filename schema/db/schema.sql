-- book-index 规范化目录库表结构（v2，PostgreSQL 16）。
-- 本文件由 book-index-manager 生成，不要手改：python -m book_index_manager.db ddl
-- 真源是 git 里的 JSON；映射见 book_index_manager/db/mapping.py。
-- 约定：每类记录一张主表；数组对象进明细表（owner + seq 保序）；多类共用的明细表带 owner_type（W/B/C/E）；
--   依据、判断备注、ai_note 等审计字段不建列，进该行 notes（jsonb，键名照源文件）；
--   映射里没有的键、装不进列的值原样进 extra（jsonb），还原无损。

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TYPE edition_type AS ENUM ('刻本', '抄本', '稿本', '活字本', '石印本', '油印本', '曬印本', '鉛印本', '影印本', '套印本', '拓本', '印刷本', '其他');
CREATE TYPE loss_status AS ENUM ('lost', 'partially_extant', 'extant', 'undetermined');
CREATE TYPE work_subtype AS ENUM ('book', 'article', 'poem', 'chapter');
CREATE TYPE coll_subtype AS ENUM ('work_collection', 'book_collection');
CREATE TYPE entity_subtype AS ENUM ('people', 'collective', 'dynasty', 'reign', 'office', 'place', 'seal', 'publisher');
CREATE TYPE attested_status AS ENUM ('extant', 'lost', 'partial', 'not_seen');

-- 建库记录：库里现在对应的 git 提交；ddl_sha 变了要全量重建
CREATE TABLE build_meta (
  git_commit text NOT NULL,
  built_at text NOT NULL,
  ddl_sha text NOT NULL,
  mode text NOT NULL,
  text_commit text,
  PRIMARY KEY (git_commit)
);

CREATE TABLE work (
  id text NOT NULL,
  title text,
  measure_info text,
  schema_version int,
  revision text,
  revised_at date,
  subtype work_subtype,
  original_title text,
  dynasty text,
  period text,
  period_upper text,
  loss_status loss_status,
  authenticity text,
  additional_works jsonb,
  description_text text,
  file_name text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (id)
);

CREATE TABLE book (
  id text NOT NULL,
  title text,
  measure_info text,
  schema_version int,
  revision text,
  revised_at date,
  work_id text,
  edition text,
  edition_type edition_type,
  pub_place text,
  pub_publisher text,
  pub_details text,
  dating_certainty text,
  dating_source text,
  dating_era text,
  dating_reign text,
  dating_year int,
  dating_year_range int[],
  dating_year_uncertain boolean,
  dating_text text,
  physical_leaf_style text,
  physical_binding text,
  physical_dimensions text,
  physical_condition text,
  description_text text,
  zhsy_id text,
  file_name text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (id)
);

CREATE TABLE collection (
  id text NOT NULL,
  title text,
  measure_info text,
  schema_version int,
  revision text,
  revised_at date,
  subtype coll_subtype,
  edition text,
  work_id text,
  count_juan int,
  count_ce int,
  count_zhong int,
  count_han int,
  pub_year text,
  pub_year_iso text,
  pub_place text,
  pub_publisher text,
  pub_details text,
  description_text text,
  file_name text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (id)
);

CREATE TABLE entity (
  id text NOT NULL,
  subtype entity_subtype,
  primary_name text,
  dynasty text,
  period text,
  schema_version int,
  revision text,
  revised_at date,
  images jsonb,
  locations jsonb,
  todo jsonb,
  appears_in jsonb,
  description_text text,
  file_name text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (id)
);

-- entity 子类（subtype=people）
CREATE TABLE person (
  id text NOT NULL,
  title_or_office text,
  native_place text,
  native_place_entity_id text,
  cbdb_match text,
  cbdb_source text,
  PRIMARY KEY (id)
);

-- entity 子类（subtype=collective）
CREATE TABLE collective (
  id text NOT NULL,
  concept_id text,
  collective_kind text,
  institution_level text,
  function text,
  PRIMARY KEY (id)
);

-- entity 子类（subtype=publisher）
CREATE TABLE publisher (
  id text NOT NULL,
  publisher_kind text,
  status text,
  PRIMARY KEY (id)
);

-- entity 子类（subtype=office）
CREATE TABLE office (
  id text NOT NULL,
  concept_id text,
  office_level text,
  office_class text,
  function text,
  base_office_id text,
  rank_text text,
  qualifier_kind text,
  qualifier_name text,
  qualifier_note text,
  qualifier_target text,
  PRIMARY KEY (id)
);

-- entity 子类（subtype=place）
CREATE TABLE place (
  id text NOT NULL,
  concept_id text,
  place_level text,
  modern_text text,
  modern_relation text,
  modern_adcode text,
  modern_note text,
  PRIMARY KEY (id)
);

-- entity 子类（subtype=seal）
CREATE TABLE seal (
  id text NOT NULL,
  seal_text text,
  seal_kind text,
  seal_style text,
  seal_form text,
  usage_scope text,
  PRIMARY KEY (id)
);

-- entity 子类（subtype=reign）
CREATE TABLE reign (
  id text NOT NULL,
  ruler_name text,
  ruler_entity_id text,
  PRIMARY KEY (id)
);

CREATE TABLE bt_item (
  id text NOT NULL,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (id)
);

CREATE TABLE bt_version (
  id text NOT NULL,
  work_id text,
  book_id text,
  title text,
  entry_type text,
  schema_version int,
  revision text,
  revised_at text,
  version_label text,
  edition_note text,
  fetched_at text,
  updated_at text,
  guji_markdown text,
  line_is_column boolean,
  total_chapters int,
  total_entries int,
  matched_entries int,
  books_linked int,
  books_listed int,
  dropped_refs int,
  placeholder_chars int,
  collated_edition_type text,
  edition text,
  author text,
  compiler text,
  compiler_role text,
  annotator text,
  annotator_role text,
  table_notation text,
  heading_levels text[],
  juan_groups jsonb,
  variants jsonb,
  unknown_templates jsonb,
  fetch_stats jsonb,
  coverage jsonb,
  refs jsonb,
  volume_structure jsonb,
  source_name text,
  source_url text,
  source_license text,
  source_base_edition text,
  source_commit text,
  source_dump_date text,
  source_page_title text,
  source_revid int,
  source_siku_class text,
  source_catalog_line jsonb,
  source_upstream jsonb,
  source_type text,
  quality_grade text,
  quality_scope text,
  quality_issues jsonb,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (id)
);

CREATE TABLE fragment (
  id text NOT NULL,
  work_id text,
  title text,
  frag_type text,
  schema_version int,
  schema_ref text,
  loss_status loss_status,
  provenance text,
  statement text,
  updated_at text,
  text_condition text,
  cited_in_summary jsonb,
  collection_attested jsonb,
  other_statements jsonb,
  related_titles jsonb,
  coverage_level text,
  coverage_note text,
  fragments_attested int,
  fragments_recorded int,
  text_available boolean,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (id)
);

-- 共用：Book、Collection、Work
CREATE TABLE authorship (
  owner_id text NOT NULL,
  owner_type char(1) NOT NULL,
  seq int NOT NULL,
  name text,
  role text,
  entity_id text,
  dynasty text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

-- 共用：Book、Collection、Work
CREATE TABLE index_entry (
  owner_id text NOT NULL,
  owner_type char(1) NOT NULL,
  kind text NOT NULL,
  seq int NOT NULL,
  source text,
  source_bid text,
  title_info text,
  summary text,
  section text,
  author_info text,
  juan_count text,
  juan text,
  volume text,
  page text,
  edition text,
  catalog_no text,
  in_note_of text,
  attested_status attested_status,
  attested_status_raw text,
  misattached boolean,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id, kind, seq)
);

-- 共用：Book、Collection、Work
CREATE TABLE source_ref (
  owner_id text NOT NULL,
  owner_type char(1) NOT NULL,
  seq int NOT NULL,
  sid text,
  name text,
  type text,
  details text,
  version text,
  processor_version text,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

-- 共用：Book、Collection、Work
CREATE TABLE resource (
  owner_id text NOT NULL,
  owner_type char(1) NOT NULL,
  seq int NOT NULL,
  rid text,
  name text,
  label text,
  short_name text,
  url text,
  types text[],
  details text,
  grp text,
  group_role text,
  root_type text,
  color_mode text,
  expected_volumes int,
  note text,
  source_label text,
  volumes jsonb,
  metadata jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

-- 共用：Book、Work
CREATE TABLE resource_group (
  owner_id text NOT NULL,
  owner_type char(1) NOT NULL,
  key text NOT NULL,
  label text,
  description text,
  extra jsonb,
  PRIMARY KEY (owner_id, key)
);

-- 共用：Book、Collection、Work
CREATE TABLE member_of (
  member_id text NOT NULL,
  owner_type char(1) NOT NULL,
  seq int NOT NULL,
  collection_id text,
  volume_index jsonb,
  grp text,
  details text,
  section text,
  orig_order int,
  sub_items jsonb,
  extra jsonb,
  PRIMARY KEY (member_id, seq)
);

-- 共用：Book、Collection、Work
CREATE TABLE measure (
  owner_id text NOT NULL,
  owner_type char(1) NOT NULL,
  seq int NOT NULL,
  number int,
  unit text,
  note text,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

-- 共用：Book、Collection、Entity、Work
CREATE TABLE id_map (
  old_id text NOT NULL,
  owner_type char(1) NOT NULL,
  kind text NOT NULL,
  src text NOT NULL,
  direct_into text,
  rule text,
  at text,
  by text,
  why text,
  live_id text,
  title text,
  extra jsonb,
  PRIMARY KEY (old_id, kind, src, direct_into)
);

-- 共用：Book、Collection、Entity、Work
CREATE TABLE description_source (
  owner_id text NOT NULL,
  owner_type char(1) NOT NULL,
  seq int NOT NULL,
  source jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

-- 共用：Book、Collection、Entity、Work
CREATE TABLE alt_name (
  owner_id text NOT NULL,
  owner_type char(1) NOT NULL,
  seq int NOT NULL,
  name text,
  kind text,
  ambiguous boolean,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

CREATE TABLE work_relation (
  src text NOT NULL,
  seq int NOT NULL,
  dst text,
  relation text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (src, seq)
);

CREATE TABLE book_provenance (
  owner_id text NOT NULL,
  seq int NOT NULL,
  institution text,
  call_number text,
  note text,
  source text,
  seals text[],
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

CREATE TABLE book_seal_mark (
  owner_id text NOT NULL,
  prov_seq int NOT NULL,
  seq int NOT NULL,
  seal_id text,
  note text,
  extra jsonb,
  PRIMARY KEY (owner_id, prov_seq, seq)
);

CREATE TABLE book_base_edition (
  owner_id text NOT NULL,
  seq int NOT NULL,
  role text,
  relation text,
  name text,
  source text,
  book_id text,
  hypothetical_id text,
  confidence text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

CREATE TABLE book_location_history (
  owner_id text NOT NULL,
  seq int NOT NULL,
  location text,
  name text,
  item_id text,
  url text,
  note text,
  description text,
  source text,
  acckey text,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

-- 共用：Book、Collection
CREATE TABLE related_record (
  src text NOT NULL,
  owner_type char(1) NOT NULL,
  seq int NOT NULL,
  dst text,
  relation text,
  confidence text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (src, seq)
);

CREATE TABLE collection_content (
  owner_id text NOT NULL,
  seq int NOT NULL,
  type text,
  title text,
  scope text,
  note text,
  position text,
  work_id text,
  book_id text,
  collection_id text,
  related_work_id text,
  own_work_id text,
  categorization text,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

CREATE TABLE entity_external_id (
  owner_id text NOT NULL,
  key text NOT NULL,
  value jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id, key)
);

CREATE TABLE entity_dates (
  owner_id text NOT NULL,
  birth int,
  death int,
  floruit_start int,
  floruit_end int,
  start_year int,
  end_year int,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id)
);

CREATE TABLE place_history (
  owner_id text NOT NULL,
  seq int NOT NULL,
  name text,
  level text,
  start_year int,
  end_year int,
  parent_id text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (owner_id, seq)
);

CREATE TABLE place_history_dynasty (
  owner_id text NOT NULL,
  hseq int NOT NULL,
  seq int NOT NULL,
  dynasty_id text,
  extra jsonb,
  PRIMARY KEY (owner_id, hseq, seq)
);

CREATE TABLE entity_relation (
  src text NOT NULL,
  rel text NOT NULL,
  src_key text NOT NULL,
  seq int NOT NULL,
  dst text,
  kind text,
  year int,
  start_year int,
  role text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (src, rel, src_key, seq)
);

CREATE TABLE bt_manifest_version (
  item_id text NOT NULL,
  seq int NOT NULL,
  key text,
  kind text,
  label text,
  edition_label text,
  is_original boolean,
  license text,
  quality text,
  script text,
  source text,
  source_name text,
  source_url text,
  chapters_total int,
  note text,
  extra jsonb,
  PRIMARY KEY (item_id, seq)
);

CREATE TABLE bt_chapter (
  version_id text NOT NULL,
  seq int NOT NULL,
  n int,
  file text,
  title text,
  has_json boolean,
  md_len int,
  page_title text,
  revid int,
  juan text,
  volume int,
  pdf_pages text,
  has_table boolean,
  pages text,
  proofing boolean,
  text_version text,
  punct_version text,
  entity_version text,
  char_file text,
  cord_file text,
  punct_file text,
  entity_file text,
  norm_file text,
  fig_file text,
  extra jsonb,
  PRIMARY KEY (version_id, seq)
);

CREATE TABLE bt_heading (
  version_id text NOT NULL,
  ch_seq int NOT NULL,
  seq int NOT NULL,
  level int,
  label text,
  anchor text,
  extra jsonb,
  PRIMARY KEY (version_id, ch_seq, seq)
);

CREATE TABLE bt_other_source (
  version_id text NOT NULL,
  seq int NOT NULL,
  src_id text,
  name text,
  url text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (version_id, seq)
);

CREATE TABLE fragment_based_on (
  fragment_id text NOT NULL,
  seq int NOT NULL,
  source text,
  source_bid text,
  field text,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (fragment_id, seq)
);

CREATE TABLE fragment_collector (
  fragment_id text NOT NULL,
  seq int NOT NULL,
  collector text,
  work text,
  collector_work_id text,
  work_alias text,
  count int,
  count_unit text,
  statement text,
  statement_label text,
  note text,
  location jsonb,
  juans jsonb,
  edition text,
  measure text,
  appendix_count int,
  verified_against text,
  verify_result text,
  attested_count int,
  attested_count_basis jsonb,
  notes jsonb,
  extra jsonb,
  PRIMARY KEY (fragment_id, seq)
);

CREATE TABLE fragment_collector_section (
  fragment_id text NOT NULL,
  cseq int NOT NULL,
  seq int NOT NULL,
  file text,
  idx int,
  juan_no int,
  lei text,
  part text,
  section_title text,
  extra jsonb,
  PRIMARY KEY (fragment_id, cseq, seq)
);

CREATE TABLE fragment_piece (
  fragment_id text NOT NULL,
  seq int NOT NULL,
  num int,
  heading text,
  piece_title text,
  text text,
  text_status text,
  text_from text,
  attested_by text,
  confidence text,
  note text,
  editor_note text,
  extra jsonb,
  PRIMARY KEY (fragment_id, seq)
);

CREATE TABLE fragment_piece_collector (
  fragment_id text NOT NULL,
  pseq int NOT NULL,
  seq int NOT NULL,
  collector text,
  work text,
  collector_work_id text,
  juan text,
  extra jsonb,
  PRIMARY KEY (fragment_id, pseq, seq)
);

CREATE TABLE fragment_citation (
  fragment_id text NOT NULL,
  pseq int NOT NULL,
  seq int NOT NULL,
  raw text,
  book text,
  juan text,
  title text,
  section text,
  detail text,
  work_id text,
  note text,
  extra jsonb,
  PRIMARY KEY (fragment_id, pseq, seq)
);

CREATE INDEX ON work USING gin (title gin_trgm_ops);
CREATE INDEX ON book USING gin (title gin_trgm_ops);
CREATE INDEX ON collection USING gin (title gin_trgm_ops);
CREATE INDEX ON entity USING gin (primary_name gin_trgm_ops);
CREATE INDEX ON alt_name USING gin (name gin_trgm_ops);
CREATE INDEX ON authorship USING gin (name gin_trgm_ops);
CREATE INDEX ON authorship (entity_id) WHERE entity_id IS NOT NULL;
CREATE INDEX ON book (work_id);
CREATE INDEX ON work (period);
CREATE INDEX ON entity (subtype);
CREATE INDEX ON book_provenance (institution);
CREATE INDEX ON book_seal_mark (seal_id);
CREATE INDEX ON book_base_edition (book_id);
CREATE INDEX ON index_entry (source_bid);
CREATE INDEX ON resource (rid);
CREATE INDEX ON member_of (collection_id);
CREATE INDEX ON work_relation (dst, relation);
CREATE INDEX ON related_record (dst);
CREATE INDEX ON entity_relation (dst, rel);
CREATE INDEX ON entity_external_id (key, value);
CREATE INDEX ON place_history_dynasty (dynasty_id);
CREATE INDEX ON id_map (live_id);
CREATE INDEX ON bt_version (work_id);
CREATE INDEX ON bt_version (book_id);
CREATE INDEX ON fragment (work_id);
CREATE INDEX ON fragment_piece USING gin (text gin_trgm_ops);
