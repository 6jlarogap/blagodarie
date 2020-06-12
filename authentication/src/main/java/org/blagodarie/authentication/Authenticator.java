package org.blagodarie.authentication;

import android.accounts.AbstractAccountAuthenticator;
import android.accounts.Account;
import android.accounts.AccountAuthenticatorResponse;
import android.accounts.AccountManager;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/raw/master/LICENSE License
 */
public final class Authenticator
        extends AbstractAccountAuthenticator {

    private static final String TAG = Authenticator.class.getSimpleName();

    public static final String OPTION_IS_INCOGNITO_USER = "org.blagodarie.authentication.Authenticator.isIncognitoUser";

    @NonNull
    private final Context mContext;


    Authenticator (@NonNull final Context context) {
        super(context);
        Log.d(TAG, "Authenticator");
        mContext = context;
    }

    @Override
    public Bundle editProperties (
            final AccountAuthenticatorResponse response,
            final String accountType
    ) {
        Log.d(TAG, "editProperties");
        return null;
    }

    @Override
    public Bundle addAccount (
            final AccountAuthenticatorResponse response,
            final String accountType,
            final String authTokenType,
            final String[] requiredFeatures,
            final Bundle options
    ) {
        Log.d(TAG, "addAccount");
        final Intent intent = AuthenticationActivity.createSelfIntent(mContext, accountType, response);
        final Bundle bundle = new Bundle();
        bundle.putAll(options);
        bundle.putParcelable(AccountManager.KEY_INTENT, intent);
        return bundle;
    }

    @Override
    public Bundle confirmCredentials (
            final AccountAuthenticatorResponse response,
            final Account account,
            final Bundle options
    ) {
        Log.d(TAG, "confirmCredentials");
        return null;
    }

    @Override
    public Bundle getAuthToken (
            final AccountAuthenticatorResponse response,
            final Account account,
            final String authTokenType,
            final Bundle options
    ) {
        Log.d(TAG, "getAuthToken");
        final Bundle bundle = new Bundle();
        if (options != null) {
            bundle.putAll(options);
        }
        //если не анонимный аккаунт
        if (!account.name.equals(mContext.getString(R.string.incognito_account_name))) {
            final Long userId = Long.valueOf(AccountManager.get(mContext).getUserData(account, AccountGeneral.USER_DATA_USER_ID));
            final Intent intent = AuthenticationActivity.createSelfIntent(mContext, account.type, userId, response);
            bundle.putParcelable(AccountManager.KEY_INTENT, intent);
        }
        return bundle;
    }

    @Override
    public String getAuthTokenLabel (final String authTokenType) {
        Log.d(TAG, "getAuthTokenLabel");
        return authTokenType + "_label";
    }

    @Override
    public Bundle updateCredentials (
            final AccountAuthenticatorResponse response,
            final Account account,
            final String authTokenType,
            final Bundle options
    ) {
        Log.d(TAG, "updateCredentials");
        throw new UnsupportedOperationException();
    }

    @Override
    public Bundle hasFeatures (
            final AccountAuthenticatorResponse response,
            final Account account,
            final String[] features
    ) {
        Log.d(TAG, "hasFeatures");
        throw new UnsupportedOperationException();
    }

}
