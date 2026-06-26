CREATE DATABASE carbonsense1;

USE carbonsense1;

CREATE TABLE users (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(50),
email VARCHAR(100),
password VARCHAR(100)
);

CREATE TABLE actions (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT,
category VARCHAR(50),
action_type VARCHAR(100),
value FLOAT,
carbon_saved FLOAT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
