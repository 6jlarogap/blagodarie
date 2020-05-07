package org.blagodatie.database;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Transaction;

import java.util.Collection;
import java.util.List;

@Dao
public interface SymptomGroupDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    void insert (final Collection<SymptomGroup> symptomGroups);

    @Query ("DELETE FROM tbl_symptom_group")
    void deleteAll ();

    @Transaction
    @Query ("SELECT * " +
            "FROM tbl_symptom_group")
    LiveData<List<SymptomGroupWithSymptoms>> getAll ();
}
