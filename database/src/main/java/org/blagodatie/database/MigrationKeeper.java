package org.blagodatie.database;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.room.migration.Migration;
import androidx.sqlite.db.SupportSQLiteDatabase;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

final class MigrationKeeper {

    private static final String TAG = MigrationKeeper.class.getSimpleName();

    private MigrationKeeper () {
    }

    private static final Migration MIGRATION_1_2 = new Migration(1, 2) {
        @Override
        public void migrate (final SupportSQLiteDatabase database) {
            Log.d(TAG, "Migrate from 1 to 2");
            //выключить внешние ключи
            database.execSQL("PRAGMA foreign_keys = OFF");
            //начать транзакцию
            database.execSQL("BEGIN TRANSACTION");

            //создать таблицу tbl_symptom
            database.execSQL(
                    "CREATE TABLE IF NOT EXISTS `tbl_symptom` (" +
                            "`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                            "`name` TEXT NOT NULL)"
            );
            database.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS " +
                            "`index_tbl_symptom_name` ON `tbl_symptom` (`name`)"
            );

            //заполнить таблицу tbl_symptom
            database.execSQL(
                    "INSERT INTO `tbl_symptom` (`id`, `name`) " +
                            "VALUES (25, 'Пробуждение'), " +
                            "(19, 'Хорошее настроение'), " +
                            "(15, 'Хорошее самочувствие'), " +
                            "(20, 'Плохое настроение'), " +
                            "(29, 'Плохое самочувствие'), " +
                            "(1, 'Нехватка питьевой воды'), " +
                            "(2, 'Нехватка еды'), " +
                            "(3, 'Нехватка лекарств'), " +
                            "(17, 'Повышенное давление'), " +
                            "(18, 'Пониженное давление'), " +
                            "(16, 'Сердечная боль'), " +
                            "(11, 'Головная боль'), " +
                            "(10, 'Сухость носа'), " +
                            "(26, 'Заложенность носа'), " +
                            "(27, 'Насморк'), " +
                            "(5, 'Температура'), " +
                            "(28, 'Озноб'), " +
                            "(24, 'Аллергия'), " +
                            "(6, 'Кашель'), " +
                            "(4, 'Слабость'), " +
                            "(7, 'Боль в груди при дыхании'), " +
                            "(8, 'Затруднённое дыхание'), " +
                            "(9, 'Одышка'), " +
                            "(12, 'Боль и ломота в мышцах и суставах'), " +
                            "(13, 'Рвота'), " +
                            "(14, 'Диарея'), " +
                            "(21, 'Зубная боль'), " +
                            "(22, 'Боль в ушах'), " +
                            "(23, 'Головокружение'), " +
                            "(30, 'Чувство тревоги'), " +
                            "(31, 'Похолодало'), " +
                            "(32, 'Потеплело'), " +
                            "(33, 'Дождь'), " +
                            "(34, 'Ветер'), " +
                            "(35, 'Жара'), " +
                            "(36, 'Астма'), " +
                            "(37, 'Хорошая погода'), " +
                            "(40, 'Влажно'), " +
                            "(41, 'Сухо'), " +
                            "(42, 'Свежо'), " +
                            "(44, 'Прием пищи'), " +
                            "(45, 'Запор')"
            );

