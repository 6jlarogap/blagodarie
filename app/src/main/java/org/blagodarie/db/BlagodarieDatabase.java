package org.blagodarie.db;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;


@Database (
        entities = {
                UserSymptom.class
        },
        version = 1)
public abstract class BlagodarieDatabase
        extends RoomDatabase {

    private static final String DATABASE_NAME = "blagodarie.db";

    private static volatile BlagodarieDatabase INSTANCE;

    public static BlagodarieDatabase getInstance (@NonNull final Context context) {
        synchronized (BlagodarieDatabase.class) {
            if (INSTANCE == null) {
                INSTANCE = buildDatabase(context.getApplicationContext());
            }
        }
        return INSTANCE;
    }

    private static BlagodarieDatabase buildDatabase (final Context applicationContext) {
        return Room.
                databaseBuilder(applicationContext, BlagodarieDatabase.class, DATABASE_NAME).
                build();
    }

    public abstract UserSymptomDao userSymptomDao ();
}