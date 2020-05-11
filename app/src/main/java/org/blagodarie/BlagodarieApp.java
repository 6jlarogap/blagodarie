package org.blagodarie;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.ContentResolver;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.multidex.MultiDexApplication;

import java.text.DateFormat;
import java.text.FieldPosition;
import java.text.ParseException;
import java.text.ParsePosition;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

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
}
