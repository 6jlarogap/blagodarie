package blagodarie.health.sync;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.AbstractThreadedSyncAdapter;
import android.content.ContentProviderClient;
import android.content.Context;
import android.content.Intent;
import android.content.SyncResult;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import blagodarie.health.Repository;
import blagodarie.health.UnauthorizedException;
import blagodarie.health.authentication.AccountGeneral;
import blagodarie.health.server.ServerConnector;
import org.json.JSONException;

import java.io.IOException;
import java.util.UUID;

public final class SyncAdapter
        extends AbstractThreadedSyncAdapter {

    private static final String TAG = SyncAdapter.class.getSimpleName();

    private static final String GENERAL_PREFERENCE = "blagodarie.health.sync.preference.general";

    SyncAdapter (Context context, boolean autoInitialize) {
        super(context, autoInitialize);
    }

    @Override
    public void onPerformSync (
            final Account account,
            final Bundle extras,
            final String authority,
            final ContentProviderClient provider,
            final SyncResult syncResult
    ) {
        Log.d(TAG, "onPerformSync");
        final String authToken = extras.getString(AccountManager.KEY_AUTHTOKEN);
        final UUID incognitoId = UUID.fromString(AccountManager.get(getContext()).getUserData(account, AccountGeneral.USER_DATA_INCOGNITO_PRIVATE_KEY));
        try {
            syncAll(incognitoId, authToken);
            sendBroadcastException(null);
        } catch (JSONException | IOException e) {
            Log.e(TAG, "onPerformSync error=" + e);
            e.printStackTrace();
            sendBroadcastException(e);
        } catch (UnauthorizedException e) {
            Log.e(TAG, "onPerformSync error=" + e);
            e.printStackTrace();
            //очистить токен
            AccountManager.get(getContext()).invalidateAuthToken(account.type, authToken);
            sendBroadcastException(e);
        }
    }

    private void syncAll (
            @NonNull final UUID incognitoId,
            @Nullable final String authToken
    ) throws JSONException, IOException, UnauthorizedException {
        Log.d(TAG, "syncAll");
        final Repository repository = Repository.getInstance(getContext());
        final ServerConnector serverConnector = new ServerConnector(getContext());

        //синхронизировать справочник симптомов
        SymptomSyncer.
                getInstance().
                sync(
                        serverConnector,
                        repository,
                        getContext().getSharedPreferences(GENERAL_PREFERENCE, Context.MODE_PRIVATE)
                );

        //синхронизировать симптомы пользователя
        UserSymptomSyncer.
                getInstance().
                sync(
                        incognitoId,
                        authToken,
                        serverConnector,
                        repository
                );

    }

    private void sendBroadcastException (@Nullable final Throwable throwable) {
        Log.d(TAG, "sendBroadcastException");
        final Intent intent = new Intent(SyncService.ACTION_SYNC_EXCEPTION);
        if (throwable != null) {
            intent.putExtra(SyncService.EXTRA_EXCEPTION, throwable);
        }
        getContext().sendBroadcast(intent);
    }

}