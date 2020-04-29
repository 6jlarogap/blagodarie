package org.blagodatie.database;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import java.util.Collection;
import java.util.List;

@Dao
abstract class SymptomDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    abstract void insert (final Collection<Symptom> symptoms);

    @Query ("SELECT * " +
            "FROM tbl_symptom")
    public abstract List<Symptom> getAll ();
}
