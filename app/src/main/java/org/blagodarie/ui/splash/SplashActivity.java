package org.blagodarie.ui.splash;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.app.AlertDialog;
import android.os.Bundle;
import android.widget.ArrayAdapter;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import org.blagodarie.R;
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
    }

    @Override
    protected void onResume () {
        super.onResume();
        chooseAccount();
    }

    private void chooseAccount () {
        final String accountType = getString(R.string.account_type);
        final Account[] accounts = mAccountManager.getAccountsByType(accountType);
        if (accounts.length == 1) {
            toMainActivity(accounts[0]);
        } else if (accounts.length > 1) {
            showAccountPicker(accounts);
        } else {
            addNewAccount(accountType);
        }
    }

    private void showAccountPicker (@NonNull final Account[] accounts) {
        final String[] names = new String[accounts.length];
        for (int i = 0; i < accounts.length; i++) {
            names[i] = accounts[i].name;
        }

        new AlertDialog.
                Builder(this).
                setTitle(R.string.choose_account).
                setCancelable(false).
                setAdapter(
                        new ArrayAdapter<>(
                                getBaseContext(),
                                android.R.layout.simple_list_item_1, names),
                        (dialog, which) -> toMainActivity(accounts[which])
                ).
                create().
                show();
    }

    private void addNewAccount (@NonNull final String accountType) {
        mAccountManager.addAccount(
                accountType,
                getString(R.string.token_type),
                null,
                null,
                this,
                future -> chooseAccount(),
                null);
    }

    private void toMainActivity (@NonNull final Account account) {
        startActivity(SymptomsActivity.createSelfIntent(this, account));
        finish();
    }
}
