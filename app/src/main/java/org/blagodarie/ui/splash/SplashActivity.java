package org.blagodarie.ui.splash;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.text.Spannable;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.method.LinkMovementMethod;
import android.text.style.ClickableSpan;
import android.text.style.UnderlineSpan;
import android.util.Log;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.databinding.DataBindingUtil;

import org.blagodarie.R;
import org.blagodarie.authentication.AccountGeneral;
import org.blagodarie.authentication.Authenticator;
import org.blagodarie.databinding.TransitionToPlayMarketDialogBinding;

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

    private void showMandatoryUpdateDialog (
            @NonNull final String incognitoId
    ) {
        final String msg = getString(R.string.txt_transition_to_play_market);
        final Spannable spannable = new SpannableString(msg);

        final ClickableSpan cs1 = new ClickableSpan() {
            @Override
            public void onClick (@NonNull View v) {
                final Intent i = new Intent(Intent.ACTION_VIEW);
                i.setData(Uri.parse("https://play.google.com/store/apps/details?id=org.blagodarie"));
                startActivity(i);
            }
        };
        final ClickableSpan cs2 = new ClickableSpan() {
            @Override
            public void onClick (@NonNull View v) {
                final Intent i = new Intent(Intent.ACTION_VIEW);
                i.setData(Uri.parse("https://play.google.com/store/apps/details?id=org.blagodarie"));
                startActivity(i);
            }
        };
        spannable.setSpan(new UnderlineSpan(), 42, 53, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        spannable.setSpan(new UnderlineSpan(), 226, 237, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        spannable.setSpan(cs1, 42, 53, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        spannable.setSpan(cs2, 226, 237, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);

        final TransitionToPlayMarketDialogBinding binding = DataBindingUtil.inflate(getLayoutInflater(), R.layout.transition_to_play_market_dialog, null, false);
        binding.setText(spannable);
        binding.tvText.setMovementMethod(LinkMovementMethod.getInstance());
        binding.setIncognitoId(incognitoId);

        final AlertDialog alertDialog = new AlertDialog.
                Builder(this).
                setView(binding.getRoot()).
                setNegativeButton(R.string.btn_copy, null).
                setPositiveButton(R.string.btn_delete, (dialog, which) -> {
                    Intent intent = new Intent(Intent.ACTION_DELETE);
                    intent.setData(Uri.parse("package:" + getApplicationContext().getPackageName()));
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                    finish();
                }).
                setCancelable(false).
                create();

        alertDialog.show();

        alertDialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(Color.rgb(255, 50, 50));
        alertDialog.getButton(AlertDialog.BUTTON_NEGATIVE).setOnClickListener(v -> {
            final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            final ClipData clip = ClipData.newPlainText(getString(R.string.txt_incognito_id), incognitoId);
            clipboard.setPrimaryClip(clip);
            Toast.makeText(this, R.string.copied_to_clipboard, Toast.LENGTH_SHORT).show();
        });

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
            addNewAccount(accountType, true);
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

    private void addNewAccount (
            @NonNull final String accountType,
            final boolean isIncognitoAccount
    ) {
        Log.d(TAG, "addNewAccount accountType=" + accountType);
        Bundle bundle = new Bundle();
        bundle.putBoolean(Authenticator.OPTION_IS_INCOGNITO_USER, isIncognitoAccount);
        mAccountManager.addAccount(
                accountType,
                getString(R.string.token_type),
                null,
                bundle,
                this,
                future -> chooseAccount(),
                null
        );
    }

    private void toSymptomsActivity (
            @NonNull final Account account
    ) {
        Log.d(TAG, "toSymptomsActivity account=" + account);
        showMandatoryUpdateDialog(mAccountManager.getUserData(account, AccountGeneral.USER_DATA_INCOGNITO_ID));
        //startActivity(SymptomsActivity.createSelfIntent(this, account));
        //finish();
    }

}
