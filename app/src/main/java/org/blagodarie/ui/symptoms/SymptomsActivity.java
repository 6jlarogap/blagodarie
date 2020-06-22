package org.blagodarie.ui.symptoms;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.accounts.AuthenticatorException;
import android.accounts.OperationCanceledException;
import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.Uri;
import android.os.Bundle;
import android.text.Spannable;
import android.text.SpannableString;
import android.text.style.UnderlineSpan;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.ActionBar;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.GravityCompat;
import androidx.databinding.DataBindingUtil;
import androidx.drawerlayout.widget.DrawerLayout;
import androidx.lifecycle.ViewModelProvider;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import org.blagodarie.BlagodarieApp;
import org.blagodarie.BuildConfig;
import org.blagodarie.R;
import org.blagodarie.Repository;
import org.blagodarie.UnauthorizedException;
import org.blagodarie.authentication.AccountGeneral;
import org.blagodarie.authentication.IncognitoSignUpFragment;
import org.blagodarie.databinding.NavHeaderBinding;
import org.blagodarie.databinding.SymptomsActivityBinding;
import org.blagodarie.server.ServerConnector;
import org.blagodarie.sync.SyncService;
import org.blagodarie.ui.update.UpdateActivity;
import org.blagodatie.database.Identifier;
import org.blagodatie.database.Symptom;
import org.blagodatie.database.SymptomGroupWithSymptoms;
import org.blagodatie.database.UserSymptom;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

import io.reactivex.Completable;
import io.reactivex.CompletableObserver;
import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.disposables.Disposable;
import io.reactivex.schedulers.Schedulers;

