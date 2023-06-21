\c greetings

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS contacts;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name text NOT NULL,
    last_name text NOT NULL,
    username text NOT NULL UNIQUE,
    email text NOT NULL UNIQUE,
    password text NOT NULL
);

CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    username text NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    number bigint NOT NULL UNIQUE
);

INSERT INTO users
  (username, first_name, last_name, email, password)
VALUES
  ('abc', 'first', 'name', 'firstname@gmail', 'newguy23');

INSERT INTO contacts
  (username, first_name, last_name, number)
VALUES
  ('abc', 'contact1', 'person', 1234567890);
