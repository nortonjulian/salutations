\c salutations

-- Drop the "contacts" table
DROP TABLE IF EXISTS "contacts" CASCADE;
-- Finally, drop the "users" table
DROP TABLE IF EXISTS "users" CASCADE;
-- Drop the "conversations" table if it exists
DROP TABLE IF EXISTS "conversations" CASCADE;

-- Check if the "messages" table exists and drop it if it does
DROP TABLE IF EXISTS "messages" CASCADE;

-- Create the "users" table
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

-- Create the "conversations" table (with foreign keys)
CREATE TABLE "conversations" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "users" (id),
    FOREIGN KEY (contact_id) REFERENCES "contacts" (id)
);

-- Create the "messages" table (with foreign key)
CREATE TABLE "messages" (
    id SERIAL PRIMARY KEY,
    content text NOT NULL,
    conversation_id INTEGER NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES "conversations" (id)
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

-- Insert sample conversation data into the "conversations" table
-- You can add conversation data as needed
INSERT INTO "conversations" (user_id, contact_id)
VALUES
  (1, 1),
  (1, 2);

-- Insert sample message data into the "messages" table
-- You can add message data as needed
INSERT INTO "messages" (content, conversation_id)
VALUES
    ('Hello, how are you?', 1),
    ('Doing well, thanks!', 1);
