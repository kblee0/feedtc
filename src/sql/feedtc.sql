CREATE TABLE IF NOT EXISTS "T_ITEM_HIST" (
        TITLE TEXT PRIMARY KEY,
        MATCH_NAME TEXT,
        SERIES_NAME TEXT,
        REG_DT    TIMESTAMP  DEFAULT (datetime('now','localtime'))
);
