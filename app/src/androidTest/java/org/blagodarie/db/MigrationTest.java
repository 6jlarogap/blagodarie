package org.blagodarie.db;

import androidx.room.testing.MigrationTestHelper;
import androidx.sqlite.db.SupportSQLiteDatabase;
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory;
import androidx.test.platform.app.InstrumentationRegistry;

import org.junit.Test;

import java.io.IOException;

public class MigrationTest {
    private static final String TEST_DB = "migration-test";

    MigrationTestHelper helper;

    public MigrationTest() {
        helper = new MigrationTestHelper(InstrumentationRegistry.getInstrumentation(),
                BlagodarieDatabase.class.getName(),
                new FrameworkSQLiteOpenHelperFactory());
    }

    @Test
    public void migrate1To2() throws IOException {
        SupportSQLiteDatabase db = helper.createDatabase(TEST_DB, 1);

        // Prepare for the next version.
        db.close();

        db = helper.runMigrationsAndValidate(TEST_DB, 2, true, MigrationKeeper.getMigrations());

        // MigrationTestHelper automatically verifies the schema changes,
        // but you need to validate that the data was migrated properly.
    }
}