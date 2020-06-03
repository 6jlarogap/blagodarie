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
import android.view.View;
import android.widget.ScrollView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.ActionBar;
import androidx.appcompat.app.AlertDialog;
import androidx.databinding.DataBindingUtil;
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
import org.blagodarie.authentication.IncognitoSignUpFragment;
import org.blagodarie.databinding.LogDialogBinding;
import org.blagodarie.databinding.SymptomsActivityBinding;
import org.blagodarie.server.ServerConnector;
import org.blagodarie.sync.SyncService;
import org.blagodarie.ui.update.UpdatingActivity;
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

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SymptomsActivity
        extends UpdatingActivity {

    private static final String TAG = SymptomsActivity.class.getSimpleName();

    private static final String EXTRA_ACCOUNT = "org.blagodarie.ui.symptoms.ACCOUNT";

    private Account mAccount;

    private UUID mIncognitoId;

    private SymptomsViewModel mViewModel;

    private CompositeDisposable mDisposables = new CompositeDisposable();

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
                String message = getString(R.string.err_msg_no_internet_connection);
                if (BuildConfig.DEBUG) {
                    message = throwable.getLocalizedMessage();
                }
                Toast.makeText(getApplicationContext(), message, Toast.LENGTH_LONG).show();
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

    private void updateSymptomCatalogIfNeed (
            @Nullable final List<SymptomGroupWithSymptoms> newSymptomCatalog
    ) {
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
                mViewModel.loadLastValues(mIncognitoId, () -> {
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
                getApplication()
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
                            mRepository.isHaveNotSyncedUserSymptoms(mIncognitoId, symptom.getId()),
                            mRepository.getLatestUserSymptom(mIncognitoId, symptom.getId()),
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
            actionBar.setTitle(spannableTitle);
        }
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
            final String incognitoId = AccountManager.get(this).getUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PRIVATE_KEY);
            //если анонимного ключа не существует
            if (incognitoId != null) {
                //попытаться преобразовать строку в UUID
                try {
                    mIncognitoId = UUID.fromString(incognitoId);
                } catch (IllegalArgumentException e) {
                    errorMessage = getString(R.string.err_msg_incorrect_incognito_id) + e.getLocalizedMessage();
                }
            } else {
                //установить сообщение об ошибке
                errorMessage = getString(R.string.err_msg_incognito_id_is_missing);
            }
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
        final Date currentDate = new Date();

        final UserSymptom userSymptom = new UserSymptom(
                mIncognitoId,
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
        final String incognitoPublicKey = mAccountManager.getUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY);
        if (incognitoPublicKey != null) {
            openWebsite(incognitoPublicKey);
        } else {
            //TODO: временный костыль
            createIncognitoPublicKey();
        }
    }

    private void createIncognitoPublicKey () {
        Log.d(TAG, "createIncognitoPublicKey");
        final String newIncognitoPublicKey = UUID.randomUUID().toString();
        final ServerConnector serverConnector = new ServerConnector(this);
        final IncognitoSignUpFragment.IncognitoSignUpExecutor signUpExecutor = new IncognitoSignUpFragment.IncognitoSignUpExecutor(mIncognitoId.toString(), newIncognitoPublicKey);
        mDisposables.add(
                Observable.
                        fromCallable(() -> serverConnector.execute(signUpExecutor)).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                apiResult -> {
                                    openWebsite(newIncognitoPublicKey);
                                    mAccountManager.setUserData(mAccount, AccountGeneral.USER_DATA_USER_ID, apiResult.getUserId().toString());
                                    mAccountManager.setUserData(mAccount, AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY, newIncognitoPublicKey);
                                },
                                throwable -> Toast.makeText(this, throwable.getMessage(), Toast.LENGTH_LONG).show()
                        )
        );
    }

    private void openWebsite (@NonNull final String incognitoPublicKey) {
        Log.d(TAG, "openWebsite");
        final Intent i = new Intent(Intent.ACTION_VIEW);
        i.setData(Uri.parse(String.format(getString(R.string.website_url), incognitoPublicKey)));
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
                R.string.btn_copy,
                (dialog, which) -> {
                    final ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                    final ClipData clip = ClipData.newPlainText(getString(R.string.txt_log), log);
                    clipboard.setPrimaryClip(clip);
                    Toast.makeText(this, R.string.copied_to_clipboard, Toast.LENGTH_SHORT).show();
                });
        builder.setNeutralButton(
                R.string.btn_share,
                (dialog, which) -> {
                    final Intent sendIntent = new Intent();
                    sendIntent.setAction(Intent.ACTION_SEND);
                    sendIntent.putExtra(Intent.EXTRA_TEXT, (CharSequence) log);
                    sendIntent.putExtra(Intent.EXTRA_SUBJECT, "Благодарие журнал");
                    sendIntent.setType("text/plain");
                    startActivity(Intent.createChooser(sendIntent, getString(R.string.btn_share)));
                });
        builder.create();
        builder.show();
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
