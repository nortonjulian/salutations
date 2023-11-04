\c salutations

-- Drop the "contacts" table
DROP TABLE IF EXISTS "contacts" CASCADE;
-- Finally, drop the "users" table
DROP TABLE IF EXISTS "users" CASCADE;
-- Drop the "conversations" table if it exists
DROP TABLE IF EXISTS "conversations" CASCADE;

-- Check if the "messages" table exists and drop it if it does
DROP TABLE IF EXISTS "messages" CASCADE;

DROP TABLE IF EXISTS twilio_number_association;

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
    sender_number VARCHAR(255) NOT NULL,
    receiver_number VARCHAR(255) NOT NULL,
    user_id INTEGER NULL,
    contact_id INTEGER NULL,
    messages_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES "users" (id),
    FOREIGN KEY (contact_id) REFERENCES "contacts" (id)
);

-- Create the "messages" table (with foreign key)
CREATE TABLE "messages" (
    id SERIAL PRIMARY KEY,
    content text NOT NULL,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NULL,
    receiver_number VARCHAR(255) NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NULL,
    messages_read BOOLEAN,
    FOREIGN KEY (conversation_id) REFERENCES "conversations" (id),
    FOREIGN KEY (sender_id) REFERENCES "users" (id)
);

-- Create the "twilio_number_association" table
CREATE TABLE "twilio_number_association" (
    id SERIAL PRIMARY KEY,
    twilio_number VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
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

-- Insert sample conversation data into the "conversations" table
-- You can add conversation data as needed
INSERT INTO "conversations" (user_id, sender_number, receiver_number, contact_id)
VALUES
  (1, 'sender_number1', 'receiver_number1', 1),
  (2, 'sender_number2', 'receiver_number2', 2);

-- Insert a message without specifying a receiver number
INSERT INTO "messages" (content, conversation_id, sender_id)
VALUES
    ('Hello, how are you?', 1, 1),
    ('Doing well, thanks!', 2, 2);

-- Insert sample twilio number associations
-- You can add associations as needed
INSERT INTO "twilio_number_association" (twilio_number, user_id)
VALUES
  ('+1234567890', 1),
  ('+9876543210', 2);