            //добавить в таблицу tbl_user_symptom внешний ключ к таблице tbl_symptom
            {
                //создать новую таблицу tbl_user_symptom с внешним ключом к tbl_symptom
                database.execSQL(
                        "CREATE TABLE IF NOT EXISTS `tbl_user_symptom_new` (" +
                                "`id` INTEGER PRIMARY KEY AUTOINCREMENT, " +
                                "`server_id` INTEGER, " +
                                "`user_id` INTEGER NOT NULL, " +
                                "`symptom_id` INTEGER NOT NULL, " +
                                "`timestamp` INTEGER NOT NULL, " +
                                "`latitude` REAL, " +
                                "`longitude` REAL, " +
                                "FOREIGN KEY(`symptom_id`) REFERENCES `tbl_symptom`(`id`) ON UPDATE NO ACTION ON DELETE NO ACTION )"
                );
                //перенести данные из старой таблицы в новую
                database.execSQL(
                        "INSERT INTO `tbl_user_symptom_new` " +
                                "SELECT * " +
                                "FROM tbl_user_symptom"
                );
                //удалить старую таблицу
                database.execSQL("DROP TABLE IF EXISTS `tbl_user_symptom`");
                //переименовать новую таблицу
                database.execSQL(
                        "ALTER TABLE `tbl_user_symptom_new` " +
                                "RENAME TO tbl_user_symptom"
                );
                //добавить индексы к новой таблице
                database.execSQL(
                        "CREATE UNIQUE INDEX IF NOT EXISTS " +
                                "`index_tbl_user_symptom_server_id` ON `tbl_user_symptom` (`server_id`)"
                );
            }

