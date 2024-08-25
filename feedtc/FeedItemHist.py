import sqlite3

from feedtc.FeedItem import FeedItem


class FeedItemHist:
    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(FeedItemHist, cls).__new__(cls)
            cls.__initialized = False
        return cls.__instance

    def __init__(self, database=None):
        if self.__initialized: return
        self.__initialized = True
        self.conn = None
        if database: self.conn = sqlite3.connect(database)

    def __del__(self):
        if self.conn: self.conn.close()

    def connect(self, database):
        if not self.conn is None: self.conn.close()
        self.conn = None
        self.conn = sqlite3.connect(database)

    def close(self):
        self.conn.close()
        self.conn = None

    def count_item(self, item: FeedItem) -> int:
        cursor = self.conn.cursor()

        cursor.execute(
            "select count(*) from t_added_item where ? like '%'||match_name||'%' or (series_name != '' and series_name = ?)",
            (item.title, item.series_name))
        row = cursor.fetchall()

        return row[0][0]

    def save_item(self, item: FeedItem):
        print(item)
        self.conn.execute(
            "insert into t_added_item (title,match_name,series_name) values (?,?,?)",
            (item.title, item.match.group(0), item.series_name))
        self.conn.commit()
