CREATE TABLE IF NOT EXISTS venues (
  venue_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  acronym      TEXT,
  type         TEXT CHECK(type IN ('conference','journal','workshop')) NOT NULL,
  scope        TEXT CHECK(scope IN ('BR','INT','both')) NOT NULL,
  area         TEXT,
  qualis       TEXT,
  core         TEXT,
  sjr_quartile TEXT,
  h5           INTEGER,
  url          TEXT,
  notes        TEXT,
  submission_mode TEXT CHECK(submission_mode IN ('rolling','cfp')),
  UNIQUE(name, type)
);

CREATE TABLE IF NOT EXISTS deadlines (
  deadline_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  venue_id      INTEGER NOT NULL REFERENCES venues(venue_id) ON DELETE CASCADE,
  edition       TEXT,
  abstract_due  DATE,
  paper_due     DATE,
  notification  DATE,
  camera_ready  DATE,
  event_start   DATE,
  event_end     DATE,
  location      TEXT,
  cfp_url       TEXT
);

CREATE TABLE IF NOT EXISTS submissions (
  submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
  title         TEXT NOT NULL,
  venue_id      INTEGER REFERENCES venues(venue_id),
  status        TEXT CHECK(status IN (
                  'idea','drafting','submitted','under_review',
                  'revision','accepted','rejected','published','withdrawn'
                )) NOT NULL DEFAULT 'idea',
  submitted_on  DATE,
  decision_on   DATE,
  topics        TEXT,
  coauthors     TEXT,
  notes         TEXT,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deadlines_paper_due ON deadlines(paper_due);
CREATE INDEX IF NOT EXISTS idx_submissions_status  ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_venues_scope        ON venues(scope);
