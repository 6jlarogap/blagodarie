package org.blagodarie.authentication;

import android.accounts.AbstractAccountAuthenticator;
import android.accounts.Account;
import android.accounts.AccountAuthenticatorResponse;
import android.accounts.AccountManager;
import android.accounts.NetworkErrorException;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class Authenticator
        extends AbstractAccountAuthenticator {

    private static final String TAG = Authenticator.class.getSimpleName();

    @NonNull
    private final Context mContext;


    Authenticator(@NonNull final Context context) {
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
    ) throws NetworkErrorException {
        Log.d(TAG, "addAccount");
        final Intent intent = AuthenticationActivity.createSelfIntent(mContext, accountType, response);
        final Bundle bundle = new Bundle();
        if (options != null) {
            bundle.putAll(options);
        }
        bundle.putParcelable(AccountManager.KEY_INTENT, intent);
        return bundle;
    }

    @Override
    public Bundle confirmCredentials (
            final AccountAuthenticatorResponse response, Account account, Bundle options) throws NetworkErrorException {
        Log.d(TAG, "confirmCredentials");
        return null;
    }

    @Override
    public Bundle getAuthToken (
            final AccountAuthenticatorResponse response,
            final Account account,
            final String authTokenType,
            final Bundle options
    ) throws NetworkErrorException {
        Log.d(TAG, "getAuthToken");
        final Intent intent = AuthenticationActivity.createSelfIntent(mContext, account.type, Long.valueOf(account.name), response);
        final Bundle bundle = new Bundle();
        if (options != null) {
            bundle.putAll(options);
        }
        bundle.putParcelable(AccountManager.KEY_INTENT, intent);
        return bundle;
    }

    @Override
    public String getAuthTokenLabel (final String authTokenType) {
        Log.d(TAG, "getAuthTokenLabel");
        return authTokenType + "_label";
    }

    @Override
    public Bundle updateCredentials (
            final AccountAuthenticatorResponse response, Account account, String authTokenType, Bundle options) throws NetworkErrorException {
        Log.d(TAG, "updateCredentials");
        throw new UnsupportedOperationException();
    }

    @Override
    public Bundle hasFeatures (AccountAuthenticatorResponse response, Account account, String[] features) throws NetworkErrorException {
        Log.d(TAG, "hasFeatures");
        throw new UnsupportedOperationException();
    }
/*
    @Override
    public Bundle editProperties(
            AccountAuthenticatorResponse r, String s) {
        throw new UnsupportedOperationException();
    }
    // Don't add additional accounts
    @Override
    public Bundle addAccount(
            final AccountAuthenticatorResponse r,
            final String s,
            final String s2,
            final String[] strings,
            final Bundle bundle
    ) throws NetworkErrorException {
        final Intent intent = new Intent(mContext, NewAccountActivity.class);
        intent.putExtra(NewAccountActivity.EXTRA_TOKEN_TYPE, accountType);
        intent.putExtra(AccountManager.KEY_ACCOUNT_AUTHENTICATOR_RESPONSE, response);
        final Bundle _bundle = new Bundle();
        if (options != null) {
            bundle.putAll(options);
        }
        bundle.putParcelable(AccountManager.KEY_INTENT, intent);
        return bundle;
    }
    // Ignore attempts to confirm credentials
    @Override
    public Bundle confirmCredentials(
            AccountAuthenticatorResponse r,
            Account account,
            Bundle bundle) throws NetworkErrorException {
        return null;
    }
    // Getting an authentication token is not supported
    @Override
    public Bundle getAuthToken(
            AccountAuthenticatorResponse r,
            Account account,
            String s,
            Bundle bundle) throws NetworkErrorException {
        throw new UnsupportedOperationException();
    }
    // Getting a label for the auth token is not supported
    @Override
    public String getAuthTokenLabel(String s) {
        throw new UnsupportedOperationException();
    }
    // Updating user credentials is not supported
    @Override
    public Bundle updateCredentials(
            AccountAuthenticatorResponse r,
            Account account,
            String s, Bundle bundle) throws NetworkErrorException {
        throw new UnsupportedOperationException();
    }
    // Checking features for the account is not supported
    @Override
    public Bundle hasFeatures(
            AccountAuthenticatorResponse r,
            Account account, String[] strings) throws NetworkErrorException {
        throw new UnsupportedOperationException();
    }*/
}
