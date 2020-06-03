package org.blagodarie.ui.update;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import org.blagodarie.BuildConfig;
import org.blagodarie.R;
import org.blagodarie.server.ServerConnector;

import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;

public abstract class UpdatingActivity
        extends AppCompatActivity {

    private static final String TAG = UpdatingActivity.class.getSimpleName();

    private static final String NEW_VERSION_NOTIFICATION_PREFERENCE = "org.blagodarie.ui.update.preference.newVersionNotification";

    private CompositeDisposable mDisposables = new CompositeDisposable();

    @Override
    public void onResume () {
        Log.d(TAG, "onResume");
        super.onResume();
        checkLatestVersion();
    }

    @Override
    protected void onDestroy () {
        Log.d(TAG, "onDestroy");
        super.onDestroy();
        mDisposables.clear();
    }

    private void checkLatestVersion () {
        Log.d(TAG, "checkLatestVersion");
        final ServerConnector serverConnector = new ServerConnector(this);
        final GetLatestVersionExecutor getLatestVersionExecutor = new GetLatestVersionExecutor();
        mDisposables.add(
                Observable.
                        fromCallable(() -> serverConnector.execute(getLatestVersionExecutor)).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                apiResult -> {
                                    if (BuildConfig.VERSION_CODE < apiResult.getVersionCode()) {
                                        final Update update = Update.determine(apiResult.getVersionName());
                                        switch (update) {
                                            case OPTIONAL:
                                                if (!getSharedPreferences(NEW_VERSION_NOTIFICATION_PREFERENCE, Context.MODE_PRIVATE).contains(apiResult.getVersionName().toString())) {
                                                    showUpdateVersionDialog(apiResult.isGooglePlayUpdate(), update, apiResult.getVersionName(), apiResult.getUri(), apiResult.getPlayMarketUri());
                                                    getSharedPreferences(NEW_VERSION_NOTIFICATION_PREFERENCE, Context.MODE_PRIVATE).
                                                            edit().
                                                            putString(apiResult.getVersionName().toString(), "").
                                                            apply();
                                                }
                                                break;
                                            case MANDATORY:
                                                showUpdateVersionDialog(apiResult.isGooglePlayUpdate(), update, apiResult.getVersionName(), apiResult.getUri(), apiResult.getPlayMarketUri());
                                                getSharedPreferences(NEW_VERSION_NOTIFICATION_PREFERENCE, Context.MODE_PRIVATE).
                                                        edit().
                                                        putString(apiResult.getVersionName().toString(), "").
                                                        apply();
                                                break;
                                            case NO:
                                                break;
                                            default:
                                                Log.e(TAG, "Indefinite update type");
                                        }
                                    }
                                },
                                throwable -> {
                                    Log.e(TAG, "checkLatestVersion error=" + throwable);
                                    Toast.makeText(this, R.string.error_server_connection, Toast.LENGTH_LONG).show();
                                }
                        )
        );
    }

    private void showUpdateVersionDialog (
            final boolean googlePlayUpdate,
            @NonNull final Update update,
            @NonNull final VersionName versionName,
            @NonNull final Uri latestVersionUri,
            @NonNull final Uri playMarketUri
    ) {
        Log.d(TAG, "showUpdateVersionDialog");
        new AlertDialog.
                Builder(this).
                setTitle(R.string.info_msg_update_available).
                setMessage(String.format(getString(R.string.qstn_want_load_new_version), versionName)).
                setPositiveButton(
                        R.string.btn_update,
                        (dialog, which) -> {
                            if (googlePlayUpdate) {
                                toPlayMarket(playMarketUri);
                            } else {
                                toIndependentUpdate(versionName, latestVersionUri);
                            }
                        }).
                setNegativeButton(
                        update == Update.MANDATORY ? R.string.btn_finish : R.string.btn_cancel,
                        (dialog, which) -> {
                            if (update == Update.MANDATORY) {
                                finish();
                            }
                        }).
                create().
                show();
    }

    public void toPlayMarket (@NonNull final Uri playMarketUri) {
        final Intent i = new Intent(Intent.ACTION_VIEW);
        i.setData(playMarketUri);
        startActivity(i);
        finish();
    }

    private void toIndependentUpdate (
            @NonNull final VersionName versionName,
            @NonNull final Uri latestVersionUri
    ) {
        Log.d(TAG, "toIndependentUpdate versionName=" + versionName + "; latestVersionUri=" + latestVersionUri);
        startActivity(UpdateActivity.createSelfIntent(this, versionName.toString(), latestVersionUri));
        finish();
    }

}
