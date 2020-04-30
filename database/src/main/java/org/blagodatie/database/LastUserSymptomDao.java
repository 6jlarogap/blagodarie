package org.blagodatie.database;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Update;

import java.util.UUID;

@Dao
public abstract class LastUserSymptomDao {

    @Insert (onConflict = OnConflictStrategy.IGNORE)
    public abstract void insert(final LastUserSymptom lastUserSymptom);

    @Update(onConflict = OnConflictStrategy.IGNORE)
    public abstract void update(final LastUserSymptom lastUserSymptom);

    @Query ("SELECT * " +
            "FROM tbl_last_user_symptom " +
            "WHERE incognito_id = :incognitoId " +
            "AND symptom_id = :symptomId")
    public abstract LastUserSymptom get (final UUID incognitoId, final long symptomId);

    @Query ("UPDATE tbl_last_user_symptom " +
            "SET incognito_id = :incognitoId " +
            "WHERE incognito_id = 'null'")
    public abstract void setupIncognitoId (final UUID incognitoId);

}
