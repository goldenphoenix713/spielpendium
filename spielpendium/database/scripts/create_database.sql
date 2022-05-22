DROP TABLE IF EXISTS Games;
DROP TABLE IF EXISTS Publishers;
DROP TABLE IF EXISTS Searches;
DROP TABLE IF EXISTS Search_Results;
DROP TABLE IF EXISTS Related_Games;
DROP TABLE IF EXISTS Recent_Files;
DROP TABLE IF EXISTS Game_Relationships;
DROP TABLE IF EXISTS BGG_Lists;
DROP TABLE IF EXISTS Authors;
DROP TABLE IF EXISTS BGG_List_Games;
DROP TABLE IF EXISTS Games_Categories;
DROP TABLE IF EXISTS Artists;
DROP TABLE IF EXISTS Ownership_Statuses;
DROP TABLE IF EXISTS Author_Game;
DROP TABLE IF EXISTS Artist_Game;
DROP TABLE IF EXISTS User_Settings;
DROP TABLE IF EXISTS People;
DROP TABLE IF EXISTS Categories;


CREATE TABLE Publishers (
id INT PRIMARY KEY NOT NULL,
name TEXT NOT NULL);

CREATE TABLE Searches (
id INT PRIMARY KEY NOT NULL,
query TEXT NOT NULL,
date_time DATETIME NOT NULL);

CREATE TABLE Recent_Files (
id INT PRIMARY KEY NOT NULL,
path TEXT NOT NULL,
date_time DATETIME NOT NULL);

CREATE TABLE Game_Relationships (
id INT PRIMARY KEY NOT NULL,
type TEXT NOT NULL UNIQUE);

CREATE TABLE BGG_Lists (
id INT PRIMARY KEY NOT NULL,
username TEXT NOT NULL,
xml TEXT NOT NULL,
last_refreshed DATETIME NOT NULL);

CREATE TABLE Ownership_Statuses (
id INT PRIMARY KEY NOT NULL,
name TEXT NOT NULL);

CREATE TABLE People (
id INT PRIMARY KEY NOT NULL,
name TEXT NOT NULL);

CREATE TABLE Categories (
id INT PRIMARY KEY NOT NULL,
name TEXT NOT NULL);

CREATE TABLE Games (
id INT PRIMARY KEY NOT NULL UNIQUE,
timestamp DATETIME NOT NULL,
name TEXT NOT NULL,
sub_name TEXT,
version INT NOT NULL,
image BLOB NOT NULL,
description TEXT NOT NULL,
publisher_id INT NOT NULL,
release_year DATE NOT NULL,
min_players INT NOT NULL,
max_players INT NOT NULL,
recommended_players INT,
min_age INT NOT NULL,
min_play_time INT NOT NULL,
max_play_time INT NOT NULL,
bgg_rating FLOAT,
bgg_rank INT,
complexity FLOAT NOT NULL,
FOREIGN KEY(publisher_id) REFERENCES Publishers(id));

CREATE TABLE Search_Results (
game_id INT NOT NULL,
search_id INT NOT NULL,
xml TEXT NOT NULL,
PRIMARY KEY (game_id,search_id),
FOREIGN KEY(game_id) REFERENCES Games(id),
FOREIGN KEY(search_id) REFERENCES Searches(id));

CREATE TABLE Related_Games (
game1_id INT NOT NULL,
game2_id INT NOT NULL,
relationship_id INT NOT NULL,
PRIMARY KEY (game1_id,game2_id),
FOREIGN KEY(game1_id) REFERENCES Games(id),
FOREIGN KEY(game2_id) REFERENCES Games(id),
FOREIGN KEY(relationship_id) REFERENCES Game_Relationships(id));

CREATE TABLE Authors (
id INT PRIMARY KEY NOT NULL,
person_id INT NOT NULL,
FOREIGN KEY(person_id) REFERENCES People(id));

CREATE TABLE BGG_List_Games (
id INT PRIMARY KEY NOT NULL,
bgg_list_id INT NOT NULL,
game_id INT NOT NULL,
ownership_status_id INT NOT NULL,
FOREIGN KEY(bgg_list_id) REFERENCES BGG_Lists(id),
FOREIGN KEY(game_id) REFERENCES Games(id),
FOREIGN KEY(ownership_status_id) REFERENCES Ownership_Statuses(id));

CREATE TABLE Games_Categories (
category_id INT NOT NULL,
game_id INT NOT NULL,
PRIMARY KEY (category_id,game_id),
FOREIGN KEY(category_id) REFERENCES Categories(id),
FOREIGN KEY(game_id) REFERENCES Games(id));

CREATE TABLE Artists (
id INT PRIMARY KEY NOT NULL,
person_id INT NOT NULL,
FOREIGN KEY(person_id) REFERENCES People(id));

CREATE TABLE Author_Game (
author_id INT NOT NULL,
game_id INT NOT NULL,
PRIMARY KEY (author_id,game_id),
FOREIGN KEY(author_id) REFERENCES Authors(id),
FOREIGN KEY(game_id) REFERENCES Games(id));

CREATE TABLE Artist_Game (
artist_id INT NOT NULL,
game_id INT NOT NULL,
PRIMARY KEY (artist_id,game_id),
FOREIGN KEY(artist_id) REFERENCES Artists(id),
FOREIGN KEY(game_id) REFERENCES Games(id));

CREATE TABLE User_Settings (
id INT NOT NULL,
keyword TEXT NOT NULL,
value TEXT NOT NULL
);
