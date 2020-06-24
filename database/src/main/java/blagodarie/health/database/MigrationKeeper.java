package blagodarie.health.database;

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

    static Migration[] getMigrations () {
        Log.d(TAG, "getMigrations");
        return new Migration[]{
        };
    }
}
