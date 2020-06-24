package blagodarie.health.database;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Update;

import java.util.UUID;

@Dao
public interface LastUserMessageDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    void insert(final LastUserMessage lastUserMessage);

    @Update(onConflict = OnConflictStrategy.IGNORE)
    void update(final LastUserMessage lastUserMessage);

    @Query ("SELECT * " +
            "FROM tbl_last_user_message " +
            "WHERE incognito_id = :incognitoId " +
            "AND message_id = :messageId")
    LastUserMessage get (final UUID incognitoId, final Identifier messageId);

}
