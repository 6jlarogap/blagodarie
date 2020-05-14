package org.blagodatie.database;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Update;

import java.util.UUID;

@Dao
public interface LastUserSymptomDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    void insert(final LastUserSymptom lastUserSymptom);

    @Update(onConflict = OnConflictStrategy.IGNORE)
    void update(final LastUserSymptom lastUserSymptom);

    @Query ("SELECT * " +
            "FROM tbl_last_user_symptom " +
            "WHERE incognito_id = :incognitoId " +
            "AND symptom_id = :symptomId")
    LastUserSymptom get (final UUID incognitoId, final Identifier symptomId);

}
