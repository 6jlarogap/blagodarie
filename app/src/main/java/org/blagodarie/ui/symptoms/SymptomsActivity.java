package org.blagodarie.ui.symptoms;

import android.Manifest;
import android.accounts.Account;
import android.annotation.SuppressLint;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.ActionBar;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.databinding.DataBindingUtil;
import androidx.lifecycle.ViewModelProvider;

import org.blagodarie.BlagodarieApp;
import org.blagodarie.BuildConfig;
import org.blagodarie.R;
import org.blagodarie.databinding.SymptomsActivityBinding;
import org.blagodarie.db.BlagodarieDatabase;
import org.blagodarie.db.UserSymptom;
import org.blagodarie.server.ServerConnector;
import org.blagodarie.ui.update.UpdateActivity;

import java.util.ArrayList;
import java.util.Date;

import io.reactivex.Completable;
import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SymptomsActivity
        extends AppCompatActivity
        implements LocationListener {


    private static final String EXTRA_ACCOUNT = "org.blagodarie.ui.symptoms.ACCOUNT";

    /**
     * Минимальное время между обновлениями местоположения (в миллисекундах).
     *
     * @see LocationManager#requestLocationUpdates
     */
    private static final long MIN_TIME_LOCATION_UPDATE = 180000L;

    /**
     * Минимальная дистанция между обновлениями местоположения (в метрах).
     *
     * @see LocationManager#requestLocationUpdates
     */
    private static final float MIN_DISTANCE_LOCATION_UPDATE = 100.0F;

    /**
     * Идентификатор запроса на разрешение использования определения местоположения.
     */
    private static final int PERM_REQ_ACCESS_FINE_LOCATION = 1;

    private Account mAccount;

    private SymptomsViewModel mViewModel;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    private LocationManager mLocationManager;

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        initAccount();

        initViewModel();

        final SymptomsAdapter symptomsAdapter = new SymptomsAdapter(new ArrayList<>(mViewModel.getDisplaySymptoms()), this::createUserSymptom);

        final SymptomsActivityBinding mainActivityBinding = DataBindingUtil.setContentView(this, R.layout.symptoms_activity);
        mainActivityBinding.setViewModel(mViewModel);
        mainActivityBinding.rvSymptoms.setAdapter(symptomsAdapter);

        setupToolbar();

        mLocationManager = (LocationManager) getSystemService(LOCATION_SERVICE);
    }

    private void initViewModel () {
        //создаем фабрику
        final SymptomsViewModel.Factory factory = new SymptomsViewModel.Factory(BlagodarieDatabase.getInstance(this).userSymptomDao());

        //создаем UpdateViewModel
        mViewModel = new ViewModelProvider(this, factory).get(SymptomsViewModel.class);
    }

    @Override
    public void onResume () {
        super.onResume();
        checkLatestVersion();
        if (checkLocationPermission()) {
            startLocationUpdates();
        } else {
            attemptRequestLocationPermissions();
        }
    }

    @Override
    protected void onPause () {
        super.onPause();
        stopLocationUpdates();
    }

    @Override
    protected void onDestroy () {
        super.onDestroy();
        mDisposables.dispose();
    }

    private void setupToolbar () {
        setSupportActionBar(findViewById(R.id.toolbar));
        final ActionBar actionBar = getSupportActionBar();
        if (actionBar != null) {
            actionBar.setTitle(getTitle() + " " + BuildConfig.VERSION_NAME + getString(R.string.build_type_label));
        }
    }

    @SuppressLint ("MissingPermission")
    private void startLocationUpdates () {
        Location lastLocation = mLocationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
        if (lastLocation == null) {
            lastLocation = mLocationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
        }
        if (lastLocation != null) {
            mViewModel.getCurrentLatitude().set(lastLocation.getLatitude());
            mViewModel.getCurrentLongitude().set(lastLocation.getLongitude());
        }

        mLocationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, MIN_TIME_LOCATION_UPDATE, MIN_DISTANCE_LOCATION_UPDATE, this);
        mLocationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, MIN_TIME_LOCATION_UPDATE, MIN_DISTANCE_LOCATION_UPDATE, this);
    }

    private void stopLocationUpdates () {
        mLocationManager.removeUpdates(this);
    }

    private void initAccount () {
        mAccount = getIntent().getParcelableExtra(EXTRA_ACCOUNT);
    }

    public void createUserSymptom (
            @NonNull final DisplaySymptom displaySymptom
    ) {
        long timestamp = System.currentTimeMillis();
        displaySymptom.getLastDate().set(new Date(timestamp));

        final Double latitude = mViewModel.getCurrentLatitude().get();
        final Double longitude = mViewModel.getCurrentLongitude().get();

        displaySymptom.getLastLatitude().set(latitude);
        displaySymptom.getLastLongitude().set(longitude);

        final UserSymptom userSymptom = new UserSymptom(
                Long.valueOf(mAccount.name),
                displaySymptom.getSymptomId(),
                timestamp,
                latitude,
                longitude);

        mDisposables.add(
                Completable.
                        fromAction(() -> BlagodarieDatabase.getInstance(this).userSymptomDao().insert(userSymptom)).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(() -> {
                            displaySymptom.highlight();
                            BlagodarieApp.requestSync(mAccount);
                        })
        );
    }


    private boolean checkLocationPermission () {
        return ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void attemptRequestLocationPermissions () {
        boolean shouldProvideRationale = ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.ACCESS_FINE_LOCATION);
        if (shouldProvideRationale) {
            mViewModel.isShowLocationPermissionDeniedExplanation().set(false);
            mViewModel.isShowLocationPermissionRationale().set(true);
        } else {
            if (!mViewModel.isShowLocationPermissionDeniedExplanation().get()) {
                requestLocationPermission();
            }
        }
    }

    @Override
    public void onRequestPermissionsResult (final int requestCode, @NonNull final String[] permissions, @NonNull final int[] grantResults) {
        if (requestCode == PERM_REQ_ACCESS_FINE_LOCATION) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startLocationUpdates();
            } else {
                if (!mViewModel.isShowLocationPermissionDeniedExplanation().get()) {
                    mViewModel.isShowLocationPermissionRationale().set(false);
                    mViewModel.isShowLocationPermissionDeniedExplanation().set(true);
                }
            }
        }
    }

    public void onLocationPermissionRationaleClick (final View view) {
        mViewModel.isShowLocationPermissionRationale().set(false);
        requestLocationPermission();
    }

    public void onLocationPermissionDeniedExplanationClick (final View view) {
        mViewModel.isShowLocationPermissionDeniedExplanation().set(false);
        final Intent intent = new Intent();
        intent.setAction(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
        final Uri uri = Uri.fromParts("package", BuildConfig.APPLICATION_ID, null);
        intent.setData(uri);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
    }

    public void onLocationProvidersDisabledWarningClick (final View view) {
        final Intent viewIntent = new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS);
        startActivity(viewIntent);
    }

    public void requestLocationPermission () {
        ActivityCompat.requestPermissions(SymptomsActivity.this,
                new String[]{Manifest.permission.ACCESS_FINE_LOCATION},
                PERM_REQ_ACCESS_FINE_LOCATION);
    }

    @Override
    public void onLocationChanged (Location location) {
        checkHaveEnabledLocationProvider();
        if (location != null) {
            mViewModel.getCurrentLatitude().set(location.getLatitude());
            mViewModel.getCurrentLongitude().set(location.getLongitude());
        }
    }

    @Override
    public void onStatusChanged (String provider, int status, Bundle extras) {

    }

    @Override
    public void onProviderEnabled (String provider) {
        checkHaveEnabledLocationProvider();
    }

    @Override
    public void onProviderDisabled (String provider) {
        checkHaveEnabledLocationProvider();
    }

    private void checkHaveEnabledLocationProvider () {
        mViewModel.isShowLocationProvidersDisabledWarning().set(
                !(mLocationManager.isProviderEnabled(LocationManager.GPS_PROVIDER) ||
                        mLocationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
                )
        );
    }


    private void checkLatestVersion () {
        final ServerConnector serverConnector = new ServerConnector(this);
        final GetLatestVersionExecutor getLatestVersionExecutor = new GetLatestVersionExecutor();
        mDisposables.add(
                Observable.
                        fromCallable(() -> serverConnector.execute(getLatestVersionExecutor)).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(apiResult -> {
                            if (BuildConfig.VERSION_CODE < apiResult.getVersionCode()) {
                                showUpdateVersionDialog(apiResult.getVersionName(), apiResult.getUri());
                            }
                        })
        );
    }

    private void showUpdateVersionDialog (
            @NonNull final String versionName,
            @NonNull final Uri latestVersionUri
    ) {
        final AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.txt_update_available);
        builder.setMessage(String.format(getString(R.string.txt_want_load_new_version), versionName));
        builder.setPositiveButton(R.string.action_update, (dialog, which) -> toUpdate(versionName, latestVersionUri));
        builder.setNegativeButton(R.string.action_finish, (dialog, which) -> finish());
        builder.setCancelable(false);
        builder.create();
        builder.show();
    }

    private void toUpdate (
            @NonNull final String versionName,
            @NonNull final Uri latestVersionUri
    ) {
        startActivity(UpdateActivity.createSelfIntent(this, versionName, latestVersionUri));
        finish();
    }

    public static Intent createSelfIntent (
            @NonNull final Context context,
            @NonNull final Account account
    ) {
        final Intent intent = new Intent(context, SymptomsActivity.class);
        intent.putExtra(EXTRA_ACCOUNT, account);
        return intent;
    }
}
