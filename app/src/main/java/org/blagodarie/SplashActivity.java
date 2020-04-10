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

        mAccountManager = AccountManager.get(this);

        final Account[] accounts = mAccountManager.getAccountsByType(getString(R.string.account_type));

        if (accounts.length == 0) {
            addNewAccount(getString(R.string.account_type), getString(R.string.token_type));
        } else {
            toMainActivity();
        }
    }

    private void addNewAccount (String accountType, String authTokenType) {

        mAccountManager.addAccount(
                accountType,
                authTokenType,
                null,
                null,
                this,
                future -> getAuthToken(),
                null);
    }

    private void getAuthToken(){
        mAccountManager.getAuthToken(
                mAccountManager.getAccountsByType(getString(R.string.account_type))[0],
                getString(R.string.token_type), null, this,
                new AccountManagerCallback<Bundle>() {
                    @Override
                    public void run (AccountManagerFuture<Bundle> future) {
                        try {
                            String token = future.getResult().getString((AccountManager.KEY_AUTHTOKEN));
                            mAccountManager.invalidateAuthToken(getString(R.string.account_type), token);
                        }catch(Exception e){

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
