package org.blagodarie;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import org.blagodarie.ui.symptoms.SymptomsActivity;

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

        final String accountType = getString(R.string.account_type);
        final Account account = getAccount(accountType);

        if (account != null) {
            toMainActivity(account);
        } else {
            addNewAccount(accountType);
        }
    }

    @Nullable
    private Account getAccount (@NonNull final String accountType) {
        Account account = null;
        final Account[] accounts = mAccountManager.getAccountsByType(accountType);
        if (accounts.length > 0) {
            account = accounts[0];
        }
        return account;
    }

    private void addNewAccount (@NonNull final String accountType) {
        mAccountManager.addAccount(
                accountType,
                getString(R.string.token_type),
                null,
                null,
                this,
                future -> {
                    final Account account = getAccount(accountType);
                    if (account != null) {
                        toMainActivity(account);
                    }
                },
                null);
    }

    private void toMainActivity (
            @NonNull final Account account
    ) {
        startActivity(SymptomsActivity.createSelfIntent(this, account));
        finish();
    }
}
