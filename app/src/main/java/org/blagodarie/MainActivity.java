package org.blagodarie;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.databinding.DataBindingUtil;
import androidx.lifecycle.ViewModelProvider;

import org.blagodarie.databinding.MainActivityBinding;
import org.blagodarie.server.ServerDataSource;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Locale;

import io.reactivex.Completable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.schedulers.Schedulers;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class MainActivity
        extends AppCompatActivity {

    private Long mUserId;

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        initUserId();
        final MainActivityBinding mainActivityBinding = DataBindingUtil.setContentView(this, R.layout.main_activity);
        final SymptomsAdapter symptomsAdapter = new SymptomsAdapter(this::createUserSymptom);
        final MainViewModel mViewModel = new ViewModelProvider(this).get(MainViewModel.class);
        mViewModel.getSymptoms().observe(this, symptoms -> symptomsAdapter.setSymptoms(new ArrayList<>(symptoms)));
        mainActivityBinding.rvSymptoms.setAdapter(symptomsAdapter);
    }

    private void initUserId () {

        final Account[] accounts = AccountManager.get(this).getAccountsByType(getString(R.string.account_type));

        if (accounts.length == 1) {
            mUserId = Long.valueOf(accounts[0].name);
        } else {
            finish();
        }
    }

    public void createUserSymptom (
            @NonNull final Symptom symptom,
            final long timestamp
    ) {
        final UserSymptom userSymptom = new UserSymptom(mUserId, symptom.getId(), timestamp);
        Collection<UserSymptom> userSymptoms = new ArrayList<>();
        userSymptoms.add(userSymptom);
        final ServerDataSource serverDataSource = new ServerDataSource(this);
        Completable.
                fromAction(() -> serverDataSource.addUserSymptom(createJsonContent(userSymptoms))).
                subscribeOn(Schedulers.io()).
                observeOn(AndroidSchedulers.mainThread()).
                subscribe();
    }

    private String createJsonContent (@NonNull final Collection<UserSymptom> userSymptoms) {
        final StringBuilder content = new StringBuilder();
        content.append(String.format(Locale.ENGLISH, "{\"user_id\":%d,\"user_symptoms\":[", mUserId));

        boolean isFirst = true;
        for (UserSymptom userSymptom : userSymptoms) {
            if (!isFirst) {
                content.append(',');
            } else {
                isFirst = false;
            }
            content.append(String.format(Locale.ENGLISH, "{\"symptom_id\":%d,\"timestamp\":%d,\"latitude\":null,\"longitude\":null}",
                    userSymptom.getSymptomId(), (userSymptom.getTimestamp() / 1000)));
        }
        content.append("]}");
        return content.toString();
    }
}