import static org.blagodarie.log.LogActivity.ACTION_SEND_LOG;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SymptomsActivity
        extends AppCompatActivity {

    private static final String TAG = SymptomsActivity.class.getSimpleName();

    private static final String NEW_VERSION_NOTIFICATION_PREFERENCE = "org.blagodarie.ui.update.preference.newVersionNotification";

    private static final String EXTRA_ACCOUNT = "org.blagodarie.ui.symptoms.ACCOUNT";

    private Account mAccount;

    private UUID mIncognitoPrivateKey;

    private UUID mIncognitoPublicKey;

    private Long mIncognitoPublicKeyTimestamp;

    private SymptomsViewModel mViewModel;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    private SymptomGroupsAdapter mSymptomGroupsAdapter;

    private SymptomsAdapter mSymptomsAdapter;

    private SymptomsActivityBinding mActivityBinding;

    private Repository mRepository;

    private AccountManager mAccountManager;

    /**
     * Боковое меню.
     */
    private DrawerLayout mDrawerLayout;

    private final BroadcastReceiver mSyncErrorReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive (
                final Context context,
                final Intent intent
        ) {
            final Throwable throwable = (Throwable) intent.getSerializableExtra(SyncService.EXTRA_EXCEPTION);
            if (throwable == null) {
                mViewModel.isShowNoServerConnectionErrMsg().set(false);
            } else {
                mViewModel.isShowNoServerConnectionErrMsg().set(false);
                if (throwable instanceof UnauthorizedException) {
                    Toast.makeText(getApplicationContext(), R.string.txt_authorization_required, Toast.LENGTH_LONG).show();
                    getAuthTokenAndRequestSync();
                } else {
                    mViewModel.isShowNoServerConnectionErrMsg().set(true);
                    String message = getString(R.string.err_msg_no_internet_connection);
                    if (BuildConfig.DEBUG) {
                        message = throwable.getLocalizedMessage();
                    }
                    Toast.makeText(getApplicationContext(), message, Toast.LENGTH_LONG).show();
                }
            }
        }
    };

    @Override
    protected void onCreate (@Nullable final Bundle savedInstanceState) {
        Log.d(TAG, "onCreate");
        super.onCreate(savedInstanceState);

        registerReceiver(mSyncErrorReceiver, new IntentFilter(SyncService.ACTION_SYNC_EXCEPTION));

        //попытаться инициализировать данные пользователя
        final String initUserDataErrorMessage = tryInitUserData();
        //если ошибок нет
        if (initUserDataErrorMessage == null) {
            mRepository = Repository.getInstance(this);
            mAccountManager = AccountManager.get(this);

            initViewModel();

            initBinding();

            setupNavigationDrawer();

            setupToolbar();

            mRepository.getSymptomGroupsWithSymptoms().observe(
                    this,
                    this::updateSymptomCatalogIfNeed
            );
        } else {
            //иначе показать сообщение об ошибке и завершить Activity
            Toast.makeText(this, initUserDataErrorMessage, Toast.LENGTH_SHORT).show();
            finish();
        }
    }

    private void setupNavigationDrawer () {
        Log.d(TAG, "setupNavigationDrawer");
        mDrawerLayout = findViewById(R.id.drawer_layout);
        mDrawerLayout.setStatusBarBackground(R.color.colorPrimaryDark);

        NavHeaderBinding binding = DataBindingUtil.inflate(getLayoutInflater(), R.layout.nav_header, null, false);
        binding.setViewModel(mViewModel);
        mActivityBinding.nvNavigation.addHeaderView(binding.getRoot());

        mActivityBinding.nvNavigation.setNavigationItemSelectedListener(menuItem -> {
            switch (menuItem.getItemId()) {
                case R.id.miShowIncognitoPrivateKey:
                    showIncognitoPrivateKeyDialog();
                    break;
                case R.id.miUpdateIncognitoPublicKey:
                    updateIncognitoPublicKey();
                    break;
            }
            mDrawerLayout.closeDrawers();
            return true;
        });
    }

    private void updateSymptomCatalogIfNeed (
            @Nullable final List<SymptomGroupWithSymptoms> newSymptomCatalog
    ) {
        Log.d(TAG, "updateSymptomCatalogIfNeed");
        if (newSymptomCatalog != null) {
            if (!mViewModel.getSymptomCatalog().equals(newSymptomCatalog)) {
                mViewModel.setSymptomCatalog(newSymptomCatalog);
                //создать отображаемые группы
                final List<DisplaySymptomGroup> newDisplaySymptomGroups = createDisplaySymptomGroups(newSymptomCatalog);

                //запомнить идентификатор выбранной группы
                final Identifier selectedGroupId = mViewModel.getSelectedSymptomGroupId();

                //задать новые данные
                mViewModel.setDisplaySymptomGroups(newDisplaySymptomGroups);

                //загрузить последние пользовательские данные о симптомах
                mViewModel.loadLastValues(mIncognitoPrivateKey, () -> {
                    orderSymptomCatalog();
                    //восстановить выбранную группу
                    if (mViewModel.getDisplaySymptomGroups().size() > 0) {
                        //по-умолчанию выделить первую группу
                        int selectedGroupIndex = 0;

                        //если существует идентификатор выбранной группы
                        if (selectedGroupId != null) {
                            //найти группу с выбранным идентификатором в новом списке
                            for (int i = 0; i < mViewModel.getDisplaySymptomGroups().size() && selectedGroupIndex == 0; i++) {
                                if (mViewModel.getDisplaySymptomGroups().get(i).getSymptomGroupId().equals(selectedGroupId)) {
                                    selectedGroupIndex = i;
                                }
                            }
                        }

                        //показать симптомы для выбранной группы
                        showSymptomsForGroup(mViewModel.getDisplaySymptomGroups().get(selectedGroupIndex));
                    }
                });
            }
        }
    }

    private void initViewModel () {
        Log.d(TAG, "initViewModel");

        //создаем фабрику
        final SymptomsViewModel.Factory factory = new SymptomsViewModel.Factory(
                getApplication(),
                mIncognitoPublicKey.toString()
        );

        //создаем UpdateViewModel
        mViewModel = new ViewModelProvider(this, factory).get(SymptomsViewModel.class);

    }

    private void initBinding () {
        mActivityBinding = DataBindingUtil.setContentView(this, R.layout.symptoms_activity);
        mActivityBinding.setViewModel(mViewModel);
        mActivityBinding.rvSymptomGroups.setLayoutManager(new LinearLayoutManager(this, RecyclerView.HORIZONTAL, false));
    }

    @Override
    public void onResume () {
        Log.d(TAG, "onResume");
        super.onResume();
        checkLatestVersion();
        getAuthTokenAndRequestSync();

        orderSymptomCatalog();
    }

    private void orderSymptomCatalog () {
        orderSymptomGroups();
        orderSymptoms();
    }

    private void orderSymptomGroups () {
        mViewModel.orderDisplaySymptomGroups();
        if (mSymptomGroupsAdapter != null) {
            mSymptomGroupsAdapter.setData(mViewModel.getDisplaySymptomGroups());
        }
        if (mActivityBinding.rvSymptomGroups.getLayoutManager() != null) {
            mActivityBinding.rvSymptomGroups.getLayoutManager().scrollToPosition(0);
        }
    }

    private void orderSymptoms () {
        mViewModel.orderDisplaySymptoms();
        if (mSymptomsAdapter != null) {
            mSymptomsAdapter.setData(mViewModel.getDisplaySymptoms());
        }
        if (mActivityBinding.rvSymptoms.getLayoutManager() != null) {
            mActivityBinding.rvSymptoms.getLayoutManager().scrollToPosition(0);
        }
    }

    @Override
    protected void onPause () {
        Log.d(TAG, "onPause");
        super.onPause();
    }

    @Override
    protected void onStop () {
        Log.d(TAG, "onStop");
        super.onStop();
    }

    @Override
    protected void onDestroy () {
        Log.d(TAG, "onDestroy");
        unregisterReceiver(mSyncErrorReceiver);
        super.onDestroy();
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
            displaySymptoms.add(
                    new DisplaySymptom(
                            symptom,
                            mRepository.isHaveNotSyncedUserSymptoms(mIncognitoPrivateKey, symptom.getId()),
                            mRepository.getLatestUserSymptom(mIncognitoPrivateKey, symptom.getId()),
                            new DisplaySymptom.UnconfirmedUserSymptomListener() {
                                @Override
                                public void onConfirm (@NonNull final DisplaySymptom displaySymptom) {
                                    updateLastUserSymptom(displaySymptom);
                                    getAuthTokenAndRequestSync();
                                }

                                @Override
                                public void onCancel (@NonNull final UserSymptom canceledUserSymptom) {
                                    deleteNotConfirmedUserSymptom(canceledUserSymptom);
                                }
                            }
                    )
            );
        }
        return displaySymptoms;
    }

    private void setupToolbar () {
        Log.d(TAG, "setupToolbar");
        setSupportActionBar(findViewById(R.id.toolbar));
        final ActionBar actionBar = getSupportActionBar();
        if (actionBar != null) {
            final String title = getString(R.string.toolbar_title);
            final SpannableString spannableTitle = new SpannableString(title + " " + BuildConfig.VERSION_NAME);
            spannableTitle.setSpan(new UnderlineSpan(), 0, title.length(), Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
            actionBar.setTitle(null);
            final TextView tvTitle = findViewById(R.id.tvTitle);
            tvTitle.setText(spannableTitle);
            actionBar.setHomeAsUpIndicator(R.drawable.ic_menu);
            actionBar.setDisplayHomeAsUpEnabled(true);
        }
    }

    @Override
    public boolean onOptionsItemSelected (final MenuItem item) {
        Log.d(TAG, "onOptionsItemSelected item=" + item);
        switch (item.getItemId()) {
            case android.R.id.home:
                mDrawerLayout.openDrawer(GravityCompat.START);
                return true;
            case R.id.miShowIncognitoPrivateKey:
                mDrawerLayout.openDrawer(GravityCompat.START);
                return true;
        }
        return super.onOptionsItemSelected(item);
    }

    /**
     * Инициализирует данные о пользователе.
     */
    @Nullable
    private String tryInitUserData () {
        Log.d(TAG, "tryInitUserData");
        String errorMessage = null;
        //если аккаунт передан
        if (getIntent().hasExtra(EXTRA_ACCOUNT)) {
            //получить аккаунт
            mAccount = getIntent().getParcelableExtra(EXTRA_ACCOUNT);
            Log.d(TAG, "account=" + mAccount);

            //получить приватный анонимный ключ
            final String incognitoPrivateKey = AccountManager.get(this).getUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PRIVATE_KEY);
            //если приватный анонимный ключ существует
            if (incognitoPrivateKey != null) {
                //попытаться преобразовать строку в UUID
                try {
                    mIncognitoPrivateKey = UUID.fromString(incognitoPrivateKey);
                } catch (IllegalArgumentException e) {
                    errorMessage = getString(R.string.err_msg_incorrect_incognito_private_key) + e.getLocalizedMessage();
                }
            } else {
                //иначе установить сообщение об ошибке
                errorMessage = getString(R.string.err_msg_incognito_private_key_is_missing);
            }

            //получить публичный анонимный ключ
            final String incognitoPublicKey = AccountManager.get(this).getUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY);
            //если публичный анонимный ключ существует
            if (incognitoPublicKey != null) {
                //попытаться преобразовать строку в UUID
                try {
                    mIncognitoPublicKey = UUID.fromString(incognitoPublicKey);
                } catch (IllegalArgumentException e) {
                    errorMessage = getString(R.string.err_msg_incorrect_incognito_public_key) + e.getLocalizedMessage();
                }
            } else {
                //иначе обновить публичный ключ
                updateIncognitoPublicKey();
            }

            final String incognitoPublicKeyTimestamp = AccountManager.get(this).getUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY_TIMESTAMP);
            mIncognitoPublicKeyTimestamp = incognitoPublicKeyTimestamp != null ? Long.parseLong(incognitoPublicKeyTimestamp) : 0L;
        } else {
            //иначе установить сообщение об ошибке
            errorMessage = getString(R.string.err_msg_account_not_set);
        }
        return errorMessage;
    }

    public void showSymptomsForGroup (
            @NonNull final DisplaySymptomGroup displaySymptomGroup
    ) {
        mViewModel.setSelectedDisplaySymptomGroup(displaySymptomGroup);
        mViewModel.setDisplaySymptoms(displaySymptomGroup.getDisplaySymptoms());

        if (mSymptomGroupsAdapter == null) {
            mSymptomGroupsAdapter = new SymptomGroupsAdapter(mViewModel.getDisplaySymptomGroups(), this::showSymptomsForGroup);
            mActivityBinding.rvSymptomGroups.setAdapter(mSymptomGroupsAdapter);
        } else {
            mSymptomGroupsAdapter.setData(mViewModel.getDisplaySymptomGroups());
        }
        if (mSymptomsAdapter == null) {
            mSymptomsAdapter = new SymptomsAdapter(mViewModel.getDisplaySymptoms(), this::createUserSymptom);
            mActivityBinding.rvSymptoms.setAdapter(mSymptomsAdapter);
        } else {
            mSymptomsAdapter.setData(mViewModel.getDisplaySymptoms());
        }

        orderSymptoms();
    }

    public void createUserSymptom (
            @NonNull final DisplaySymptom displaySymptom
    ) {
        Log.d(TAG, "createUserSymptom displaySymptom" + displaySymptom);
        displaySymptom.highlight();
        final Date currentDate = new Date();

        final UserSymptom userSymptom = new UserSymptom(
                mIncognitoPrivateKey,
                displaySymptom.getSymptomId(),
                currentDate,
                null,
                null);

        Completable.
                fromAction(() -> mRepository.insertUserSymptomAndSetId(userSymptom)).
                subscribeOn(Schedulers.io()).
                observeOn(AndroidSchedulers.mainThread()).
                subscribe();
    }

    private void deleteNotConfirmedUserSymptom (
            @NonNull final UserSymptom canceledUserSymptom
    ) {
        Log.d(TAG, "deleteNotConfirmedUserSymptom canceledUserSymptom=" + canceledUserSymptom);
        Completable.
                fromAction(() -> mRepository.deleteUserSymptom(canceledUserSymptom)).
                subscribeOn(Schedulers.io()).
                observeOn(AndroidSchedulers.mainThread()).
                subscribe();
    }

    private void updateLastUserSymptom (
            @NonNull final DisplaySymptom displaySymptom
    ) {
        Log.d(TAG, "updateLastUserSymptom displaySymptom=" + displaySymptom);
        final UserSymptom userSymptom = displaySymptom.getNotConfirmedUserSymptom();
        if (userSymptom != null) {
            Completable.
                    fromAction(() -> mRepository.updateLastUserSymptom(userSymptom)).
                    subscribeOn(Schedulers.io()).
                    observeOn(AndroidSchedulers.mainThread()).
                    subscribe(new CompletableObserver() {
                        @Override
                        public void onSubscribe (Disposable d) {

                        }

                        @Override
                        public void onComplete () {
                            displaySymptom.setLastDate(userSymptom.getTimestamp());
                            displaySymptom.setUserSymptomCount(displaySymptom.getUserSymptomCount() + 1);
                        }

                        @Override
                        public void onError (Throwable e) {

                        }
                    });
        }
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
                            BlagodarieApp.requestSync(mAccount, authToken, getString(R.string.content_provider_authorities));
                        }
                    } catch (AuthenticatorException | IOException | OperationCanceledException e) {
                        e.printStackTrace();
                    }
                },
                null
        );
    }

    public void onLinkClick (final View view) {
        Log.d(TAG, "onLinkClick");
        openWebsite();
    }

    private void updateIncognitoPublicKey () {
        Log.d(TAG, "updateIncognitoPublicKey");
        mIncognitoPublicKey = UUID.randomUUID();
        mIncognitoPublicKeyTimestamp = System.currentTimeMillis() / 1000L;
        final ServerConnector serverConnector = new ServerConnector(this);
        final IncognitoSignUpFragment.IncognitoSignUpExecutor signUpExecutor = new IncognitoSignUpFragment.IncognitoSignUpExecutor(mIncognitoPrivateKey.toString(), mIncognitoPublicKey.toString());
        mDisposables.add(
                Observable.
                        fromCallable(() -> signUpExecutor.execute(serverConnector)).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                apiResult -> {
                                    mViewModel.isShowNoServerConnectionErrMsg().set(false);
                                    mAccountManager.setUserData(mAccount, AccountGeneral.USER_DATA_USER_ID, apiResult.getUserId().toString());
                                    mAccountManager.setUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY, mIncognitoPublicKey.toString());
                                    mAccountManager.setUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY_TIMESTAMP, mIncognitoPublicKeyTimestamp.toString());
                                    mViewModel.getIncognitoPublicKey().set(mIncognitoPublicKey.toString());
                                    Toast.makeText(this, R.string.incognito_public_key_updated, Toast.LENGTH_LONG).show();
                                },
                                throwable -> {
                                    mViewModel.isShowNoServerConnectionErrMsg().set(true);
                                    Log.e(TAG, "updateIncognitoPublicKey error=" + throwable);
                                    Toast.makeText(this, throwable.getMessage(), Toast.LENGTH_LONG).show();
                                }
                        )
        );
    }

    private void openWebsite () {
        Log.d(TAG, "openWebsite");
        final Intent i = new Intent(Intent.ACTION_VIEW);
        i.setData(Uri.parse(String.format(getString(R.string.website_url), mIncognitoPublicKey.toString())));
        startActivity(i);
    }

    public void showLog (final View view) {
        Log.d(TAG, "showLog");

        final Intent intent = new Intent();
        intent.setAction(ACTION_SEND_LOG);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
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

    public void showIncognitoPrivateKeyDialog () {
        Log.d(TAG, "showIncognitoPrivateKeyDialog");
        new AlertDialog.Builder(this).
                setTitle(R.string.incognito_private_key).
                setMessage(String.format(getString(R.string.txt_incognito_private_key), mIncognitoPrivateKey.toString())).
                setNegativeButton(
                        R.string.btn_copy,
                        (dialog, which) -> {
                            final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                            final ClipData clip = ClipData.newPlainText(getString(R.string.txt_log), mIncognitoPrivateKey.toString());
                            if (clipboard != null) {
                                clipboard.setPrimaryClip(clip);
                                Toast.makeText(this, R.string.copied_to_clipboard, Toast.LENGTH_SHORT).show();
                            }
                        }).
                setPositiveButton(
                        R.string.btn_cancel,
                        null).
                create().
                show();
    }

    private void checkLatestVersion () {
        Log.d(TAG, "checkLatestVersion");
        final ServerConnector serverConnector = new ServerConnector(this);
        final GetLatestVersionExecutor getLatestVersionExecutor = new GetLatestVersionExecutor(mIncognitoPrivateKey);
        mDisposables.add(
                Observable.
                        fromCallable(() -> getLatestVersionExecutor.execute(serverConnector)).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                apiResult -> {
                                    mViewModel.isShowNoServerConnectionErrMsg().set(false);
                                    if (apiResult.getIncognitoPublicKeyTimestamp() >= mIncognitoPublicKeyTimestamp) {
                                        mIncognitoPublicKey = apiResult.getIncognitoPublicKey();
                                        mIncognitoPublicKeyTimestamp = apiResult.getIncognitoPublicKeyTimestamp();
                                        mViewModel.getIncognitoPublicKey().set(mIncognitoPublicKey.toString());
                                        mAccountManager.setUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY, mIncognitoPublicKey.toString());
                                        mAccountManager.setUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY_TIMESTAMP, mIncognitoPublicKeyTimestamp.toString());
                                    }
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
                                    mViewModel.isShowNoServerConnectionErrMsg().set(true);
                                    Log.e(TAG, "checkLatestVersion error=" + throwable);
                                    Toast.makeText(this, R.string.err_msg_server_connection, Toast.LENGTH_LONG).show();
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
