package org.blagodarie;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.ContentResolver;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.multidex.MultiDexApplication;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class BlagodarieApp
        extends MultiDexApplication {

    private static final String TAG = BlagodarieApp.class.getSimpleName();

    @Override
    public void onCreate () {
        super.onCreate();
        Log.d(TAG, "start application");
        Thread.setDefaultUncaughtExceptionHandler(this::handleUncaughtException);
    }

    public static void requestSync (
            @NonNull final Account account,
            @Nullable final String authToken,
            @Nullable final String authority
    ) {
        Log.d(TAG, "requestSync account=" + account);
        final Bundle settingsBundle = new Bundle();
        settingsBundle.putBoolean(ContentResolver.SYNC_EXTRAS_MANUAL, true);
        settingsBundle.putBoolean(ContentResolver.SYNC_EXTRAS_EXPEDITED, true);
        settingsBundle.putString(AccountManager.KEY_AUTHTOKEN, authToken);

        ContentResolver.requestSync(account, authority, settingsBundle);
    }

    public void handleUncaughtException (Thread thread, Throwable e) {
        Log.d(TAG, "handleUncaughtException");
        Log.e(TAG, Log.getStackTraceString(e));

        Intent intent = new Intent();
        intent.setAction("org.blagodarie.SEND_LOG");
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);

        System.exit(1);
    }
}
