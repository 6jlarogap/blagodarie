package org.blagodarie.authentication;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/raw/master/LICENSE License
 */
public final class AuthenticatorService
        extends Service {

    private static final String TAG = AuthenticatorService.class.getSimpleName();

    @Override
    public IBinder onBind (final Intent intent) {
        Log.d(TAG, "onBind");
        return new Authenticator(this).getIBinder();
    }

}