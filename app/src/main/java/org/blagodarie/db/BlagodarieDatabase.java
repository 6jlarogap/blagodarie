package org.blagodarie.db;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.sqlite.db.SupportSQLiteDatabase;

import io.reactivex.Completable;
import io.reactivex.schedulers.Schedulers;


@Database (
        entities = {
                Symptom.class,
                UserSymptom.class
        },
        version = 2)
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
                addCallback(new RoomDatabase.Callback() {
                    @Override
                    public void onCreate (@NonNull final SupportSQLiteDatabase db) {
                        Completable.
                                fromAction(() -> BlagodarieDatabase.getInstance(applicationContext).symptomDao().insert(Symptom.getSymptoms())).
                                subscribeOn(Schedulers.io()).
                                subscribe();

                    }
                }).
                addMigrations(MigrationKeeper.getMigrations()).
                build();
    }

    public abstract SymptomDao symptomDao ();

    public abstract UserSymptomDao userSymptomDao ();
}