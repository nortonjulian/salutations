\c greetings

-- Drop the "contacts" table
DROP TABLE IF EXISTS "contacts" CASCADE;
-- Finally, drop the "users" table
DROP TABLE IF EXISTS "users" CASCADE;

-- Create the "user" table
CREATE TABLE "users" (
    id SERIAL PRIMARY KEY,
    first_name text NOT NULL,
    last_name text NOT NULL,
    username text NOT NULL UNIQUE,
    email text NOT NULL UNIQUE,
    password text NOT NULL
);

-- Create the "contacts" table
CREATE TABLE "contacts" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    number bigint NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES "users" (id)
);


-- Insert sample user data into the "user" table
INSERT INTO "users"
  (username, first_name, last_name, email, password)
VALUES
  ('user1', 'John', 'Doe', 'john@example.com', 'hashed_password1'),
  ('user2', 'Jane', 'Smith', 'jane@example.com', 'hashed_password2');

-- Insert sample contact data into the "contact" table
INSERT INTO "contacts"
  (user_id, first_name, last_name, number)
VALUES
  (1, 'contact1', 'person', 1234567890),
  (2, 'contact2', 'person', 2345678901);
ON CONFLICT (number) DO UPDATE
SET
  user_id = EXCLUDED.user_id,
  first_name = EXCLUDED.first_name,
  last_name = EXCLUDED.last_name;
