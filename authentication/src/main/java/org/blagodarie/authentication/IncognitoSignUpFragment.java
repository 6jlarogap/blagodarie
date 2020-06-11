package org.blagodarie.authentication;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.databinding.DataBindingUtil;
import androidx.fragment.app.Fragment;

import org.blagodarie.authentication.databinding.IncognitoSignUpFragmentBinding;
import org.blagodarie.server.ServerApiExecutor;
import org.blagodarie.server.ServerConnector;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.UUID;

import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static android.app.Activity.RESULT_OK;
import static org.blagodarie.server.ServerConnector.JSON_TYPE;

public final class IncognitoSignUpFragment
        extends Fragment {

    private static final String TAG = IncognitoSignUpFragment.class.getSimpleName();

    public interface IncognitoSignUpUserAction {

        void createNewIncognitoId ();

        void enterExistingIncognitoId ();

    }

    public static final class IncognitoSignUpExecutor
            implements ServerApiExecutor<IncognitoSignUpExecutor.ApiResult> {

        private static final String TAG = IncognitoSignUpExecutor.class.getSimpleName();

        public static final class ApiResult
                extends ServerApiExecutor.ApiResult {

            @NonNull
            private final Long mUserId;

            ApiResult (
                    @NonNull final Long userId
            ) {
                mUserId = userId;
            }

            @NonNull
            public Long getUserId () {
                return mUserId;
            }
        }

        private static final String JSON_PATTERN = "{\"incognito\":{\"private_key\":\"%s\",\"public_key\":\"%s\"}}";

        @NonNull
        private final String mIncognitoPrivateKey;

        @NonNull
        private final String mIncognitoPublicKey;

        public IncognitoSignUpExecutor (
                @NonNull final String incognitoPrivateKey,
                @NonNull final String incognitoPublicKey
        ) {
            mIncognitoPrivateKey = incognitoPrivateKey;
            mIncognitoPublicKey = incognitoPublicKey;
        }

        @Override
        public IncognitoSignUpExecutor.ApiResult execute (
                @NonNull final String apiBaseUrl,
                @NonNull final OkHttpClient okHttpClient
        ) throws JSONException, IOException {
            Log.d(TAG, "execute");
            Long userId = null;
            final String content = String.format(JSON_PATTERN, mIncognitoPrivateKey, mIncognitoPublicKey);
            Log.d(TAG, "content=" + content);
            final RequestBody body = RequestBody.create(JSON_TYPE, content);
            final Request request = new Request.Builder()
                    .url(apiBaseUrl + "auth/signup/incognito")
                    .post(body)
                    .build();
            final Response response = okHttpClient.newCall(request).execute();
            Log.d(TAG, "response.code=" + response.code());
            if (response.body() != null) {
                final String responseBody = response.body().string();
                Log.d(TAG, "responseBody=" + responseBody);
                if (response.code() == 200) {
                    final JSONObject userJSON = new JSONObject(responseBody);
                    userId = userJSON.getLong("incognito_user_id");
                }
            }
            return new IncognitoSignUpExecutor.ApiResult(userId);

        }
    }

    private CompositeDisposable mDisposables = new CompositeDisposable();

    @Override
    public View onCreateView (
            @NonNull final LayoutInflater inflater,
            final ViewGroup container,
            final Bundle savedInstanceState
    ) {
        Log.d(TAG, "onCreateView");
        final IncognitoSignUpFragmentBinding binding = DataBindingUtil.inflate(inflater, R.layout.incognito_sign_up_fragment, null, false);
        binding.setIncognitoSignUpUserActionListener(new IncognitoSignUpUserAction() {
            @Override
            public void createNewIncognitoId () {
                startSignUp(UUID.randomUUID(), UUID.randomUUID(), (System.currentTimeMillis() / 1000L));
            }

            @Override
            public void enterExistingIncognitoId () {
                showIncognitoIdDialog();
            }
        });
        return binding.getRoot();
    }

    private void showIncognitoIdDialog () {
        Log.e(TAG, "showIncognitoIdDialog");
        final View view = getLayoutInflater().inflate(R.layout.enter_incognito_id_dialog, null, false);

        final ClipboardManager clipboard = (ClipboardManager) requireContext().getSystemService(Context.CLIPBOARD_SERVICE);
        final ClipData clipData = clipboard.getPrimaryClip();
        if (clipData != null) {
            final ClipData.Item item = clipData.getItemAt(0);
            final String incognitoIdString = item.getText().toString();
            try {
                final UUID incognitoId = UUID.fromString(incognitoIdString);
                ((EditText) view.findViewById(R.id.etIncognitoId)).setText(incognitoId.toString());
            } catch (IllegalArgumentException e) {
                Log.e(TAG, "error=" + e);
            }
        }

        final AlertDialog alertDialog = new AlertDialog.
                Builder(requireContext()).
                setView(view).
                setNeutralButton(R.string.btn_back, null).
                setNegativeButton(R.string.btn_paste, null).
                setPositiveButton(R.string.btn_continue, (dialog, which) -> {
                    final String incognitoIdString = ((EditText) view.findViewById(R.id.etIncognitoId)).getText().toString();
                    try {
                        final UUID incognitoId = UUID.fromString(incognitoIdString);
                        startSignUp(incognitoId, UUID.randomUUID(), (System.currentTimeMillis() / 1000L));
                    } catch (IllegalArgumentException e) {
                        Toast.makeText(requireContext(), getString(R.string.err_msg_incorrect_incognito_id), Toast.LENGTH_SHORT).show();
                    }
                }).
                create();

        alertDialog.show();

        alertDialog.getButton(DialogInterface.BUTTON_NEGATIVE).setOnClickListener(v -> {
            if (clipboard.getPrimaryClip() != null) {
                final ClipData.Item item = clipboard.getPrimaryClip().getItemAt(0);
                final String bufferString = item.getText().toString();
                ((EditText) view.findViewById(R.id.etIncognitoId)).setText(bufferString);
            }
        });
    }

    private void startSignUp (
            @NonNull final UUID incognitoPrivateKey,
            @NonNull final UUID incognitoPublicKey,
            @NonNull final Long incognitoPublicKeyTimestamp
    ) {
        Log.d(TAG, "startSignUp");
        final ServerConnector serverConnector = new ServerConnector(requireContext());
        final IncognitoSignUpExecutor signUpExecutor = new IncognitoSignUpExecutor(incognitoPrivateKey.toString(), incognitoPublicKey.toString());
        mDisposables.add(
                Observable.
                        fromCallable(() -> serverConnector.execute(signUpExecutor)).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                apiResult -> createIncognitoAccount(incognitoPrivateKey, incognitoPublicKey, incognitoPublicKeyTimestamp, apiResult.getUserId()),
                                throwable -> Toast.makeText(requireActivity(), throwable.getMessage(), Toast.LENGTH_LONG).show()
                        )
        );
    }

    private void createIncognitoAccount (
            @NonNull final UUID incognitoPrivateKey,
            @NonNull final UUID incognitoPublicKey,
            @NonNull final Long incognitoPublicKeyTimestamp,
            @NonNull final Long userId
    ) {
        Log.d(TAG, "createAccount");
        final String accountName = getString(R.string.incognito_account_name);
        final AccountManager accountManager = AccountManager.get(requireContext());
        final Account account = new Account(accountName, getString(R.string.account_type));
        final Bundle userData = new Bundle();
        userData.putString(AccountGeneral.USER_DATA_USER_ID, userId.toString());
        userData.putString(AccountGeneral.USER_DATA_INCOGNITO_PRIVATE_KEY, incognitoPrivateKey.toString());
        userData.putString(AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY, incognitoPublicKey.toString());
        userData.putString(AccountGeneral.USER_DATA_INCOGNITO_PUBLIC_KEY_TIMESTAMP, incognitoPublicKeyTimestamp.toString());
        accountManager.addAccountExplicitly(account, "", userData);

        final Bundle bundle = new Bundle();
        bundle.putString(AccountManager.KEY_ACCOUNT_NAME, accountName);
        bundle.putString(AccountManager.KEY_ACCOUNT_TYPE, getString(R.string.account_type));
        final Intent res = new Intent();
        res.putExtras(bundle);

        ((AuthenticationActivity) requireActivity()).setAccountAuthenticatorResult(bundle);
        requireActivity().setResult(RESULT_OK, res);
        requireActivity().finish();
    }
}
