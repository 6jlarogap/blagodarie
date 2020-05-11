package org.blagodatie.database;

import androidx.room.testing.MigrationTestHelper;
import androidx.sqlite.db.SupportSQLiteDatabase;
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.IOException;

@RunWith (AndroidJUnit4.class)
public class MigrationTest {
    private static final String TEST_DB = "migration-test";

    MigrationTestHelper helper;

    public MigrationTest () {
        helper = new MigrationTestHelper(InstrumentationRegistry.getInstrumentation(),
                BlagodarieDatabase.class.getName(),
                new FrameworkSQLiteOpenHelperFactory());
    }

    @Test
    public void migrate1To2() throws IOException {
        SupportSQLiteDatabase db = helper.createDatabase(TEST_DB, 1);

        db.close();

        db = helper.runMigrationsAndValidate(TEST_DB, 2, true, MigrationKeeper.getMigrations()[0]);
    }

    @Test
    public void migrate2To3() throws IOException {
        SupportSQLiteDatabase db = helper.createDatabase(TEST_DB, 2);

        db.close();

        db = helper.runMigrationsAndValidate(TEST_DB, 3, true, MigrationKeeper.getMigrations()[1]);
    }

    @Test
    public void migrate3To4() throws IOException {
        SupportSQLiteDatabase db = helper.createDatabase(TEST_DB, 3);

        db.close();

        db = helper.runMigrationsAndValidate(TEST_DB, 4, true, MigrationKeeper.getMigrations()[2]);
    }

    @Test
    public void migrate4To5() throws IOException {
        SupportSQLiteDatabase db = helper.createDatabase(TEST_DB, 4);

        db.close();

        db = helper.runMigrationsAndValidate(TEST_DB, 5, true, MigrationKeeper.getMigrations()[3]);
    }
}
