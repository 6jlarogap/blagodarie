package org.blagodarie;

import android.Manifest;
import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.Intent;
import android.content.IntentSender;
import android.content.pm.PackageManager;
import android.location.Location;
import android.net.Uri;
import android.os.Bundle;
import android.os.Looper;
import android.provider.Settings;
import android.view.View;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.databinding.DataBindingUtil;
import androidx.lifecycle.ViewModelProvider;

import com.google.android.gms.common.api.ApiException;
import com.google.android.gms.common.api.ResolvableApiException;
import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationCallback;
import com.google.android.gms.location.LocationRequest;
import com.google.android.gms.location.LocationResult;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.location.LocationSettingsRequest;
import com.google.android.gms.location.LocationSettingsResponse;
import com.google.android.gms.location.LocationSettingsStatusCodes;
import com.google.android.gms.location.SettingsClient;
import com.google.android.gms.tasks.OnSuccessListener;
import com.google.android.material.snackbar.Snackbar;

import org.blagodarie.databinding.MainActivityBinding;
import org.blagodarie.server.ServerDataSource;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.Locale;

import io.reactivex.Completable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.functions.Action;
import io.reactivex.schedulers.Schedulers;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class MainActivity
        extends AppCompatActivity {

    /**
     * Идентификатор запуска диалога включения определения местоположения.
     */
    private static final int REQUEST_CHECK_SETTINGS = 1;

    /**
     * Идентификатор запроса на разрешение использования определения местоположения.
     */
    private static final int PERM_REQ_ACCESS_COARSE_LOCATION = 1;

    /**
     * Желаемый интервал для обновления местоположения. Неточный. Обновления могут быть более или
     * менее частыми.
     */
    private static final long UPDATE_INTERVAL_IN_MILLISECONDS = 10000L;

    /**
     * Самый быстрый показатель для активных обновлений местоположения. Обновления никогда не будут
     * более частыми, чем это значение.
     */
    private static final long FASTEST_UPDATE_INTERVAL_IN_MILLISECONDS = UPDATE_INTERVAL_IN_MILLISECONDS / 2;

    private Long mUserId;

    private boolean mPermissionDeniedExplanationShowed = false;

    /**
     * Предоставляет доступ к Fused Location Provider API.
     *
     * @link https://developers.google.com/location-context/fused-location-provider
     */
    private FusedLocationProviderClient mFusedLocationClient;

    /**
     * Предоставляет доступ к локальным настройкам API.
     */
    private SettingsClient mSettingsClient;

    /**
     * Хранит параметры для запроса к FusedLocationProviderApi.
     */
    private LocationRequest mLocationRequest;

    /**
     * Хранит типы сервисов определения местоположения, которыми заинтересован клиент. Используется
     * для проверки настроек, чтобы определить, имеет ли устройство оптимальные настройки
     * местоположения.
     */
    private LocationSettingsRequest mLocationSettingsRequest;

    /**
     * Колбэк для событий определения местоположения.
     */
    private LocationCallback mLocationCallback;

    /**
     * Текущее местоположение.
     */
    private Location mCurrentLocation;

    private MainViewModel mViewModel;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        initUserId();

        mViewModel = new ViewModelProvider(this).get(MainViewModel.class);

        final SymptomsAdapter symptomsAdapter = new SymptomsAdapter(new ArrayList<>(mViewModel.getSymptoms()), this::createUserSymptom);

        final MainActivityBinding mainActivityBinding = DataBindingUtil.setContentView(this, R.layout.main_activity);
        mainActivityBinding.setViewModel(mViewModel);
        mainActivityBinding.rvSymptoms.setAdapter(symptomsAdapter);

        mFusedLocationClient = LocationServices.getFusedLocationProviderClient(this);
        mSettingsClient = LocationServices.getSettingsClient(this);
        createLocationCallback();
        createLocationRequest();
        buildLocationSettingsRequest();
    }

    @Override
    public void onResume () {
        super.onResume();
        if (checkAccessFineLocationPermission()) {
            startGetLastLocation();
            startLocationUpdates();
        } else {
            requestPermissions();
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

        Double latitude = null;
        Double longitude = null;
        if (mCurrentLocation != null) {
            latitude = mCurrentLocation.getLatitude();
            longitude = mCurrentLocation.getLongitude();

            displaySymptom.getLastLatitude().set(latitude);
            displaySymptom.getLastLongitude().set(longitude);
        }
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

    private void createLocationRequest () {
        mLocationRequest = new LocationRequest();
        mLocationRequest.setInterval(UPDATE_INTERVAL_IN_MILLISECONDS);
        mLocationRequest.setFastestInterval(FASTEST_UPDATE_INTERVAL_IN_MILLISECONDS);
        mLocationRequest.setPriority(LocationRequest.PRIORITY_BALANCED_POWER_ACCURACY);
    }

    private void createLocationCallback () {
        mLocationCallback = new LocationCallback() {
            @Override
            public void onLocationResult (LocationResult locationResult) {
                super.onLocationResult(locationResult);

                mCurrentLocation = locationResult.getLastLocation();
                mViewModel.mCurrentLatitude.set(mCurrentLocation.getLatitude());
                mViewModel.mCurrentLongitude.set(mCurrentLocation.getLongitude());
            }
        };
    }

    private void buildLocationSettingsRequest () {
        LocationSettingsRequest.Builder builder = new LocationSettingsRequest.Builder();
        builder.addLocationRequest(mLocationRequest);
        mLocationSettingsRequest = builder.build();
    }

    private void startLocationUpdates () {
        mSettingsClient.checkLocationSettings(mLocationSettingsRequest)
                .addOnSuccessListener(this, this::onSuccess)
                .addOnFailureListener(this, e -> {
                    int statusCode = ((ApiException) e).getStatusCode();
                    switch (statusCode) {

                        case LocationSettingsStatusCodes.RESOLUTION_REQUIRED:
                            showSnackbar(R.string.location_disabled, R.string.location_enable, v -> {

                                try {
                                    ResolvableApiException rae = (ResolvableApiException) e;
                                    rae.startResolutionForResult(MainActivity.this, REQUEST_CHECK_SETTINGS);
                                } catch (IntentSender.SendIntentException sie) {
                                }
                            });
                            break;
                        case LocationSettingsStatusCodes.SETTINGS_CHANGE_UNAVAILABLE:
                            String errorMessage = "Location settings are inadequate, and cannot be " +
                                    "fixed here. Fix in Settings.";
                            Toast.makeText(MainActivity.this, errorMessage, Toast.LENGTH_LONG).show();
                    }
                });
    }

    private void stopLocationUpdates () {
        mFusedLocationClient.removeLocationUpdates(mLocationCallback);
    }

    private void showSnackbar (final int mainTextStringId, final int actionStringId, View.OnClickListener listener) {
        Snackbar.make(
                findViewById(android.R.id.content),
                getString(mainTextStringId),
                Snackbar.LENGTH_INDEFINITE)
                .setAction(getString(actionStringId), listener).show();
    }

    private boolean checkAccessFineLocationPermission () {
        return ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void requestPermissions () {
        boolean shouldProvideRationale = ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.ACCESS_COARSE_LOCATION);
        if (shouldProvideRationale) {
            mPermissionDeniedExplanationShowed = false;
            showSnackbar(
                    R.string.permission_rationale,
                    android.R.string.ok,
                    view -> ActivityCompat.requestPermissions(MainActivity.this,
                            new String[]{Manifest.permission.ACCESS_COARSE_LOCATION},
                            PERM_REQ_ACCESS_COARSE_LOCATION));
        } else {
            if (!mPermissionDeniedExplanationShowed) {
                ActivityCompat.requestPermissions(MainActivity.this,
                        new String[]{Manifest.permission.ACCESS_COARSE_LOCATION},
                        PERM_REQ_ACCESS_COARSE_LOCATION);
            }
        }
    }

    @Override
    public void onRequestPermissionsResult (final int requestCode, @NonNull final String[] permissions, @NonNull final int[] grantResults) {
        if (requestCode == PERM_REQ_ACCESS_COARSE_LOCATION) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startLocationUpdates();
            } else {
                if (!mPermissionDeniedExplanationShowed) {
                    showSnackbar(
                            R.string.permission_denied_explanation,
                            R.string.settings,
                            view -> {
                                mPermissionDeniedExplanationShowed = false;
                                Intent intent = new Intent();
                                intent.setAction(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                                Uri uri = Uri.fromParts("package", BuildConfig.APPLICATION_ID, null);
                                intent.setData(uri);
                                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                                startActivity(intent);
                            }
                    );
                    mPermissionDeniedExplanationShowed = true;
                }
            }
        }
    }

    private void startGetLastLocation () {
        mFusedLocationClient.getLastLocation().addOnSuccessListener(location -> {
            if (mCurrentLocation == null && location != null) {
                mCurrentLocation = location;
                mViewModel.mCurrentLatitude.set(mCurrentLocation.getLatitude());
                mViewModel.mCurrentLongitude.set(mCurrentLocation.getLongitude());
            }
        });
    }

    private void onSuccess (LocationSettingsResponse locationSettingsResponse) {
        mFusedLocationClient.requestLocationUpdates(mLocationRequest,
                mLocationCallback, Looper.myLooper());
    }
}
