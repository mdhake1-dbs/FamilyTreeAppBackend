PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- ===============================
-- PEOPLE: Birth location using DIGIPIN
-- ===============================
ALTER TABLE People ADD COLUMN birth_digipin TEXT;


-- ===============================
-- EVENTS: Event location using DIGIPIN
-- ===============================
ALTER TABLE Events ADD COLUMN place_digipin TEXT;

COMMIT;

