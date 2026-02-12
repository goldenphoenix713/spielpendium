    INSERT OR REPLACE INTO User_Lists
    (username, xml, last_refreshed)
    VALUES(?, ?, strftime('%Y-%m-%dT%H:%M:%S','now'));