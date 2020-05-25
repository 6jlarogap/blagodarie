package org.blagodarie.ui.greeting;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.databinding.DataBindingUtil;

import org.blagodarie.R;
import org.blagodarie.authentication.AccountGeneral;
import org.blagodarie.authentication.Authenticator;
import org.blagodarie.databinding.GreetingActivityBinding;
import org.blagodarie.ui.symptoms.SymptomsActivity;

import java.util.UUID;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/raw/master/LICENSE License
 */
public final class GreetingActivity
        extends AppCompatActivity
        implements GreetingUserActionListener {

    private static final String TAG = GreetingActivity.class.getSimpleName();

    private AccountManager mAccountManager;

    @Override
    protected void onCreate (@Nullable final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.e(TAG, "onCreate");

        mAccountManager = AccountManager.get(this);

        final GreetingActivityBinding activityBinding = DataBindingUtil.setContentView(this, R.layout.greeting_activity);
        activityBinding.setGreetingUserActionListener(this);
    }

    public void toSymptomsActivity (@NonNull final Account account) {
        Log.d(TAG, "toSymptomsActivity");
        startActivity(SymptomsActivity.createSelfIntent(this, account));
        finish();
    }

    public void showIncognitoIdDialog () {
        Log.e(TAG, "showIncognitoIdDialog");
        final View view = getLayoutInflater().inflate(R.layout.enter_incognito_id_dialog, null, false);

        final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        final ClipData clipData = clipboard.getPrimaryClip();
        if (clipData != null) {
            final ClipData.Item item = clipboard.getPrimaryClip().getItemAt(0);
            final String incognitoIdString = item.getText().toString();
            try {
                final UUID incognitoId = UUID.fromString(incognitoIdString);
                ((EditText) view.findViewById(R.id.etIncognitoId)).setText(incognitoId.toString());
            } catch (IllegalArgumentException e) {
                Log.e(TAG, "error=" + e);
            }
        }

        new AlertDialog.
                Builder(this).
                setView(view).
                setPositiveButton(R.string.btn_continue, (dialog, which) -> {
                    final String incognitoIdString = ((EditText) view.findViewById(R.id.etIncognitoId)).getText().toString();
                    try {
                        final UUID incognitoId = UUID.fromString(incognitoIdString);
                        addNewAccount(getString(R.string.account_type), true, incognitoId.toString());
                    } catch (IllegalArgumentException e) {
                        Toast.makeText(this, getString(R.string.err_msg_incorrect_incognito_id) + e.getLocalizedMessage(), Toast.LENGTH_SHORT).show();
                    }
                }).
                create().
                show();
    }

    public static Intent createSelfIntent (
            @NonNull final Context context
    ) {
        Log.d(TAG, "createSelfIntent");
        return new Intent(context, GreetingActivity.class);
    }

    @Override
    public void createNewIncognitoId () {
        final String accountType = getString(R.string.account_type);
        addNewAccount(accountType, true, null);
    }

    @Override
    public void enterExistingIncognitoId () {
        showIncognitoIdDialog();
    }

    private void addNewAccount (
            @NonNull final String accountType,
            final boolean isIncognitoAccount,
            @Nullable final String incognitoId
    ) {
        Log.d(TAG, "addNewAccount accountType=" + accountType);
        final Bundle bundle = new Bundle();
        bundle.putBoolean(Authenticator.OPTION_IS_INCOGNITO_USER, isIncognitoAccount);
        bundle.putString(Authenticator.OPTION_INCOGNITO_ID, incognitoId);
        mAccountManager.addAccount(
                accountType,
                getString(R.string.token_type),
                null,
                bundle,
                this,
                future -> {
                    final Account account = getAccount();
                    if (account != null) {
                        toSymptomsActivity(account);
                    }
                },
                null
        );
    }

    private Account getAccount () {
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
            return accounts[0];
        }
        return null;
    }
}
