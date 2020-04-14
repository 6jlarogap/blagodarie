package org.blagodarie.authentication;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class AuthenticatorService
        extends Service {

    @Override
    public IBinder onBind (final Intent intent) {
        return new Authenticator(this).getIBinder();
    }

}