PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- ===============================
-- PEOPLE: Birth location (GPS)
-- ===============================
ALTER TABLE People ADD COLUMN birth_lat REAL;
ALTER TABLE People ADD COLUMN birth_lng REAL;

-- ===============================
-- EVENTS: Event location (GPS)
-- ===============================
ALTER TABLE Events ADD COLUMN place_lat REAL;
ALTER TABLE Events ADD COLUMN place_lng REAL;

COMMIT;

