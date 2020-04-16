package org.blagodarie.db;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;

import java.util.Collection;
import java.util.List;

@Dao
public abstract class UserSymptomDao {

    @Insert
    public abstract void insert (final UserSymptom userSymptom);

    @Update
    public abstract void update (final Collection<UserSymptom> userSymptom);

    @Query ("SELECT us.* " +
            "FROM tbl_user_symptom us " +
            "WHERE symptom_id = :symptomId " +
            "AND timestamp = (SELECT MAX(timestamp) " +
            "                 FROM tbl_user_symptom us2" +
            "                 WHERE us2.symptom_id = :symptomId)")
    public abstract UserSymptom getLastForSymptomId (final Long symptomId);

    @Query ("SELECT us.* " +
            "FROM tbl_user_symptom us " +
            "WHERE user_id = :userId " +
            "AND server_id IS NULL")
    public abstract List<UserSymptom> getNotSynced (final Long userId);

}
