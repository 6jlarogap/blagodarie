package org.blagodarie.authentication;

import android.accounts.Account;
import android.accounts.AccountAuthenticatorResponse;
import android.accounts.AccountManager;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.navigation.NavController;
import androidx.navigation.Navigation;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class AuthenticationActivity
        extends AppCompatActivity
        implements AuthenticationNavigator {

    @NonNull
    private static final String EXTRA_ACCOUNT_TYPE = "org.blagodarie.ACCOUNT_TYPE";

    private NavController mNavController;
    private AccountAuthenticatorResponse mAccountAuthenticatorResponse = null;
    private Bundle mResultBundle = null;

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mAccountAuthenticatorResponse =
                getIntent().getParcelableExtra(AccountManager.KEY_ACCOUNT_AUTHENTICATOR_RESPONSE);

        if (mAccountAuthenticatorResponse != null) {
            mAccountAuthenticatorResponse.onRequestContinued();
        }

        final AccountManager accountManager = (AccountManager) getApplicationContext().getSystemService(ACCOUNT_SERVICE);

        final Account[] accounts = accountManager.getAccountsByType(getString(R.string.account_type));

        if (accounts.length == 1) {
            finish();
        } else {
            setContentView(R.layout.authentication_activity);
            this.mNavController = Navigation.findNavController(this, R.id.nav_host_fragment);
        }
    }

    public static Intent createIntent (
            @NonNull final Context context,
            @NonNull final String accountType,
            AccountAuthenticatorResponse response
    ) {
        final Intent intent = new Intent(context, AuthenticationActivity.class);
        intent.putExtra(AuthenticationActivity.EXTRA_ACCOUNT_TYPE, accountType);
        intent.putExtra(AccountManager.KEY_ACCOUNT_AUTHENTICATOR_RESPONSE, response);
        return intent;
    }

    @Override
    public void fromGreetingToEnter () {
        this.mNavController.navigate(R.id.action_greetingFragment_to_enterFragment);
    }

    @Override
    public void finish() {
        if (mAccountAuthenticatorResponse != null) {
            // send the result bundle back if set, otherwise send an error.
            if (mResultBundle != null) {
                mAccountAuthenticatorResponse.onResult(mResultBundle);
            } else {
                mAccountAuthenticatorResponse.onError(AccountManager.ERROR_CODE_CANCELED,
                        "canceled");
            }
            mAccountAuthenticatorResponse = null;
        }
        super.finish();
    }
    public final void setAccountAuthenticatorResult(Bundle result) {
        mResultBundle = result;
    }
}
