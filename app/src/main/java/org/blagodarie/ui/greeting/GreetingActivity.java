package org.blagodarie.ui.greeting;

import android.accounts.Account;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.databinding.DataBindingUtil;

import org.blagodarie.R;
import org.blagodarie.databinding.GreetingActivityBinding;
import org.blagodarie.ui.symptoms.SymptomsActivity;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class GreetingActivity
        extends AppCompatActivity
        implements GreetingNavigator {

    private static final String TAG = GreetingActivity.class.getSimpleName();

    private static final String EXTRA_ACCOUNT = "org.blagodarie.ui.greeting.ACCOUNT";

    @Override
    protected void onCreate (@Nullable final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.e(TAG, "onCreate");
        final GreetingActivityBinding activityBinding = DataBindingUtil.setContentView(this, R.layout.greeting_activity);
        activityBinding.setGreetingNavigator(this);
    }

    @Override
    public void toSymptomsActivity () {
        final Account account = getIntent().getParcelableExtra(EXTRA_ACCOUNT);
        Log.d(TAG, "toSymptomsActivity account=" + account);
        startActivity(SymptomsActivity.createSelfIntent(this, account));
        finish();
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
