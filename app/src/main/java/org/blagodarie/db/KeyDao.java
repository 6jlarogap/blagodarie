package org.blagodarie.db;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Transaction;

import java.util.UUID;

@Dao
public abstract class KeyDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    abstract long insert (final Key key);

    @Query("SELECT * " +
            "FROM tbl_key " +
            "WHERE owner_id = :ownerId " +
            "AND type_id = :typeId")
    abstract Key getKey(final long ownerId, final long typeId);

    @Transaction
    public Key getOrCreateIncognitoKey(final long ownerId){
        Key key = getKey(ownerId, KeyType.Type.BLAGODARIE_KEY.getKeyType().getId());
        if (key == null){
            key = new Key(UUID.randomUUID().toString(), KeyType.Type.BLAGODARIE_KEY.getKeyType().getId());
            key.setOwnerId(ownerId);
            key.setId(insert(key));
        }
        return key;
    }
}
