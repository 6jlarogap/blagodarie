package org.blagodatie.database;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import java.util.Collection;

@Dao
public interface SymptomDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    void insert (final Collection<Symptom> symptoms);

    @Query ("DELETE FROM tbl_symptom")
    void deleteAll ();

}
