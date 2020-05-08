package org.blagodarie.ui.symptoms;

import android.Manifest;
import android.accounts.Account;
import android.accounts.AccountManager;
import android.accounts.AuthenticatorException;
import android.accounts.OperationCanceledException;
import android.annotation.SuppressLint;
import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
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
import androidx.databinding.ObservableBoolean;
import androidx.lifecycle.ViewModelProvider;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import org.blagodarie.BlagodarieApp;
import org.blagodarie.BuildConfig;
import org.blagodarie.LogReader;
import org.blagodarie.R;
import org.blagodarie.Repository;
import org.blagodarie.UnauthorizedException;
import org.blagodarie.authentication.AccountGeneral;
import org.blagodarie.databinding.LogDialogBinding;
import org.blagodarie.databinding.SymptomsActivityBinding;
import org.blagodarie.server.ServerConnector;
import org.blagodarie.sync.SyncService;
import org.blagodarie.ui.update.UpdateActivity;
import org.blagodatie.database.Symptom;
import org.blagodatie.database.SymptomGroupWithSymptoms;
import org.blagodatie.database.UserSymptom;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
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

    private static final String USER_PREFERENCE_PATTERN = "org.blagodarie.ui.symptoms.preference.%s";
    private static final String PREF_LOCATION_ENABLED = "locationEnabled";
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

    private UUID mIncognitoId;

    private SymptomsViewModel mViewModel;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    private LocationManager mLocationManager;

    private SymptomGroupsAdapter mSymptomGroupsAdapter;

    private SymptomsAdapter mSymptomsAdapter;

    private SymptomsActivityBinding mActivityBinding;

    private Repository mRepository;

    private AccountManager mAccountManager;

    private final BroadcastReceiver mSyncErrorReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive (
                final Context context,
                final Intent intent
        ) {
            final Throwable throwable = (Throwable) intent.getSerializableExtra(SyncService.EXTRA_EXCEPTION);
            if (throwable instanceof UnauthorizedException) {
                Toast.makeText(getApplicationContext(), R.string.txt_authorization_required, Toast.LENGTH_LONG).show();
                getAuthTokenAndRequestSync();
            } else {
                Toast.makeText(getApplicationContext(), throwable.getLocalizedMessage(), Toast.LENGTH_LONG).show();
            }
        }
    };

    @Override
    protected void onCreate (@Nullable final Bundle savedInstanceState) {
        Log.d(TAG, "onCreate");
        super.onCreate(savedInstanceState);

        //попытаться инициализировать данные пользователя
        final String initUserDataErrorMessage = tryInitUserData();
        //если ошибок нет
        if (initUserDataErrorMessage == null) {
            mRepository = new Repository(this);
            mAccountManager = AccountManager.get(this);
            mLocationManager = (LocationManager) getSystemService(LOCATION_SERVICE);

            initViewModel();
            setupToolbar();

            mSymptomGroupsAdapter = new SymptomGroupsAdapter(mViewModel.getDisplaySymptomGroups(), this::showSymptomsForGroup);
            mSymptomsAdapter = new SymptomsAdapter(mViewModel.getDisplaySymptoms(), this::checkLocationEnabled);

            initBinding();

            //!!!УБРАТЬ КОГДА НА СЕРВЕРЕ У ВСЕХ БУДЕТ user_id = null
            mDisposables.add(
                    Completable.
                            fromAction(() ->
                                    mRepository.setupIncognitoId(mIncognitoId)
                            ).
                            subscribeOn(Schedulers.io()).
                            subscribe(() ->
                                    mViewModel.loadLastValues(mIncognitoId)
                            )
            );
            /////////////////////////////////

            mRepository.getSymptomGroups().observe(
                    this,
                    symptomGroupsWithSymptoms -> {
                        if (symptomGroupsWithSymptoms != null) {
                            final List<DisplaySymptomGroup> newDisplaySymptomsGroup = createDisplaySymptomGroups(symptomGroupsWithSymptoms);
                            if (!newDisplaySymptomsGroup.equals(mViewModel.getDisplaySymptomGroups())) {
                                //запомнить выбранную группу
                                final DisplaySymptomGroup selectedGroup = mViewModel.getSelectedDisplaySymptomGroup();

                                //задать новые данные
                                mViewModel.setDisplaySymptomGroups(createDisplaySymptomGroups(symptomGroupsWithSymptoms));
                                mSymptomGroupsAdapter.setData(mViewModel.getDisplaySymptomGroups());

                                //вернуть выбранную группу
                                if (mViewModel.getDisplaySymptomGroups().size() > 0) {
                                    //если существует выбранная группа, и она присутствует в новом списке
                                    if (selectedGroup != null && mViewModel.getDisplaySymptomGroups().contains(selectedGroup)) {
                                        //выделить ее
                                        showSymptomsForGroup(selectedGroup);
                                    } else {
                                        //иначе выбрать первую
                                        showSymptomsForGroup(mViewModel.getDisplaySymptomGroups().get(0));
                                    }
                                }
                            }
                        }
                    }
            );

            registerReceiver(mSyncErrorReceiver, new IntentFilter(SyncService.ACTION_SYNC_EXCEPTION));
            getAuthTokenAndRequestSync();
        } else {
            //иначе показать сообщение об ошибке и завершить Activity
            Toast.makeText(this, initUserDataErrorMessage, Toast.LENGTH_SHORT).show();
            finish();
        }
    }

    private void initViewModel () {
        Log.d(TAG, "initViewModel");

        final SharedPreferences userSharedPreferences = getSharedPreferences(String.format(USER_PREFERENCE_PATTERN, mAccount.name), MODE_PRIVATE);

        final boolean locationEnable = userSharedPreferences.getBoolean(PREF_LOCATION_ENABLED, false);

        //создаем фабрику
        final SymptomsViewModel.Factory factory = new SymptomsViewModel.Factory(
                getApplication(),
                mIncognitoId,
                locationEnable
        );

        //создаем UpdateViewModel
        mViewModel = new ViewModelProvider(this, factory).get(SymptomsViewModel.class);

        //добавить слушатель включения/выключения местоположения
        mViewModel.isLocationEnabled().addOnPropertyChangedCallback(new androidx.databinding.Observable.OnPropertyChangedCallback() {
            @Override
            public void onPropertyChanged (androidx.databinding.Observable sender, int propertyId) {
                if (sender == mViewModel.isLocationEnabled()) {
                    final boolean newValue = ((ObservableBoolean) sender).get();
                    userSharedPreferences.edit().putBoolean(PREF_LOCATION_ENABLED, newValue).apply();
                    if (newValue) {
                        checkLocationPermissionAndStartUpdates();
                    } else {
                        mViewModel.getCurrentLatitude().set(null);
                        mViewModel.getCurrentLongitude().set(null);
                    }
                }
            }
        });
    }

    private void initBinding () {
        mActivityBinding = DataBindingUtil.setContentView(this, R.layout.symptoms_activity);
        mActivityBinding.setViewModel(mViewModel);
        mActivityBinding.rvSymptoms.setAdapter(mSymptomsAdapter);
        mActivityBinding.rvSymptomGroups.setLayoutManager(new LinearLayoutManager(this, RecyclerView.HORIZONTAL, false));
        mActivityBinding.rvSymptomGroups.setAdapter(mSymptomGroupsAdapter);
    }

    @Override
    public void onResume () {
        Log.d(TAG, "onResume");
        super.onResume();
        checkLatestVersion();
        if (mViewModel.isLocationEnabled().get()) {
            checkLocationPermissionAndStartUpdates();
        }

        mSymptomsAdapter.order();
        if (mActivityBinding.rvSymptoms.getLayoutManager() != null) {
            mActivityBinding.rvSymptoms.getLayoutManager().scrollToPosition(0);
        }
    }

    @Override
    protected void onPause () {
        Log.d(TAG, "onPause");
        super.onPause();
        stopLocationUpdates();
    }

    @Override
    protected void onDestroy () {
        Log.d(TAG, "onDestroy");
        super.onDestroy();
        mDisposables.dispose();
        unregisterReceiver(mSyncErrorReceiver);
    }

    private List<DisplaySymptomGroup> createDisplaySymptomGroups (
            @NonNull final List<SymptomGroupWithSymptoms> symptomGroups
    ) {
        Log.d(TAG, "createDisplaySymptomGroups");
        final List<DisplaySymptomGroup> displaySymptomGroups = new ArrayList<>();
        for (SymptomGroupWithSymptoms symptomGroupWithSymptoms : symptomGroups) {
            displaySymptomGroups.add(
                    new DisplaySymptomGroup(
                            symptomGroupWithSymptoms.getSymptomGroup().getId(),
                            symptomGroupWithSymptoms.getSymptomGroup().getName(),
                            createDisplaySymptoms(symptomGroupWithSymptoms.getSymptoms())
                    )
            );
        }
        return displaySymptomGroups;
    }

    private List<DisplaySymptom> createDisplaySymptoms (
            @NonNull final List<Symptom> symptoms
    ) {
        Log.d(TAG, "createDisplaySymptoms");
        final List<DisplaySymptom> displaySymptoms = new ArrayList<>();
        for (Symptom symptom : symptoms) {
            displaySymptoms.add(new DisplaySymptom(symptom.getId(), symptom.getName(), mRepository.isHaveNotSyncedUserSymptoms(mIncognitoId, symptom.getId())));
        }
        return displaySymptoms;
    }

    private void checkLocationPermissionAndStartUpdates () {
        Log.d(TAG, "checkLocationPermissionAndStartUpdates");
        if (checkLocationPermission()) {
            startLocationUpdates();
        } else {
            attemptRequestLocationPermissions();
        }
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

    /**
     * Инициализирует данные о пользователе.
     */
    @Nullable
    private String tryInitUserData () {
        String errorMessage = null;
        //если аккаунт передан
        if (getIntent().hasExtra(EXTRA_ACCOUNT)) {
            //получить аккаунт
            mAccount = getIntent().getParcelableExtra(EXTRA_ACCOUNT);
            Log.d(TAG, "account=" + mAccount);

            //получить анонимный ключ
            final String incognitoId = AccountManager.get(this).getUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_ID);
            //если анонимного ключа не существует
            if (incognitoId != null) {
                //попытаться преобразовать строку в UUID
                try {
                    mIncognitoId = UUID.fromString(incognitoId);
                } catch (IllegalArgumentException e) {
                    errorMessage = getString(R.string.error_incorrect_incognito_id) + e.getLocalizedMessage();
                }
            } else {
                //установить сообщение об ошибке
                errorMessage = getString(R.string.error_incognito_id_is_missing);
            }
        } else {
            //иначе установить сообщение об ошибке
            errorMessage = getString(R.string.error_account_not_set);
        }
        return errorMessage;
    }

    public void showSymptomsForGroup (
            @NonNull final DisplaySymptomGroup displaySymptomGroup
    ) {
        mViewModel.setSelectedDisplaySymptomGroup(displaySymptomGroup);
        mViewModel.setDisplaySymptoms(displaySymptomGroup.getDisplaySymptoms());
        mSymptomsAdapter.setData(mViewModel.getDisplaySymptoms());
        mSymptomsAdapter.order();
    }

    public void checkLocationEnabled (
            @NonNull final DisplaySymptom displaySymptom
    ) {
        if (mViewModel.isLocationEnabled().get() &&
                (mViewModel.getCurrentLatitude().get() == null ||
                        mViewModel.getCurrentLongitude().get() == null)) {
            showEmptyLocationAlertDialog(displaySymptom);
        } else {
            createUserSymptom(displaySymptom);
        }
    }

    private void showEmptyLocationAlertDialog (
            @NonNull final DisplaySymptom displaySymptom
    ) {
        final AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.empty_location_alert);
        builder.setMessage(R.string.add_symptom_without_location);
        builder.setPositiveButton(
                R.string.action_save_symptom,
                (dialog, which) -> createUserSymptom(displaySymptom));
        builder.setNegativeButton(R.string.action_wait, null);
        builder.create();
        builder.show();
    }

    public void createUserSymptom (
            @NonNull final DisplaySymptom displaySymptom
    ) {
        Log.d(TAG, "createUserSymptom displaySymptom" + displaySymptom);
        Date currentDate = new Date();
        displaySymptom.setLastDate(currentDate);

        final Double latitude = mViewModel.getCurrentLatitude().get();
        final Double longitude = mViewModel.getCurrentLongitude().get();

        displaySymptom.setLastLatitude(latitude);
        displaySymptom.setLastLongitude(longitude);
        displaySymptom.setUserSymptomCount(displaySymptom.getUserSymptomCount() + 1);

        final UserSymptom userSymptom = new UserSymptom(
                mIncognitoId,
                displaySymptom.getSymptomId(),
                currentDate,
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
                            displaySymptom.setHaveNotSynced(true);
                            displaySymptom.highlight();
                            getAuthTokenAndRequestSync();
                        })
        );
    }

    private void getAuthTokenAndRequestSync () {
        Log.d(TAG, "getAuthTokenAndRequestSync");
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
                            BlagodarieApp.requestSync(mAccount, authToken);
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
        String log = LogReader.getLog();

        final LogDialogBinding logDialogBinding = LogDialogBinding.inflate(getLayoutInflater(), null, false);
        logDialogBinding.setLog(log);
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
        Log.d(TAG, "onStatusChanged");
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
                        subscribe(
                                apiResult -> {
                                    if (BuildConfig.VERSION_CODE < apiResult.getVersionCode()) {
                                        showUpdateVersionDialog(apiResult.getVersionName(), apiResult.getUri());
                                    }
                                },
                                throwable -> {
                                    Log.e(TAG, "chechLatestVersion error=" + throwable);
                                    Toast.makeText(this, R.string.error_server_connection, Toast.LENGTH_LONG).show();
                                })
        );
    }

    private void showUpdateVersionDialog (
            @NonNull final String versionName,
            @NonNull final Uri latestVersionUri
    ) {
        Log.d(TAG, "showUpdateVersionDialog");
        new AlertDialog.
                Builder(this).
                setTitle(R.string.txt_update_available).
                setMessage(String.format(getString(R.string.txt_want_load_new_version), versionName)).
                setPositiveButton(R.string.action_update, (dialog, which) -> toUpdate(versionName, latestVersionUri)).
                setNegativeButton(R.string.action_finish, (dialog, which) -> finish()).
                setCancelable(false).
                create().
                show();
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
