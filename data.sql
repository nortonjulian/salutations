\c greetings

-- Drop the "user" table if it exists
DROP TABLE IF EXISTS "users";
DROP TABLE IF EXISTS "contacts";

-- Create the "user" table
CREATE TABLE "users" (
    id SERIAL PRIMARY KEY,
    first_name text NOT NULL,
    last_name text NOT NULL,
    username text NOT NULL UNIQUE,
    email text NOT NULL UNIQUE,
    password text NOT NULL
);

-- Create the "contact" table
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    number bigint NOT NULL UNIQUE
);

-- Insert sample user data into the "user" table
INSERT INTO "user"
  (username, first_name, last_name, email, password)
VALUES
  ('abc', 'first', 'name', 'firstname@gmail.com', 'hashed_password');

-- Insert sample contact data into the "contact" table
INSERT INTO contact
  (user_id, first_name, last_name, number)
VALUES
  (1, 'contact1', 'person', 1234567890)
ON CONFLICT (number) DO UPDATE
SET
  user_id = EXCLUDED.user_id,
  first_name = EXCLUDED.first_name,
  last_name = EXCLUDED.last_name;
