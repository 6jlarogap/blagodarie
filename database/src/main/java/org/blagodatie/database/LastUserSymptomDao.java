package org.blagodatie.database;

import androidx.room.Dao;
import androidx.room.Query;

import java.util.UUID;

@Dao
public abstract class LastUserSymptomDao {

    @Query ("UPDATE tbl_last_user_symptom " +
            "SET incognito_id = :incognitoId " +
            "WHERE incognito_id = 'null'")
    public abstract void setupIncognitoId (final UUID incognitoId);

}
