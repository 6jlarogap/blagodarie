package org.blagodarie;

import android.accounts.Account;
import android.content.ContentResolver;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;
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
    }

    public static void requestSync(@NonNull final Account account){
        Log.d(TAG, "requestSync account=" + account);
        final Bundle settingsBundle = new Bundle();
        settingsBundle.putBoolean(ContentResolver.SYNC_EXTRAS_MANUAL, true);
        settingsBundle.putBoolean(ContentResolver.SYNC_EXTRAS_EXPEDITED, true);

        ContentResolver.requestSync(account, "org.blagodarie.datasync.provider", settingsBundle);

    }
}
