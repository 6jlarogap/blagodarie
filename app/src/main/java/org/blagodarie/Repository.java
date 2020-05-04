package org.blagodarie;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;

import org.blagodatie.database.BlagodarieDatabase;
import org.blagodatie.database.LastUserSymptom;
import org.blagodatie.database.LastUserSymptomDao;
import org.blagodatie.database.UserSymptom;
import org.blagodatie.database.UserSymptomDao;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

import static org.blagodatie.database.BlagodarieDatabase.getDatabase;

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

    public void setupIncognitoId (@NonNull final UUID incognitoId) {
        mBlagodarieDatabase.runInTransaction(() -> {
            mUserSymptomDao.setupIncognitoId(incognitoId);
            mLastUserSymptomDao.setupIncognitoId(incognitoId);
        });
    }

    public void insertUserSymptom (@NonNull final UserSymptom userSymptom) {
        mBlagodarieDatabase.runInTransaction(() -> {
            mUserSymptomDao.insert(userSymptom);
            LastUserSymptom lastUserSymptom = mLastUserSymptomDao.get(userSymptom.getIncognitoId(), userSymptom.getSymptomId());
            if (lastUserSymptom != null) {
                lastUserSymptom.setTimestamp(userSymptom.getTimestamp());
                if (userSymptom.getLatitude() != null &&
                        userSymptom.getLongitude() != null) {
                    lastUserSymptom.setLatitude(userSymptom.getLatitude());
                    lastUserSymptom.setLongitude(userSymptom.getLongitude());
                    lastUserSymptom.setSymptomsCount(lastUserSymptom.getSymptomsCount() + 1);
                }
                mLastUserSymptomDao.update(lastUserSymptom);
            } else {
                lastUserSymptom = new LastUserSymptom(
                        userSymptom.getIncognitoId(),
                        userSymptom.getSymptomId(),
                        userSymptom.getTimestamp(),
                        userSymptom.getLatitude(),
                        userSymptom.getLongitude()
                );
                mLastUserSymptomDao.insert(lastUserSymptom);
            }
        });
    }

    public LastUserSymptom getLastUserSymptom (@NonNull final UUID incognitoId, final long symptomId) {
        return mLastUserSymptomDao.get(incognitoId, symptomId);
    }

    public void deleteUserSymptoms (@NonNull final Collection<UserSymptom> userSymptoms) {
        mUserSymptomDao.delete(userSymptoms);
    }
}
