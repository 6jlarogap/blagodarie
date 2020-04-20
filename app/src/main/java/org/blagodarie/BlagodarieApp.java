package org.blagodarie;

import android.accounts.Account;
import android.content.ContentResolver;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.multidex.MultiDexApplication;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class BlagodarieApp
        extends MultiDexApplication {

    public static void requestSync(@NonNull final Account account){
        final Bundle settingsBundle = new Bundle();
        settingsBundle.putBoolean(ContentResolver.SYNC_EXTRAS_MANUAL, true);
        settingsBundle.putBoolean(ContentResolver.SYNC_EXTRAS_EXPEDITED, true);

        ContentResolver.requestSync(account, "org.blagodarie.datasync.provider", settingsBundle);

    }
}