            //коммит
            database.execSQL("COMMIT");
            //включить внешние ключи
            database.execSQL("PRAGMA foreign_keys = ON");
        }
    };

    private static final Migration MIGRATION_2_3 = new Migration(2, 3) {
        @Override
        public void migrate (final SupportSQLiteDatabase database) {
            Log.d(TAG, "Migrate from 2 to 3");
            //выключить внешние ключи
            database.execSQL("PRAGMA foreign_keys = OFF");
            //начать транзакцию
            database.execSQL("BEGIN TRANSACTION");

            final SimpleDateFormat sdf = new SimpleDateFormat("Z", Locale.ENGLISH);
            final String currentTimezone = sdf.format(new Date());

            //в таблице tbl_symptom изменить столбец id, он может быть пустым
            {
                //создать новую таблицу
                database.execSQL(
                        "CREATE TABLE IF NOT EXISTS `tbl_symptom_new` (" +
                                "`name` TEXT NOT NULL, " +
                                "`id` INTEGER PRIMARY KEY AUTOINCREMENT)"
                );
                //перенести данные из старой таблицы в новую
                database.execSQL(
                        "INSERT INTO `tbl_symptom_new`(`id`, `name`) " +
                                "SELECT `id`, `name` " +
                                "FROM `tbl_symptom`"
                );
                //удалить старую таблицу
                database.execSQL("DROP TABLE IF EXISTS `tbl_symptom`");
                //переименовать новую таблицу
                database.execSQL(
                        "ALTER TABLE `tbl_symptom_new` " +
                                "RENAME TO `tbl_symptom`"
                );
                //Добавить индексы
                database.execSQL(
                        "CREATE UNIQUE INDEX IF NOT EXISTS " +
                                "`index_tbl_symptom_name` ON `tbl_symptom` (`name`)"
                );

                //добавить симптомы tbl_symptom
                database.execSQL(
                        "INSERT INTO `tbl_symptom` (`id`, `name`) " +
                                "VALUES (46, 'Чихание'), " +
                                "(47, 'Першит в горле'), " +
                                "(48, 'Пасмурно'), " +
                                "(49, 'Учащённое сердцебиение')"
                );
            }

            //добавить таблицу tbl_last_user_symptom
            {
                database.execSQL(
                        "CREATE TABLE IF NOT EXISTS `tbl_last_user_symptom` (" +
                                "`incognito_id` TEXT NOT NULL, " +
                                "`symptom_id` INTEGER NOT NULL, " +
                                "`timestamp` TEXT NOT NULL, " +
                                "`latitude` REAL, " +
                                "`longitude` REAL, " +
                                "`symptoms_count` INTEGER NOT NULL DEFAULT 1, " +
                                "PRIMARY KEY(`incognito_id`, `symptom_id`), " +
                                "FOREIGN KEY(`symptom_id`) REFERENCES `tbl_symptom`(`id`) ON UPDATE NO ACTION ON DELETE NO ACTION )"
                );
                database.execSQL(
                        "CREATE INDEX IF NOT EXISTS " +
                                "`index_tbl_last_user_symptom_symptom_id` ON `tbl_last_user_symptom` (`symptom_id`)"
                );
                database.execSQL(
                        "INSERT INTO `tbl_last_user_symptom` (`incognito_id`, `symptom_id`, `timestamp`, `latitude`, `longitude`, `symptoms_count`) " +
                                "WITH last_coords AS ( " +
                                "SELECT 'null', " +
                                "       symptom_id, " +
                                "       latitude as last_latitude, " +
                                "       longitude as last_longitude " +
                                "FROM tbl_user_symptom us1 " +
                                "WHERE us1.timestamp = (SELECT MAX(timestamp) " +
                                "                       FROM tbl_user_symptom us2 " +
                                "                       WHERE us2.symptom_id = us1.symptom_id " +
                                "                       AND latitude IS NOT NULL " +
                                "                       AND longitude IS NOT NULL) " +
                                ") " +
                                "SELECT 'null', " +
                                "       us.symptom_id, " +
                                "       strftime('%Y-%m-%d %H:%M:%S.000" + currentTimezone + "', datetime(MAX(us.timestamp) / 1000, 'unixepoch')), " +
                                "       lc.last_latitude, " +
                                "       lc.last_longitude, " +
                                "       COUNT(us.id) " +
                                "FROM tbl_user_symptom us " +
                                "LEFT JOIN last_coords lc ON lc.symptom_id = us.symptom_id " +
                                "GROUP BY us.symptom_id"
                );
            }

            //добавить в таблицу tbl_user_symptom столбец incognito_id, изменить тип столбца Timestamp, удалить user_id
            {
                //создать новую таблицу
                database.execSQL(
                        "CREATE TABLE IF NOT EXISTS `tbl_user_symptom_new` (" +
                                "`incognito_id` TEXT NOT NULL, " +
                                "`symptom_id` INTEGER NOT NULL, " +
                                "`timestamp` TEXT NOT NULL, " +
                                "`latitude` REAL, " +
                                "`longitude` REAL, " +
                                "`id` INTEGER PRIMARY KEY AUTOINCREMENT, " +
                                "FOREIGN KEY(`symptom_id`) REFERENCES `tbl_symptom`(`id`) ON UPDATE NO ACTION ON DELETE NO ACTION )"
                );
                //перенести данные из старой таблицы в новую
                database.execSQL(
                        "INSERT INTO `tbl_user_symptom_new` (`id`, `incognito_id`, `symptom_id`, `timestamp`, `latitude`, `longitude`) " +
                                "SELECT `id`, 'null', `symptom_id`, strftime('%Y-%m-%d %H:%M:%S.000" + currentTimezone + "', datetime(`timestamp` / 1000, 'unixepoch')), `latitude`, `longitude` " +
                                "FROM tbl_user_symptom " +
                                "WHERE server_id IS NULL"
                );
                //удалить старую таблицу
                database.execSQL("DROP TABLE IF EXISTS `tbl_user_symptom`");
                //переименовать новую таблицу
                database.execSQL(
                        "ALTER TABLE `tbl_user_symptom_new` " +
                                "RENAME TO `tbl_user_symptom`"
                );
                //Добавить индексы
                database.execSQL(
                        "CREATE INDEX IF NOT EXISTS " +
                                "`index_tbl_user_symptom_symptom_id` ON `tbl_user_symptom` (`symptom_id`)"
                );
            }

            //коммит
            database.execSQL("COMMIT");
            //включить внешние ключи
            database.execSQL("PRAGMA foreign_keys = ON");
        }
    };

    private static final Migration MIGRATION_3_4 = new Migration(3, 4) {
        @Override
        public void migrate (@NonNull SupportSQLiteDatabase database) {
            //добавить симптомы
            database.execSQL(
                    "INSERT INTO `tbl_symptom` (`id`, `name`) " +
                            "VALUES (50, 'Почки'), " +
                            "(51, 'Лицевой нерв')"
            );
        }
    };

    static Migration[] getMigrations () {
        Log.d(TAG, "getMigrations");
        return new Migration[]{
                MIGRATION_1_2,
                MIGRATION_2_3,
                MIGRATION_3_4
        };
    }
}
