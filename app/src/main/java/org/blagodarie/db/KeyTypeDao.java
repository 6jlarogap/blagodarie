package org.blagodarie.db;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;

import java.util.Collection;

@Dao
public abstract class KeyTypeDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    abstract void insert (final Collection<KeyType> keyTypes);

}
