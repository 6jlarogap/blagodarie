package blagodarie.health.database;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Delete;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

@Dao
public interface UserMessageDao {

    @Insert
    long insert (final UserMessage userMessage);

    default void insertAndSetId (@NonNull final UserMessage userMessage) {
        userMessage.setId(Identifier.newInstance(insert(userMessage)));
    }

    @Update
    void update (final Collection<UserMessage> userMessage);

    @Delete
    void delete (final UserMessage userMessage);

    @Delete
    void delete (final Collection<UserMessage> userMessages);

    @Query ("SELECT um.* " +
            "FROM tbl_user_message um " +
            "WHERE incognito_id = :incognitoId")
    List<UserMessage> getNotSynced (final UUID incognitoId);

    @Query ("SELECT COUNT(*) " +
            "FROM tbl_user_message " +
            "WHERE message_id = :messageId " +
            "AND incognito_id = :incognitoId")
    LiveData<Boolean> isHaveNotSynced (final UUID incognitoId, final Identifier messageId);

    @Query ("SELECT * " +
            "FROM tbl_user_message " +
            "WHERE message_id = :messageId " +
            "AND incognito_id = :incognitoId " +
            "AND STRFTIME('%s', SUBSTR(timestamp, 0, 24)) = " +
            "                (SELECT MAX(STRFTIME('%s', SUBSTR(timestamp, 0, 24))) " +
            "                 FROM tbl_user_message " +
            "                 WHERE message_id = :messageId " +
            "                 AND incognito_id = :incognitoId)")
    LiveData<UserMessage> getLatestUserMessage (final UUID incognitoId, final Identifier messageId);

}
