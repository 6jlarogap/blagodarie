package org.blagodatie.database;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;

import java.util.Collection;

@Dao
interface SymptomGroupDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    void insert (final Collection<SymptomGroup> symptomGroups);

}
