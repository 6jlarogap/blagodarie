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

            //создать таблицу симптомов
            database.execSQL("CREATE TABLE IF NOT EXISTS `tbl_symptom` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL)");

            //создать уникальный индекс для имени симптома
            database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_symptom_name` ON `tbl_symptom` (`name`)");
            database.execSQL("INSERT INTO `tbl_symptom` (`id`, `name`) values(25, 'Пробуждение')");

            //заполнить таблицу симптомов
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

            //создать новую таблицу tbl_user_symptom с внешним ключом к tbl_symptom
            database.execSQL("CREATE TABLE IF NOT EXISTS `tbl_user_symptom_new` (`id` INTEGER PRIMARY KEY AUTOINCREMENT, `server_id` INTEGER, `user_id` INTEGER NOT NULL, `symptom_id` INTEGER NOT NULL, `timestamp` INTEGER NOT NULL, `latitude` REAL, `longitude` REAL, FOREIGN KEY(`symptom_id`) REFERENCES `tbl_symptom`(`id`) ON UPDATE NO ACTION ON DELETE NO ACTION )");


            //заполнить новую таблицу
            database.execSQL("INSERT INTO tbl_user_symptom_new SELECT * FROM tbl_user_symptom");

            //удалить старую таблицу
            database.execSQL("DROP TABLE IF EXISTS `tbl_user_symptom`");

            //переименовать новую таблицу
            database.execSQL("ALTER TABLE tbl_user_symptom_new RENAME TO tbl_user_symptom");

            //Добавить индексы
            database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_tbl_user_symptom_server_id` ON `tbl_user_symptom` (`server_id`)");

            //коммит
            database.execSQL("COMMIT");

            //включить внешние ключи
            database.execSQL("PRAGMA foreign_keys=on");
        }
    };

    static Migration[] getMigrations () {
        return new Migration[]{MIGRATION_1_2};
    }
}
