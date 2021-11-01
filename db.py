import sqlite3
import datetime
import pytz
import config


class BotDB:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.error = None
        self.db_name = config.DB_NAME
        self.tz = pytz.timezone('Etc/GMT-7')

    def open_connection(self):
        self.error = None
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

    def close_connection(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()

    def print_error(self, error):
        print('Error wish your db! Error:\n', error)
        self.error = error

    def get_today(self):
        cur_time = datetime.datetime.now(tz=self.tz)
        return datetime.datetime.strptime(cur_time.strftime('%Y-%m-%d'), '%Y-%m-%d')

    def user_exist(self, user_id):
        try:
            self.open_connection()
            result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
            return False if result.fetchone() is None else True
        except sqlite3.Error as error:
            self.print_error(error)
        finally:
            self.close_connection()

    def add_user(self, user_id):
        try:
            self.open_connection()
            self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))
            self.connection.commit()
        except sqlite3.Error as error:
            self.print_error(error)
        finally:
            self.close_connection()

    def insert_data(self, user_id, plan=0, earned=0):
        try:
            self.open_connection()
            today = self.get_today()
            self.cursor.execute("INSERT INTO `statistic` (`fk_user_id`, `date`, `plan`, `earned`) VALUES (?, ?, ?, ?)",
                                (user_id, today, plan, earned,))
            self.connection.commit()
        except sqlite3.Error as error:
            self.print_error(error)
        finally:
            self.close_connection()

    def update_data(self, user_id, field, value):
        try:
            self.open_connection()
            today = self.get_today()
            self.cursor.execute(f"UPDATE `statistic` SET {field} = ? WHERE `fk_user_id` = ? AND `date` = ?",
                                (value, user_id, today,))
            self.connection.commit()
            return self.cursor.rowcount
        except sqlite3.Error as error:
            self.print_error(error)
        finally:
            self.close_connection()

    def get_today_earned(self, user_id):
        try:
            self.open_connection()
            today = self.get_today()
            result = self.cursor.execute("SELECT `earned` FROM `statistic` WHERE `fk_user_id` = ? AND `date` = ?",
                                         (user_id, today,))
            return result.fetchone()
        except sqlite3.Error as error:
            self.print_error(error)
        finally:
            self.close_connection()

    def get_stats(self, user_id, other_day, today):
        try:
            self.open_connection()
            result = self.cursor.execute("SELECT ROW_NUMBER () OVER (ORDER BY `date`) as `№`, "
                "strftime('%Y.%m.%d', `date`) as `date`, `plan`, `earned` "
                "FROM `statistic` WHERE `fk_user_id` = ? AND `date` BETWEEN ? AND ?", (user_id, other_day, today,))
            return result.fetchall()
        except sqlite3.Error as error:
            self.print_error(error)
        finally:
            self.close_connection()

    def delete_data(self, user_id):
        try:
            self.open_connection()
            self.cursor.execute("PRAGMA foreign_keys = 1")
            self.cursor.execute("DELETE FROM `users` WHERE `user_id` = ?", (user_id,))
            self.connection.commit()
        except sqlite3.Error as error:
            self.print_error(error)
        finally:
            self.close_connection()
