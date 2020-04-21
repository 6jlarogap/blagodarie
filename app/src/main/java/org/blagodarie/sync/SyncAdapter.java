package org.blagodarie.sync;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.AbstractThreadedSyncAdapter;
import android.content.ContentProviderClient;
import android.content.Context;
import android.content.SyncResult;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;

import org.blagodarie.R;
import org.blagodarie.db.BlagodarieDatabase;
import org.blagodarie.db.UserSymptom;
import org.blagodarie.server.ServerConnector;
import org.blagodarie.ui.symptoms.AddUserSymptomsExecutor;

import java.util.List;

import io.reactivex.Completable;
import io.reactivex.schedulers.Schedulers;

public final class SyncAdapter
        extends AbstractThreadedSyncAdapter {

    private static final String TAG = SyncAdapter.class.getSimpleName();

    @NonNull
    private final BlagodarieDatabase mBlagodarieDatabase;

    @NonNull
    private final ServerConnector mServerConnector;

    @NonNull
    private final AccountManager mAccountManager;

    @NonNull
    private final String mTokenType;

    SyncAdapter (Context context, boolean autoInitialize) {
        super(context, autoInitialize);
        mBlagodarieDatabase = BlagodarieDatabase.getInstance(context);
        mServerConnector = new ServerConnector(context);
        mAccountManager = AccountManager.get(context);
        mTokenType = context.getString(R.string.token_type);
    }

    @Override
    public void onPerformSync (
            Account account,
            Bundle extras,
            String authority,
            ContentProviderClient provider,
            SyncResult syncResult
    ) {
        Log.d(TAG, "onPerformSync");
        getAuthTokenAndSyncAll(account);
    }

    private void getAuthTokenAndSyncAll (
            @NonNull final Account account
    ) {
        Log.d(TAG, "getAuthTokenAndSyncAll account=" + account);
        mAccountManager.getAuthToken(
                account,
                mTokenType,
                null,
                false,
                future -> {
                    try {
                        String authToken = future.getResult().getString((AccountManager.KEY_AUTHTOKEN));
                        if (authToken == null) {
                            authToken = "";
                        }
                        syncUserSymptoms(account, authToken);
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                },
                null);
    }

    private void syncUserSymptoms (
            @NonNull final Account account,
            @NonNull final String authToken
    ) {
        Log.d(TAG, "syncUserSymptoms account=" + account + "; authToken=" + authToken);
        final Long userId = Long.valueOf(account.name);
        Completable.
                fromAction(() -> {
                    final List<UserSymptom> notSyncedUserSymtpoms = mBlagodarieDatabase.userSymptomDao().getNotSynced(userId);
                    final AddUserSymptomsExecutor addUserSymptomsExecutor = new AddUserSymptomsExecutor(Long.valueOf(account.name), notSyncedUserSymtpoms);
                    mServerConnector.execute(addUserSymptomsExecutor);
                    mBlagodarieDatabase.userSymptomDao().update(notSyncedUserSymtpoms);
                }).
                subscribeOn(Schedulers.io()).
                subscribe(
                        () -> Log.d(TAG, "syncUserSymptoms complete"),
                        throwable -> Log.e(TAG, "syncUserSymptoms error=" + throwable)
                );
    }
}