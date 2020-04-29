package org.blagodarie;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;

import org.blagodatie.database.BlagodarieDatabase;
import org.blagodatie.database.UserSymptom;
import org.blagodatie.database.UserSymptomDao;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

import static org.blagodatie.database.BlagodarieDatabase.*;

public final class Repository {

    @NonNull
    private final UserSymptomDao mUserSymptomDao;

    public Repository (@NonNull final Context context) {
        final BlagodarieDatabase blagodarieDatabase = getDatabase(context);
        this.mUserSymptomDao = blagodarieDatabase.userSymptomDao();
    }

    public LiveData<Boolean> isHaveNotSyncedUserSymptoms (@NonNull final UUID incognitoId, final long symptomId) {
        return mUserSymptomDao.isHaveNotSynced(incognitoId, symptomId);
    }

    public List<UserSymptom> getNotSyncedUserSymptoms (@NonNull final UUID incognitoId) {
        return mUserSymptomDao.getNotSynced(incognitoId);
    }

    public void updateUserSymptoms (@NonNull final Collection<UserSymptom> userSymptoms) {
        mUserSymptomDao.update(userSymptoms);
    }

    public void updateIncognitoId (final long userId, @NonNull final UUID incognitoId) {
        mUserSymptomDao.updateIncognitoId(userId, incognitoId);
    }

    public UserSymptom getLastUserSymptomForSymptomId (@NonNull final UUID incognitoId, final long symptomId) {
        return mUserSymptomDao.getLastForSymptomId(incognitoId, symptomId);
    }

    public int getUserSymptomsCountBySymptomId (@NonNull final UUID incognitoId, final long symptomId) {
        return mUserSymptomDao.getCountBySymptomId(incognitoId, symptomId);
    }

    public void insertUserSymptom(@NonNull final UserSymptom userSymptom){
        mUserSymptomDao.insert(userSymptom);
    }
}
