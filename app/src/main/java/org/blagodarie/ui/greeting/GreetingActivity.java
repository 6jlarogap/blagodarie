package org.blagodarie.ui.greeting;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.databinding.DataBindingUtil;

import org.blagodarie.R;
import org.blagodarie.authentication.AccountGeneral;
import org.blagodarie.databinding.GreetingActivityBinding;
import org.blagodarie.ui.symptoms.SymptomsActivity;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/raw/master/LICENSE License
 */
public final class GreetingActivity
        extends AppCompatActivity
        implements GreetingUserActionListener {

    private static final String TAG = GreetingActivity.class.getSimpleName();

    private static final String EXTRA_ACCOUNT = "org.blagodarie.ui.greeting.ACCOUNT";

    /**
     * Аккаунт.
     */
    private Account mAccount;

    /**
     * Анонимный ключ.
     */
    private String mIncognitoId;

    @Override
    protected void onCreate (@Nullable final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.e(TAG, "onCreate");

        //если аккаунт передан
        if (getIntent().hasExtra(EXTRA_ACCOUNT)) {
            //получить аккаунт
            mAccount = getIntent().getParcelableExtra(EXTRA_ACCOUNT);
            Log.d(TAG, "account=" + mAccount);

            //получить анонимный ключ
            mIncognitoId = AccountManager.get(this).getUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_ID);
            //если анонимный ключ существует
            if (mIncognitoId != null) {
                //отобразить экран
                final GreetingActivityBinding activityBinding = DataBindingUtil.setContentView(this, R.layout.greeting_activity);
                activityBinding.setGreetingUserActionListener(this);
            } else {
                //иначе показать сообщение об ошибке и закрыть экран
                Toast.makeText(this, R.string.error_incognito_id_is_missing, Toast.LENGTH_SHORT).show();
                finish();
            }
        } else {
            //иначе показать сообщение об ошибке и закрыть экран
            Toast.makeText(this, R.string.error_account_not_set, Toast.LENGTH_SHORT).show();
            finish();
        }
    }

    @Override
    public void toSymptomsActivity () {
        Log.d(TAG, "toSymptomsActivity");
        startActivity(SymptomsActivity.createSelfIntent(this, mAccount));
        finish();
    }

    @Override
    public void showIncognitoIdDialog () {
        Log.e(TAG, "showIncognitoIdDialog");
        new AlertDialog.
                Builder(this).
                setTitle(R.string.txt_your_incognito_id).
                setMessage(mIncognitoId).
                setPositiveButton(
                        R.string.action_to_clipboard,
                        (dialog, which) -> {
                            final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                            final ClipData clip = ClipData.newPlainText(getString(R.string.txt_incognito_id), mIncognitoId);
                            clipboard.setPrimaryClip(clip);
                            Toast.makeText(this, R.string.copied_to_clipboard, Toast.LENGTH_SHORT).show();
                        }).
                setNegativeButton(R.string.action_close, null).
                create().
                show();
    }

    public static Intent createSelfIntent (
            @NonNull final Context context,
            @NonNull final Account account
    ) {
        Log.d(TAG, "createSelfIntent account=" + account);
        final Intent intent = new Intent(context, GreetingActivity.class);
        intent.putExtra(EXTRA_ACCOUNT, account);
        return intent;
    }
}
