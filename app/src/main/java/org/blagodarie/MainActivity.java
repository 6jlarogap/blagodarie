package org.blagodarie;

import android.Manifest;
import android.accounts.Account;
import android.accounts.AccountManager;
import android.annotation.SuppressLint;
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
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.databinding.DataBindingUtil;
import androidx.lifecycle.ViewModelProvider;

import org.blagodarie.databinding.MainActivityBinding;
import org.blagodarie.server.ServerDataSource;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.Locale;

import io.reactivex.Completable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class MainActivity
        extends AppCompatActivity
        implements LocationListener {

    /**
     * Минимальное время между обновлениями местоположения (в миллисекундах).
     *
     * @see LocationManager#requestLocationUpdates
     */
    private static final long MIN_TIME_LOCATION_UPDATE = 60000L;

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

    private Long mUserId;

    private MainViewModel mViewModel;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    private LocationManager mLocationManager;

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        initUserId();

        mViewModel = new ViewModelProvider(this).get(MainViewModel.class);

        final SymptomsAdapter symptomsAdapter = new SymptomsAdapter(new ArrayList<>(mViewModel.getSymptoms()), this::createUserSymptom);

        final MainActivityBinding mainActivityBinding = DataBindingUtil.setContentView(this, R.layout.main_activity);
        mainActivityBinding.setViewModel(mViewModel);
        mainActivityBinding.rvSymptoms.setAdapter(symptomsAdapter);


        mLocationManager = (LocationManager) getSystemService(LOCATION_SERVICE);
    }

    @Override
    public void onResume () {
        super.onResume();
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

    private void initUserId () {
        final Account[] accounts = AccountManager.get(this).getAccountsByType(getString(R.string.account_type));

        if (accounts.length == 1) {
            mUserId = Long.valueOf(accounts[0].name);
        } else {
            finish();
        }
    }

    public void createUserSymptom (
            @NonNull final DisplaySymptom displaySymptom
    ) {
        long timestamp = System.currentTimeMillis();
        displaySymptom.getLastAdd().set(new Date(timestamp));

        final Double latitude = mViewModel.getCurrentLatitude().get();
        final Double longitude = mViewModel.getCurrentLongitude().get();

        displaySymptom.getLastLatitude().set(latitude);
        displaySymptom.getLastLongitude().set(longitude);

        final UserSymptom userSymptom = new UserSymptom(
                mUserId,
                displaySymptom.getSymptomId(),
                timestamp,
                latitude,
                longitude);
        final Collection<UserSymptom> userSymptoms = new ArrayList<>();
        userSymptoms.add(userSymptom);
        final ServerDataSource serverDataSource = new ServerDataSource(this);
        mDisposables.add(
                Completable.
                        fromAction(() -> {
                            displaySymptom.getInLoadProgress().set(true);
                            serverDataSource.addUserSymptom(createJsonContent(userSymptoms));
                        }).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(() -> {
                            displaySymptom.getInLoadProgress().set(false);
                            displaySymptom.highlight();
                        })
        );

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
            content.append(String.format(Locale.ENGLISH, "{\"symptom_id\":%d,\"timestamp\":%d,\"latitude\":%f,\"longitude\":%f}",
                    userSymptom.getSymptomId(), (userSymptom.getTimestamp() / 1000), userSymptom.getLatitude(), userSymptom.getLongitude()));
        }
        content.append("]}");
        return content.toString();
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
        ActivityCompat.requestPermissions(MainActivity.this,
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
}
