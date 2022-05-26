DROP TABLE IF EXISTS Games;
DROP TABLE IF EXISTS Publishers;
DROP TABLE IF EXISTS Searches;
DROP TABLE IF EXISTS Search_Results;
DROP TABLE IF EXISTS Related_Games;
DROP TABLE IF EXISTS Recent_Files;
DROP TABLE IF EXISTS Game_Relationships;
DROP TABLE IF EXISTS User_Lists;
DROP TABLE IF EXISTS Authors;
DROP TABLE IF EXISTS User_List_Games;
DROP TABLE IF EXISTS Games_Categories;
DROP TABLE IF EXISTS Artists;
DROP TABLE IF EXISTS Ownership_Statuses;
DROP TABLE IF EXISTS Author_Game;
DROP TABLE IF EXISTS Artist_Game;
DROP TABLE IF EXISTS User_Settings;
DROP TABLE IF EXISTS People;
DROP TABLE IF EXISTS Categories;
DROP VIEW IF EXISTS BGG_Games_View;


CREATE TABLE Publishers (
id INTEGER PRIMARY KEY NOT NULL,
name TEXT NOT NULL UNIQUE);

CREATE TABLE Searches (
id INTEGER PRIMARY KEY NOT NULL,
query TEXT NOT NULL UNIQUE,
date_time DATETIME NOT NULL);

CREATE TABLE Recent_Files (
id INTEGER PRIMARY KEY NOT NULL,
path TEXT NOT NULL UNIQUE,
date_time DATETIME NOT NULL);

CREATE TABLE Game_Relationships (
id INTEGER PRIMARY KEY NOT NULL,
type TEXT NOT NULL UNIQUE);

CREATE TABLE User_Lists (
id INTEGER PRIMARY KEY NOT NULL,
username TEXT NOT NULL UNIQUE,
xml TEXT NOT NULL,
last_refreshed DATETIME NOT NULL);

CREATE TABLE Ownership_Statuses (
id INTEGER PRIMARY KEY NOT NULL,
name TEXT NOT NULL UNIQUE);

CREATE TABLE People (
id INTEGER PRIMARY KEY NOT NULL,
name TEXT NOT NULL UNIQUE);

CREATE TABLE Categories (
id INTEGER PRIMARY KEY NOT NULL,
name TEXT NOT NULL UNIQUE);

CREATE TABLE Games (
id INTEGER PRIMARY KEY NOT NULL UNIQUE,
timestamp DATETIME NOT NULL,
name TEXT NOT NULL,
sub_name TEXT,
version INTEGER NOT NULL,
image BLOB NOT NULL,
description TEXT NOT NULL,
publisher_id INTEGER NOT NULL,
release_year DATE NOT NULL,
min_players INTEGER NOT NULL,
max_players INTEGER NOT NULL,
recommended_players INTEGER,
min_age INTEGER NOT NULL,
min_play_time INTEGER NOT NULL,
max_play_time INTEGER NOT NULL,
bgg_rating FLOAT,
bgg_rank INTEGER,
complexity FLOAT NOT NULL,
UNIQUE(name, sub_name, version),
FOREIGN KEY(publisher_id) REFERENCES Publishers(id));

CREATE TABLE Search_Results (
game_id INTEGER NOT NULL,
search_id INTEGER NOT NULL,
xml TEXT NOT NULL,
PRIMARY KEY (game_id,search_id),
FOREIGN KEY(game_id) REFERENCES Games(id),
FOREIGN KEY(search_id) REFERENCES Searches(id));

CREATE TABLE Related_Games (
game1_id INTEGER NOT NULL,
game2_id INTEGER NOT NULL,
relationship_id INTEGER NOT NULL,
PRIMARY KEY (game1_id,game2_id),
FOREIGN KEY(game1_id) REFERENCES Games(id),
FOREIGN KEY(game2_id) REFERENCES Games(id),
FOREIGN KEY(relationship_id) REFERENCES Game_Relationships(id));

CREATE TABLE Authors (
id INTEGER PRIMARY KEY NOT NULL,
person_id INTEGER NOT NULL,
FOREIGN KEY(person_id) REFERENCES People(id));

CREATE TABLE User_List_Games (
id INTEGER PRIMARY KEY NOT NULL,
user_List_id INTEGER NOT NULL,
game_id INTEGER NOT NULL,
ownership_status_id INTEGER NOT NULL,
FOREIGN KEY(user_List_id) REFERENCES User_Lists(id),
FOREIGN KEY(game_id) REFERENCES Games(id),
FOREIGN KEY(ownership_status_id) REFERENCES Ownership_Statuses(id));

CREATE TABLE Games_Categories (
category_id INTEGER NOT NULL,
game_id INTEGER NOT NULL,
PRIMARY KEY (category_id,game_id),
FOREIGN KEY(category_id) REFERENCES Categories(id),
FOREIGN KEY(game_id) REFERENCES Games(id));

CREATE TABLE Artists (
id INTEGER PRIMARY KEY NOT NULL,
person_id INTEGER NOT NULL,
FOREIGN KEY(person_id) REFERENCES People(id));

CREATE TABLE Author_Game (
author_id INTEGER NOT NULL,
game_id INTEGER NOT NULL,
PRIMARY KEY (author_id,game_id),
FOREIGN KEY(author_id) REFERENCES Authors(id),
FOREIGN KEY(game_id) REFERENCES Games(id));

CREATE TABLE Artist_Game (
artist_id INTEGER NOT NULL,
game_id INTEGER NOT NULL,
PRIMARY KEY (artist_id,game_id),
FOREIGN KEY(artist_id) REFERENCES Artists(id),
FOREIGN KEY(game_id) REFERENCES Games(id));

CREATE TABLE User_Settings (
id INTEGER NOT NULL,
keyword TEXT NOT NULL,
value TEXT NOT NULL
);

CREATE VIEW BGG_Games_View AS
    SELECT g.name,
           g.sub_name,
           g.version,
           pub.name,
           g.image,
           g.description,
           g.release_year,
           g.min_players,
           g.max_players,
           g.recommended_players,
           g.min_age,
           g.min_play_time,
           g.max_play_time,
           g.bgg_rating,
           g.bgg_rank
    FROM User_Lists bggl
        LEFT JOIN User_List_Games bgglg ON bgglg.user_List_id = bggl.id
        LEFT JOIN Games g ON bgglg.game_id = g.id
        LEFT JOIN Publishers pub ON pub.id = g.publisher_id
        LEFT JOIN Author_Game aug ON aug.game_id = g.id
        LEFT JOIN Authors au ON au.id = aug.author_id
        LEFT JOIN Artist_Game arg ON arg.game_id = g.id
        LEFT JOIN Artists ar ON ar.id = arg.artist_id
        LEFT JOIN Ownership_Statuses own ON own.id = bggl.ownership_status_id
        LEFT JOIN Games_Categories gcat ON gcat.game_id = g.id
        LEFT JOIN Categories cat ON gcat.category_id = cat.id
        LEFT JOIN Related_Games rg ON rg.game_id1 = g.id
        LEFT JOIN Game_Relationships grg ON grg.id = rg.relationship_id;