package org.blagodarie;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.accounts.AccountManagerCallback;
import android.accounts.AccountManagerFuture;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.widget.Toast;

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

        this.mAccountManager = AccountManager.get(this);

        final Account[] accounts = mAccountManager.getAccountsByType(getString(R.string.account_type));

        if (accounts.length == 0) {
            addNewAccount(getString(R.string.account_type), "");
        } else {
            toMainActivity();
        }
    }

    private void addNewAccount (String accountType, String authTokenType) {

        this.mAccountManager.addAccount(
                accountType,
                authTokenType,
                null,
                null,
                this,
                new AccountManagerCallback<Bundle>() {
                    @Override
                    public void run (AccountManagerFuture<Bundle> future) {
                        Bundle bnd = null;
                        try {
                            bnd = future.getResult();
                            final String authtoken = bnd.getString(AccountManager.KEY_AUTHTOKEN);
                            toMainActivity();
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                    }
                }, null);
    }

    private void toMainActivity () {
        Intent intent = new Intent(this, MainActivity.class);
        startActivity(intent);
        finish();
    }
}
