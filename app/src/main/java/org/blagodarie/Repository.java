package org.blagodarie;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;

import org.blagodatie.database.BlagodarieDatabase;
import org.blagodatie.database.LastUserSymptomDao;
import org.blagodatie.database.UserSymptom;
import org.blagodatie.database.UserSymptomDao;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

import static org.blagodatie.database.BlagodarieDatabase.*;

public final class Repository {

    @NonNull
    private final BlagodarieDatabase mBlagodarieDatabase;

    @NonNull
    private final UserSymptomDao mUserSymptomDao;

    @NonNull
    private final LastUserSymptomDao mLastUserSymptomDao;

    public Repository (@NonNull final Context context) {
        mBlagodarieDatabase = getDatabase(context);
        mUserSymptomDao = mBlagodarieDatabase.userSymptomDao();
        mLastUserSymptomDao = mBlagodarieDatabase.lastUserSymptomDao();
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

    public void setupIncognitoId (@NonNull final UUID incognitoId) {
        mBlagodarieDatabase.runInTransaction(()->{
            mUserSymptomDao.setupIncognitoId(incognitoId);
            mLastUserSymptomDao.setupIncognitoId(incognitoId);
        });
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
