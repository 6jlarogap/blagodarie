package blagodarie.health.database;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Transaction;

import java.util.Collection;
import java.util.List;

@Dao
public interface MessageGroupDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    void insert (final Collection<MessageGroup> messageGroups);

    @Query ("DELETE FROM tbl_message_group")
    void deleteAll ();

    @Transaction
    @Query ("SELECT * " +
            "FROM tbl_message_group sg " +
            "WHERE EXISTS (SELECT * " +
            "              FROM tbl_message s " +
            "              WHERE s.group_id = sg.id) " +
            "ORDER BY id")
    LiveData<List<MessageGroupWithMessages>> getMessageCatalog ();

}
