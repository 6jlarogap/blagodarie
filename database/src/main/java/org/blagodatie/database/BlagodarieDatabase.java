package org.blagodatie.database;

import android.content.Context;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.room.TypeConverters;
import androidx.sqlite.db.SupportSQLiteDatabase;

import java.util.concurrent.Executors;


@Database (
        entities = {
                Symptom.class,
                UserSymptom.class,
                LastUserSymptom.class
        },
        version = 3)
@TypeConverters ({Converters.class})
public abstract class BlagodarieDatabase
        extends RoomDatabase {

    private static final String TAG = BlagodarieDatabase.class.getSimpleName();

    private static final String DATABASE_NAME = "blagodarie.db";

    private static volatile BlagodarieDatabase INSTANCE;

    public static BlagodarieDatabase getDatabase (@NonNull final Context context) {
        if (INSTANCE == null) {
            synchronized (BlagodarieDatabase.class) {
                if (INSTANCE == null) {
                    INSTANCE = buildDatabase(context.getApplicationContext());
                }
            }
        }
        return INSTANCE;
    }

    private static BlagodarieDatabase buildDatabase (@NonNull final Context applicationContext) {
        Log.d(TAG, "buildDatabase");
        return Room.
                databaseBuilder(applicationContext, BlagodarieDatabase.class, DATABASE_NAME).
                addCallback(new RoomDatabase.Callback() {
                    @Override
                    public void onCreate (@NonNull final SupportSQLiteDatabase db) {
                        super.onCreate(db);
                        prepopulateDatabase(applicationContext);
                    }
                }).
                addMigrations(MigrationKeeper.getMigrations()).
                build();
    }

    private static void prepopulateDatabase (@NonNull final Context context) {
        Log.d(TAG, "prepopulateDatabase");
        Executors.
                newSingleThreadExecutor().
                execute(() ->
                        getDatabase(context).symptomDao().insert(Symptom.getSymptoms())

                );
    }


    public abstract SymptomDao symptomDao ();

    public abstract UserSymptomDao userSymptomDao ();

    public abstract LastUserSymptomDao lastUserSymptomDao ();
}