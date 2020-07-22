package blagodarie.health.database;

import android.content.Context;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.room.TypeConverters;
import androidx.sqlite.db.SimpleSQLiteQuery;

@Database(
        entities = {
                MessageGroup.class,
                Message.class,
                UserMessage.class,
                LastUserMessage.class
        },
        version = 1)
@TypeConverters({Converters.class})
public abstract class HealthDatabase
        extends RoomDatabase {

    private static final String TAG = HealthDatabase.class.getSimpleName();

    /**
     * Запрос для отключения внешних ключей.
     */
    private static final SimpleSQLiteQuery QUERY_DEFER_FOREIGN_KEYS = new SimpleSQLiteQuery("PRAGMA defer_foreign_keys = true");

    /**
     * Название файла базы данных.
     */
    private static final String DATABASE_NAME = "health.db";

    private static volatile HealthDatabase INSTANCE;

    public static HealthDatabase getDatabase (@NonNull final Context context) {
        if (INSTANCE == null) {
            synchronized (HealthDatabase.class) {
                if (INSTANCE == null) {
                    INSTANCE = buildDatabase(context.getApplicationContext());
                }
            }
        }
        return INSTANCE;
    }

    private static HealthDatabase buildDatabase (@NonNull final Context applicationContext) {
        Log.d(TAG, "buildDatabase");
        return Room.
                databaseBuilder(applicationContext, HealthDatabase.class, DATABASE_NAME).
                addMigrations(MigrationKeeper.getMigrations()).
                build();
    }

    /**
     * Отключает внешние ключи до конца транзакции.
     */
    public void deferForeignKeys () {
        query(QUERY_DEFER_FOREIGN_KEYS);
    }

    public abstract MessageGroupDao messageGroupDao ();

    public abstract MessageDao messageDao ();

    public abstract UserMessageDao userMessageDao ();

    public abstract LastUserMessageDao lastUserMessageDao ();
}