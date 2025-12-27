PRAGMA foreign_keys = ON;

-- Add profile photo to Users
ALTER TABLE Users
ADD COLUMN profile_photo TEXT;

-- Add photo to People
ALTER TABLE People
ADD COLUMN photo TEXT;

