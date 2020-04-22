package org.blagodarie.db;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;

import java.util.Collection;

@Dao
abstract class SymptomDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    public abstract void insert (final Collection<Symptom> symptoms);

}
