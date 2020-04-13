package org.blagodarie;

import android.Manifest;
import android.accounts.Account;
import android.accounts.AccountManager;
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
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.databinding.DataBindingUtil;
import androidx.lifecycle.ViewModelProvider;

import org.blagodarie.databinding.MainActivityBinding;
import org.blagodarie.server.ServerApiExecutor;
import org.blagodarie.server.ServerConnector;
import org.json.JSONException;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.Locale;
import java.util.Random;

import io.reactivex.Completable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static org.blagodarie.server.ServerConnector.JSON_TYPE;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class MainActivity
        extends AppCompatActivity
        implements LocationListener {

    private static final class AddUserSymptomExecutor
            implements ServerApiExecutor<AddUserSymptomExecutor.ApiResult> {

        private static final class ApiResult
                extends ServerApiExecutor.ApiResult {

        }

        @NonNull
        private final Long mUserId;

        @NonNull
        private final Collection<UserSymptom> mUserSymptoms = new ArrayList<>();

        private AddUserSymptomExecutor (
                @NonNull final Long userId,
                @NonNull final Collection<UserSymptom> userSymptoms
        ) {
            mUserId = userId;
            mUserSymptoms.addAll(userSymptoms);
        }

        private String createJsonContent () {
            final StringBuilder content = new StringBuilder();
            content.append(String.format(Locale.ENGLISH, "{\"user_id\":%d,\"user_symptoms\":[", mUserId));

            boolean isFirst = true;
            for (UserSymptom userSymptom : mUserSymptoms) {
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

        @Override
        public ApiResult execute (
                @NonNull final String apiBaseUrl,
                @NonNull final OkHttpClient okHttpClient
        ) throws JSONException, IOException, ForbiddenException {
            final RequestBody body = RequestBody.create(createJsonContent(), JSON_TYPE);
            final Request request = new Request.Builder()
                    .url(apiBaseUrl + "addusersymptom")
                    .post(body)
                    .build();
            final Response response = okHttpClient.newCall(request).execute();
            if (response.code() == 200) {
                if (response.body() != null) {
                    final String responseBody = response.body().string();
                    boolean a = responseBody.isEmpty();
                }
            } else if (response.code() == 403) {
                throw new ForbiddenException();
            }
            return new ApiResult();
        }


    }

    private static final String EXTRA_ACCOUNT = "org.blagodarie.ACCOUNT";

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

    private MainViewModel mViewModel;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    private AccountManager mAccountManager;

    private LocationManager mLocationManager;

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        mAccountManager = AccountManager.get(this);

        initAccount();

        mViewModel = new ViewModelProvider(this).get(MainViewModel.class);

        final SymptomsAdapter symptomsAdapter = new SymptomsAdapter(new ArrayList<>(mViewModel.getSymptoms()), this::createUserSymptom);

        final MainActivityBinding mainActivityBinding = DataBindingUtil.setContentView(this, R.layout.main_activity);
        mainActivityBinding.setViewModel(mViewModel);
        mainActivityBinding.rvSymptoms.setAdapter(symptomsAdapter);

        setupToolbar();

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
        displaySymptom.getLastAdd().set(new Date(timestamp));

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

        getAuthTokenAndSendUserSymptomOnServer(displaySymptom, userSymptom);
    }

    private void sendUserSymptomOnServer (
            @NonNull final String authToken,
            @NonNull final DisplaySymptom displaySymptom,
            @NonNull final UserSymptom userSymptom
    ) {
        final Collection<UserSymptom> userSymptoms = new ArrayList<>();
        userSymptoms.add(userSymptom);
        final ServerConnector serverConnector = new ServerConnector(this);
        final AddUserSymptomExecutor addUserSymptomExecutor = new AddUserSymptomExecutor(Long.valueOf(mAccount.name), userSymptoms);
        mDisposables.add(
                Completable.
                        fromAction(() -> {
                            displaySymptom.getInLoadProgress().set(true);
                            serverConnector.execute(addUserSymptomExecutor);
                        }).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(() -> {
                                    displaySymptom.getInLoadProgress().set(false);
                                    displaySymptom.highlight();
                                },
                                throwable -> {
                                    if (throwable instanceof ForbiddenException) {
                                        final AccountManager accountManager = AccountManager.get(this);
                                        accountManager.invalidateAuthToken(getString(R.string.account_type), authToken);
                                        getAuthTokenAndSendUserSymptomOnServer(displaySymptom, userSymptom);
                                    }
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


    private void getAuthTokenAndSendUserSymptomOnServer (
            @NonNull final DisplaySymptom displaySymptom,
            @NonNull final UserSymptom userSymptom
    ) {
        mAccountManager.getAuthToken(
                mAccount,
                getString(R.string.token_type),
                null,
                this,
                future -> {
                    try {
                        final String authToken = future.getResult().getString((AccountManager.KEY_AUTHTOKEN));
                        sendUserSymptomOnServer(authToken, displaySymptom, userSymptom);
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }, null);
    }

    public static Intent createIntent (
            @NonNull final Context context,
            @NonNull final Account account
    ) {
        final Intent intent = new Intent(context, MainActivity.class);
        intent.putExtra(EXTRA_ACCOUNT, account);
        return intent;
    }
}
