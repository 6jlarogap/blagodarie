package blagodarie.health.database;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Delete;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

@Dao
public interface UserSymptomDao {

    @Insert
    long insert (final UserSymptom userSymptom);

    default void insertAndSetId (@NonNull final UserSymptom userSymptom) {
        userSymptom.setId(Identifier.newInstance(insert(userSymptom)));
    }

    @Update
    void update (final Collection<UserSymptom> userSymptom);

    @Delete
    void delete (final UserSymptom userSymptom);

    @Delete
    void delete (final Collection<UserSymptom> userSymptoms);

    @Query ("SELECT us.* " +
            "FROM tbl_user_symptom us " +
            "WHERE incognito_id = :incognitoId")
    List<UserSymptom> getNotSynced (final UUID incognitoId);

    @Query ("SELECT COUNT(*) " +
            "FROM tbl_user_symptom " +
            "WHERE symptom_id = :symptomId " +
            "AND incognito_id = :incognitoId")
    LiveData<Boolean> isHaveNotSynced (final UUID incognitoId, final Identifier symptomId);

    @Query ("SELECT * " +
            "FROM tbl_user_symptom " +
            "WHERE symptom_id = :symptomId " +
            "AND incognito_id = :incognitoId " +
            "AND STRFTIME('%s', SUBSTR(timestamp, 0, 24)) = " +
            "                (SELECT MAX(STRFTIME('%s', SUBSTR(timestamp, 0, 24))) " +
            "                 FROM tbl_user_symptom " +
            "                 WHERE symptom_id = :symptomId " +
            "                 AND incognito_id = :incognitoId)")
    LiveData<UserSymptom> getLatestUserSymptom (final UUID incognitoId, final Identifier symptomId);

}
