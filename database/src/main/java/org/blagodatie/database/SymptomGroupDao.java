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
            "FROM tbl_symptom_group sg " +
            "WHERE EXISTS (SELECT * " +
            "              FROM tbl_symptom s " +
            "              WHERE s.group_id = sg.id) " +
            "ORDER BY /*(SELECT SUM(lus.symptoms_count) " +
            "          FROM tbl_last_user_symptom lus " +
            "          LEFT JOIN tbl_symptom s ON s.id = lus.symptom_id " +
            "          WHERE s.group_id = sg.id) DESC,*/ " +
            "          name")
    LiveData<List<SymptomGroupWithSymptoms>> getAll ();
}
