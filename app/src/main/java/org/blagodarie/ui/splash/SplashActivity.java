package org.blagodarie.ui.splash;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.app.AlertDialog;
import android.os.Bundle;
import android.util.Log;
import android.widget.ArrayAdapter;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import org.blagodarie.R;
import org.blagodarie.authentication.AccountGeneral;
import org.blagodarie.authentication.Authenticator;
import org.blagodarie.ui.greeting.GreetingActivity;
import org.blagodarie.ui.symptoms.SymptomsActivity;

import java.util.Arrays;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SplashActivity
        extends AppCompatActivity {

    private static final String TAG = SplashActivity.class.getSimpleName();

    private AccountManager mAccountManager;

    @Override
    protected final void onCreate (
            @Nullable final Bundle savedInstanceState
    ) {
        super.onCreate(savedInstanceState);
        Log.d(TAG, "onCreate");

        mAccountManager = AccountManager.get(this);
    }

    @Override
    protected void onResume () {
        super.onResume();
        Log.d(TAG, "onResume");
        chooseAccount();
    }

    private void chooseAccount () {
        Log.d(TAG, "chooseAccount");
        final String accountType = getString(R.string.account_type);
        final Account[] accounts = mAccountManager.getAccountsByType(accountType);
        if (accounts.length == 1) {
            if (!accounts[0].name.equals(getString(R.string.incognito_account_name))) {
                final String userId = mAccountManager.getUserData(accounts[0], AccountGeneral.USER_DATA_USER_ID);
                if (userId == null) {
                    mAccountManager.setUserData(accounts[0], AccountGeneral.USER_DATA_USER_ID, accounts[0].name);
                }
            }
            toSymptomsActivity(accounts[0]);
        } else if (accounts.length > 1) {
            showAccountPicker(accounts);
        } else {
            toGreetingActivity();
        }
    }

    private void showAccountPicker (
            @NonNull final Account[] accounts
    ) {
        Log.d(TAG, "showAccountPicker accounts=" + Arrays.toString(accounts));
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
                        (dialog, which) -> toSymptomsActivity(accounts[which])
                ).
                create().
                show();
    }

    private void toSymptomsActivity (
            @NonNull final Account account
    ) {
        Log.d(TAG, "toSymptomsActivity account=" + account);
        startActivity(SymptomsActivity.createSelfIntent(this, account));
        finish();
    }

    private void toGreetingActivity () {
        Log.d(TAG, "toGreetingActivity");
        startActivity(GreetingActivity.createSelfIntent(this));
        finish();
    }

}
