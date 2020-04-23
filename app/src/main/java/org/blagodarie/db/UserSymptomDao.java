package org.blagodarie.db;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;

import java.util.Collection;
import java.util.List;

@Dao
public abstract class UserSymptomDao {

    @Insert
    public abstract long insert (final UserSymptom userSymptom);

    @Update
    public abstract void update (final Collection<UserSymptom> userSymptom);

    @Query ("SELECT * " +
            "FROM tbl_user_symptom " +
            "WHERE symptom_id = :symptomId " +
            "AND user_id = :userId " +
            "AND timestamp = (SELECT MAX(timestamp) " +
            "                 FROM tbl_user_symptom us2" +
            "                 WHERE us2.symptom_id = :symptomId" +
            "                 AND us2.user_id = :userId)")
    public abstract UserSymptom getLastForSymptomId (final long userId, final long symptomId);

    @Query ("SELECT us.* " +
            "FROM tbl_user_symptom us " +
            "WHERE user_id = :userId " +
            "AND server_id IS NULL")
    public abstract List<UserSymptom> getNotSynced (final long userId);

    @Query ("SELECT COUNT(*) " +
            "FROM tbl_user_symptom " +
            "WHERE symptom_id = :symptomId " +
            "AND user_id = :userId ")
    public abstract int getCountBySymptomId (final long userId, final long symptomId);

    @Query ("SELECT COUNT(*) " +
            "FROM tbl_user_symptom " +
            "WHERE symptom_id = :symptomId " +
            "AND user_id = :userId " +
            "AND server_id IS NULL")
    public abstract LiveData<Boolean> isHaveNotSynced (final long userId, final long symptomId);

}
