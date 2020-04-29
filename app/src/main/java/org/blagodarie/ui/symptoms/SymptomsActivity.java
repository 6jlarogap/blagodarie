package org.blagodarie.ui.symptoms;

import android.Manifest;
import android.accounts.Account;
import android.accounts.AccountManager;
import android.accounts.AuthenticatorException;
import android.accounts.OperationCanceledException;
import android.annotation.SuppressLint;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.text.Spannable;
import android.text.SpannableString;
import android.text.style.UnderlineSpan;
import android.util.Log;
import android.view.View;
import android.widget.ScrollView;
import android.widget.Toast;

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
import org.blagodarie.Repository;
import org.blagodarie.authentication.AccountGeneral;
import org.blagodarie.databinding.LogDialogBinding;
import org.blagodarie.databinding.SymptomsActivityBinding;
import org.blagodarie.server.ServerConnector;
import org.blagodarie.sync.SyncAdapter;
import org.blagodarie.sync.SyncService;
import org.blagodarie.ui.splash.SplashActivity;
import org.blagodarie.ui.update.UpdateActivity;
import org.blagodatie.database.UserSymptom;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Date;
import java.util.UUID;

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

    private static final String TAG = SymptomsActivity.class.getSimpleName();

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

    private Long mUserId;

    private UUID mIncognitoId;

    private SymptomsViewModel mViewModel;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    private LocationManager mLocationManager;

    private SymptomsAdapter mSymptomsAdapter;

    private SymptomsActivityBinding mActivityBinding;

    private Repository mRepository;

    private AccountManager mAccountManager;

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.d(TAG, "onCreate");

        mRepository = new Repository(this);

        mAccountManager = AccountManager.get(this);

        initUserData();

        initViewModel();

        mSymptomsAdapter = new SymptomsAdapter(new ArrayList<>(mViewModel.getDisplaySymptoms()), this::createUserSymptom);

        mActivityBinding = DataBindingUtil.setContentView(this, R.layout.symptoms_activity);
        mActivityBinding.setViewModel(mViewModel);
        mActivityBinding.rvSymptoms.setAdapter(mSymptomsAdapter);

        setupToolbar();

        mLocationManager = (LocationManager) getSystemService(LOCATION_SERVICE);

        Completable.
                fromAction(() ->
                        mRepository.updateIncognitoId(mUserId, mIncognitoId)
                ).
                subscribeOn(Schedulers.io()).
                subscribe();
    }

    private void initViewModel () {
        Log.d(TAG, "initViewModel");
        //создаем фабрику
        final SymptomsViewModel.Factory factory = new SymptomsViewModel.Factory(getApplication(), mIncognitoId);

        //создаем UpdateViewModel
        mViewModel = new ViewModelProvider(this, factory).get(SymptomsViewModel.class);
    }

    @Override
    public void onResume () {
        super.onResume();
        Log.d(TAG, "onResume");
        checkLatestVersion();
        if (checkLocationPermission()) {
            startLocationUpdates();
        } else {
            attemptRequestLocationPermissions();
        }
        mViewModel.updateUserSymptomCount(
                mIncognitoId,
                () -> {
                    mSymptomsAdapter.order();
                    if (mActivityBinding.rvSymptoms.getLayoutManager() != null) {
                        mActivityBinding.rvSymptoms.getLayoutManager().scrollToPosition(0);
                    }
                });
    }

    @Override
    protected void onPause () {
        super.onPause();
        Log.d(TAG, "onPause");
        stopLocationUpdates();
    }

    @Override
    protected void onDestroy () {
        super.onDestroy();
        Log.d(TAG, "onDestroy");
        mDisposables.dispose();
    }

    private void setupToolbar () {
        Log.d(TAG, "setupToolbar");
        setSupportActionBar(findViewById(R.id.toolbar));
        final ActionBar actionBar = getSupportActionBar();
        if (actionBar != null) {
            final String title = getString(R.string.toolbar_title);
            final SpannableString spannableTitle = new SpannableString(title + " " + BuildConfig.VERSION_NAME + getString(R.string.build_type_label));
            spannableTitle.setSpan(new UnderlineSpan(), 0, title.length(), Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
            actionBar.setTitle(spannableTitle);
        }
    }

    @SuppressLint ("MissingPermission")
    private void startLocationUpdates () {
        Log.d(TAG, "startLocationUpdates");
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
        Log.d(TAG, "stopLocationUpdates");
        mLocationManager.removeUpdates(this);
    }

    private void initUserData () {
        Log.d(TAG, "initUserData");
        mAccount = getIntent().getParcelableExtra(EXTRA_ACCOUNT);
        mUserId = Long.valueOf(mAccount.name);
        String incognitoId = mAccountManager.getUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_ID);
        if (incognitoId == null) {
            incognitoId = UUID.randomUUID().toString();
            mAccountManager.setUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_ID, incognitoId);
        }
        mIncognitoId = UUID.fromString(incognitoId);
    }

    public void createUserSymptom (
            @NonNull final DisplaySymptom displaySymptom
    ) {
        Log.d(TAG, "createUserSymptom displaySymptom" + displaySymptom);
        long timestamp = System.currentTimeMillis();
        displaySymptom.getLastDate().set(new Date(timestamp));

        final Double latitude = mViewModel.getCurrentLatitude().get();
        final Double longitude = mViewModel.getCurrentLongitude().get();

        displaySymptom.getLastLatitude().set(latitude);
        displaySymptom.getLastLongitude().set(longitude);

        final UserSymptom userSymptom = new UserSymptom(
                mIncognitoId,
                displaySymptom.getSymptomId(),
                timestamp,
                latitude,
                longitude);

        mDisposables.add(
                Completable.
                        fromAction(() ->
                                mRepository.insertUserSymptom(userSymptom)
                        ).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(() -> {
                            displaySymptom.isHaveNotSynced().set(true);
                            displaySymptom.highlight();
                            getAuthTokenAndRequestSync();
                        })
        );
    }

    private void getAuthTokenAndRequestSync () {
        mAccountManager.getAuthToken(
                mAccount,
                getString(R.string.token_type),
                null,
                this,
                future -> {
                    try {
                        Bundle bundle = future.getResult();
                        if (bundle != null) {
                            final String authToken = bundle.getString(AccountManager.KEY_AUTHTOKEN);
                            if (authToken != null) {
                                BlagodarieApp.requestSync(mAccount, authToken);
                            }
                        }
                    } catch (AuthenticatorException | IOException | OperationCanceledException e) {
                        e.printStackTrace();
                    }
                },
                null
        );
    }

    private boolean checkLocationPermission () {
        Log.d(TAG, "checkLocationPermission");
        return ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void attemptRequestLocationPermissions () {
        Log.d(TAG, "attemptRequestLocationPermissions");
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
        Log.d(TAG, "onRequestPermissionsResult");
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
        Log.d(TAG, "onLocationPermissionRationaleClick");
        mViewModel.isShowLocationPermissionRationale().set(false);
        requestLocationPermission();
    }

    public void onLocationPermissionDeniedExplanationClick (final View view) {
        Log.d(TAG, "onLocationPermissionDeniedExplanationClick");
        mViewModel.isShowLocationPermissionDeniedExplanation().set(false);
        final Intent intent = new Intent();
        intent.setAction(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
        final Uri uri = Uri.fromParts("package", BuildConfig.APPLICATION_ID, null);
        intent.setData(uri);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
    }

    public void onLinkClick (final View view) {
        Log.d(TAG, "onLinkClick");
        final Intent i = new Intent(Intent.ACTION_VIEW);
        i.setData(Uri.parse(getString(R.string.website_url)));
        startActivity(i);
    }

    public void showLog (final View view) {
        Log.d(TAG, "showLog");
        Process logcat;
        final StringBuilder log = new StringBuilder();
        try {
            logcat = Runtime.getRuntime().exec(new String[]{
                    "logcat",
                    "-d",
                    "-s",
                    "-v long",
                    BlagodarieApp.class.getSimpleName() + ":D",
                    SplashActivity.class.getSimpleName() + ":D",
                    SymptomsActivity.class.getSimpleName() + ":D",
                    AddUserSymptomsExecutor.class.getSimpleName() + ":D",
                    SyncService.class.getSimpleName() + ":D",
                    SyncAdapter.class.getSimpleName() + ":D"
            });
            BufferedReader br = new BufferedReader(new InputStreamReader(logcat.getInputStream()), 4 * 1024);
            String line;
            String separator = System.getProperty("line.separator");
            while ((line = br.readLine()) != null) {
                log.append(line);
                log.append(separator);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        final LogDialogBinding logDialogBinding = LogDialogBinding.inflate(getLayoutInflater(), null, false);
        logDialogBinding.setLog(log.toString());
        //перемотать в конец
        logDialogBinding.svLog.post(() -> logDialogBinding.svLog.fullScroll(ScrollView.FOCUS_DOWN));

        final AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.txt_log);
        builder.setView(logDialogBinding.getRoot());
        builder.setPositiveButton(
                R.string.action_to_clipboard,
                (dialog, which) -> {
                    final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                    final ClipData clip = ClipData.newPlainText(getString(R.string.txt_log), log);
                    clipboard.setPrimaryClip(clip);
                    Toast.makeText(this, R.string.copied_to_clipboard, Toast.LENGTH_SHORT).show();
                });
        builder.setNeutralButton(
                R.string.action_share,
                (dialog, which) -> {
                    final Intent sendIntent = new Intent();
                    sendIntent.setAction(Intent.ACTION_SEND);
                    sendIntent.putExtra(Intent.EXTRA_TEXT, (CharSequence) log);
                    sendIntent.putExtra(Intent.EXTRA_SUBJECT, "Благодарие журнал");
                    sendIntent.setType("text/plain");
                    startActivity(Intent.createChooser(sendIntent, getString(R.string.action_share)));
                });
        builder.create();
        builder.show();
    }

    public void onLocationProvidersDisabledWarningClick (final View view) {
        Log.d(TAG, "onLocationProvidersDisabledWarningClick");
        final Intent viewIntent = new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS);
        startActivity(viewIntent);
    }

    public void requestLocationPermission () {
        Log.d(TAG, "requestLocationPermission");
        ActivityCompat.requestPermissions(SymptomsActivity.this,
                new String[]{Manifest.permission.ACCESS_FINE_LOCATION},
                PERM_REQ_ACCESS_FINE_LOCATION);
    }

    @Override
    public void onLocationChanged (Location location) {
        Log.d(TAG, "onLocationChanged location=" + location);
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
        Log.d(TAG, "onProviderEnabled");
        checkHaveEnabledLocationProvider();
    }

    @Override
    public void onProviderDisabled (String provider) {
        Log.d(TAG, "onProviderDisabled provider=" + provider);
        checkHaveEnabledLocationProvider();
    }

    private void checkHaveEnabledLocationProvider () {
        boolean isHaveEnabledLocationProvider = !(mLocationManager.isProviderEnabled(LocationManager.GPS_PROVIDER) ||
                mLocationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
        );
        Log.d(TAG, "checkHaveEnabledLocationProvider isHaveEnabledLocationProvider=" + isHaveEnabledLocationProvider);
        mViewModel.isShowLocationProvidersDisabledWarning().set(isHaveEnabledLocationProvider);
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
        Log.d(TAG, "showUpdateVersionDialog");
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
        Log.d(TAG, "toUpdate versionName=" + versionName + "; latestVersionUri=" + latestVersionUri);
        startActivity(UpdateActivity.createSelfIntent(this, versionName, latestVersionUri));
        finish();
    }

    public static Intent createSelfIntent (
            @NonNull final Context context,
            @NonNull final Account account
    ) {
        Log.d(TAG, "createSelfIntent account=" + account);
        final Intent intent = new Intent(context, SymptomsActivity.class);
        intent.putExtra(EXTRA_ACCOUNT, account);
        return intent;
    }
}
