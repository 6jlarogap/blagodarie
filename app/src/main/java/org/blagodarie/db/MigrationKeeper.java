package org.blagodarie.db;

import android.util.Log;

import androidx.room.migration.Migration;
import androidx.sqlite.db.SupportSQLiteDatabase;

final class MigrationKeeper {

    private static final String TAG = MigrationKeeper.class.getSimpleName();

    private MigrationKeeper () {
    }

    private static final Migration MIGRATION_1_2 = new Migration(1, 2) {
        @Override
        public void migrate (final SupportSQLiteDatabase database) {
            Log.d(TAG, "Migrate from 1 to 2");
            //выключить внешние ключи
            database.execSQL("PRAGMA foreign_keys=off");
            //начать транзакцию
            database.execSQL("BEGIN TRANSACTION");

            //создать таблицу tbl_symptom
            database.execSQL("CREATE TABLE IF NOT EXISTS `tbl_symptom` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL)");
            database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_symptom_name` ON `tbl_symptom` (`name`)");

            //заполнить таблицу tbl_symptom
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(25, 'Пробуждение')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(19, 'Хорошее настроение')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(15, 'Хорошее самочувствие')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(20, 'Плохое настроение')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(29, 'Плохое самочувствие')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(1, 'Нехватка питьевой воды')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(2, 'Нехватка еды')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(3, 'Нехватка лекарств')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(17, 'Повышенное давление')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(18, 'Пониженное давление')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(16, 'Сердечная боль')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(11, 'Головная боль')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(10, 'Сухость носа')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(26, 'Заложенность носа')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(27, 'Насморк')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(5, 'Температура')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(28, 'Озноб')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(24, 'Аллергия')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(6, 'Кашель')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(4, 'Слабость')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(7, 'Боль в груди при дыхании')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(8, 'Затруднённое дыхание')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(9, 'Одышка')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(12, 'Боль и ломота в мышцах и суставах')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(13, 'Рвота')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(14, 'Диарея')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(21, 'Зубная боль')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(22, 'Боль в ушах')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(23, 'Головокружение')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(30, 'Чувство тревоги')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(31, 'Похолодало')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(32, 'Потеплело')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(33, 'Дождь')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(34, 'Ветер')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(35, 'Жара')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(36, 'Астма')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(37, 'Хорошая погода')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(40, 'Влажно')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(41, 'Сухо')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(42, 'Свежо')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(44, 'Прием пищи')");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(45, 'Запор')");

            //добавить в таблицу tbl_user_symptom внешний ключ к таблице tbl_symptom
            {
                //создать новую таблицу tbl_user_symptom с внешним ключом к tbl_symptom
                database.execSQL("CREATE TABLE IF NOT EXISTS `tbl_user_symptom_new` (`id` INTEGER PRIMARY KEY AUTOINCREMENT, `server_id` INTEGER, `user_id` INTEGER NOT NULL, `symptom_id` INTEGER NOT NULL, `timestamp` INTEGER NOT NULL, `latitude` REAL, `longitude` REAL, FOREIGN KEY(`symptom_id`) REFERENCES `tbl_symptom`(`id`) ON UPDATE NO ACTION ON DELETE NO ACTION )");
                //перенести данные из старой таблицы в новую
                database.execSQL("INSERT INTO tbl_user_symptom_new SELECT * FROM tbl_user_symptom");
                //удалить старую таблицу
                database.execSQL("DROP TABLE IF EXISTS `tbl_user_symptom`");
                //переименовать новую таблицу
                database.execSQL("ALTER TABLE tbl_user_symptom_new RENAME TO tbl_user_symptom");
                //добавить индексы к новой таблице
                database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_user_symptom_server_id` ON `tbl_user_symptom` (`server_id`)");
            }

            //коммит
            database.execSQL("COMMIT");
            //включить внешние ключи
            database.execSQL("PRAGMA foreign_keys=on");
        }
    };

    private static final Migration MIGRATION_2_3 = new Migration(2, 3) {
        @Override
        public void migrate (final SupportSQLiteDatabase database) {
            Log.d(TAG, "Migrate from 2 to 3");
            //выключить внешние ключи
            database.execSQL("PRAGMA foreign_keys=off");
            //начать транзакцию
            database.execSQL("BEGIN TRANSACTION");

            //в таблице tbl_symptom изменить столбец id, он может быть пустым
            {
                //создать новую таблицу tbl_symptom
                database.execSQL("CREATE TABLE IF NOT EXISTS `tbl_symptom_new` (`name` TEXT NOT NULL, `id` INTEGER PRIMARY KEY AUTOINCREMENT)");
                //перенести данные из старой таблицы в новую
                database.execSQL("INSERT INTO tbl_symptom_new(`id`, `name`) SELECT id, name FROM tbl_symptom");
                //удалить старую таблицу
                database.execSQL("DROP TABLE IF EXISTS `tbl_symptom`");
                //переименовать новую таблицу
                database.execSQL("ALTER TABLE tbl_symptom_new RENAME TO tbl_symptom");
                //Добавить индексы
                database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_symptom_name` ON `tbl_symptom` (`name`)");
            }

            //создать таблицу tbl_key_type
            database.execSQL("CREATE TABLE IF NOT EXISTS `tbl_key_type` (`title` TEXT NOT NULL, `id` INTEGER PRIMARY KEY AUTOINCREMENT)");
            database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_key_type_title` ON `tbl_key_type` (`title`)");

            //заполнить таблицу tbl_key_type
            database.execSQL("INSERT INTO `tbl_key_type` (`id`, `title`) values(1, 'PhoneNumber')");
            database.execSQL("INSERT INTO `tbl_key_type` (`id`, `title`) values(2, 'Email')");
            database.execSQL("INSERT INTO `tbl_key_type` (`id`, `title`) values(3, 'GoogleAccountId')");
            database.execSQL("INSERT INTO `tbl_key_type` (`id`, `title`) values(4, 'BlagodarieKey')");

            //создать таблицу tbl_key
            database.execSQL("CREATE TABLE IF NOT EXISTS `tbl_key` (`owner_id` INTEGER, `value` TEXT NOT NULL, `type_id` INTEGER NOT NULL, `id` INTEGER PRIMARY KEY AUTOINCREMENT, FOREIGN KEY(`type_id`) REFERENCES `tbl_key_type`(`id`) ON UPDATE NO ACTION ON DELETE NO ACTION )");
            database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_key_value_type_id` ON `tbl_key` (`value`, `type_id`)");
            database.execSQL("CREATE INDEX IF NOT EXISTS `index_tbl_key_owner_id` ON `tbl_key` (`owner_id`)");
            database.execSQL("CREATE INDEX IF NOT EXISTS `index_tbl_key_type_id` ON `tbl_key` (`type_id`)");
            database.execSQL("CREATE INDEX IF NOT EXISTS `index_tbl_key_value` ON `tbl_key` (`value`)");

            //создать таблицу tbl_user_symptom_key_join
            database.execSQL("CREATE TABLE IF NOT EXISTS `tbl_user_symptom_key_join` (`user_symptom_id` INTEGER NOT NULL, `key_id` INTEGER NOT NULL, `server_id` INTEGER, `id` INTEGER PRIMARY KEY AUTOINCREMENT, FOREIGN KEY(`user_symptom_id`) REFERENCES `tbl_user_symptom`(`id`) ON UPDATE NO ACTION ON DELETE NO ACTION , FOREIGN KEY(`key_id`) REFERENCES `tbl_key`(`id`) ON UPDATE NO ACTION ON DELETE NO ACTION )");
            database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_user_symptom_key_join_user_symptom_id` ON `tbl_user_symptom_key_join` (`user_symptom_id`)");
            database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_user_symptom_key_join_key_id` ON `tbl_user_symptom_key_join` (`key_id`)");
            database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_user_symptom_key_join_server_id` ON `tbl_user_symptom_key_join` (`server_id`)");

            //создать индекс для таблицы tbl_user_symptom к столбцу symptom_id
            database.execSQL("CREATE INDEX IF NOT EXISTS `index_tbl_user_symptom_symptom_id` ON `tbl_user_symptom` (`symptom_id`)");

            //коммит
            database.execSQL("COMMIT");
            //включить внешние ключи
            database.execSQL("PRAGMA foreign_keys=on");
        }
    };

    static Migration[] getMigrations () {
        return new Migration[]{
                MIGRATION_1_2,
                MIGRATION_2_3
        };
    }
}
