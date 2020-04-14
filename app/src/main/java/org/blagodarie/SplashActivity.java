package org.blagodarie;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SplashActivity
        extends AppCompatActivity {

    private AccountManager mAccountManager;

    @Override
    protected final void onCreate (@Nullable final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        mAccountManager = AccountManager.get(this);

        final Account account = getAccount();

        if (account != null) {
            toMainActivity(account);
        } else {
            addNewAccount(getString(R.string.account_type), getString(R.string.token_type));
        }
    }

    @Nullable
    private Account getAccount () {
        Account account = null;
        final Account[] accounts = mAccountManager.getAccountsByType(getString(R.string.account_type));
        if (accounts.length > 0) {
            account = accounts[0];
        }
        return account;
    }

    private void addNewAccount (
            @NonNull final String accountType,
            @NonNull final String authTokenType
    ) {
        mAccountManager.addAccount(
                accountType,
                authTokenType,
                null,
                null,
                this,
                future -> {
                    final Account account = getAccount();
                    if (account != null) {
                        toMainActivity(account);
                    }
                },
                null);
    }

    private void toMainActivity (
            @NonNull final Account account
    ) {
        startActivity(MainActivity.createIntent(this, account));
        finish();
    }
}
