package org.blagodatie.database;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

@Dao
public abstract class UserSymptomDao {

    @Insert
    public abstract long insert (final UserSymptom userSymptom);

    @Update
    public abstract void update (final Collection<UserSymptom> userSymptom);

    @Query ("SELECT * " +
            "FROM tbl_user_symptom " +
            "WHERE symptom_id = :symptomId " +
            "AND incognito_id = :incognitoId " +
            "AND timestamp = (SELECT MAX(timestamp) " +
            "                 FROM tbl_user_symptom us2" +
            "                 WHERE us2.symptom_id = :symptomId" +
            "                 AND us2.incognito_id = :incognitoId)")
    public abstract UserSymptom getLastForSymptomId (final UUID incognitoId, final long symptomId);

    @Query ("SELECT us.* " +
            "FROM tbl_user_symptom us " +
            "WHERE incognito_id = :incognitoId " +
            "AND server_id IS NULL")
    public abstract List<UserSymptom> getNotSynced (final UUID incognitoId);

    @Query ("SELECT COUNT(*) " +
            "FROM tbl_user_symptom " +
            "WHERE symptom_id = :symptomId " +
            "AND incognito_id = :incognitoId ")
    public abstract int getCountBySymptomId (final UUID incognitoId, final long symptomId);

    @Query ("SELECT COUNT(*) " +
            "FROM tbl_user_symptom " +
            "WHERE symptom_id = :symptomId " +
            "AND incognito_id = :incognitoId " +
            "AND server_id IS NULL")
    public abstract LiveData<Boolean> isHaveNotSynced (final UUID incognitoId, final long symptomId);

    @Query ("UPDATE tbl_user_symptom " +
            "SET user_id = null, " +
            "incognito_id = :incognitoId " +
            "WHERE user_id = :userId " +
            "AND incognito_id = 'null'")
    public abstract void updateIncognitoId (final long userId, final UUID incognitoId);
}
