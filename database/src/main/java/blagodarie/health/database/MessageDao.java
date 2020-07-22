package blagodarie.health.database;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import java.util.Collection;

@Dao
public interface MessageDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    void insert (final Collection<Message> messages);

    @Query ("DELETE FROM tbl_message")
    void deleteAll ();

}
