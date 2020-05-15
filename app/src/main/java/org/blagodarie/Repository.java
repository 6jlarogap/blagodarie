package org.blagodarie;

import android.content.Context;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;

import org.blagodatie.database.BlagodarieDatabase;
import org.blagodatie.database.Identifier;
import org.blagodatie.database.LastUserSymptom;
import org.blagodatie.database.LastUserSymptomDao;
import org.blagodatie.database.Symptom;
import org.blagodatie.database.SymptomDao;
import org.blagodatie.database.SymptomGroup;
import org.blagodatie.database.SymptomGroupDao;
import org.blagodatie.database.SymptomGroupWithSymptoms;
import org.blagodatie.database.UserSymptom;
import org.blagodatie.database.UserSymptomDao;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

public final class Repository {

    private static final String TAG = Repository.class.getSimpleName();

    private static volatile Repository INSTANCE;

    @NonNull
    private final BlagodarieDatabase mBlagodarieDatabase;

    @NonNull
    private final SymptomGroupDao mSymptomGroupDao;

    @NonNull
    private final SymptomDao mSymptomDao;

    @NonNull
    private final UserSymptomDao mUserSymptomDao;

    @NonNull
    private final LastUserSymptomDao mLastUserSymptomDao;

    private LiveData<List<SymptomGroupWithSymptoms>> mSymptomGroupsWithSymptoms;

    private Repository (@NonNull final Context context) {
        mBlagodarieDatabase = BlagodarieDatabase.getDatabase(context);
        mSymptomGroupDao = mBlagodarieDatabase.symptomGroupDao();
        mSymptomDao = mBlagodarieDatabase.symptomDao();
        mUserSymptomDao = mBlagodarieDatabase.userSymptomDao();
        mLastUserSymptomDao = mBlagodarieDatabase.lastUserSymptomDao();
    }

    public static Repository getInstance (@NonNull final Context context) {
        if (INSTANCE == null) {
            synchronized (Repository.class) {
                if (INSTANCE == null) {
                    INSTANCE = new Repository(context);
                }
            }
        }
        return INSTANCE;
    }

    public final LiveData<Boolean> isHaveNotSyncedUserSymptoms (
            @NonNull final UUID incognitoId,
            @NonNull final Identifier symptomId
    ) {
        Log.d(TAG, "isHaveNotSyncedUserSymptoms");
        return mUserSymptomDao.isHaveNotSynced(incognitoId, symptomId);
    }


    public final LiveData<UserSymptom> getLatestUserSymptom (
            @NonNull final UUID incognitoId,
            @NonNull final Identifier symptomId
    ) {
        Log.d(TAG, "getLatestUserSymptom");
        return mUserSymptomDao.getLatestUserSymptom(incognitoId, symptomId);
    }

    public final List<UserSymptom> getNotSyncedUserSymptoms (@NonNull final UUID incognitoId) {
        Log.d(TAG, "getNotSyncedUserSymptoms");
        return mUserSymptomDao.getNotSynced(incognitoId);
    }

    public final void updateLastUserSymptom (@NonNull final UserSymptom userSymptom) {
        Log.d(TAG, "updateLastUserSymptom");
        //выполнить в транзакции
        mBlagodarieDatabase.runInTransaction(() -> {
            //получить lastUserSymptom, соответствующий userSymptom
            LastUserSymptom lastUserSymptom = mLastUserSymptomDao.get(userSymptom.getIncognitoId(), userSymptom.getSymptomId());
            //если существует
            if (lastUserSymptom != null) {
                //обновить данные
                lastUserSymptom.setTimestamp(userSymptom.getTimestamp());
                lastUserSymptom.setSymptomsCount(lastUserSymptom.getSymptomsCount() + 1);
                if (userSymptom.getLatitude() != null &&
                        userSymptom.getLongitude() != null) {
                    lastUserSymptom.setLatitude(userSymptom.getLatitude());
                    lastUserSymptom.setLongitude(userSymptom.getLongitude());
                }
                mLastUserSymptomDao.update(lastUserSymptom);
            } else {
                //иначе создать новый lastUserSymptom
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

    public final void deleteUserSymptom (@NonNull final UserSymptom userSymptom) {
        Log.d(TAG, "deleteUserSymptom");
        mUserSymptomDao.delete(userSymptom);
    }

    public final void insertUserSymptomAndSetId (@NonNull final UserSymptom userSymptom) {
        Log.d(TAG, "insertUserSymptomAndSetId");
        mUserSymptomDao.insertAndSetId(userSymptom);
    }

    public final LastUserSymptom getLastUserSymptom (
            @NonNull final UUID incognitoId,
            @NonNull final Identifier symptomId
    ) {
        Log.d(TAG, "getLastUserSymptom");
        return mLastUserSymptomDao.get(incognitoId, symptomId);
    }

    public final void deleteUserSymptoms (@NonNull final Collection<UserSymptom> userSymptoms) {
        Log.d(TAG, "deleteUserSymptoms");
        mUserSymptomDao.delete(userSymptoms);
    }

    public final void updateSymptoms (
            @NonNull final Collection<SymptomGroup> newSymptomGroups,
            @NonNull final Collection<Symptom> newSymptoms
    ) {
        Log.d(TAG, "updateSymptoms");
        mBlagodarieDatabase.runInTransaction(() -> {
            mBlagodarieDatabase.deferForeignKeys();
            //удалить все симптомы
            mSymptomDao.deleteAll();
            //удалить все группы симптомов
            mSymptomGroupDao.deleteAll();
            //вставить новые группы
            mSymptomGroupDao.insert(newSymptomGroups);
            //вставить новые симптомы
            mSymptomDao.insert(newSymptoms);
        });
    }

    public final LiveData<List<SymptomGroupWithSymptoms>> getSymptomGroupsWithSymptoms () {
        Log.d(TAG, "getSymptomGroupsWithSymptoms");
        if (mSymptomGroupsWithSymptoms == null) {
            mSymptomGroupsWithSymptoms = mSymptomGroupDao.getSymptomCatalog();
        }
        return mSymptomGroupsWithSymptoms;
    }

}
